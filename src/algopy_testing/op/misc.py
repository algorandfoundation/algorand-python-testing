from __future__ import annotations

import base64
import enum
import json
import typing

from algopy_testing._context_storage import get_account_data, get_test_context
from algopy_testing.constants import (
    MAX_BOX_SIZE,
    MAX_UINT64,
)
from algopy_testing.enums import TransactionType
from algopy_testing.models import Account, Application, Asset
from algopy_testing.models.contract import get_global_states, get_local_states
from algopy_testing.primitives.bytes import Bytes
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.state import GlobalState
from algopy_testing.utils import (
    as_bytes,
    as_int,
)

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.models.contract import ARC4Contract, Contract


class Base64(enum.Enum):
    URLEncoding = 0
    StdEncoding = 1


class EC(enum.StrEnum):
    """Available values for the `EC` enum."""

    BN254g1 = "BN254g1"
    BN254g2 = "BN254g2"
    BLS12_381g1 = "BLS12_381g1"
    BLS12_381g2 = "BLS12_381g2"


def base64_decode(e: Base64, a: Bytes | bytes, /) -> Bytes:
    a_str = _bytes_to_string(a, "illegal base64 data")
    a_str = a_str + "="  # append padding to ensure there is at least one

    result = (
        base64.urlsafe_b64decode(a_str) if e == Base64.URLEncoding else base64.b64decode(a_str)
    )
    return Bytes(result)


def err() -> None:
    raise RuntimeError("err opcode executed")


def _bytes_to_string(a: Bytes | bytes, err_msg: str) -> str:
    a = as_bytes(a)
    try:
        return a.decode()
    except UnicodeDecodeError:
        raise ValueError(err_msg) from None


def _get_app(app: algopy.Application | algopy.UInt64 | int) -> Application:
    if isinstance(app, Application):
        return app
    context = get_test_context()
    if app >= 1001:
        return context.get_application(app)
    txn = context.last_active_txn
    return txn.apps(app)


def _get_account(acc: algopy.Account | algopy.UInt64 | int) -> Account:
    if isinstance(acc, Account):
        return acc
    txn = get_test_context().last_active_txn
    return txn.accounts(acc)


def _get_asset(asset: algopy.Asset | algopy.UInt64 | int) -> Asset:
    if isinstance(asset, Asset):
        return asset
    context = get_test_context()
    if asset >= 1001:
        return context.get_asset(asset)
    txn = context.last_active_txn
    return txn.assets(asset)


class _MultiKeyDict(dict[typing.Any, typing.Any]):
    def __init__(self, items: list[typing.Any]):
        self[""] = ""
        items = [
            (
                (i[0], _MultiKeyDict(i[1]))
                if isinstance(i[1], list) and all(isinstance(j, tuple) for j in i[1])
                else i
            )
            for i in items
        ]
        self._items = items

    def items(self) -> typing.Any:
        return self._items


class JsonRef:
    @staticmethod
    def _load_json(a: Bytes | bytes) -> dict[typing.Any, typing.Any]:
        a = as_bytes(a)
        try:
            # load the whole json payload as an array of key value pairs
            pairs = json.loads(a, object_pairs_hook=lambda x: x)
        except json.JSONDecodeError:
            raise ValueError("error while parsing JSON text, invalid json text") from None

        # turn the pairs into the dictionay for the top level,
        # all other levels remain as key value pairs
        # e.g.
        # input bytes: b'{"key0": 1,"key1": {"key2":2,"key2":"10"}, "key2": "test"}'
        # output dict: {'key0': 1, 'key1': [('key2', 2), ('key2', '10')], 'key2': 'test'}
        result = dict(pairs)
        if len(pairs) != len(result):
            raise ValueError(
                "error while parsing JSON text, invalid json text, duplicate keys found"
            )

        return result

    @staticmethod
    def _raise_key_error(key: str) -> None:
        raise ValueError(f"key {key} not found in JSON text")

    @staticmethod
    def json_string(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, str):
            raise TypeError(f"value must be a string type, not {type(result).__name__!r}")

        # encode with `surrogatepass` to allow sequences such as `\uD800`
        # decode with `replace` to replace with official replacement character `U+FFFD`
        # encode with default settings to get the final bytes result
        result = result.encode("utf-16", "surrogatepass").decode("utf-16", "replace").encode()
        return Bytes(result)

    @staticmethod
    def json_uint64(a: Bytes | bytes, b: Bytes | bytes, /) -> UInt64:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        result = as_int(result, max=MAX_UINT64)
        return UInt64(result)

    @staticmethod
    def json_object(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None
        try:
            # using a custom dict object to allow duplicate keys which is essentially a list
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, list) or not all(isinstance(i, tuple) for i in result):
            raise TypeError(f"value must be an object type, not {type(result).__name__!r}")

        result = _MultiKeyDict(result)
        result_string = json.dumps(result, separators=(",", ":"))
        return Bytes(result_string.encode())


def _gload(a: UInt64 | int, b: UInt64 | int, /) -> Bytes | UInt64:
    context = get_test_context()
    txn = context.get_transaction(int(a))
    try:
        return context.get_scratch_slot(txn, b)
    except IndexError:
        raise ValueError("invalid scratch slot") from None


class _Scratch:
    def load_bytes(self, a: UInt64 | int, /) -> Bytes | UInt64:
        context = get_test_context()
        active_txn = context.last_active_txn
        return _gload(active_txn.group_index, a)

    load_uint64 = load_bytes  # functionally these are the same

    @staticmethod
    def store(a: algopy.UInt64 | int, b: algopy.Bytes | algopy.UInt64 | bytes | int, /) -> None:
        context = get_test_context()
        active_txn = context.last_active_txn
        context.set_scratch_slot(active_txn, a, b)


Scratch = _Scratch()
gload_uint64 = _gload
gload_bytes = _gload


def gaid(a: algopy.UInt64 | int, /) -> algopy.Application:
    # TODO: add tests
    context = get_test_context()
    txn = context.get_transaction(int(a))

    if not txn.type == TransactionType.ApplicationCall:
        raise TypeError(f"Transaction at index {a} is not an ApplicationCallTransaction")

    app_id = txn.created_application_id
    if app_id is None:
        raise ValueError(f"Transaction at index {a} did not create an application")

    return context.get_application(typing.cast(int, app_id))


def balance(a: algopy.Account | algopy.UInt64 | int, /) -> algopy.UInt64:
    # TODO: add tests
    context = get_test_context()
    active_txn = context.last_active_txn

    account = _get_account(a)
    balance = account.balance
    # Deduct the fee for the current transaction
    if account == active_txn.sender:
        fee = active_txn.fee
        assert isinstance(fee, UInt64)
        balance -= fee

    return balance


def min_balance(a: algopy.Account | algopy.UInt64 | int, /) -> algopy.UInt64:
    account = _get_account(a)
    return account.min_balance


def exit(a: UInt64 | int, /) -> typing.Never:  # noqa: A001
    value = UInt64(a) if isinstance(a, int) else a
    # TODO: this should raise a less severe exception and then be caught by the active txn context
    #       and used to determine if the overall txn was successful
    raise RuntimeError(value)


def app_opted_in(
    a: algopy.Account | algopy.UInt64 | int, b: algopy.Application | algopy.UInt64 | int, /
) -> bool:
    account = _get_account(a)
    app = _get_app(b)

    return account.is_opted_in(app)


class _AcctParamsGet:
    def __getattr__(
        self, name: str
    ) -> typing.Callable[
        [algopy.Account | algopy.UInt64 | int], tuple[algopy.UInt64 | algopy.Account, bool]
    ]:
        def get_account_param(
            a: algopy.Account | algopy.UInt64 | int,
        ) -> tuple[algopy.UInt64 | algopy.Account, bool]:
            account = _get_account(a)
            field = name.removeprefix("acct_")
            if field == "auth_addr":
                field = "auth_address"

            return getattr(account, field), account.balance != 0

        return get_account_param


AcctParamsGet = _AcctParamsGet()


class _AssetParamsGet:
    def __getattr__(
        self, name: str
    ) -> typing.Callable[[algopy.Asset | algopy.UInt64 | int], tuple[typing.Any, bool]]:
        def get_asset_param(a: algopy.Asset | algopy.UInt64 | int) -> tuple[typing.Any, bool]:
            try:
                asset = _get_asset(a)
            except ValueError:
                return UInt64(0), False

            short_name = name.removeprefix("asset_")
            try:
                return getattr(asset, short_name), True
            except AttributeError:
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                ) from None

        return get_asset_param


AssetParamsGet = _AssetParamsGet()


class _AssetHoldingGet:
    def _get_asset_holding(
        self,
        account_or_index: algopy.Account | algopy.UInt64 | int,
        asset_or_index: algopy.Asset | algopy.UInt64 | int,
        field: str,
    ) -> tuple[typing.Any, bool]:
        # Resolve account
        context = get_test_context()
        account = _get_account(account_or_index)
        try:
            asset = _get_asset(asset_or_index)
        except ValueError:
            return UInt64(0), False

        account_data = get_account_data(account.public_key)
        asset_balance = account_data.opted_asset_balances.get(asset.id)
        if asset_balance is None:
            return UInt64(0), False

        if field == "balance":
            return asset_balance, True
        elif field == "frozen":
            try:
                asset_data = context.get_asset(asset.id)
            except KeyError:
                return UInt64(0), False
            return asset_data.default_frozen, True
        else:
            raise ValueError(f"Invalid asset holding field: {field}")

    def asset_balance(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Asset | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        balance, exists = self._get_asset_holding(a, b, "balance")
        return balance if exists else UInt64(), exists

    def asset_frozen(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Asset | algopy.UInt64 | int, /
    ) -> tuple[bool, bool]:
        frozen, exists = self._get_asset_holding(a, b, "frozen")
        return bool(frozen), exists


AssetHoldingGet = _AssetHoldingGet()


class _AppParamsGet:
    def _get_app_param_from_ctx(
        self, a: algopy.Application | algopy.UInt64 | int, param: str
    ) -> tuple[typing.Any, bool]:
        try:
            app = _get_app(a)
        except ValueError:
            return UInt64(0), False

        value = getattr(app, param)
        return value, True

    def app_approval_program(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Bytes, bool]:
        return self._get_app_param_from_ctx(a, "approval_program")

    def app_clear_state_program(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Bytes, bool]:
        return self._get_app_param_from_ctx(a, "clear_state_program")

    def app_global_num_uint(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "global_num_uint")

    def app_global_num_byte_slice(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "global_num_bytes")

    def app_local_num_uint(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "local_num_uint")

    def app_local_num_byte_slice(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "local_num_bytes")

    def app_extra_program_pages(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "extra_program_pages")

    def app_creator(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Account, bool]:
        return self._get_app_param_from_ctx(a, "creator")

    def app_address(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Account, bool]:
        return self._get_app_param_from_ctx(a, "address")


AppParamsGet = _AppParamsGet()


# TODO: backing state should be on context rather than contract instances
class _AppLocal:
    def _get_local_state(self, key: bytes) -> algopy.LocalState[typing.Any]:
        test_context = get_test_context()
        if not test_context or not test_context._active_contract:
            raise ValueError("No active contract or test context found.")

        local_states = get_local_states(test_context._active_contract)
        local_state = local_states.get(key)
        if local_state is None:
            key_repr = key.decode("utf-8", errors="backslashreplace")
            raise ValueError(f"Local state with key {key_repr!r} not found")
        return local_state

    def _get_key(self, b: algopy.Bytes | bytes) -> bytes:
        return b.value if isinstance(b, Bytes) else b

    def _parse_local_state_value(self, value: typing.Any) -> algopy.Bytes:
        if hasattr(value, "bytes"):
            value = value.bytes
        assert isinstance(value, Bytes)
        return value

    def get_bytes(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> algopy.Bytes:
        try:
            key = self._get_key(b)
            local_state = self._get_local_state(key)[a]
        except (ValueError, KeyError):
            # returning UInt64 on key error matches AVM behaviour
            return UInt64(0)  # type: ignore[return-value]
        return self._parse_local_state_value(local_state)

    def get_uint64(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> algopy.UInt64:
        try:
            local_state = self._get_local_state(self._get_key(b))
        except (ValueError, KeyError):
            return UInt64(0)
        return local_state.get(a)  # type: ignore[no-any-return]

    def get_ex_bytes(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Application | algopy.UInt64 | int,
        c: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.Bytes, bool]:
        contract = _get_contract(b)  # TODO: check if b might also be an array offset
        local_states = get_local_states(contract)
        local_state = local_states.get(self._get_key(c))

        if local_state and a in local_state and local_state[a] is not None:
            return self._parse_local_state_value(local_state[a]), True
        else:
            # note: returns uint64 when not founds, to match AVM
            return UInt64(), False  # type: ignore[return-value]

    def get_ex_uint64(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Application | algopy.UInt64 | int,
        c: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.UInt64, bool]:
        contract = _get_contract(b)
        local_states = get_local_states(contract)
        local_state = local_states.get(self._get_key(c))

        if local_state and a in local_state:
            return UInt64(local_state[a]), True
        else:
            return UInt64(), False

    def delete(self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /) -> None:
        local_state = self._get_local_state(self._get_key(b))
        del local_state[a]

    def put(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Bytes | bytes,
        c: algopy.Bytes | algopy.UInt64 | bytes | int,
        /,
    ) -> None:
        local_state = self._get_local_state(self._get_key(b))
        local_state[a] = c


def _get_contract(app_id: algopy.Application | algopy.UInt64 | int) -> Contract | ARC4Contract:
    context = get_test_context()

    app = _get_app(app_id)
    contract = context.get_contract_for_app(app)
    if contract is None:
        raise ValueError(f"Contract with app id {app_id} not found")
    return contract


AppLocal = _AppLocal()


class _AppGlobal:
    def _get_global_state(self, key: bytes) -> algopy.GlobalState[typing.Any]:
        test_context = get_test_context()
        if not test_context._active_contract:
            raise ValueError(
                "No active contract found in test context. Make sure you are calling an contract "
                "method inside a test context."
            )

        global_states = get_global_states(test_context._active_contract)
        return global_states[key]

    def _get_key(self, b: algopy.Bytes | bytes) -> bytes:
        return b.value if isinstance(b, Bytes) else b

    def _parse_global_state_value(self, value: typing.Any) -> algopy.Bytes:
        if hasattr(value, "bytes"):
            value = value.bytes
        assert isinstance(value, Bytes)
        return value

    def get_bytes(self, b: algopy.Bytes | bytes, /) -> algopy.Bytes:
        try:
            global_state = self._get_global_state(self._get_key(b))
            return self._parse_global_state_value(global_state.get(b))
        except (ValueError, KeyError):
            return UInt64(0)  # type: ignore[return-value]

    def get_uint64(self, b: algopy.Bytes | bytes, /) -> algopy.UInt64:
        try:
            global_state = self._get_global_state(self._get_key(b))
        except (ValueError, KeyError):
            return UInt64(0)
        value = global_state.get(b)
        # TODO: this might not be a UInt64
        return value  # type: ignore[no-any-return]

    def get_ex_bytes(
        self, a: algopy.Application | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> tuple[algopy.Bytes, bool]:
        contract = _get_contract(a)
        global_states = get_global_states(contract)
        global_state = global_states.get(self._get_key(b))
        # TODO: this is subtly different than AVM behaviour
        value = self._parse_global_state_value(
            global_state if not isinstance(global_state, GlobalState) else global_state.value
        )
        return value or Bytes(), value is not None

    def get_ex_uint64(
        self, a: algopy.Application | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> tuple[algopy.UInt64, bool]:
        contract = _get_contract(a)
        global_state = contract._get_global_state()
        value = global_state.get(self._get_key(b))
        # TODO: this wont work for Application, Asset state
        return UInt64(value or 0), value is None

    def delete(self, b: algopy.Bytes | bytes, /) -> None:
        test_context = get_test_context()
        if not test_context or not test_context._active_contract:
            raise ValueError("No active contract or test context found.")

        delattr(test_context._active_contract, self._get_key(b).decode("utf-8"))

    def put(
        self, a: algopy.Bytes | bytes, b: algopy.Bytes | algopy.UInt64 | bytes | int, /
    ) -> None:
        global_state = self._get_global_state(self._get_key(a))
        global_state.value = b


AppGlobal = _AppGlobal()


def arg(a: UInt64 | int, /) -> Bytes:
    context = get_test_context()
    if not context:
        raise ValueError("Test context is not initialized!")

    return context._active_lsig_args[int(a)]


class _EllipticCurve:
    def __getattr__(self, name: str) -> typing.Any:
        raise NotImplementedError(
            f"EllipticCurve.{name} is currently not available as a native "
            "`algorand-python-testing` type. Use your own preferred testing "
            "framework of choice to mock the behaviour."
        )


EllipticCurve = _EllipticCurve()


class Box:
    @staticmethod
    def create(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> bool:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        size = int(b)
        if not name_bytes or size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        if context.get_box(name_bytes):
            return False
        context.set_box(name_bytes, b"\x00" * size)
        return True

    @staticmethod
    def delete(a: algopy.Bytes | bytes, /) -> bool:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        if context.get_box(name_bytes):
            context.delete_box(name_bytes)
            return True
        return False

    @staticmethod
    def extract(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.UInt64 | int, /
    ) -> algopy.Bytes:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        length = int(c)
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        result = box_content[start : start + length]
        return Bytes(result)

    @staticmethod
    def get(a: algopy.Bytes | bytes, /) -> tuple[algopy.Bytes, bool]:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        box_content = Bytes(context.get_box(name_bytes))
        box_exists = context.box_exists(name_bytes)
        return box_content, box_exists

    @staticmethod
    def length(a: algopy.Bytes | bytes, /) -> tuple[algopy.UInt64, bool]:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        box_content = context.get_box(name_bytes)
        box_exists = context.box_exists(name_bytes)
        return UInt64(len(box_content)), box_exists

    @staticmethod
    def put(a: algopy.Bytes | bytes, b: algopy.Bytes | bytes, /) -> None:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        content = b.value if isinstance(b, Bytes) else b
        existing_content = context.get_box(name_bytes)
        if existing_content and len(existing_content) != len(content):
            raise ValueError("New content length does not match existing box length")
        context.set_box(name_bytes, Bytes(content))

    @staticmethod
    def replace(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.Bytes | bytes, /
    ) -> None:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        new_content = c.value if isinstance(c, Bytes) else c
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if start + len(new_content) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = (
            box_content[:start] + new_content + box_content[start + len(new_content) :]
        )
        context.set_box(name_bytes, updated_content)

    @staticmethod
    def resize(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> None:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        new_size = int(b)
        if not name_bytes or new_size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if new_size > len(box_content):
            updated_content = box_content + b"\x00" * (new_size - len(box_content))
        else:
            updated_content = box_content[:new_size]
        context.set_box(name_bytes, updated_content)

    @staticmethod
    def splice(
        a: algopy.Bytes | bytes,
        b: algopy.UInt64 | int,
        c: algopy.UInt64 | int,
        d: algopy.Bytes | bytes,
        /,
    ) -> None:
        context = get_test_context()
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        delete_count = int(c)
        insert_content = d.value if isinstance(d, Bytes) else d
        box_content = context.get_box(name_bytes)

        if not box_content:
            raise RuntimeError("Box does not exist")

        if start > len(box_content):
            raise ValueError("Start index exceeds box size")

        # Calculate the end index for deletion
        end = min(start + delete_count, len(box_content))

        # Construct the new content
        new_content = box_content[:start] + insert_content + box_content[end:]

        # Adjust the size if necessary
        if len(new_content) > len(box_content):
            # Truncate if the new content is too long
            new_content = new_content[: len(box_content)]
        elif len(new_content) < len(box_content):
            # Pad with zeros if the new content is too short
            new_content += b"\x00" * (len(box_content) - len(new_content))

        # Update the box with the new content
        context.set_box(name_bytes, new_content)
