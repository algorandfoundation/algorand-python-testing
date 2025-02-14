import types
import typing
from collections.abc import Iterable, Iterator, Reversible

from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import Serializable
from _algopy_testing.serialize import deserialize_from_bytes, serialize_to_bytes

_T = typing.TypeVar("_T")


class _ImmutableArrayMeta(type):
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    # get or create a type that is parametrized with element_t
    def __getitem__(cls, element_t: type) -> type:
        cache = cls.__concrete__
        if c := cache.get(element_t, None):
            return c

        cls_name = f"{cls.__name__}[{element_t.__name__}]"
        cache[element_t] = c = types.new_class(
            cls_name,
            bases=(cls,),
            exec_body=lambda ns: ns.update(
                _element_type=element_t,
            ),
        )

        return c


class ImmutableArray(Serializable, typing.Generic[_T], metaclass=_ImmutableArrayMeta):
    _element_type: typing.ClassVar[type]

    # ensure type is fully parameterized by looking up type from metaclass
    def __new__(cls, *items: _T) -> typing.Self:
        from _algopy_testing.serialize import type_of

        try:
            assert cls._element_type
        except AttributeError:
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            cls = cls[type_of(item)]
        instance = super().__new__(cls)
        return instance

    def __init__(self, *items: _T):
        for item in items:
            if not isinstance(item, typing.get_origin(self._element_type) or self._element_type):
                raise TypeError(f"expected items of type {self._element_type}")
        self._items = tuple(items)

    def __iter__(self) -> Iterator[_T]:
        return iter(self._items)

    def __reversed__(self) -> Iterator[_T]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __getitem__(self, index: UInt64 | int) -> _T:
        return self._items[index]

    def replace(self, index: UInt64 | int, value: _T) -> "ImmutableArray[_T]":
        copied = list(self._items)
        copied[int(index)] = value
        return self._from_iter(copied)

    def append(self, item: _T, /) -> "ImmutableArray[_T]":
        copied = list(self._items)
        copied.append(item)
        return self._from_iter(copied)

    def __add__(self, other: Iterable[_T], /) -> "ImmutableArray[_T]":
        return self._from_iter((*self._items, *other))

    def pop(self) -> "ImmutableArray[_T]":
        copied = list(self._items)
        copied.pop()
        return self._from_iter(copied)

    def _from_iter(self, items: Iterable[_T]) -> "ImmutableArray[_T]":
        """Returns a new array populated with items, also ensures element type info is
        preserved."""
        el_type = self._element_type
        typ = ImmutableArray[el_type]  # type: ignore[valid-type]
        return typ(*items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def serialize(self) -> bytes:
        return serialize_to_bytes(self)

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)


class Array(Reversible[_T]):

    def __init__(self, *items: _T):
        self._items = list(items)

    def __iter__(self) -> Iterator[_T]:
        return iter(list(self._items))

    def __reversed__(self) -> Iterator[_T]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __getitem__(self, index: UInt64 | int) -> _T:
        return self._items[int(index)]

    def __setitem__(self, index: UInt64 | int, value: _T) -> _T:
        self._items[int(index)] = value
        return value

    def append(self, item: _T, /) -> None:
        self._items.append(item)

    def extend(self, other: Iterable[_T], /) -> None:
        self._items.extend(other)

    def pop(self) -> _T:
        return self._items.pop()

    def copy(self) -> "Array[_T]":
        return Array(*self._items)

    def freeze(self) -> ImmutableArray[_T]:
        return ImmutableArray(*self._items)

    def __bool__(self) -> bool:
        return bool(self._items)
