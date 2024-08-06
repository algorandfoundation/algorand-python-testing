from __future__ import annotations

import typing
from contextlib import contextmanager
from contextvars import ContextVar

if typing.TYPE_CHECKING:
    from collections.abc import Generator

    import algopy

    from algopy_testing import AlgopyTestContext

_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


def get_test_context() -> AlgopyTestContext:
    try:
        result = _var.get()
    except LookupError:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to "
            "access the context manager."
        ) from None
    return result


@contextmanager
def algopy_testing_context(
    *,
    default_creator: algopy.Account | None = None,
) -> Generator[AlgopyTestContext, None, None]:
    from algopy_testing.context import AlgopyTestContext

    token = _var.set(
        AlgopyTestContext(
            default_creator=default_creator,
        )
    )
    try:
        yield _var.get()
    finally:
        _var.reset(token)
