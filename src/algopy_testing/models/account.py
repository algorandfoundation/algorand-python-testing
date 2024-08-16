from __future__ import annotations

import dataclasses
import typing

import algosdk

from algopy_testing.constants import DEFAULT_ACCOUNT_MIN_BALANCE
from algopy_testing.primitives import Bytes, UInt64
from algopy_testing.protocols import BytesBacked
from algopy_testing.utils import as_bytes

if typing.TYPE_CHECKING:
    import algopy


T = typing.TypeVar("T")


class AccountFields(typing.TypedDict, total=False):
    balance: algopy.UInt64
    min_balance: algopy.UInt64
    auth_address: algopy.Account
    total_num_uint: algopy.UInt64
    total_num_byte_slice: algopy.UInt64
    total_extra_app_pages: algopy.UInt64
    total_apps_created: algopy.UInt64
    total_apps_opted_in: algopy.UInt64
    total_assets_created: algopy.UInt64
    total_assets: algopy.UInt64
    total_boxes: algopy.UInt64
    total_box_bytes: algopy.UInt64


def get_empty_account() -> AccountContextData:
    zero = UInt64()
    return AccountContextData(
        fields={
            "balance": zero,
            "min_balance": UInt64(DEFAULT_ACCOUNT_MIN_BALANCE),
            "auth_address": Account(),
            "total_num_uint": zero,
            "total_num_byte_slice": zero,
            "total_extra_app_pages": zero,
            "total_apps_created": zero,
            "total_apps_opted_in": zero,
            "total_assets_created": zero,
            "total_assets": zero,
            "total_boxes": zero,
            "total_box_bytes": zero,
        }
    )


@dataclasses.dataclass
class AccountContextData:
    """Stores account-related information.

    Attributes:
        opted_asset_balances (dict[int, algopy.UInt64]): Mapping of asset IDs to balances.
        opted_apps (dict[int, algopy.UInt64]): Mapping of application IDs to instances.
        fields (AccountFields): Additional account fields.
    """

    opted_asset_balances: dict[algopy.UInt64, algopy.UInt64] = dataclasses.field(
        default_factory=dict
    )
    opted_apps: dict[algopy.UInt64, algopy.Application] = dataclasses.field(default_factory=dict)
    fields: AccountFields = dataclasses.field(default_factory=AccountFields)  # type: ignore[arg-type]


class Account(BytesBacked):
    def __init__(self, value: str | Bytes = algosdk.constants.ZERO_ADDRESS, /):
        if not isinstance(value, str | Bytes):
            raise TypeError("Invalid value for Account")

        self._public_key: bytes = (
            algosdk.encoding.decode_address(value) if isinstance(value, str) else value.value
        )

    @property
    def data(self) -> AccountContextData:
        from algopy_testing._context_helpers import lazy_context

        return lazy_context.ledger.account_data[self.public_key]

    @property
    def balance(self) -> algopy.UInt64:
        return self.data.fields["balance"]

    @property
    def min_balance(self) -> algopy.UInt64:
        return self.data.fields["min_balance"]

    def is_opted_in(self, asset_or_app: algopy.Asset | algopy.Application, /) -> bool:
        from algopy_testing.models import Application, Asset

        if isinstance(asset_or_app, Asset):
            return asset_or_app.id in self.data.opted_asset_balances
        elif isinstance(asset_or_app, Application):
            return asset_or_app.id in self.data.opted_apps

        raise TypeError(
            "Invalid `asset_or_app` argument type. Must be an `algopy.Asset` or "
            "`algopy.Application` instance."
        )

    @classmethod
    def from_bytes(cls, value: algopy.Bytes | bytes) -> typing.Self:
        # NOTE: AVM does not perform any validation beyond type.
        validated_value = as_bytes(value)
        return cls(Bytes(validated_value))

    @property
    def bytes(self) -> Bytes:
        return Bytes(self._public_key)

    @property
    def public_key(self) -> str:
        return algosdk.encoding.encode_address(self._public_key)  # type: ignore[no-any-return]

    def __getattr__(self, name: str) -> typing.Any:
        try:
            return self.data.fields[name]  # type: ignore[literal-required]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            ) from None

    def __repr__(self) -> str:
        return self.public_key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Account | str):
            raise TypeError("Invalid value for Account")
        if isinstance(other, Account):
            return self._public_key == other._public_key
        return self._public_key == as_bytes(other)

    def __bool__(self) -> bool:
        return bool(self._public_key) and self._public_key != algosdk.encoding.decode_address(
            algosdk.constants.ZERO_ADDRESS
        )

    def __hash__(self) -> int:
        return hash(self._public_key)
