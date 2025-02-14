from __future__ import annotations

import typing
from typing import TypedDict, TypeVar

import algosdk

from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.models import Account
from _algopy_testing.primitives import UInt64

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    import algopy

T = TypeVar("T")


class GlobalFields(TypedDict, total=False):
    min_txn_fee: algopy.UInt64
    min_balance: algopy.UInt64
    max_txn_life: algopy.UInt64
    zero_address: algopy.Account
    logic_sig_version: algopy.UInt64
    round: algopy.UInt64
    latest_timestamp: algopy.UInt64
    group_id: algopy.Bytes
    caller_application_id: algopy.UInt64
    asset_create_min_balance: algopy.UInt64
    asset_opt_in_min_balance: algopy.UInt64
    genesis_hash: algopy.Bytes
    opcode_budget: Callable[[], int]
    payouts_enabled: bool
    payouts_go_online_fee: algopy.UInt64
    payouts_max_balance: algopy.UInt64
    payouts_min_balance: algopy.UInt64
    payouts_percent: algopy.UInt64


class _Global:
    @property
    def _fields(self) -> GlobalFields:
        return lazy_context.ledger._global_fields

    @property
    def current_application_address(self) -> algopy.Account:
        app_address = algosdk.logic.get_application_address(int(self.current_application_id.id))
        return Account(app_address)

    @property
    def current_application_id(self) -> algopy.Application:
        return lazy_context.active_app

    @property
    def caller_application_id(self) -> algopy.UInt64:
        return self._fields["caller_application_id"]

    @property
    def caller_application_address(self) -> algopy.Account:
        app_address = algosdk.logic.get_application_address(int(self.caller_application_id))
        return Account(app_address)

    @property
    def creator_address(self) -> algopy.Account:
        app = lazy_context.active_app
        app_data = lazy_context.get_app_data(app)
        return app_data.fields["creator"]

    @property
    def latest_timestamp(self) -> algopy.UInt64:
        try:
            return self._fields["latest_timestamp"]
        except KeyError:
            return UInt64(lazy_context.active_group._latest_timestamp)

    @property
    def group_size(self) -> algopy.UInt64:
        group = lazy_context.active_group
        return UInt64(len(group.txns))

    @property
    def group_id(self) -> algopy.Bytes:
        from _algopy_testing import op

        try:
            return self._fields["group_id"]
        except KeyError:
            group_hash = hash(lazy_context.active_group)
            group_hash_bytes = group_hash.to_bytes((group_hash.bit_length() + 7) // 8)
            return op.sha256(group_hash_bytes)

    @property
    def round(self) -> algopy.UInt64:
        try:
            return self._fields["round"]
        except KeyError:
            # size of groups will suffice as an increasing integer similar to ground
            num_groups = len(lazy_context.txn._groups) + 1
            return UInt64(num_groups)

    @property
    def zero_address(self) -> algopy.Account:
        try:
            return self._fields["zero_address"]
        except KeyError:
            return Account(algosdk.constants.ZERO_ADDRESS)

    def __getattr__(self, name: str) -> typing.Any:
        try:
            return self._fields[name]  # type: ignore[literal-required]
        except KeyError:
            raise AttributeError(
                f"'algopy.Global' object has no value set for attribute named '{name}'. "
                f"Use `context.ledger.patch_global_fields({name}=your_value)` to set the value "
                "in your test setup."
            ) from None


Global = _Global()
