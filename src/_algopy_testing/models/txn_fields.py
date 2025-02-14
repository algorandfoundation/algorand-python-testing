from __future__ import annotations

import abc
import typing

from _algopy_testing.constants import MAX_BYTES_SIZE
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.enums import OnCompleteAction, TransactionType
from _algopy_testing.models import Account, Application, Asset
from _algopy_testing.primitives import Bytes, String, UInt64
from _algopy_testing.utils import generate_random_bytes32

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    import algopy


# NOTE: type and tx_id are excluded, first is inferred from other txn related classes
# the second can't be meaningfully inferred in unit testing context
class TransactionBaseFields(typing.TypedDict, total=False):
    sender: algopy.Account
    fee: algopy.UInt64
    first_valid: algopy.UInt64
    first_valid_time: algopy.UInt64
    last_valid: algopy.UInt64
    note: algopy.Bytes
    lease: algopy.Bytes
    rekey_to: algopy.Account


class AssetTransferFields(TransactionBaseFields, total=False):
    xfer_asset: algopy.Asset
    asset_amount: algopy.UInt64
    asset_sender: algopy.Account
    asset_receiver: algopy.Account
    asset_close_to: algopy.Account


class PaymentFields(TransactionBaseFields, total=False):
    receiver: algopy.Account
    amount: algopy.UInt64
    close_remainder_to: algopy.Account


class AssetFreezeFields(TransactionBaseFields, total=False):
    freeze_asset: algopy.Asset
    freeze_account: algopy.Account
    frozen: bool


class AssetConfigFields(TransactionBaseFields, total=False):
    config_asset: algopy.Asset
    total: algopy.UInt64
    decimals: algopy.UInt64
    default_frozen: bool
    unit_name: algopy.Bytes
    asset_name: algopy.Bytes
    url: algopy.Bytes
    metadata_hash: algopy.Bytes
    manager: algopy.Account
    reserve: algopy.Account
    freeze: algopy.Account
    clawback: algopy.Account
    created_asset: algopy.Asset


class ActiveTransactionFields(TransactionBaseFields, total=False):
    on_completion: algopy.OnCompleteAction
    app_args: Sequence[algopy.Bytes]
    accounts: Sequence[algopy.Account]
    assets: Sequence[algopy.Asset]
    apps: Sequence[algopy.Application]


class ApplicationCallFields(ActiveTransactionFields, total=False):
    app_id: algopy.Application
    global_num_uint: algopy.UInt64
    global_num_bytes: algopy.UInt64
    local_num_uint: algopy.UInt64
    local_num_bytes: algopy.UInt64
    extra_program_pages: algopy.UInt64
    logs: Sequence[algopy.Bytes]
    approval_program: Sequence[algopy.Bytes]
    clear_state_program: Sequence[algopy.Bytes]
    created_app: algopy.Application


class KeyRegistrationFields(TransactionBaseFields, total=False):
    vote_key: algopy.Bytes
    selection_key: algopy.Bytes
    vote_first: algopy.UInt64
    vote_last: algopy.UInt64
    vote_key_dilution: algopy.UInt64
    non_participation: bool
    state_proof_key: algopy.Bytes


class TransactionFields(  # type: ignore[misc]
    PaymentFields,
    KeyRegistrationFields,
    AssetConfigFields,
    AssetTransferFields,
    AssetFreezeFields,
    ApplicationCallFields,
    total=False,
):
    type: algopy.TransactionType


_FIELD_TYPES = {
    "sender": Account,
    "rekey_to": Account,
    "asset_sender": Account,
    "asset_receiver": Account,
    "asset_close_to": Account,
    "receiver": Account,
    "close_remainder_to": Account,
    "manager": Account,
    "reserve": Account,
    "freeze": Account,
    "clawback": Account,
    "app_id": Application,
    "xfer_asset": Asset,
    "freeze_asset": Asset,
    "freeze_account": Account,
    "config_asset": Asset,
    "frozen": bool,
    "default_frozen": bool,
    "non_participation": bool,
    "unit_name": Bytes,
    "asset_name": Bytes,
    "url": Bytes,
    "metadata_hash": Bytes,
    "note": Bytes,
    "lease": Bytes,
    "vote_key": Bytes,
    "selection_key": Bytes,
    "state_proof_key": Bytes,
    "type": TransactionType,
    "on_completion": OnCompleteAction,
    "fee": UInt64,
    "first_valid": UInt64,
    "first_valid_time": UInt64,
    "last_valid": UInt64,
    "asset_amount": UInt64,
    "amount": UInt64,
    "total": UInt64,
    "decimals": UInt64,
    "global_num_uint": UInt64,
    "global_num_bytes": UInt64,
    "local_num_uint": UInt64,
    "local_num_bytes": UInt64,
    "extra_program_pages": UInt64,
    "vote_first": UInt64,
    "vote_last": UInt64,
    "vote_key_dilution": UInt64,
    "created_app": Application,
    "created_asset": Asset,
}


def get_txn_defaults() -> Mapping[str, typing.Any]:
    fields = dict[str, typing.Any]()
    for field, factory in _FIELD_TYPES.items():
        fields[field] = factory()

    # a random 32 byte hash is as good as a real txn id here
    fields["txn_id"] = Bytes(generate_random_bytes32())

    # logs intentionally omitted, as they can fall back to application mocked logs
    for field in (
        "app_args",
        "accounts",
        "assets",
        "apps",
    ):
        fields[field] = ()
    for field in (
        "approval_program",
        "clear_state_program",
    ):
        fields[field] = (Bytes(),)
    return fields


class TransactionFieldsGetter(abc.ABC):
    """Base transaction type used across both inner and global transactions
    implementations."""

    @property
    @abc.abstractmethod
    def fields(self) -> dict[str, object]:
        raise NotImplementedError

    # explicitly define some properties commonly accessed by algopy testing
    @property
    def amount(self) -> algopy.UInt64:
        return self.fields["amount"]  # type: ignore[return-value]

    @property
    def app_id(self) -> algopy.Application:
        return self.fields["app_id"]  # type: ignore[return-value]

    @property
    def sender(self) -> algopy.Account:
        return self.fields["sender"]  # type: ignore[return-value]

    @property
    def txn_id(self) -> algopy.Bytes:
        return self.fields["txn_id"]  # type: ignore[return-value]

    @property
    def group_index(self) -> algopy.UInt64:
        return self.fields["group_index"]  # type: ignore[return-value]

    @property
    def _accounts(self) -> Sequence[algopy.Account]:
        return self.fields["accounts"]  # type: ignore[return-value]

    @property
    def num_accounts(self) -> algopy.UInt64:
        return UInt64(len(self._accounts))

    @property
    def accounts(self) -> Callable[[algopy.UInt64 | int], algopy.Account]:
        return _create_array_accessor(self._accounts)

    @property
    def _assets(self) -> Sequence[algopy.Asset]:
        return self.fields["assets"]  # type: ignore[return-value]

    @property
    def num_assets(self) -> algopy.UInt64:
        return UInt64(len(self._assets))

    @property
    def assets(self) -> Callable[[algopy.UInt64 | int], algopy.Asset]:
        return _create_array_accessor(self._assets)

    @property
    def _apps(self) -> Sequence[algopy.Application]:
        return self.fields["apps"]  # type: ignore[return-value]

    @property
    def num_apps(self) -> algopy.UInt64:
        return UInt64(len(self._apps))

    @property
    def apps(self) -> Callable[[algopy.UInt64 | int], algopy.Application]:
        return _create_array_accessor(self._apps)

    @property
    def _app_args(self) -> Sequence[algopy.Bytes]:
        return self.fields["app_args"]  # type: ignore[return-value]

    @property
    def num_app_args(self) -> algopy.UInt64:
        return UInt64(len(self._app_args))

    @property
    def app_args(self) -> Callable[[algopy.UInt64 | int], algopy.Bytes]:
        return _create_array_accessor(self._app_args)

    @property
    def type(self) -> algopy.TransactionType:
        return self.fields["type"]  # type: ignore[return-value]

    @property
    def type_bytes(self) -> algopy.Bytes:
        return Bytes(self.type.txn_name.encode("utf8"))

    @property
    def approval_program(self) -> algopy.Bytes:
        pages = self._approval_program_pages
        return pages[0] if pages else Bytes()

    @property
    def _approval_program_pages(self) -> Sequence[algopy.Bytes]:
        return self.fields["approval_program"]  # type: ignore[return-value]

    @property
    def approval_program_pages(self) -> Callable[[algopy.UInt64 | int], algopy.Bytes]:
        return _create_array_accessor(self._approval_program_pages)

    @property
    def num_approval_program_pages(self) -> algopy.UInt64:
        return UInt64(len(self._approval_program_pages))

    @property
    def clear_state_program(self) -> algopy.Bytes:
        pages = self._clear_state_program_pages
        return pages[0] if pages else Bytes()

    @property
    def _clear_state_program_pages(self) -> Sequence[algopy.Bytes]:
        return self.fields["clear_state_program"]  # type: ignore[return-value]

    @property
    def clear_state_program_pages(self) -> Callable[[algopy.UInt64 | int], algopy.Bytes]:
        return _create_array_accessor(self._clear_state_program_pages)

    @property
    def num_clear_state_program_pages(self) -> algopy.UInt64:
        return UInt64(len(self._clear_state_program_pages))

    @property
    def on_completion(self) -> algopy.OnCompleteAction:
        return self.fields["on_completion"]  # type: ignore[return-value]

    @property
    def created_app(self) -> algopy.Application:
        return self.fields["created_app"]  # type: ignore[return-value]

    @property
    def created_asset(self) -> algopy.Asset:
        return self.fields["created_asset"]  # type: ignore[return-value]

    @property
    def _logs(self) -> Sequence[algopy.Bytes]:
        try:
            logs: Sequence[algopy.Bytes] = self.fields["logs"]  # type: ignore[assignment]
        except KeyError:
            # if no txn logs, fall back to logs on app
            app_data = lazy_context.get_app_data(self.app_id)
            logs = list(map(Bytes, app_data.app_logs))
        return logs

    @property
    def last_log(self) -> algopy.Bytes:
        try:
            return self._logs[-1]
        except IndexError:
            return Bytes(b"")

    @property
    def num_logs(self) -> algopy.UInt64:
        return UInt64(len(self._logs))

    @property
    def logs(self) -> Callable[[algopy.UInt64 | int], algopy.Bytes]:
        return _create_array_accessor(self._logs)

    def __getattr__(self, name: str) -> object:
        try:
            return self.fields[name]
        except KeyError:
            raise AttributeError(f"'{type(self)}' object has no attribute '{name}'") from None


def narrow_field_type(field: str, value: object) -> object:  # noqa: PLR0911
    if field == "app_args":
        if not isinstance(value, tuple):
            raise TypeError("unexpected type")
        return tuple(map(_as_bytes_allow_bytes_backed, value))
    if field == "assets":
        return _narrow_tuple(value, Asset)
    if field == "accounts":
        return _narrow_tuple(value, Account)
    if field == "applications":
        return _narrow_tuple(value, Application)
    if field in ("approval_program", "clear_state_program"):
        pages = _narrow_tuple(value, Bytes)
        pages = combine_into_max_byte_pages(pages)
        return pages

    try:
        field_type = _FIELD_TYPES[field]
    except KeyError:
        return value
    narrow = _NARROW_TYPE_MAP[field_type]
    return narrow(value)


def combine_into_max_byte_pages(pages: Sequence[Bytes]) -> Sequence[Bytes]:
    raw_pages = b"".join(page.value for page in pages)
    total_pages = (len(raw_pages) + MAX_BYTES_SIZE - 1) // MAX_BYTES_SIZE
    full_pages = [
        raw_pages[page * MAX_BYTES_SIZE : (page + 1) * MAX_BYTES_SIZE]
        for page in range(total_pages)
    ]
    return tuple(Bytes(page) for page in full_pages)


def _as_application(value: typing.Any) -> Application:
    match value:
        case int(int_id) | UInt64(value=int_id):
            return Application(int_id)
        case Application() as app:
            return app
        case _:
            raise TypeError("unexpected type")


def _as_asset(value: typing.Any) -> Asset:
    match value:
        case int(int_id) | UInt64(value=int_id):
            return Asset(int_id)
        case Asset() as asset:
            return asset
        case _:
            raise TypeError("unexpected type")


def _as_account(value: typing.Any) -> Account:
    match value:
        case str(address):
            return Account(address)
        case Account() as acc:
            return acc
        case _:
            raise TypeError("unexpected type")


def _as_bytes(value: typing.Any) -> Bytes:
    match value:
        case bytes(bytes_val):
            return Bytes(bytes_val)
        case str(str_val):
            return Bytes(str_val.encode("utf8"))
        case String() as string:
            return string.bytes
        case Bytes() as bites:
            return bites
        case _:
            raise TypeError("unexpected type")


def _as_bytes_allow_bytes_backed(value: typing.Any) -> Bytes:
    from _algopy_testing.arc4 import Struct
    from _algopy_testing.protocols import BytesBacked

    match value:
        case BytesBacked() as bb:
            return bb.bytes
        case Struct() as struct:
            return struct.bytes
        case _:
            return _as_bytes(value)


def _as_uint64(value: typing.Any) -> UInt64:
    match value:
        case int(int_val):
            return UInt64(int_val)
        case UInt64() as uint64:
            return uint64
        case _:
            raise TypeError("unexpected type")


def _as_on_complete_action(value: typing.Any) -> OnCompleteAction:
    match value:
        case int(int_val) | UInt64(value=int_val) | OnCompleteAction(value=int_val):
            return OnCompleteAction(int_val)
        case _:
            raise TypeError("unexpected type")


def _as_transaction_type(value: typing.Any) -> TransactionType:
    match value:
        case int(int_val) | UInt64(value=int_val) | TransactionType(value=int_val):
            return TransactionType(int_val)
        case _:
            raise TypeError("unexpected type")


def _as_bool(value: typing.Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError("unexpected type")
    return value


def _narrow_tuple(value: typing.Any, item_type: type) -> Sequence[typing.Any]:
    if not isinstance(value, tuple):
        raise TypeError("unexpected type")

    narrow = _NARROW_TYPE_MAP[item_type]
    return tuple(map(narrow, value))


_T = typing.TypeVar("_T")


def _create_array_accessor(values: Sequence[_T]) -> Callable[[algopy.UInt64 | int], _T]:
    def wrapper(index: algopy.UInt64 | int) -> _T:
        try:
            return values[int(index)]
        except IndexError:
            raise ValueError("invalid array index") from None

    return wrapper


_NARROW_TYPE_MAP = {
    Application: _as_application,
    Asset: _as_asset,
    Account: _as_account,
    Bytes: _as_bytes,
    UInt64: _as_uint64,
    OnCompleteAction: _as_on_complete_action,
    TransactionType: _as_transaction_type,
    bool: _as_bool,
}


__all__ = [
    "ApplicationCallFields",
    "AssetConfigFields",
    "AssetFreezeFields",
    "AssetTransferFields",
    "KeyRegistrationFields",
    "PaymentFields",
    "TransactionFields",
    "TransactionFieldsGetter",
    "get_txn_defaults",
    "narrow_field_type",
]
