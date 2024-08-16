from __future__ import annotations

import typing

from algopy_testing._context_helpers import lazy_context
from algopy_testing.constants import (
    MAX_BOX_SIZE,
)
from algopy_testing.enums import TransactionType
from algopy_testing.models import Account, Application, Asset
from algopy_testing.primitives.bytes import Bytes
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import raise_mocked_function_error

if typing.TYPE_CHECKING:
    import algopy


def err() -> None:
    raise RuntimeError("err opcode executed")


def _get_app(app: algopy.Application | algopy.UInt64 | int) -> Application:
    if isinstance(app, Application):
        return app
    if app >= 1001:
        return lazy_context.ledger.get_application(app)
    txn = lazy_context.active_group.active_txn
    return txn.apps(app)


def _get_account(acc: algopy.Account | algopy.UInt64 | int) -> Account:
    if isinstance(acc, Account):
        return acc
    txn = lazy_context.active_group.active_txn
    return txn.accounts(acc)


def _get_asset(asset: algopy.Asset | algopy.UInt64 | int) -> Asset:
    if isinstance(asset, Asset):
        return asset
    if asset >= 1001:
        return lazy_context.ledger.get_asset(asset)
    txn = lazy_context.active_group.active_txn
    return txn.assets(asset)


def _get_bytes(b: algopy.Bytes | bytes) -> bytes:
    return b.value if isinstance(b, Bytes) else b


def _gload(a: UInt64 | int, b: UInt64 | int, /) -> Bytes | UInt64:
    txn = lazy_context.active_group.get_txn(a)
    try:
        return txn.get_scratch_slot(b)
    except IndexError:
        raise ValueError("invalid scratch slot") from None


class _Scratch:
    def load_bytes(self, a: UInt64 | int, /) -> Bytes | UInt64:
        active_txn = lazy_context.active_group.active_txn
        return _gload(active_txn.group_index, a)

    load_uint64 = load_bytes  # functionally these are the same

    @staticmethod
    def store(a: algopy.UInt64 | int, b: algopy.Bytes | algopy.UInt64 | bytes | int, /) -> None:
        active_txn = lazy_context.active_group.active_txn
        active_txn.set_scratch_slot(a, b)


Scratch = _Scratch()
gload_uint64 = _gload
gload_bytes = _gload


def gaid(a: algopy.UInt64 | int, /) -> algopy.UInt64:
    # TODO: 1.0 add tests
    group = lazy_context.active_group
    if a >= group.active_txn.group_index:
        raise ValueError("can only get id's for transactions earlier in the group")

    txn = group.get_txn(a)
    if txn.type == TransactionType.ApplicationCall:
        return txn.created_app.id
    elif txn.type == TransactionType.AssetConfig:
        return txn.created_asset.id
    else:
        raise ValueError(f"transaction at index {a} is not an Application Call or Asset Config")


def balance(a: algopy.Account | algopy.UInt64 | int, /) -> algopy.UInt64:
    # TODO: 1.0 add tests
    active_txn = lazy_context.active_group.active_txn

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


def exit(_a: UInt64 | int, /) -> typing.Never:  # noqa: A001
    raise_mocked_function_error("exit")


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
        account = _get_account(account_or_index)
        try:
            asset = _get_asset(asset_or_index)
        except ValueError:
            return UInt64(0), False

        account_data = lazy_context.get_account_data(account.public_key)
        asset_balance = account_data.opted_asset_balances.get(asset.id)
        if asset_balance is None:
            return UInt64(0), False

        if field == "balance":
            return asset_balance, True
        elif field == "frozen":
            try:
                asset_data = lazy_context.ledger.get_asset(asset.id)
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


class _AppLocal:
    def get_bytes(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> algopy.Bytes | algopy.UInt64:
        return self.get_ex_bytes(a, 0, b)[0]

    get_uint64 = get_bytes

    def get_ex_bytes(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Application | algopy.UInt64 | int,
        c: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.Bytes | algopy.UInt64, bool]:
        account = _get_account(a)
        app = _get_app(b)
        app_data = lazy_context.get_app_data(app)
        key = _get_bytes(c)
        try:
            native = app_data.get_local_state(account, key)
        except KeyError:
            # note: returns uint64 when not found, to match AVM
            value: Bytes | UInt64 = UInt64()
            found = False
        else:
            value = UInt64(native) if isinstance(native, int) else Bytes(native)
            found = True
        return value, found

    get_ex_uint64 = get_ex_bytes

    def delete(self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /) -> None:
        app_data = lazy_context.get_app_data(0)
        account = _get_account(a)
        key = _get_bytes(b)
        app_data.set_local_state(account, key, None)

    def put(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Bytes | bytes,
        c: algopy.Bytes | algopy.UInt64 | bytes | int,
        /,
    ) -> None:
        app_data = lazy_context.get_app_data(0)
        account = _get_account(a)
        key = _get_bytes(b)
        value = c.value if isinstance(c, Bytes | UInt64) else c
        app_data.set_local_state(account, key, value)


AppLocal = _AppLocal()


class _AppGlobal:
    def get_bytes(self, a: algopy.Bytes | bytes, /) -> algopy.Bytes | algopy.UInt64:
        return self.get_ex_bytes(0, a)[0]

    get_uint64 = get_bytes

    def get_ex_bytes(
        self,
        a: algopy.Application | algopy.UInt64 | int,
        b: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.Bytes | algopy.UInt64, bool]:
        app = _get_app(a)
        app_data = lazy_context.get_app_data(app)
        key = _get_bytes(b)
        try:
            native = app_data.get_global_state(key)
        except KeyError:
            # note: returns uint64 when not found, to match AVM
            value: Bytes | UInt64 = UInt64()
            found = False
        else:
            value = UInt64(native) if isinstance(native, int) else Bytes(native)
            found = True
        return value, found

    get_ex_uint64 = get_ex_bytes

    def delete(self, a: algopy.Bytes | bytes, /) -> None:
        app_data = lazy_context.get_app_data(0)
        key = _get_bytes(a)
        app_data.set_global_state(key, None)

    def put(
        self,
        a: algopy.Bytes | bytes,
        b: algopy.Bytes | algopy.UInt64 | bytes | int,
        /,
    ) -> None:
        app_data = lazy_context.get_app_data(0)
        key = _get_bytes(a)
        value = b.value if isinstance(b, Bytes | UInt64) else b
        app_data.set_global_state(key, value)


AppGlobal = _AppGlobal()


def arg(a: UInt64 | int, /) -> Bytes:
    return lazy_context.value._active_lsig_args[int(a)]


class Box:
    @staticmethod
    def create(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> bool:
        name_bytes = a.value if isinstance(a, Bytes) else a
        size = int(b)
        if not name_bytes or size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        if lazy_context.ledger.get_box(name_bytes):
            return False
        lazy_context.ledger.set_box(name_bytes, b"\x00" * size)
        return True

    @staticmethod
    def delete(a: algopy.Bytes | bytes, /) -> bool:
        name_bytes = a.value if isinstance(a, Bytes) else a
        if lazy_context.ledger.get_box(name_bytes):
            lazy_context.ledger.delete_box(name_bytes)
            return True
        return False

    @staticmethod
    def extract(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.UInt64 | int, /
    ) -> algopy.Bytes:
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        length = int(c)
        box_content = lazy_context.ledger.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        result = box_content[start : start + length]
        return Bytes(result)

    @staticmethod
    def get(a: algopy.Bytes | bytes, /) -> tuple[algopy.Bytes, bool]:
        name_bytes = a.value if isinstance(a, Bytes) else a
        box_content = Bytes(lazy_context.ledger.get_box(name_bytes))
        box_exists = lazy_context.ledger.box_exists(name_bytes)
        return box_content, box_exists

    @staticmethod
    def length(a: algopy.Bytes | bytes, /) -> tuple[algopy.UInt64, bool]:
        name_bytes = a.value if isinstance(a, Bytes) else a
        box_content = lazy_context.ledger.get_box(name_bytes)
        box_exists = lazy_context.ledger.box_exists(name_bytes)
        return UInt64(len(box_content)), box_exists

    @staticmethod
    def put(a: algopy.Bytes | bytes, b: algopy.Bytes | bytes, /) -> None:
        name_bytes = a.value if isinstance(a, Bytes) else a
        content = b.value if isinstance(b, Bytes) else b
        existing_content = lazy_context.ledger.get_box(name_bytes)
        if existing_content and len(existing_content) != len(content):
            raise ValueError("New content length does not match existing box length")
        lazy_context.ledger.set_box(name_bytes, Bytes(content))

    @staticmethod
    def replace(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.Bytes | bytes, /
    ) -> None:
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        new_content = c.value if isinstance(c, Bytes) else c
        box_content = lazy_context.ledger.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if start + len(new_content) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = (
            box_content[:start] + new_content + box_content[start + len(new_content) :]
        )
        lazy_context.ledger.set_box(name_bytes, updated_content)

    @staticmethod
    def resize(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> None:
        name_bytes = a.value if isinstance(a, Bytes) else a
        new_size = int(b)
        if not name_bytes or new_size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        box_content = lazy_context.ledger.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if new_size > len(box_content):
            updated_content = box_content + b"\x00" * (new_size - len(box_content))
        else:
            updated_content = box_content[:new_size]
        lazy_context.ledger.set_box(name_bytes, updated_content)

    @staticmethod
    def splice(
        a: algopy.Bytes | bytes,
        b: algopy.UInt64 | int,
        c: algopy.UInt64 | int,
        d: algopy.Bytes | bytes,
        /,
    ) -> None:
        name_bytes = a.value if isinstance(a, Bytes) else a
        start = int(b)
        delete_count = int(c)
        insert_content = d.value if isinstance(d, Bytes) else d
        box_content = lazy_context.ledger.get_box(name_bytes)

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
        lazy_context.ledger.set_box(name_bytes, new_content)
