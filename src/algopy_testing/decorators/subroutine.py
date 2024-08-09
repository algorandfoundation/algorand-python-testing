from collections.abc import Callable
from typing import ParamSpec, TypeVar

_P = ParamSpec("_P")
_R = TypeVar("_R")


# TODO: set up active app and transaction if subroutine is on a contract
def subroutine(sub: Callable[_P, _R]) -> Callable[_P, _R]:
    return sub
