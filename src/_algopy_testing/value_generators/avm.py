from __future__ import annotations

import secrets
import string
import typing
from collections import ChainMap

import algosdk

import _algopy_testing
from _algopy_testing.constants import (
    ALWAYS_APPROVE_TEAL_PROGRAM,
    MAX_BYTES_SIZE,
    MAX_UINT64,
    MAX_UINT512,
)
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.models.account import AccountFields
from _algopy_testing.models.application import ApplicationContextData, ApplicationFields
from _algopy_testing.models.asset import AssetFields
from _algopy_testing.utils import generate_random_int

if typing.TYPE_CHECKING:
    import algopy


class AVMValueGenerator:
    """Factory for generating test data for AVM abstractions (uint64, bytes, string,
    accounts, assets and applications)."""

    def uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.UInt64:
        """Generate a random UInt64 value within a specified range.

        :param min_value: Minimum value. Defaults to 0.
        :param max_value: Maximum value. Defaults to MAX_UINT64.
        :returns: The randomly generated UInt64 value.
        :raises ValueError: If `max_value` exceeds MAX_UINT64 or `min_value` exceeds `max_value`.
        """
        if max_value > MAX_UINT64:
            raise ValueError("max_value must be less than or equal to MAX_UINT64")
        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")
        if min_value < 0 or max_value < 0:
            raise ValueError("min_value and max_value must be greater than or equal to 0")

        return _algopy_testing.UInt64(generate_random_int(min_value, max_value))

    def biguint(self, min_value: int = 0) -> algopy.BigUInt:
        """Generate a random BigUInt value within a specified range.

        :param min_value: Minimum value. Defaults to 0.
        :returns: The randomly generated BigUInt value.
        :raises ValueError: If `min_value` is negative.
        """
        if min_value < 0:
            raise ValueError("min_value must be greater than or equal to 0")

        return _algopy_testing.BigUInt(generate_random_int(min_value, MAX_UINT512))

    def string(self, length: int = MAX_BYTES_SIZE) -> algopy.String:
        """Generate a random string of a specified length.

        :param length: int:  (Default value = MAX_BYTES_SIZE)
        :returns: The randomly generated string.
        """
        return _algopy_testing.String(
            "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
        )

    def account(
        self,
        address: str | None = None,
        opted_asset_balances: (
            dict[algopy.Asset | algopy.UInt64 | int, algopy.UInt64 | int] | None
        ) = None,
        opted_apps: typing.Sequence[algopy.Application | algopy.UInt64 | int] = (),
        **account_fields: typing.Unpack[AccountFields],
    ) -> algopy.Account:
        """Initialize a new account with specified fields and balances."""
        import algopy

        if address is not None and address in lazy_context.ledger._account_data:
            raise ValueError(
                "Account with such address already exists in testing context! "
                "Use `context.ledger.get_account(address)` to retrieve the existing account."
            )

        for key in account_fields:
            if key not in AccountFields.__annotations__:
                raise AttributeError(f"Invalid field '{key}' for Account")

        ledger = lazy_context.ledger
        new_account_address = address or algosdk.account.generate_account()[1]
        new_account = algopy.Account(new_account_address)
        # defaultdict of account_data ensures we get a new initialized account
        account_data = lazy_context.get_account_data(new_account_address)
        # update so defaults are preserved
        account_data.fields.update(account_fields)
        for asset_id, balance in (opted_asset_balances or {}).items():
            ledger.update_asset_holdings(
                asset_id,
                new_account_address,
                balance=balance,
            )
        account_data.opted_apps = {_get_app_id(app): ledger.get_app(app) for app in opted_apps}
        return new_account

    def asset(
        self, asset_id: int | None = None, **asset_fields: typing.Unpack[AssetFields]
    ) -> algopy.Asset:
        """Generate and add a new asset with a unique ID."""
        import algopy

        if asset_id and asset_id in lazy_context.ledger._asset_data:
            raise ValueError("Asset with such ID already exists in testing context!")

        for key in asset_fields:
            if key not in AssetFields.__annotations__:
                raise AttributeError(f"Invalid field '{key}' for Asset")

        new_asset = algopy.Asset(asset_id or lazy_context.ledger._get_next_asset_id())
        default_asset_fields = {
            "total": lazy_context.any.uint64(),
            "decimals": lazy_context.any.uint64(1, 6),
            "default_frozen": False,
            "unit_name": lazy_context.any.bytes(4),
            "name": lazy_context.any.bytes(32),
            "url": lazy_context.any.bytes(10),
            "metadata_hash": lazy_context.any.bytes(32),
            "manager": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "freeze": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "clawback": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "creator": lazy_context.value.default_sender,
            "reserve": algopy.Account(algosdk.constants.ZERO_ADDRESS),
        }
        merged_fields = dict(ChainMap(asset_fields, default_asset_fields))  # type: ignore[arg-type]
        lazy_context.ledger._asset_data[int(new_asset.id)] = AssetFields(**merged_fields)  # type: ignore[typeddict-item]
        return new_asset

    def application(
        self,
        id: int | None = None,
        logs: list[bytes] | None = None,
        **application_fields: typing.Unpack[ApplicationFields],
    ) -> algopy.Application:
        r"""Generate and add a new application with a unique ID."""

        new_app_id = id if id is not None else lazy_context.ledger._get_next_app_id()

        if new_app_id in lazy_context.ledger._app_data:
            raise ValueError(
                f"Application id {new_app_id} has already been configured in test context!"
            )

        for key in application_fields:
            if key not in ApplicationFields.__annotations__:
                raise AttributeError(f"Invalid field '{key}' for Application")

        new_app = _algopy_testing.Application(new_app_id)

        # Set sensible defaults
        app_fields: ApplicationFields = {
            "approval_program": _algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "clear_state_program": _algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "global_num_uint": _algopy_testing.UInt64(0),
            "global_num_bytes": _algopy_testing.UInt64(0),
            "local_num_uint": _algopy_testing.UInt64(0),
            "local_num_bytes": _algopy_testing.UInt64(0),
            "extra_program_pages": _algopy_testing.UInt64(0),
            "creator": lazy_context.value.default_sender,
        }

        # Merge provided fields with defaults, prioritizing provided fields
        for field, value in application_fields.items():
            try:
                default_value = app_fields[field]  # type: ignore[literal-required]
            except KeyError:
                raise ValueError(f"invalid field: {field!r}") from None
            if not issubclass(type(value), type(default_value)):
                raise TypeError(f"incorrect type for {field!r}")
            app_fields[field] = value  # type: ignore[literal-required]

        lazy_context.ledger._app_data[new_app_id] = ApplicationContextData(
            fields=app_fields,
            app_id=new_app_id,
            logs=logs or [],
        )

        return new_app

    def bytes(self, length: int | None = None) -> algopy.Bytes:
        """Generate a random byte sequence of a specified length.

        :param length: Length of the byte sequence. Defaults to MAX_BYTES_SIZE.
        :returns: The randomly generated byte sequence.
        """
        length = length or MAX_BYTES_SIZE
        return _algopy_testing.Bytes(secrets.token_bytes(length))


def _get_app_id(app: algopy.Application | algopy.UInt64 | int) -> int:
    from _algopy_testing.models import Application

    app_id = app.id if isinstance(app, Application) else app
    return int(app_id)
