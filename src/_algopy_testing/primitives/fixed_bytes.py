from __future__ import annotations

import base64
import operator
import types
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterator

from itertools import zip_longest

from _algopy_testing.constants import MAX_BYTES_SIZE
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import (
    as_bytes,
    get_int_literal_from_type_generic,
    get_type_generic_from_int_literal,
)

_TBytesLength = typing.TypeVar("_TBytesLength", bound=int)
_TBytesLength_Arg = typing.TypeVar("_TBytesLength_Arg", bound=int)


def _get_or_create_class_from_type(cls: type, length_t: type) -> type:
    _length = get_int_literal_from_type_generic(length_t)
    return _get_or_create_class(cls, _length, length_t)


def _get_or_create_class_from_int(cls: type, length: int) -> type:
    length_t = get_type_generic_from_int_literal(length)
    return _get_or_create_class(cls, length, length_t)


def _get_or_create_class(cls: type, length: int, length_t: type) -> type:
    """Get or create a type that is parametrized with element_t and length."""
    cache = getattr(cls, "__concrete__", {})
    if c := cache.get(length_t, None):
        assert isinstance(c, type)
        return c

    cls_name = f"{cls.__name__}[{length}]"

    cache[length_t] = t = types.new_class(
        cls_name,
        bases=(cls,),
        exec_body=lambda ns: ns.update(
            _length=length,
        ),
    )
    return t


class _FixedBytesMeta(type):
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    def __getitem__(cls, length_t: type) -> type:
        if length_t == typing.Any:
            return cls

        return _get_or_create_class_from_type(cls, length_t)


class FixedBytes(
    BytesBacked,
    typing.Generic[_TBytesLength],
    metaclass=_FixedBytesMeta,
):
    """A statically-sized byte sequence, where the length is known at compile time.

    Unlike `Bytes`, `FixedBytes` has a fixed length specified via a type parameter.

    Example:
        FixedBytes[typing.Literal[32]]  # A 32-byte fixed-size bytes value
    """

    value: bytes  # underlying 'bytes' value representing the FixedBytes
    _length: int

    def __init__(self, value: Bytes | bytes | None = None, /):
        if value is None:
            self.value = b"\x00" * self._length
            return

        self.value = as_bytes(value)
        if not hasattr(self, "_length"):
            self._length = len(self.value)

        if len(self.value) != self._length:
            raise ValueError(f"expected value of length {self._length}, not {len(self.value)}")

    def __repr__(self) -> str:
        return repr(self.value)

    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return bool(self._length)

    def __len__(self) -> int:
        return self._length

    def __eq__(self, other: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> bool:  # type: ignore[override]
        """FixedBytes can be compared using the `==` operator with another FixedBytes,
        Bytes or bytes."""

        if isinstance(other, FixedBytes) and other.length != self.length:
            return False

        try:
            other_bytes = as_bytes(other)
        except TypeError:
            return NotImplemented

        return self.value == other_bytes

    def __hash__(self) -> int:
        return hash(self.value)

    def __add__(self, other: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> Bytes:
        """Concatenate FixedBytes with another Bytes or bytes literal e.g.
        `FixedBytes[typing.Literal[5]](b"Hello ") + b"World"`."""
        result = self.value + as_bytes(other)
        return _checked_result(result, "+")

    def __radd__(self, other: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> Bytes:
        """Concatenate FixedBytes with another Bytes or bytes literal e.g. `b"Hello " +
        FixedBytes[typing.Literal[5]](b"World")`."""
        result = as_bytes(other) + self.value
        return _checked_result(result, "+")

    def __iadd__(self, _other: Bytes | typing.Self | bytes) -> typing.Self:  # type: ignore[misc]
        raise TypeError("FixedBytes does not support in-place addition")

    @property
    def length(self) -> UInt64:
        """Returns the specified length of the FixedBytes."""
        return UInt64(self._length)

    def __getitem__(self, index: UInt64 | int | slice) -> Bytes:
        """Returns a Bytes containing a single byte if indexed with UInt64 or int
        otherwise the substring of bytes described by the slice."""
        value = self.value[: self.length]
        if isinstance(index, slice):
            return Bytes(value[index])
        else:
            int_index = index.value if isinstance(index, UInt64) else index
            int_index = self.length.value + int_index if int_index < 0 else int_index
            if (int_index >= self.length) or (int_index < 0):
                raise ValueError("FixedBytes index out of range")
            # my_bytes[0:1] => b'j' whereas my_bytes[0] => 106
            return Bytes(value[slice(int_index, int_index + 1)])

    def __iter__(self) -> Iterator[Bytes]:
        """FixedBytes can be iterated, yielding each consecutive byte."""
        return _FixedBytesIter(self, 1)

    def __reversed__(self) -> Iterator[Bytes]:
        """FixedBytes can be iterated in reverse, yield each preceding byte starting at
        the end."""
        return _FixedBytesIter(self, -1)

    @typing.overload
    def __and__(self, other: typing.Self) -> typing.Self: ...  # type: ignore[overload-overlap]
    @typing.overload
    def __and__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> Bytes: ...
    def __and__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> typing.Self | Bytes:
        """Compute the bitwise AND of the FixedBytes with another FixedBytes, Bytes, or
        bytes.

        Returns FixedBytes if other has the same length, otherwise returns Bytes.
        """
        return self._operate_bitwise(other, operator.and_)

    def __rand__(self, other: bytes) -> Bytes:
        return self & other

    def __iand__(self, other: Bytes | typing.Self | bytes) -> typing.Self:  # type: ignore[misc]
        other_bytes = as_bytes(other)
        other_fixed_bytes = self.__class__(other_bytes)
        result = self._operate_bitwise(other_fixed_bytes, operator.and_)
        assert isinstance(result, self.__class__)
        return result

    @typing.overload
    def __or__(self, other: typing.Self) -> typing.Self: ...  # type: ignore[overload-overlap]
    @typing.overload
    def __or__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> Bytes: ...
    def __or__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> typing.Self | Bytes:
        return self._operate_bitwise(other, operator.or_)

    def __ror__(self, other: bytes) -> Bytes:
        return self | other

    def __ior__(self, other: Bytes | typing.Self | bytes) -> typing.Self:  # type: ignore[misc]
        other_bytes = as_bytes(other)
        other_fixed_bytes = self.__class__(other_bytes)
        result = self._operate_bitwise(other_fixed_bytes, operator.or_)
        assert isinstance(result, self.__class__)
        return result

    @typing.overload
    def __xor__(self, other: typing.Self) -> typing.Self: ...  # type: ignore[overload-overlap]
    @typing.overload
    def __xor__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> Bytes: ...
    def __xor__(self, other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes) -> typing.Self | Bytes:
        return self._operate_bitwise(other, operator.xor)

    def __rxor__(self, other: bytes) -> Bytes:
        return self ^ other

    def __ixor__(self, other: Bytes | typing.Self | bytes) -> typing.Self:  # type: ignore[misc]
        other_bytes = as_bytes(other)
        other_fixed_bytes = self.__class__(other_bytes)
        result = self._operate_bitwise(other_fixed_bytes, operator.xor)
        assert isinstance(result, self.__class__)
        return result

    def __invert__(self) -> typing.Self:
        """Compute the bitwise inversion of the FixedBytes.

        Returns:
            FixedBytes: The result of the bitwise inversion operation.
        """
        return self.__class__.from_bytes(bytes(~x + 256 for x in self.value))

    def _operate_bitwise(
        self,
        other: FixedBytes[_TBytesLength_Arg] | bytes | Bytes,
        op: Callable[[int, int], int],
    ) -> typing.Self | Bytes:
        maybe_bytes = as_bytes(other)
        # pad the shorter of self.value and other bytes with leading zero
        # by reversing them as zip_longest fills at the end

        result = bytes(
            reversed(
                bytes(
                    op(a[0], a[1])
                    for a in zip_longest(reversed(self.value), reversed(maybe_bytes), fillvalue=0)
                )
            )
        )
        if isinstance(other, FixedBytes) and len(other.value) == len(self.value):
            return self.__class__.from_bytes(result)
        return Bytes(result)

    def __contains__(self, item: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> bool:
        item_bytes = as_bytes(item)
        return item_bytes in self.value

    @classmethod
    def from_base32(cls, value: str) -> typing.Self:
        """Creates FixedBytes from a base32 encoded string e.g.
        `FixedBytes.from_base32("74======")`"""
        bytes_value = base64.b32decode(value)
        c = cls._ensure_class_with_length(bytes_value)
        return c(bytes_value)

    @classmethod
    def from_base64(cls, value: str) -> typing.Self:
        """Creates FixedBytes from a base64 encoded string e.g.
        `FixedBytes.from_base64("RkY=")`"""
        bytes_value = base64.b64decode(value)
        c = cls._ensure_class_with_length(bytes_value)
        return c(bytes_value)

    @classmethod
    def from_hex(cls, value: str) -> typing.Self:
        """Creates FixedBytes from a hex/octal encoded string e.g.
        `FixedBytes.from_hex("FF")`"""
        bytes_value = base64.b16decode(value)
        c = cls._ensure_class_with_length(bytes_value)
        return c(bytes_value)

    @classmethod
    def from_bytes(cls, value: Bytes | bytes) -> typing.Self:
        """Construct an instance from the underlying bytes (no validation)"""
        bytes_value = value.value if isinstance(value, Bytes) else value
        c = cls._ensure_class_with_length(bytes_value)
        result = c()
        result.value = bytes_value
        return result

    @classmethod
    def _ensure_class_with_length(cls, bytes_value: bytes) -> type[typing.Self]:
        """Returns the appropriate class for the given bytes value.

        If cls has a fixed _length, returns cls. Otherwise, returns or creates a
        specialized class with the length set to match bytes_value.
        """
        return (
            _get_or_create_class_from_int(cls, len(bytes_value))
            if not hasattr(cls, "_length")
            else cls
        )

    @property
    def bytes(self) -> Bytes:
        """Get the underlying Bytes."""
        return Bytes(self.value)


class _FixedBytesIter(typing.Generic[_TBytesLength]):
    value: FixedBytes[_TBytesLength]

    def __init__(self, sequence: FixedBytes[_TBytesLength], step: int = 1):
        self.value = sequence
        self.current = 0 if step > 0 else len(sequence) - 1
        self.step = step
        self.myend = len(sequence) - 1 if step > 0 else 0

    def __iter__(self) -> typing.Self:
        return self

    def __next__(self) -> Bytes:
        # if current is one step over the end
        if self.current == self.myend + self.step:
            raise StopIteration

        self.current += self.step
        return self.value[self.current - self.step]


def _checked_result(result: bytes, op: str) -> Bytes:
    """Ensures `result` is a valid Bytes value.

    Raises:
        OverflowError: If `result` of `op` is out of bounds
    """
    if len(result) > MAX_BYTES_SIZE:
        raise OverflowError(f"{op} overflows")
    return Bytes(result)
