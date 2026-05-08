from __future__ import annotations

import functools
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    import algopy


_P = typing.ParamSpec("_P")


class LogicSig:
    """A logic signature."""

    def __init__(self, func: Callable[..., bool | algopy.UInt64], name: str):
        self.func = func
        self.name = name


@typing.overload
def logicsig(sub: Callable[_P, bool | algopy.UInt64], /) -> LogicSig: ...


@typing.overload
def logicsig(
    *, name: str, **kwargs: typing.Any
) -> Callable[[Callable[_P, bool | algopy.UInt64]], LogicSig]: ...


def logicsig(
    sub: Callable[_P, bool | algopy.UInt64] | None = None,
    *,
    name: str | None = None,
    **_kwargs: typing.Any,
) -> algopy.LogicSig | Callable[[Callable[_P, bool | algopy.UInt64]], LogicSig]:
    """Decorator to indicate a function is a logic signature."""
    if sub is None:
        return functools.partial(
            logicsig,
            name=name,
        )

    return LogicSig(sub, name=name or sub.__name__)
