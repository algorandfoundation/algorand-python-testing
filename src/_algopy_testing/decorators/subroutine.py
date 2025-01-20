from collections.abc import Callable
from functools import partial, wraps
from typing import Literal, ParamSpec, TypeVar, overload

_P = ParamSpec("_P")
_R = TypeVar("_R")


@overload
def subroutine(sub: Callable[_P, _R], /) -> Callable[_P, _R]: ...
@overload
def subroutine(
    *, inline: bool | Literal["auto"] = "auto"
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...
def subroutine(
    sub: Callable[_P, _R] | None = None, *, inline: bool | Literal["auto"] = "auto"
) -> Callable[_P, _R] | Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    if sub is None:
        return partial(subroutine, inline=inline)

    @wraps(sub)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        return sub(*args, **kwargs)

    return wrapper
