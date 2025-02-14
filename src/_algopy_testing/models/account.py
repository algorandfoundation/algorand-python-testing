from __future__ import annotations

import dataclasses
import typing

import algosdk

from _algopy_testing.constants import DEFAULT_ACCOUNT_MIN_BALANCE
from _algopy_testing.primitives import Bytes, UInt64
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import as_bytes

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
    incentive_eligible: bool
    last_heartbeat: algopy.UInt64
    last_proposed: algopy.UInt64


def get_empty_account() -> AccountContextData:
    return AccountContextData(
        fields={
            "balance": UInt64(),
            "min_balance": UInt64(DEFAULT_ACCOUNT_MIN_BALANCE),
            "auth_address": Account(),
            "total_num_uint": UInt64(),
            "total_num_byte_slice": UInt64(),
            "total_extra_app_pages": UInt64(),
            "total_apps_created": UInt64(),
            "total_apps_opted_in": UInt64(),
            "total_assets_created": UInt64(),
            "total_assets": UInt64(),
            "total_boxes": UInt64(),
            "total_box_bytes": UInt64(),
            "incentive_eligible": False,
            "last_heartbeat": UInt64(),
            "last_proposed": UInt64(),
        },
    )


@dataclasses.dataclass
class AssetHolding:
    balance: algopy.UInt64
    frozen: bool


@dataclasses.dataclass
class AccountContextData:
    """Stores account-related information.

    Attributes:
        opted_assets (dict[int, AssetHolding]): Mapping of asset IDs to holdings.
        opted_apps (dict[int, algopy.Application]): Mapping of application IDs to instances.
        fields (AccountFields): Additional account fields.
    """

    opted_assets: dict[int, AssetHolding] = dataclasses.field(default_factory=dict)
    opted_apps: dict[int, algopy.Application] = dataclasses.field(default_factory=dict)
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
        from _algopy_testing.context_helpers import lazy_context

        return lazy_context.get_account_data(self.public_key)

    @property
    def balance(self) -> algopy.UInt64:
        return self.data.fields["balance"]

    @property
    def min_balance(self) -> algopy.UInt64:
        return self.data.fields["min_balance"]

    def is_opted_in(self, asset_or_app: algopy.Asset | algopy.Application, /) -> bool:
        from _algopy_testing.models import Application, Asset

        if isinstance(asset_or_app, Asset):
            return asset_or_app.id in self.data.opted_assets
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
        if isinstance(other, Account):
            return self._public_key == other._public_key
        elif isinstance(other, str):
            return self.public_key == other
        else:
            return NotImplemented

    def __bool__(self) -> bool:
        return bool(self._public_key) and self._public_key != algosdk.encoding.decode_address(
            algosdk.constants.ZERO_ADDRESS
        )

    def __hash__(self) -> int:
        return hash(self._public_key)
