import dataclasses
import types
import typing
from collections.abc import Iterable, Iterator, Reversible

from _algopy_testing.mutable import MutableBytes, add_mutable_callback, set_item_on_mutate
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import Serializable
from _algopy_testing.serialize import deserialize_from_bytes, serialize_to_bytes
from _algopy_testing.utils import (
    get_int_literal_from_type_generic,
    get_static_size_of,
    get_type_generic_from_int_literal,
    parameterize_type,
)

if typing.TYPE_CHECKING:
    from _typeshed import DataclassInstance

_TArrayItem = typing.TypeVar("_TArrayItem")
_TArrayLength = typing.TypeVar("_TArrayLength", bound=int)
_T = typing.TypeVar("_T")


class _ImmutableFixedArrayMeta(type, typing.Generic[_TArrayItem, _TArrayLength]):
    __concrete__: typing.ClassVar[dict[tuple[type, type], type]] = {}

    # get or create a type that is parametrized with element_t and length
    def __getitem__(cls, item: tuple[type[_TArrayItem], type[_TArrayLength]]) -> type:
        cache = cls.__concrete__
        if c := cache.get(item, None):
            return c

        element_t, length_t = item
        length = get_int_literal_from_type_generic(length_t)
        cls_name = f"{cls.__name__}[{element_t.__name__},{length}]"
        cache[item] = c = types.new_class(
            cls_name,
            bases=(cls,),
            exec_body=lambda ns: ns.update(
                _element_type=element_t,
                _length=length,
            ),
        )

        return c


class ImmutableFixedArray(
    Serializable,
    typing.Generic[_TArrayItem, _TArrayLength],
    metaclass=_ImmutableFixedArrayMeta,
):
    """An immutable fixed length Array of the specified type and length."""

    _element_type: typing.ClassVar[type]
    _length: int

    def __new__(cls, values: Iterable[_TArrayItem]) -> typing.Self:
        try:
            assert cls._element_type
        except AttributeError:
            items = list(values)
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            size = len(items)
            cls = parameterize_type(cls, type(item), get_type_generic_from_int_literal(size))
        instance = super().__new__(cls)
        return instance

    def __init__(self, values: Iterable[_TArrayItem]) -> None:
        super().__init__()
        items = list(values)
        if len(items) != 0 and len(items) != self._length:
            raise TypeError(f"expected {self._length} items, not {len(items)}")
        for item in items:
            if not isinstance(item, self._element_type):
                raise TypeError(f"item must be of type {self._element_type!r}, not {type(item)!r}")
        self._items = list(items)
        self._value = serialize_to_bytes(self)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return (
                self._element_type == other._element_type
                and self._length == other._length
                and self.serialize() == other.serialize()
            )
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self.serialize())

    @classmethod
    def full(cls, item: _TArrayItem) -> typing.Self:
        return cls(item for _ in range(cls._length))

    def __iter__(self) -> typing.Iterator[_TArrayItem]:
        return iter(self._items)

    def __reversed__(self) -> typing.Iterator[_TArrayItem]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: UInt64 | int) -> _TArrayItem:
        return self._items[index]

    def __setitem__(self, index: UInt64 | int, value: _TArrayItem) -> _TArrayItem:
        self._items[int(index)] = value
        self._value = serialize_to_bytes(self)
        return value

    def replace(
        self, index: UInt64 | int, value: _TArrayItem
    ) -> "ImmutableFixedArray[_TArrayItem, _TArrayLength]":
        copied = list(self._items)
        copied[int(index)] = value
        return self._from_iter(copied)

    def copy(self) -> typing.Self:
        return self.__class__.from_bytes(self.serialize())

    def _from_iter(
        self, items: Iterable[_TArrayItem]
    ) -> "ImmutableFixedArray[_TArrayItem, _TArrayLength]":
        el_type = self._element_type
        l_type = get_type_generic_from_int_literal(self._length)
        typ = ImmutableFixedArray[el_type, l_type]  # type: ignore[valid-type]
        return typ(items)

    def serialize(self) -> bytes:
        return serialize_to_bytes(self)

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)

    def validate(self) -> None:
        pass


class _FixedArrayMeta(type, typing.Generic[_TArrayItem, _TArrayLength]):
    __concrete__: typing.ClassVar[dict[tuple[type, type], type]] = {}

    # get or create a type that is parametrized with element_t and length
    def __getitem__(cls, item: tuple[type[_TArrayItem], type[_TArrayLength]]) -> type:
        cache = cls.__concrete__
        if c := cache.get(item, None):
            return c

        element_t, length_t = item
        length = get_int_literal_from_type_generic(length_t)
        cls_name = f"{cls.__name__}[{element_t.__name__},{length}]"
        cache[item] = c = types.new_class(
            cls_name,
            bases=(cls,),
            exec_body=lambda ns: ns.update(
                _element_type=element_t,
                _length=length,
            ),
        )

        return c


class FixedArray(
    Serializable,
    MutableBytes,
    typing.Generic[_TArrayItem, _TArrayLength],
    metaclass=_FixedArrayMeta,
):
    """A fixed length Array of the specified type and length."""

    _element_type: typing.ClassVar[type]
    _length: int

    def __new__(cls, values: Iterable[_TArrayItem]) -> typing.Self:
        if not hasattr(cls, "_element_type"):
            items = list(values)
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            size = len(items)
            cls = parameterize_type(cls, type(item), get_type_generic_from_int_literal(size))
        instance = super().__new__(cls)
        return instance

    def __init__(self, values: Iterable[_TArrayItem]) -> None:
        super().__init__()
        items = list(values)
        if len(items) != 0 and len(items) != self._length:
            raise TypeError(f"expected {self._length} items, not {len(items)}")
        for item in items:
            if not isinstance(item, self._element_type):
                raise TypeError(f"item must be of type {self._element_type!r}, not {type(item)!r}")
        self._items = list(items)
        self._value = serialize_to_bytes(self)

    @classmethod
    def full(cls, item: _TArrayItem) -> typing.Self:
        return cls([item] * cls._length)

    def __iter__(self) -> typing.Iterator[_TArrayItem]:
        return iter(self._items)

    def __reversed__(self) -> typing.Iterator[_TArrayItem]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: UInt64 | int) -> _TArrayItem:
        value = self._items[index]
        return set_item_on_mutate(self, index, value)

    def __setitem__(self, index: UInt64 | int, value: _TArrayItem) -> _TArrayItem:
        self._items[int(index)] = value
        self._value = serialize_to_bytes(self)
        return value

    def replace(
        self, index: UInt64 | int, value: _TArrayItem
    ) -> "FixedArray[_TArrayItem, _TArrayLength]":
        copied = list(self._items)
        copied[int(index)] = value
        return self._from_iter(copied)

    def copy(self) -> typing.Self:
        return self.__class__.from_bytes(self.serialize())

    def freeze(self) -> ImmutableFixedArray[_TArrayItem, _TArrayLength]:
        return ImmutableFixedArray(self._items)

    def _from_iter(self, items: Iterable[_TArrayItem]) -> "FixedArray[_TArrayItem, _TArrayLength]":
        el_type = self._element_type
        l_type = self._length
        typ = FixedArray[el_type, l_type]  # type: ignore[valid-type]
        return typ(items)

    def serialize(self) -> bytes:
        return self._value

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)

    def validate(self) -> None:
        pass


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


class ImmutableArray(Serializable, typing.Generic[_TArrayItem], metaclass=_ImmutableArrayMeta):
    _element_type: typing.ClassVar[type]

    # ensure type is fully parameterized by looking up type from metaclass

    def __new__(cls, values: Iterable[_TArrayItem] = ()) -> typing.Self:
        from _algopy_testing.serialize import type_of

        try:
            assert cls._element_type
        except AttributeError:
            try:
                items = list(values)
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            cls = cls[type_of(item)]
        instance = super().__new__(cls)
        return instance

    def __init__(self, values: Iterable[_TArrayItem] = ()):
        super().__init__()
        items = list(values)
        for item in items:
            if not isinstance(item, typing.get_origin(self._element_type) or self._element_type):
                raise TypeError(f"expected items of type {self._element_type}")
        self._items = list(items)
        self._value = serialize_to_bytes(self)

    def __iter__(self) -> Iterator[_TArrayItem]:
        return iter(self._items)

    def __reversed__(self) -> Iterator[_TArrayItem]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: UInt64 | int) -> _TArrayItem:
        return self._items[index]

    def __setitem__(self, index: UInt64 | int, value: _TArrayItem) -> _TArrayItem:
        self._items[int(index)] = value
        self._value = serialize_to_bytes(self)
        return value

    def replace(self, index: UInt64 | int, value: _TArrayItem) -> "ImmutableArray[_TArrayItem]":
        copied = list(self._items)
        copied[int(index)] = value
        return self._from_iter(copied)

    def append(self, item: _TArrayItem, /) -> "ImmutableArray[_TArrayItem]":
        copied = list(self._items)
        copied.append(item)
        return self._from_iter(copied)

    def __add__(self, other: Iterable[_TArrayItem], /) -> "ImmutableArray[_TArrayItem]":
        return self._from_iter((*self._items, *other))

    def pop(self) -> "ImmutableArray[_TArrayItem]":
        copied = list(self._items)
        copied.pop()
        return self._from_iter(copied)

    def _from_iter(self, items: Iterable[_TArrayItem]) -> "ImmutableArray[_TArrayItem]":
        """Returns a new array populated with items, also ensures element type info is
        preserved."""
        el_type = self._element_type
        typ = ImmutableArray[el_type]  # type: ignore[valid-type]
        return typ(items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def serialize(self) -> bytes:
        return serialize_to_bytes(self)

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)

    def validate(self) -> None:
        pass


class ReferenceArray(Reversible[_TArrayItem]):
    def __init__(self, values: Iterable[_TArrayItem] = ()):
        self._items = list(values)

    def __iter__(self) -> Iterator[_TArrayItem]:
        return iter(list(self._items))

    def __reversed__(self) -> Iterator[_TArrayItem]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __getitem__(self, index: UInt64 | int) -> _TArrayItem:
        return self._items[int(index)]

    def __setitem__(self, index: UInt64 | int, value: _TArrayItem) -> _TArrayItem:
        self._items[int(index)] = value
        return value

    def append(self, item: _TArrayItem, /) -> None:
        self._items.append(item)

    def extend(self, other: Iterable[_TArrayItem], /) -> None:
        self._items.extend(other)

    def pop(self) -> _TArrayItem:
        return self._items.pop()

    def copy(self) -> "ReferenceArray[_TArrayItem]":
        return ReferenceArray(self._items)

    def freeze(self) -> ImmutableArray[_TArrayItem]:
        return ImmutableArray(self._items)

    def __bool__(self) -> bool:
        return bool(self._items)


class _ArrayMeta(type):
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


class Array(Serializable, MutableBytes, typing.Generic[_TArrayItem], metaclass=_ArrayMeta):
    """A dynamically sized Array of the specified type."""

    _element_type: typing.ClassVar[type]

    # ensure type is fully parameterized by looking up type from metaclass
    def __new__(cls, values: Iterable[_TArrayItem]) -> typing.Self:
        from _algopy_testing.serialize import type_of

        try:
            assert cls._element_type
        except AttributeError:
            items = list(values)
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            cls = cls[type_of(item)]
        instance = super().__new__(cls)
        return instance

    def __init__(self, values: Iterable[_TArrayItem]) -> None:
        super().__init__()
        for item in values:
            if not isinstance(item, typing.get_origin(self._element_type) or self._element_type):
                raise TypeError(f"expected items of type {self._element_type}")
        self._items = list(values)
        self._value = serialize_to_bytes(self)

    def __iter__(self) -> typing.Iterator[_TArrayItem]:
        return iter(self._items)

    def __reversed__(self) -> typing.Iterator[_TArrayItem]:
        return reversed(self._items)

    @property
    def length(self) -> UInt64:
        return UInt64(len(self._items))

    def __len__(self) -> int:
        return len(self._items)

    def __getitem__(self, index: UInt64 | int) -> _TArrayItem:
        value = self._items[index]
        return set_item_on_mutate(self, index, value)

    def append(self, item: _TArrayItem, /) -> None:
        self._items.append(item)

    def extend(self, other: Iterable[_TArrayItem], /) -> None:
        self._items.extend(other)

    def __setitem__(self, index: UInt64 | int, value: _TArrayItem) -> _TArrayItem:
        self._items[index] = value
        self._value = serialize_to_bytes(self)
        return value

    def __add__(self, other: Iterable[_TArrayItem]) -> "Array[_TArrayItem]":
        return self._from_iter((*self._items, *other))

    def pop(self) -> _TArrayItem:
        return self._items.pop()

    def copy(self) -> typing.Self:
        return self.__class__.from_bytes(self.serialize())

    def freeze(self) -> ImmutableArray[_TArrayItem]:
        return ImmutableArray(self._items)

    def _from_iter(self, items: Iterable[_TArrayItem]) -> "Array[_TArrayItem]":
        """Returns a new array populated with items, also ensures element type info is
        preserved."""
        el_type = self._element_type
        typ = Array[el_type]  # type: ignore[valid-type]
        return typ(items)

    def __bool__(self) -> bool:
        return bool(self._items)

    def serialize(self) -> bytes:
        return serialize_to_bytes(self)

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)

    def validate(self) -> None:
        pass


@typing.dataclass_transform()
class Struct(Serializable, MutableBytes):
    """Base class for Struct types."""

    _field_names: typing.ClassVar[list[str]]

    def __init_subclass__(cls, *args: typing.Any, **kwargs: dict[str, typing.Any]) -> None:
        # make implementation not frozen, so we can conditionally control behaviour
        dataclasses.dataclass(cls, *args, **{**kwargs, "frozen": False})
        frozen = kwargs.get("frozen", False)
        cls._field_names = [
            f.name for f in dataclasses.fields(typing.cast("type[DataclassInstance]", cls))
        ]
        assert isinstance(frozen, bool)

    def __post_init__(self) -> None:
        # calling base class here to init Mutable
        # see https://docs.python.org/3/library/dataclasses.html#post-init-processing
        super().__init__()

    def __getattribute__(self, name: str) -> typing.Any:
        value = super().__getattribute__(name)
        return add_mutable_callback(lambda _: self._update_backing_value(), value)

    def __setattr__(self, key: str, value: typing.Any) -> None:
        super().__setattr__(key, value)
        # don't update backing value until base class has been init'd

        if hasattr(self, "_on_mutate") and key in self._field_names:
            self._update_backing_value()

    def copy(self) -> typing.Self:
        return self.__class__.from_bytes(self.serialize())

    def _replace(self, **kwargs: typing.Any) -> typing.Self:
        return self.__class__(**{**self.__dict__, **kwargs})

    def serialize(self) -> bytes:
        return serialize_to_bytes(self)

    @classmethod
    def from_bytes(cls, value: bytes, /) -> typing.Self:
        return deserialize_from_bytes(cls, value)

    def _update_backing_value(self) -> None:
        self._value = serialize_to_bytes(self)

    def validate(self) -> None:
        pass


def zero_bytes(typ: type[_T]) -> _T:
    # Get the static size of the type
    size = get_static_size_of(typ)
    if size is None:
        raise ValueError(f"{typ} is dynamically sized")

    # Create zero bytes of the required size
    zero_data = bytes(size)

    # Use the type's from_bytes method to create the instance
    if hasattr(typ, "from_bytes"):
        return typ.from_bytes(zero_data)  # type: ignore[attr-defined, no-any-return]
    else:
        raise TypeError(f"Type {typ} does not support from_bytes method")
