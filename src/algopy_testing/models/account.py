from __future__ import annotations

import dataclasses
import typing

import algosdk

import algopy_testing
from algopy_testing.primitives.bytes import Bytes
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


@dataclasses.dataclass
class AccountContextData:
    """
    Stores account-related information.

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


class Account:
    _public_key: bytes

    def __init__(self, value: str | Bytes = algosdk.constants.ZERO_ADDRESS, /):
        if not isinstance(value, str | Bytes):
            raise TypeError("Invalid value for Account")

        public_key = (
            algosdk.encoding.decode_address(value) if isinstance(value, str) else value.value
        )
        self._public_key = public_key

    @property
    def data(self) -> AccountContextData:
        context = algopy_testing.get_test_context()
        return context._account_data[self.public_key]

    def is_opted_in(self, asset_or_app: algopy.Asset | algopy.Application, /) -> bool:
        if isinstance(asset_or_app, algopy_testing.Asset):
            return asset_or_app.id in self.data.opted_asset_balances
        elif isinstance(asset_or_app, algopy_testing.Application):
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

    def __getattr__(self, name: str) -> object:
        # When accessing via AcctParamsGet, passed key differ from the one defined on account model
        # hence the mapping
        name = name if name != "auth_addr" else "auth_address"

        return_value = self.data.fields.get(name)
        if return_value is None:
            raise AttributeError(
                f"The value for '{name}' in the test context is None. "
                f"Make sure to patch the global field '{name}' using your `AlgopyTestContext` "
                "instance."
            )

        return return_value

    def __repr__(self) -> str:
        return str(algosdk.encoding.encode_address(self._public_key))

    def __str__(self) -> str:
        return str(algosdk.encoding.encode_address(self._public_key))

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
