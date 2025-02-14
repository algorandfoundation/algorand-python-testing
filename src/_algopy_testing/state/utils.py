from __future__ import annotations

import typing

from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import BytesBacked, Serializable, UInt64Backed

_TValue = typing.TypeVar("_TValue")
SerializableValue = int | bytes


def serialize(value: _TValue) -> SerializableValue:
    if isinstance(value, bool):
        return int(value)
    elif isinstance(value, Bytes | UInt64):
        return value.value
    elif isinstance(value, UInt64Backed):
        return value.int_
    elif isinstance(value, BytesBacked):
        return value.bytes.value
    elif isinstance(value, Serializable):
        return value.serialize()
    else:
        raise TypeError(f"Unsupported type: {type(value)}")


def deserialize(typ: type[_TValue], value: SerializableValue) -> _TValue:
    if issubclass(typ, bool):
        return value != 0  # type: ignore[return-value]
    elif issubclass(typ, UInt64 | Bytes):
        return typ(value)  # type: ignore[arg-type, return-value]
    elif issubclass(typ, UInt64Backed):
        if isinstance(value, bytes):
            raise TypeError("expected int, received bytes")
        return typ.from_int(value)  # type: ignore[return-value]
    elif issubclass(typ, BytesBacked):
        if isinstance(value, int):
            raise TypeError("expected bytes, received int")
        return typ.from_bytes(Bytes(value))  # type: ignore[return-value]
    elif issubclass(typ, Serializable):
        if isinstance(value, int):
            raise TypeError("expected bytes, received int")
        return typ.from_bytes(value)  # type: ignore[return-value]
    else:
        raise TypeError(f"Unsupported type: {typ}")


def cast_from_bytes(typ: type[_TValue], value: bytes) -> _TValue:
    """
    assuming _TValue to be one of the followings:
        - bool,
        - UInt64Backed
        - BytesBacked
    """
    from _algopy_testing.utils import as_int64

    if issubclass(typ, bool | UInt64Backed | UInt64):
        if len(value) > 8:
            raise ValueError("uint64 value too big")
        serialized: SerializableValue = int.from_bytes(value)
        serialized = as_int64(serialized)
    else:
        serialized = value
    return deserialize(typ, serialized)


def cast_to_bytes(value: _TValue) -> bytes:
    serialized = serialize(value)

    if isinstance(serialized, int):
        serialized = serialized.to_bytes(length=8)
    return serialized
