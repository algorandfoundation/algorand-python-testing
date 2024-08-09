from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    import algopy


class LogicSig:
    """A logic signature."""

    def __init__(self, func: Callable[[], bool | algopy.UInt64], name: str):
        self.func = func
        self.name = name


@typing.overload
def logicsig(sub: Callable[[], bool | algopy.UInt64], /) -> LogicSig: ...


@typing.overload
def logicsig(*, name: str) -> Callable[[Callable[[], bool | algopy.UInt64]], LogicSig]: ...


def logicsig(
    sub: Callable[[], bool | algopy.UInt64] | None = None, *, name: str | None = None
) -> algopy.LogicSig | Callable[[Callable[[], bool | algopy.UInt64]], LogicSig]:
    """Decorator to indicate a function is a logic signature."""
    if sub is None:
        return functools.partial(
            logicsig,
            name=name,
        )

    return LogicSig(sub, name=name or sub.__name__)
