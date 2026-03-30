from __future__ import annotations

import typing

from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.models import Account
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import BytesBacked, Serializable, UInt64Backed

if typing.TYPE_CHECKING:
    import algopy
from _algopy_testing.serialize import (
    deserialize_from_bytes,
    serialize_to_bytes,
)

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
    elif isinstance(value, tuple):
        return serialize_to_bytes(value)
    else:
        raise TypeError(f"Unsupported type: {type(value)}")


def deserialize(typ: type[_TValue], value: SerializableValue) -> _TValue:
    if (typing.get_origin(typ) is tuple or issubclass(typ, tuple)) and isinstance(value, bytes):
        return () if not value else deserialize_from_bytes(typ, value)  # type: ignore[return-value]
    elif issubclass(typ, bool):
        return value != 0  # type: ignore[return-value]
    elif issubclass(typ, UInt64 | Bytes):
        return typ(value)  # type: ignore[arg-type]
    elif issubclass(typ, UInt64Backed):
        if isinstance(value, bytes):
            raise TypeError("expected int, received bytes")
        return typ.from_int(value)
    elif issubclass(typ, BytesBacked | Serializable):
        if isinstance(value, int):
            raise TypeError("expected bytes, received int")
        return typ.from_bytes(value)
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

    if isinstance(typ, type) and issubclass(typ, bool | UInt64Backed | UInt64):
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


def get_account(account_or_index: algopy.Account | algopy.UInt64 | int) -> algopy.Account:
    if isinstance(account_or_index, Account):
        return account_or_index
    txn = lazy_context.active_group.active_txn
    return txn.accounts(account_or_index)
