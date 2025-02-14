import dataclasses
import inspect
import typing
from collections.abc import Callable, Sequence

from _algopy_testing.primitives.uint64 import UInt64

if typing.TYPE_CHECKING:
    from _algopy_testing.arc4 import _ABIEncoded


_T = typing.TypeVar("_T")
_U = typing.TypeVar("_U")


@dataclasses.dataclass(frozen=True)
class _Serializer(typing.Generic[_T, _U]):
    native_type: type[_T]
    arc4_type: type[_U]
    native_to_arc4: Callable[[_T], _U]
    arc4_to_native: Callable[[_U], _T]


def identity(i: _T) -> _T:
    return i


def get_native_to_arc4_serializer(typ: type[_T]) -> _Serializer:  # type: ignore[type-arg] # noqa: PLR0911
    from _algopy_testing import arc4
    from _algopy_testing.models import Account
    from _algopy_testing.primitives import BigUInt, Bytes, ImmutableArray, String
    from _algopy_testing.protocols import UInt64Backed

    if issubclass(typ, arc4._ABIEncoded):
        return _Serializer(
            native_type=typ, arc4_type=typ, native_to_arc4=identity, arc4_to_native=identity
        )
    if issubclass(typ, bool):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.Bool,
            native_to_arc4=arc4.Bool,
            arc4_to_native=lambda n: n.native,
        )
    if issubclass(typ, UInt64Backed):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.UInt64,
            native_to_arc4=lambda n: arc4.UInt64(n.int_),
            arc4_to_native=lambda a: typ.from_int(a.native),
        )
    if issubclass(typ, BigUInt):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.UInt512,
            native_to_arc4=arc4.UInt512,
            arc4_to_native=lambda a: a.native,
        )
    if issubclass(typ, Account):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.Address,
            native_to_arc4=arc4.Address,
            arc4_to_native=lambda a: a.native,
        )
    if issubclass(typ, UInt64):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.UInt64,
            native_to_arc4=arc4.UInt64,
            arc4_to_native=lambda a: a.native,
        )
    if issubclass(typ, Bytes):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.DynamicBytes,
            native_to_arc4=arc4.DynamicBytes,
            arc4_to_native=lambda a: a.native,
        )
    if issubclass(typ, String):
        return _Serializer(
            native_type=typ,
            arc4_type=arc4.String,
            native_to_arc4=arc4.String,
            arc4_to_native=lambda a: a.native,
        )
    if issubclass(typ, tuple) or typing.get_origin(typ) is tuple:
        if typing.NamedTuple in getattr(typ, "__orig_bases__", []):
            tuple_fields: Sequence[type] = list(inspect.get_annotations(typ).values())
        else:
            tuple_fields = typing.get_args(typ)
        serializers = [get_native_to_arc4_serializer(i) for i in tuple_fields]

        def _items_to_arc4(items: Sequence[object]) -> tuple[object, ...]:
            result = []
            for item, serializer in zip(items, serializers, strict=True):
                result.append(serializer.native_to_arc4(item))
            return tuple(result)

        def _items_to_native(items: Sequence[object]) -> tuple[object, ...]:
            result = []
            for item, serializer in zip(items, serializers, strict=True):
                result.append(serializer.arc4_to_native(item))
            return tuple(result)

        return _Serializer(
            native_type=typ,
            arc4_type=arc4.Tuple[*(s.arc4_type for s in serializers)],  # type: ignore[misc]
            native_to_arc4=lambda t: arc4.Tuple(_items_to_arc4(t)),
            arc4_to_native=lambda t: _items_to_native(t),
        )
    if issubclass(typ, ImmutableArray):
        native_element_type = typ._element_type
        element_serializer = get_native_to_arc4_serializer(native_element_type)
        arc4_element_type = element_serializer.arc4_type
        arc4_type = arc4.DynamicArray[arc4_element_type]  # type: ignore[valid-type]
        return _Serializer(
            native_type=typ,
            arc4_type=arc4_type,
            native_to_arc4=lambda arr: arc4_type(
                *(element_serializer.native_to_arc4(e) for e in arr)
            ),
            arc4_to_native=lambda arr: typ(*(element_serializer.arc4_to_native(e) for e in arr)),
        )
    raise TypeError(f"unserializable type: {typ}")


def serialize_to_bytes(value: object) -> bytes:
    return native_to_arc4(value).bytes.value


def type_of(value: object) -> type:
    """Returns the type of value, this will also ensure the type is fully parametrized
    if it is a generic type."""
    # get fully parametrized tuples
    if isinstance(value, tuple) and type(value) is tuple:
        return tuple[*(type_of(i) for i in value)]  # type: ignore[misc, no-any-return]
    else:
        return type(value)


def native_to_arc4(value: object) -> "_ABIEncoded":
    from _algopy_testing import arc4

    src_type = type_of(value)

    serializer = get_native_to_arc4_serializer(src_type)
    arc4_value = serializer.native_to_arc4(value)
    assert isinstance(arc4_value, arc4._ABIEncoded)
    return arc4_value


def deserialize_from_bytes(typ: type[_T], bites: bytes) -> _T:
    serializer = get_native_to_arc4_serializer(typ)
    arc4_value = serializer.arc4_type.from_bytes(bites)
    native_value = serializer.arc4_to_native(arc4_value)
    assert isinstance(native_value, typ)
    return native_value
