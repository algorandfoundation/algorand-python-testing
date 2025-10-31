from __future__ import annotations

import base64
import operator
import types
import typing

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

from itertools import zip_longest

from _algopy_testing.constants import MAX_BYTES_SIZE
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import as_bytes, get_int_literal_from_type_generic

_TBytesLength = typing.TypeVar("_TBytesLength", bound=int)
_TBytesLength_Arg = typing.TypeVar("_TBytesLength_Arg", bound=int)


class _FixedBytesMeta(type):
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    # get or create a type that is parametrized with element_t and length
    def __getitem__(cls, length_t: type) -> type:
        cache = cls.__concrete__
        if c := cache.get(length_t, None):
            return c

        length = get_int_literal_from_type_generic(length_t)
        cls_name = f"{cls.__name__}[{length}]"
        cache[length_t] = c = types.new_class(
            cls_name,
            bases=(cls,),
            exec_body=lambda ns: ns.update(
                _length=length,
            ),
        )

        return c


class FixedBytes(
    BytesBacked,
    typing.Generic[_TBytesLength],
    metaclass=_FixedBytesMeta,
):
    """A statically-sized byte sequence, where the length is known at compile time.

    Unlike `Bytes`, `FixedBytes` has a fixed length specified via a type parameter,
    allowing for compile-time validation and more efficient operations on the AVM.

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
        if len(self.value) != self._length:
            raise TypeError(f"expected value of length {self._length}, not {len(self.value)}")

    def __repr__(self) -> str:
        return repr(self.value)

    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __len__(self) -> int:
        return len(self.value)

    # mypy suggests due to Liskov below should be other: object
    # need to consider ramifications here, ignoring it for now
    def __eq__(self, other: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> bool:  # type: ignore[override]
        """FixedBytes can be compared using the `==` operator with another FixedBytes,
        Bytes or bytes."""
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
        if isinstance(other, (Bytes | FixedBytes)):
            return _checked_result(self.value + other.value, "+")
        else:
            result = self.value + as_bytes(other)
            return _checked_result(result, "+")

    def __radd__(self, other: Bytes | bytes) -> Bytes:
        """Concatenate FixedBytes with another Bytes or bytes literal e.g. `b"Hello " +
        FixedBytes[typing.Literal[5]](b"World")`."""
        if isinstance(other, (Bytes | FixedBytes)):
            return _checked_result(other.value + self.value, "+")
        else:
            result = as_bytes(other) + self.value
            return _checked_result(result, "+")

    @property
    def length(self) -> UInt64:
        """Returns the length of the Bytes."""
        return UInt64(len(self.value))

    def __getitem__(
        self, index: UInt64 | int | slice
    ) -> Bytes:  # maps to substring/substring3 if slice, extract/extract3 otherwise?
        """Returns a Bytes containing a single byte if indexed with UInt64 or int
        otherwise the substring o bytes described by the slice."""
        if isinstance(index, slice):
            return Bytes(self.value[index])
        else:
            int_index = index.value if isinstance(index, UInt64) else index
            int_index = len(self.value) + int_index if int_index < 0 else int_index
            # my_bytes[0:1] => b'j' whereas my_bytes[0] => 106
            return Bytes(self.value[slice(int_index, int_index + 1)])

    def __iter__(self) -> Iterator[Bytes]:
        """FixedBytes can be iterated, yielding each consecutive byte."""
        return _FixedBytesIter(self, 1)

    def __reversed__(self) -> Iterator[Bytes]:
        """FixedBytes can be iterated in reverse, yield each preceding byte starting at
        the end."""
        return _FixedBytesIter(self, -1)

    @typing.overload
    def __and__(self, other: FixedBytes[_TBytesLength]) -> FixedBytes[_TBytesLength]:  # type: ignore[overload-overlap]
        ...

    @typing.overload
    def __and__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes: ...

    def __and__(
        self, other: FixedBytes[typing.Any] | bytes | Bytes
    ) -> FixedBytes[_TBytesLength] | Bytes:
        """Compute the bitwise AND of the FixedBytes with another FixedBytes, Bytes, or
        bytes.

        Returns FixedBytes if other has the same length, otherwise returns Bytes.
        """
        return self._operate_bitwise(other, "and_")

    def __rand__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes:
        return self & other

    @typing.overload
    def __or__(self, other: FixedBytes[_TBytesLength]) -> FixedBytes[_TBytesLength]:  # type: ignore[overload-overlap]
        ...

    @typing.overload
    def __or__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes: ...

    def __or__(
        self, other: FixedBytes[typing.Any] | bytes | Bytes
    ) -> FixedBytes[_TBytesLength] | Bytes:
        return self._operate_bitwise(other, "or_")

    def __ror__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes:
        return self | other

    @typing.overload
    def __xor__(self, other: FixedBytes[_TBytesLength]) -> FixedBytes[_TBytesLength]:  # type: ignore[overload-overlap]
        ...

    @typing.overload
    def __xor__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes: ...

    def __xor__(
        self, other: FixedBytes[typing.Any] | bytes | Bytes
    ) -> FixedBytes[_TBytesLength] | Bytes:
        return self._operate_bitwise(other, "xor")

    def __rxor__(self, other: FixedBytes[typing.Any] | bytes | Bytes) -> Bytes:
        return self ^ other

    def __invert__(self) -> typing.Self:
        """Compute the bitwise inversion of the Bytes.

        Returns:
            Bytes: The result of the bitwise inversion operation.
        """
        return self.__class__(bytes(~x + 256 for x in self.value))

    def _operate_bitwise(
        self,
        other: FixedBytes[typing.Any] | bytes | Bytes,
        operator_name: str,
    ) -> FixedBytes[_TBytesLength] | Bytes:
        op = getattr(operator, operator_name)
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
            return self.__class__(result)
        return Bytes(result)

    def __contains__(self, item: FixedBytes[_TBytesLength_Arg] | Bytes | bytes) -> bool:
        item_bytes = as_bytes(item)
        return item_bytes in self.value

    @classmethod
    def from_base32(cls, value: str) -> typing.Self:
        """Creates Bytes from a base32 encoded string e.g.
        `Bytes.from_base32("74======")`"""
        bytes_value = base64.b32decode(value)
        return cls(bytes_value)

    @classmethod
    def from_base64(cls, value: str) -> typing.Self:
        """Creates Bytes from a base64 encoded string e.g.
        `Bytes.from_base64("RkY=")`"""
        bytes_value = base64.b64decode(value)
        return cls(bytes_value)

    @classmethod
    def from_hex(cls, value: str) -> typing.Self:
        """Creates Bytes from a hex/octal encoded string e.g. `Bytes.from_hex("FF")`"""
        bytes_value = base64.b16decode(value)
        return cls(bytes_value)

    @classmethod
    def from_bytes(cls, value: Bytes | bytes) -> typing.Self:
        """Construct an instance from the underlying bytes (no validation)"""
        result = cls()
        result.value = as_bytes(value)
        return result

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
        ArithmeticError: If `result` of `op` is out of bounds
    """
    if len(result) > MAX_BYTES_SIZE:
        raise OverflowError(f"{op} overflows")
    return Bytes(result)
