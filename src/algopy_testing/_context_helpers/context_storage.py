from __future__ import annotations

import typing
from contextlib import contextmanager
from contextvars import ContextVar

if typing.TYPE_CHECKING:
    from collections.abc import Generator

    import algopy

    from algopy_testing._context_helpers.ledger_context import LedgerContext
    from algopy_testing._context_helpers.txn_context import TransactionContext, TransactionGroup
    from algopy_testing._value_generators import AlgopyValueGenerator
    from algopy_testing.context import AlgopyTestContext
    from algopy_testing.models.account import AccountContextData
    from algopy_testing.models.application import ApplicationContextData
    from algopy_testing.models.asset import AssetFields

_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


# functions for use by algopy_testing implementations that shouldn't be exposed to the user
def get_test_context() -> AlgopyTestContext:
    try:
        result = _var.get()
    except LookupError:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to "
            "access the context manager."
        ) from None
    return result


class _InternalContext:
    """For accessing implementation specific functions, with a convenient
    single entry point for other modules to import Also allows for a single
    place to check and provide."""

    @property
    def value(self) -> AlgopyTestContext:
        return get_test_context()

    @property
    def ledger(self) -> LedgerContext:
        return self.value.ledger

    @property
    def txn(self) -> TransactionContext:
        return self.value.txn

    @property
    def any(self) -> AlgopyValueGenerator:
        return self.value.any

    def get_txn_op_fields(self) -> dict[str, typing.Any]:
        active_group = self.txn._active_group
        if active_group is None:
            return {}
        return (active_group._txn_op_fields or {}).copy()

    @property
    def active_group(self) -> TransactionGroup:
        group = self.value.txn._active_group
        if group is None:
            raise ValueError("no active txn group")
        return group

    @property
    def active_application(self) -> algopy.Application:
        return self.ledger.get_application(self.active_group.active_app_id)

    def get_app_data(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
    ) -> ApplicationContextData:
        from algopy_testing.models import Application, Contract
        from algopy_testing.primitives import UInt64

        if isinstance(app, Contract):
            app_id = app.__app_id__
        elif isinstance(app, Application):
            app_id = app.id.value
        elif isinstance(app, UInt64):
            app_id = app.value
        elif isinstance(app, int):
            app_id = app
        else:
            raise TypeError("invalid type")
        if app_id == 0:
            app_id = self.active_group.active_app_id
        try:
            return self.ledger.application_data[app_id]
        except KeyError:
            raise ValueError("Unknown app id, is there an active transaction?") from None

    def get_asset_data(self, asset_id: int | algopy.UInt64) -> AssetFields:
        try:
            return self.ledger.asset_data[int(asset_id)]
        except KeyError:
            raise ValueError("Unknown asset, check correct testing context is active") from None

    def get_account_data(self, account_public_key: str) -> AccountContextData:
        try:
            return self.ledger.account_data[account_public_key]
        except KeyError:
            raise ValueError("Unknown account, check correct testing context is active") from None


lazy_context = _InternalContext()


@contextmanager
def algopy_testing_context(
    *,
    default_sender: str | None = None,
) -> Generator[AlgopyTestContext, None, None]:
    from algopy_testing.context import AlgopyTestContext

    token = _var.set(
        AlgopyTestContext(
            default_sender=default_sender,
        )
    )
    try:
        yield _var.get()
    finally:
        _var.reset(token)
