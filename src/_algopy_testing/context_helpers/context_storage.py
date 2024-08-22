from __future__ import annotations

import typing
from contextlib import contextmanager
from contextvars import ContextVar

if typing.TYPE_CHECKING:
    from collections.abc import Generator

    import algopy

    from _algopy_testing.context import AlgopyTestContext
    from _algopy_testing.context_helpers.ledger_context import LedgerContext
    from _algopy_testing.context_helpers.txn_context import TransactionContext, TransactionGroup
    from _algopy_testing.models.account import AccountContextData
    from _algopy_testing.models.application import ApplicationContextData
    from _algopy_testing.models.asset import AssetFields
    from _algopy_testing.value_generators import AlgopyValueGenerator

_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


class _InternalContext:
    """For accessing implementation specific functions, with a convenient single entry
    point for other modules to import Also allows for a single place to check and
    provide."""

    @property
    def value(self) -> AlgopyTestContext:
        try:
            return _var.get()
        except LookupError:
            raise ValueError(
                "Test context is not initialized! Use `with algopy_testing_context()` to "
                "access the context manager."
            ) from None

    @property
    def ledger(self) -> LedgerContext:
        return self.value.ledger

    @property
    def txn(self) -> TransactionContext:
        return self.value.txn

    @property
    def any(self) -> AlgopyValueGenerator:
        return self.value.any

    def get_active_txn_overrides(self) -> dict[str, typing.Any]:
        active_group = self.txn._active_group
        if active_group is None:
            return {}
        return (active_group._active_txn_overrides or {}).copy()

    @property
    def active_group(self) -> TransactionGroup:
        group = self.value.txn._active_group
        if group is None:
            raise ValueError("no active txn group")
        return group

    @property
    def active_app(self) -> algopy.Application:
        return self.ledger.get_app(self.active_group.active_app_id)

    @property
    def active_app_id(self) -> int:
        return self.active_group.active_app_id

    def get_app_data(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
    ) -> ApplicationContextData:
        if app == 0:
            app = self.active_group.active_app_id
        return self.ledger._get_app_data(app)

    def get_asset_data(self, asset_id: int | algopy.UInt64) -> AssetFields:
        try:
            return self.ledger._asset_data[int(asset_id)]
        except KeyError:
            raise ValueError("Unknown asset, check correct testing context is active") from None

    def get_account_data(self, account_public_key: str) -> AccountContextData:
        try:
            return self.ledger._account_data[account_public_key]
        except KeyError:
            raise ValueError("Unknown account, check correct testing context is active") from None


lazy_context = _InternalContext()


@contextmanager
def algopy_testing_context(
    *,
    default_sender: str | None = None,
) -> Generator[AlgopyTestContext, None, None]:
    """Context manager for the AlgopyTestContext.

    Args:
        default_sender: The default sender for the context.
    """
    from _algopy_testing.context import AlgopyTestContext

    if _var.get(None) is not None:
        raise RuntimeError("Nested `algopy_testing_context`s are not allowed.")

    token = _var.set(
        AlgopyTestContext(
            default_sender=default_sender,
        )
    )
    try:
        yield _var.get()
    finally:
        _var.reset(token)
