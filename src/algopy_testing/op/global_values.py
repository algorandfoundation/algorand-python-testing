from __future__ import annotations

import time
import typing
from typing import TypedDict, TypeVar

import algosdk

from algopy_testing._context_storage import get_app_data, get_test_context
from algopy_testing.models import Account, Application
from algopy_testing.primitives import UInt64

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    import algopy

T = TypeVar("T")


class GlobalFields(TypedDict, total=False):
    min_txn_fee: algopy.UInt64
    min_balance: algopy.UInt64
    max_txn_life: algopy.UInt64
    zero_address: algopy.Account
    group_size: algopy.UInt64
    logic_sig_version: algopy.UInt64
    round: algopy.UInt64
    latest_timestamp: algopy.UInt64
    current_application_id: algopy.Application
    creator_address: algopy.Account
    current_application_address: algopy.Account
    group_id: algopy.Bytes
    caller_application_id: algopy.Application
    caller_application_address: algopy.Account
    asset_create_min_balance: algopy.UInt64
    asset_opt_in_min_balance: algopy.UInt64
    genesis_hash: algopy.Bytes
    opcode_budget: Callable[[], int]


class _Global:

    @property
    def _fields(self) -> GlobalFields:
        context = get_test_context()
        return context._global_fields

    @property
    def current_application_address(self) -> algopy.Account:
        try:
            return self._fields["current_application_address"]
        except KeyError:
            app_address = algosdk.logic.get_application_address(
                int(self.current_application_id.id)
            )
            return Account(app_address)

    @property
    def current_application_id(self) -> algopy.Application:
        try:
            return self._fields["current_application_id"]
        except KeyError:
            context = get_test_context()
            app = context.get_active_application()
            app_data = get_app_data(int(app.id))
            if app_data.is_creating:
                return Application(0)
            return context.get_active_transaction().app_id

    # TODO: move creator_address here
    @property
    def latest_timestamp(self) -> algopy.UInt64:
        try:
            return self._fields["latest_timestamp"]
        except KeyError:
            return UInt64(int(time.time()))

    @property
    def group_size(self) -> algopy.UInt64:
        try:
            return self._fields["group_size"]
        except KeyError:
            context = get_test_context()
            # TODO: active group?
            return UInt64(len(context.last_group.transactions))

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
                f"Use `context.patch_global_fields({name}=your_value)` to set the value "
                "in your test setup."
            ) from None


Global = _Global()
