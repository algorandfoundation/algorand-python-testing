from __future__ import annotations

import copy
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable

TKey = typing.TypeVar("TKey")
TItem = typing.TypeVar("TItem")


class MutableBytes:
    """Helper class to ensure mutable algopy types (currently ARC4 array, tuple and
    structs) cascade their changes to parent container types (global/local state, boxes,
    ARC4 array, tuple and structs)"""

    def __init__(self) -> None:
        # callback to call once when _value is modified
        self._on_mutate: Callable[[typing.Any], None] | None = None

    @property
    def _value(self) -> bytes:
        return self.__value

    @_value.setter
    def _value(self, value: bytes) -> None:
        self.__value = value
        if self._on_mutate:
            self._on_mutate(self)
        self._on_mutate = None

    def copy(self) -> typing.Self:
        # when copying a value discard the _on_mutate callback
        clone = copy.deepcopy(self)
        clone._on_mutate = None
        return clone


def set_item_on_mutate(container: object, index: object, value: TItem) -> TItem:
    """Used to update a container-like type when an item is modified."""

    def callback(new_value: TItem) -> None:
        container[index] = new_value  # type: ignore[index]

    return add_mutable_callback(callback, value)


def set_attr_on_mutate(parent: object, name: str, value: TItem) -> TItem:
    """Used to update an object-like type when an attr is modified."""

    def callback(new_value: TItem) -> None:
        setattr(parent, name, new_value)

    return add_mutable_callback(callback, value)


def add_mutable_callback(on_mutate: Callable[[typing.Any], None], value: TItem) -> TItem:
    """Add on_mutate callback to value, if value is mutable.

    Returns value to simplify usage
    """
    if isinstance(value, MutableBytes):
        value._on_mutate = on_mutate
    return value
