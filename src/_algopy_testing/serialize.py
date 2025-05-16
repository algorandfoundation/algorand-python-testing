import dataclasses
import functools
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
    arc4_type: type[_U]
    native_to_arc4: Callable[[_T], _U]
    arc4_to_native: Callable[[_U], _T]


def identity(i: _T) -> _T:
    return i


def get_native_to_arc4_serializer(typ: type) -> _Serializer[typing.Any, typing.Any]:
    from _algopy_testing import arc4
    from _algopy_testing.primitives import ImmutableArray
    from _algopy_testing.protocols import UInt64Backed

    origin_type = typing.get_origin(typ)
    if origin_type is tuple:
        return _get_tuple_serializer(typing.get_args(typ))
    elif isinstance(typ, type):
        if issubclass(typ, arc4._ABIEncoded):
            return _Serializer(arc4_type=typ, native_to_arc4=identity, arc4_to_native=identity)
        for native_type, simple_arc4_type in _simple_native_to_arc4_type_map().items():
            if issubclass(typ, native_type):
                return _Serializer(
                    arc4_type=simple_arc4_type,
                    native_to_arc4=simple_arc4_type,
                    arc4_to_native=lambda n: n.native,
                )
        if issubclass(typ, UInt64Backed):
            return _Serializer(
                arc4_type=arc4.UInt64,
                native_to_arc4=lambda n: arc4.UInt64(n.int_),
                arc4_to_native=lambda a: typ.from_int(a.native),
            )
        if typing.NamedTuple in getattr(typ, "__orig_bases__", []):
            tuple_fields = tuple(inspect.get_annotations(typ).values())
            if any(isinstance(f, str) for f in tuple_fields):
                raise TypeError("string annotations in typing.NamedTuple fields are not supported")
            return _get_tuple_serializer(tuple_fields)
        if issubclass(typ, ImmutableArray):
            native_element_type = typ._element_type
            element_serializer = get_native_to_arc4_serializer(native_element_type)
            arc4_element_type = element_serializer.arc4_type
            arc4_type = arc4.DynamicArray[arc4_element_type]  # type: ignore[valid-type]
            return _Serializer(
                arc4_type=arc4_type,
                native_to_arc4=lambda arr: arc4_type(
                    *(element_serializer.native_to_arc4(e) for e in arr)
                ),
                arc4_to_native=lambda arr: typ(
                    *(element_serializer.arc4_to_native(e) for e in arr)
                ),
            )
    raise TypeError(f"unserializable type: {typ}")


@functools.cache
def _simple_native_to_arc4_type_map() -> dict[type, type]:
    from _algopy_testing import arc4
    from _algopy_testing.models import Account
    from _algopy_testing.primitives import BigUInt, Bytes, String

    return {
        bool: arc4.Bool,
        UInt64: arc4.UInt64,
        BigUInt: arc4.UInt512,
        Account: arc4.Address,
        Bytes: arc4.DynamicBytes,
        String: arc4.String,
    }


def _get_tuple_serializer(item_types: tuple[type, ...]) -> _Serializer[typing.Any, typing.Any]:
    from _algopy_testing import arc4

    serializers = [get_native_to_arc4_serializer(i) for i in item_types]

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
        arc4_type=arc4.Tuple[*(s.arc4_type for s in serializers)],  # type: ignore[misc]
        native_to_arc4=lambda t: arc4.Tuple(_items_to_arc4(t)),
        arc4_to_native=lambda t: _items_to_native(t),
    )


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
