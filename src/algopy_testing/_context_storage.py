from __future__ import annotations

import typing
from contextlib import contextmanager
from contextvars import ContextVar

if typing.TYPE_CHECKING:
    from collections.abc import Generator

    import algopy

    from algopy_testing.context import AlgopyTestContext
    from algopy_testing.models.account import AccountContextData
    from algopy_testing.models.application import ApplicationContextData
    from algopy_testing.models.asset import AssetFields

_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


# functions for use by algopy_testing implementations that shouldn't be exposed to the user
# TODO: might be nicer to wrap all this into a single interface that can be imported
def get_test_context() -> AlgopyTestContext:
    try:
        result = _var.get()
    except LookupError:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to "
            "access the context manager."
        ) from None
    return result


def link_application(contract: algopy.Contract, app_id: int) -> None:
    context = get_test_context()
    context._contract_app_ids[contract] = app_id
    app_data = context._application_data[app_id]
    app_data.contract = contract


def get_app_data(app: int | algopy.Contract) -> ApplicationContextData:
    context = get_test_context()
    if not isinstance(app, int):
        # attempt to get app_id, fall back to invalid id if not found
        app = context._contract_app_ids.get(app, -1)
    try:
        return context._application_data[app]
    except KeyError:
        raise ValueError("Unknown application, check correct testing context is active") from None


def get_asset_data(asset_id: int) -> AssetFields:
    context = get_test_context()
    try:
        return context._asset_data[asset_id]
    except KeyError:
        raise ValueError("Unknown asset, check correct testing context is active") from None


def get_account_data(account_public_key: str) -> AccountContextData:
    context = get_test_context()
    try:
        return context._account_data[account_public_key]
    except KeyError:
        raise ValueError("Unknown account, check correct testing context is active") from None


@contextmanager
def algopy_testing_context(
    *,
    default_sender: algopy.Account | None = None,
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
