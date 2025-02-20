from __future__ import annotations

import dataclasses
import decimal
import functools
import types
import typing

import algosdk
from Cryptodome.Hash import SHA512

from _algopy_testing.constants import (
    ARC4_RETURN_PREFIX,
    BITS_IN_BYTE,
    MAX_UINT64,
    UINT64_SIZE,
    UINT512_SIZE,
)
from _algopy_testing.models.account import Account
from _algopy_testing.models.contract import ARC4Contract
from _algopy_testing.mutable import (
    MutableBytes,
    add_mutable_callback,
    set_item_on_mutate,
)
from _algopy_testing.primitives import Bytes
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import (
    as_bytes,
    as_int,
    as_int16,
    as_int64,
    as_int512,
    as_string,
    int_to_bytes,
    raise_mocked_function_error,
)

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator, Sequence

    import algopy

__all__ = [
    "ARC4Client",
    "ARC4Contract",
    "Address",
    "BigUFixedNxM",
    "BigUIntN",
    "Bool",
    "Byte",
    "DynamicArray",
    "DynamicBytes",
    "StaticArray",
    "String",
    "Struct",
    "Tuple",
    "UFixedNxM",
    "UInt8",
    "UInt16",
    "UInt32",
    "UInt64",
    "UInt128",
    "UInt256",
    "UInt512",
    "UIntN",
    "abi_call",
    "arc4_create",
    "arc4_signature",
    "arc4_update",
    "emit",
]

_ABI_LENGTH_SIZE = 2
_TBitSize = typing.TypeVar("_TBitSize", bound=int)

_P = typing.ParamSpec("_P")
_R = typing.TypeVar("_R")


class _TypeInfo:
    @property
    def typ(self) -> type:
        raise NotImplementedError

    @property
    def arc4_name(self) -> str:
        raise NotImplementedError

    @property
    def is_dynamic(self) -> bool:
        return False

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _TypeInfo) and self.arc4_name == other.arc4_name

    def __hash__(self) -> int:
        return hash(self.arc4_name)

    def __repr__(self) -> str:
        return self.arc4_name


def _get_int_literal(literal_type: type) -> int:
    type_args = typing.get_args(literal_type)
    try:
        (int_arg,) = type_args
    except ValueError:
        int_arg = 0
    return int(int_arg)


def _create_int_literal(value: int) -> type:
    return typing.cast(type, typing.Literal[value])


def _parameterize_type(type_: type, *params: type) -> type:
    if len(params) == 1:
        return typing.cast(type, type_[params[0]])  # type: ignore[index]
    return typing.cast(type, type_[params])  # type: ignore[index]


def _get_type_param_name(typ: type) -> str:
    if typ.__name__ == "Literal":
        int_arg = _get_int_literal(typ)
        return str(int_arg)
    return typ.__name__


def _new_parameterized_class(cls: type, type_params: Sequence[type], type_info: _TypeInfo) -> type:
    cls_name = f"{cls.__name__}[{','.join(_get_type_param_name(t) for t in type_params)}]"

    return types.new_class(
        cls_name,
        bases=(cls,),
        exec_body=lambda ns: ns.update(
            _type_info=type_info,
        ),
    )


def _check_is_arc4(items: Sequence[typing.Any]) -> Sequence[_ABIEncoded]:
    for item in items:
        if not isinstance(item, _ABIEncoded):
            raise TypeError("expected ARC4 type")
    return items


class _ABIEncoded(BytesBacked):
    _type_info: _TypeInfo
    _value: bytes

    @classmethod
    def from_bytes(cls, value: algopy.Bytes | bytes, /) -> typing.Self:
        """Construct an instance from the underlying bytes (no validation)"""
        instance = cls()
        instance._value = as_bytes(value)
        return instance

    @classmethod
    def from_log(cls, log: algopy.Bytes, /) -> typing.Self:
        """Load an ABI type from application logs, checking for the ABI return prefix
        `0x151f7c75`"""
        if log[:4] == ARC4_RETURN_PREFIX:
            return cls.from_bytes(log[4:])
        raise ValueError("ABI return prefix not found")

    @property
    def bytes(self) -> algopy.Bytes:
        """Get the underlying Bytes."""
        import algopy

        return algopy.Bytes(self._value)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ABIEncoded):
            return self._type_info == other._type_info and self.bytes == other.bytes
        else:
            return NotImplemented

    def __hash__(self) -> int:
        return hash(self.bytes)


def arc4_signature(signature: str | Callable[_P, _R], /) -> algopy.Bytes:
    """Convert a signature to ARC4 bytes."""
    import algopy

    from _algopy_testing.decorators.arc4 import get_arc4_metadata

    if isinstance(signature, str):
        method_signature = signature
    else:
        arc4_signature = get_arc4_metadata(signature).arc4_signature
        if arc4_signature is None:
            raise ValueError("signature not found")
        method_signature = arc4_signature

    hashed_signature = SHA512.new(truncate="256")
    hashed_signature.update(method_signature.encode("utf-8"))
    return_value = hashed_signature.digest()[:4]
    return algopy.Bytes(return_value)


class _StringTypeInfo(_TypeInfo):
    @property
    def typ(self) -> type:
        return String

    @property
    def arc4_name(self) -> str:
        return "string"

    @property
    def is_dynamic(self) -> bool:
        return True


class String(_ABIEncoded):
    """An ARC4 sequence of bytes containing a UTF8 string."""

    _type_info = _StringTypeInfo()
    _value: bytes

    def __init__(self, value: algopy.String | str = "", /) -> None:
        import algopy

        match value:
            case algopy.String():
                bytes_value = as_bytes(value.bytes)
            case str(value):
                bytes_value = value.encode("utf-8")
            case _:
                raise TypeError(
                    f"value must be a string or String type, not {type(value).__name__!r}"
                )

        self._value = as_bytes(_encode_length(len(bytes_value)) + bytes_value)

    @property
    def native(self) -> algopy.String:
        """Return the String representation of the UTF8 string after ARC4 decoding."""
        import algopy

        return algopy.String.from_bytes(self._value[_ABI_LENGTH_SIZE:])

    def __add__(self, other: String | str) -> String:
        return String(self.native + as_string(other))

    def __radd__(self, other: String | str) -> String:
        return String(as_string(other) + self.native)

    def __eq__(self, other: String | str) -> bool:  # type: ignore[override]
        try:
            other_string = as_string(other)
        except TypeError:
            return NotImplemented
        return self.native == other_string

    def __bool__(self) -> bool:
        """Returns `True` if length is not zero."""
        return bool(self.native)

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


class _UIntTypeInfo(_TypeInfo):
    def __init__(self, size: int) -> None:
        self.bit_size = size
        if size <= UINT64_SIZE:
            self.max_bits_len = UINT64_SIZE
            self._type: type = UIntN
        else:
            self.max_bits_len = UINT512_SIZE
            self._type = BigUIntN
        self.max_int = 2**self.bit_size - 1
        self.max_bytes_len = self.bit_size // BITS_IN_BYTE

    @property
    def typ(self) -> type:
        return _parameterize_type(self._type, _create_int_literal(self.bit_size))

    @property
    def arc4_name(self) -> str:
        return f"uint{self.bit_size}"


# https://stackoverflow.com/a/75395800
class _UIntNMeta(type(_ABIEncoded), typing.Generic[_TBitSize]):  # type: ignore[misc]
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    def __getitem__(cls, key_t: type[_TBitSize]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c
        size = _get_int_literal(key_t)
        cache[key_t] = c = _new_parameterized_class(cls, [key_t], _UIntTypeInfo(size))
        return c


class _UIntN(_ABIEncoded, typing.Generic[_TBitSize], metaclass=_UIntNMeta):
    _type_info: _UIntTypeInfo
    _value: bytes  # underlying 'bytes' value representing the UIntN

    def __init__(
        self,
        value: algopy.BigUInt | algopy.UInt64 | int = 0,
        /,
    ) -> None:
        value = as_int(value, max=self._type_info.max_int)
        bytes_value = int_to_bytes(value, self._type_info.max_bytes_len)
        self._value = as_bytes(bytes_value)

    def __bool__(self) -> bool:
        """Returns `True` if not equal to zero."""
        raise NotImplementedError


@functools.total_ordering
class UIntN(_UIntN, typing.Generic[_TBitSize]):  # type: ignore[type-arg]
    """An ARC4 UInt consisting of the number of bits specified.

    Max Size: 64 bits
    """

    @property
    def native(self) -> algopy.UInt64:
        """Return the UInt64 representation of the value after ARC4 decoding."""
        import algopy

        return algopy.UInt64(int.from_bytes(self._value))

    def __eq__(self, other: object) -> bool:
        try:
            other_int = as_int64(other)
        except (TypeError, ValueError):
            return NotImplemented
        return as_int64(self.native) == other_int

    def __lt__(self, other: object) -> bool:
        try:
            other_int = as_int64(other)
        except (TypeError, ValueError):
            return NotImplemented
        return as_int64(self.native) < other_int

    def __bool__(self) -> bool:
        return bool(self.native)

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


@functools.total_ordering
class BigUIntN(_UIntN, typing.Generic[_TBitSize]):  # type: ignore[type-arg]
    """An ARC4 UInt consisting of the number of bits specified.

    Max size: 512 bits
    """

    @property
    def native(self) -> algopy.BigUInt:
        """Return the UInt64 representation of the value after ARC4 decoding."""
        import algopy

        return algopy.BigUInt.from_bytes(self._value)

    def __eq__(self, other: object) -> bool:
        try:
            other_int = as_int512(other)
        except (TypeError, ValueError):
            return NotImplemented
        return as_int512(self.native) == other_int

    def __lt__(self, other: object) -> bool:
        try:
            other_int = as_int512(other)
        except (TypeError, ValueError):
            return NotImplemented
        return as_int512(self.native) < other_int

    def __bool__(self) -> bool:
        return bool(self.native)

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


_TDecimalPlaces = typing.TypeVar("_TDecimalPlaces", bound=int)
_MAX_M_SIZE = 160


class _UFixedTypeInfo(_UIntTypeInfo):
    def __init__(self, size: int, precision: int) -> None:
        super().__init__(size)
        self.precision = precision

    @property
    def typ(self) -> type:
        return _parameterize_type(
            _UFixedNxM, _create_int_literal(self.bit_size), _create_int_literal(self.precision)
        )

    @property
    def arc4_name(self) -> str:
        return f"ufixed{self.bit_size}x{self.precision}"


class _UFixedNxMMeta(type(_ABIEncoded), typing.Generic[_TBitSize, _TDecimalPlaces]):  # type: ignore[misc]
    __concrete__: typing.ClassVar[dict[tuple[type, type], type]] = {}

    def __getitem__(cls, key_t: tuple[type[_TBitSize], type[_TDecimalPlaces]]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        size_t, precision_t = key_t
        size = _get_int_literal(size_t)
        precision = _get_int_literal(precision_t)
        cache[key_t] = c = _new_parameterized_class(
            cls,
            key_t,
            _UFixedTypeInfo(
                size=size,
                precision=precision,
            ),
        )
        return c


class _UFixedNxM(
    _ABIEncoded, typing.Generic[_TBitSize, _TDecimalPlaces], metaclass=_UFixedNxMMeta
):
    _type_info: _UFixedTypeInfo
    _value: bytes  # underlying 'bytes' value representing the UFixedNxM

    def __init__(self, value: str = "0.0", /) -> None:
        value = as_string(value)
        with decimal.localcontext(
            decimal.Context(
                prec=160,
                traps=[
                    decimal.Rounded,
                    decimal.InvalidOperation,
                    decimal.Overflow,
                    decimal.DivisionByZero,
                ],
            )
        ):
            try:
                d = decimal.Decimal(value)
            except ArithmeticError as ex:
                raise ValueError(f"Invalid decimal literal: {value}") from ex
            if d < 0:
                raise ValueError("Negative numbers not allowed")
            try:
                q = d.quantize(decimal.Decimal(f"1e-{self._type_info.precision}"))
            except ArithmeticError as ex:
                raise ValueError(
                    f"Too many decimals, expected max of {self._type_info.precision}"
                ) from ex

            int_value = round(q * (10**self._type_info.precision))
            int_value = as_int(int_value, max=self._type_info.max_int)
            bytes_value = int_to_bytes(int_value, self._type_info.max_bytes_len)
            self._value = as_bytes(bytes_value, max_size=self._type_info.max_bytes_len)

    def __bool__(self) -> bool:
        """Returns `True` if not equal to zero."""
        return bool(int.from_bytes(self._value))

    def __str__(self) -> str:
        int_str = str(int.from_bytes(self._value))
        whole = int_str[: -self._type_info.precision]
        fractional = int_str[-self._type_info.precision :]
        return f"{whole}.{fractional}"

    def __repr__(self) -> str:
        return _arc4_repr(self)


# implementations are effectively the same for these types
UFixedNxM = _UFixedNxM
BigUFixedNxM = _UFixedNxM


class _ByteTypeInfo(_UIntTypeInfo):
    def __init__(self) -> None:
        super().__init__(8)

    @property
    def typ(self) -> type:
        return Byte

    @property
    def arc4_name(self) -> str:
        return "byte"


class Byte(UIntN[typing.Literal[8]]):
    """An ARC4 alias for a UInt8."""

    _type_info = _ByteTypeInfo()


UInt8: typing.TypeAlias = UIntN[typing.Literal[8]]
UInt16: typing.TypeAlias = UIntN[typing.Literal[16]]
UInt32: typing.TypeAlias = UIntN[typing.Literal[32]]
UInt64: typing.TypeAlias = UIntN[typing.Literal[64]]
UInt128: typing.TypeAlias = BigUIntN[typing.Literal[128]]
UInt256: typing.TypeAlias = BigUIntN[typing.Literal[256]]
UInt512: typing.TypeAlias = BigUIntN[typing.Literal[512]]


class _BoolTypeInfo(_TypeInfo):
    @property
    def typ(self) -> type:
        return Bool

    @property
    def arc4_name(self) -> str:
        return "bool"


class Bool(_ABIEncoded):
    """An ARC4 encoded bool."""

    _type_info = _BoolTypeInfo()
    _value: bytes

    # True value is encoded as having a 1 on the most significant bit (0x80 = 128)
    _true_int_value = 128
    _false_int_value = 0

    def __init__(self, value: bool = False, /) -> None:  # noqa: FBT001, FBT002
        self._value = int_to_bytes(self._true_int_value if value else self._false_int_value, 1)

    def __bool__(self) -> bool:
        """Allow Bool to be used in boolean contexts."""
        return self.native

    @property
    def native(self) -> bool:
        """Return the bool representation of the value after ARC4 decoding."""
        int_value = int.from_bytes(self._value)
        return int_value == self._true_int_value

    def __str__(self) -> str:
        return f"{self.native}"

    def __repr__(self) -> str:
        return _arc4_repr(self)


_TArrayItem = typing.TypeVar("_TArrayItem", bound=_ABIEncoded)
_TArrayLength = typing.TypeVar("_TArrayLength", bound=int)


class _StaticArrayTypeInfo(_TypeInfo):
    def __init__(self, item_type: _TypeInfo, size: int):
        self.item_type = item_type
        self.size = size

    @property
    def typ(self) -> type:
        return _parameterize_type(StaticArray, self.item_type.typ, _create_int_literal(self.size))

    @property
    def arc4_name(self) -> str:
        return f"{self.item_type.arc4_name}[{self.size}]"

    @property
    def is_dynamic(self) -> bool:
        return self.item_type.is_dynamic


class _StaticArrayMeta(type(_ABIEncoded), typing.Generic[_TArrayItem, _TArrayLength]):  # type: ignore  # noqa: PGH003
    __concrete__: typing.ClassVar[dict[tuple[type, type], type]] = {}

    def __getitem__(cls, key_t: tuple[type[_TArrayItem], type[_TArrayLength]]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        item_t, size_t = key_t
        assert issubclass(item_t, _ABIEncoded)
        size = _get_int_literal(size_t)
        cache[key_t] = c = _new_parameterized_class(
            cls,
            key_t,
            _StaticArrayTypeInfo(
                item_type=item_t._type_info,
                size=size,
            ),
        )
        return c


class StaticArray(
    _ABIEncoded,
    MutableBytes,
    typing.Generic[_TArrayItem, _TArrayLength],
    metaclass=_StaticArrayMeta,
):
    """A fixed length ARC4 Array of the specified type and length."""

    _type_info: _StaticArrayTypeInfo

    def __new__(cls, *items: _TArrayItem) -> typing.Self:
        try:
            assert cls._type_info
        except AttributeError:
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            size = len(items)
            cls = _parameterize_type(cls, type(item), _create_int_literal(size))
        instance = super().__new__(cls)
        return instance

    def __init__(self, *_items: _TArrayItem):
        super().__init__()
        items = _check_is_arc4(_items)
        for item in items:
            if len(items) != self._type_info.size:
                raise TypeError(f"expected {self._type_info.size} items, not {len(items)}")
            if self._type_info.item_type != item._type_info:
                raise TypeError(
                    f"item must be of type {self._type_info.item_type!r}, not {item._type_info!r}"
                )
        self._value = _encode(items)

    def __iter__(self) -> Iterator[_TArrayItem]:
        # """Returns an iterator for the items in the array"""
        return iter(self._list())

    def __reversed__(self) -> Iterator[_TArrayItem]:
        # """Returns an iterator for the items in the array, in reverse order"""
        return reversed(self._list())

    @property
    def length(self) -> algopy.UInt64:
        # """Returns the current length of the array"""
        import algopy

        return algopy.UInt64(self._type_info.size)

    def __getitem__(self, index: algopy.UInt64 | int) -> _TArrayItem:
        value = self._list()[index]
        return set_item_on_mutate(self, index, value)

    def __setitem__(self, index: algopy.UInt64 | int, item: _TArrayItem) -> _TArrayItem:
        if item._type_info != self._type_info.item_type:
            raise TypeError(
                f"item must be of type {self._type_info.item_type!r}, not {item._type_info!r}"
            )
        x = self._list()
        x[index] = item
        self._value = _encode(x)
        return item

    def _list(self) -> list[_TArrayItem]:
        return _decode_tuple_items(self._value, [self._type_info.item_type] * self._type_info.size)

    def __str__(self) -> str:
        items = map(str, self._list())
        return f"[{', '.join(items)}]"

    def __repr__(self) -> str:
        items = map(repr, self._list())
        return f"{_arc4_type_repr(type(self))}({', '.join(items)})"


class _AddressTypeInfo(_StaticArrayTypeInfo):
    def __init__(self) -> None:
        super().__init__(Byte._type_info, 32)

    @property
    def typ(self) -> type:
        return Address

    @property
    def arc4_name(self) -> str:
        return "address"


class Address(StaticArray[Byte, typing.Literal[32]]):
    _type_info = _AddressTypeInfo()

    def __init__(self, value: Account | str | algopy.Bytes = algosdk.constants.ZERO_ADDRESS):
        super().__init__()
        if isinstance(value, str):
            try:
                bytes_value = algosdk.encoding.decode_address(value)
            except Exception as e:
                raise ValueError(f"cannot encode the following address: {value!r}") from e
        elif isinstance(value, Account):
            bytes_value = value.bytes.value
        else:
            bytes_value = as_bytes(value)
        if len(bytes_value) != 32:
            raise ValueError(f"expected 32 bytes, got: {len(bytes_value)}")
        self._value = bytes_value

    @property
    def native(self) -> Account:
        # """Return the Account representation of the address after ARC4 decoding"""
        return Account(self.bytes)

    def __bool__(self) -> bool:
        # """Returns `True` if not equal to the zero address"""
        zero_bytes: bytes = algosdk.encoding.decode_address(algosdk.constants.ZERO_ADDRESS)
        return self.bytes != zero_bytes

    def __eq__(self, other: Address | Account | str) -> bool:  # type: ignore[override]
        """Address equality is determined by the address of another `arc4.Address`,
        `Account` or `str`"""
        if isinstance(other, Address | Account):
            return self.bytes == other.bytes
        elif isinstance(other, str):
            other_bytes: bytes = algosdk.encoding.decode_address(other)
            return self.bytes == other_bytes
        else:
            return NotImplemented

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


class _DynamicArrayTypeInfo(_TypeInfo):
    def __init__(self, item_type: _TypeInfo):
        self.item_type = item_type

    @property
    def typ(self) -> type:
        return _parameterize_type(DynamicArray, self.item_type.typ)

    @property
    def arc4_name(self) -> str:
        return f"{self.item_type.arc4_name}[]"

    @property
    def is_dynamic(self) -> bool:
        return True


class _DynamicArrayMeta(type(_ABIEncoded), typing.Generic[_TArrayItem]):  # type: ignore[misc]
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    def __getitem__(cls, key_t: type[_TArrayItem]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        cache[key_t] = c = _new_parameterized_class(
            cls, [key_t], _DynamicArrayTypeInfo(key_t._type_info)
        )
        return c


class DynamicArray(  # TODO: inherit from StaticArray?
    _ABIEncoded,
    MutableBytes,
    typing.Generic[_TArrayItem],
    metaclass=_DynamicArrayMeta,
):
    """A dynamically sized ARC4 Array of the specified type."""

    _type_info: _DynamicArrayTypeInfo

    def __new__(cls, *items: _TArrayItem) -> typing.Self:
        try:
            assert cls._type_info
        except AttributeError:
            try:
                item = items[0]
            except IndexError:
                raise TypeError("array must have an item type") from None
            cls = _parameterize_type(cls, type(item))
        instance = super().__new__(cls)
        return instance

    def __init__(self, *_items: _TArrayItem):
        super().__init__()
        items = _check_is_arc4(_items)
        for item in items:
            if self._type_info.item_type != item._type_info:
                raise TypeError(
                    f"item must be of type {self._type_info.item_type!r}, not {item._type_info!r}"
                )
        self._value = self._encode_with_length(items)

    def __iter__(self) -> typing.Iterator[_TArrayItem]:
        """Returns an iterator for the items in the array."""
        return iter(self._list())

    def __reversed__(self) -> typing.Iterator[_TArrayItem]:
        """Returns an iterator for the items in the array, in reverse order."""
        return reversed(self._list())

    @property
    def length(self) -> algopy.UInt64:
        """Returns the current length of the array."""
        import algopy

        return algopy.UInt64(len(self._list()))

    def __getitem__(self, index: algopy.UInt64 | int) -> _TArrayItem:
        value = self._list()[index]
        return set_item_on_mutate(self, index, value)

    def __setitem__(self, index: algopy.UInt64 | int, item: _TArrayItem) -> _TArrayItem:
        if item._type_info != self._type_info.item_type:
            raise TypeError(
                f"item must be of type {self._type_info.item_type!r}, not {item._type_info!r}"
            )
        x = self._list()
        x[index] = item
        self._value = self._encode_with_length(x)
        return item

    def append(self, item: _TArrayItem, /) -> None:
        """Append items to this array."""
        if item._type_info != self._type_info.item_type:
            raise TypeError(
                f"item must be of type {self._type_info.item_type!r}, not {item._type_info!r}"
            )
        x = self._list()
        x.append(item)
        self._value = self._encode_with_length(x)

    def extend(self, other: Iterable[_TArrayItem], /) -> None:
        """Extend this array with the contents of another array."""
        incorrect_types = [
            o._type_info for o in other if o._type_info != self._type_info.item_type
        ]
        if incorrect_types:
            other_types_str = ", ".join(sorted(set(map(str, incorrect_types))))
            raise TypeError(
                f"items must be of type {self._type_info.item_type!r}: {other_types_str}"
            )
        x = self._list()
        x.extend(other)
        self._value = self._encode_with_length(x)

    def __add__(self, other: Iterable[_TArrayItem]) -> typing.Self:
        self.extend(other)
        return self

    def pop(self) -> _TArrayItem:
        """Remove and return the last item in the array."""
        x = self._list()
        item = x.pop()
        self._value = self._encode_with_length(x)
        return item

    def __bool__(self) -> bool:
        """Returns `True` if not an empty array."""
        return bool(self._list())

    def _list(self) -> list[_TArrayItem]:
        length, data = _read_length(self._value)
        return _decode_tuple_items(data, [self._type_info.item_type] * length)

    def _encode_with_length(self, items: Sequence[_ABIEncoded]) -> bytes:
        return _encode_length(len(items)) + _encode(items)

    def __str__(self) -> str:
        items = map(str, self._list())
        return f"[{', '.join(items)}]"

    def __repr__(self) -> str:
        items = map(repr, self._list())
        return f"{_arc4_type_repr(type(self))}({', '.join(items)})"


class DynamicBytes(DynamicArray[Byte]):
    """A variable sized array of bytes."""

    @typing.overload
    def __init__(self, *values: Byte | UInt8 | int): ...

    @typing.overload
    def __init__(self, value: algopy.Bytes | bytes, /): ...

    def __init__(self, *value: algopy.Bytes | bytes | Byte | UInt8 | int):
        items = []
        for x in value:
            match x:
                case Bytes() | bytes():
                    if len(value) > 1:
                        raise ValueError("expected single Bytes value")
                    items.extend([Byte(b) for b in as_bytes(x)])
                case UIntN(_type_info=_UIntTypeInfo(bit_size=8)) as uint:
                    items.append(Byte(as_int(uint.native, max=2**8)))
                case int(int_value):
                    items.append(Byte(int_value))
                case _:
                    raise TypeError("expected algopy.Bytes | bytes | Byte | UInt8 | int")
        super().__init__(*items)

    @property
    def native(self) -> algopy.Bytes:
        return self.bytes[_ABI_LENGTH_SIZE:]

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


_TTuple = typing.TypeVarTuple("_TTuple")


class _TupleTypeInfo(_TypeInfo):
    def __init__(self, child_types: list[_TypeInfo]) -> None:
        self.child_types = child_types

    @property
    def typ(self) -> type:
        return _parameterize_type(Tuple, *(t.typ for t in self.child_types))

    @property
    def arc4_name(self) -> str:
        inner_name = ",".join([t.arc4_name for t in self.child_types])
        return f"({inner_name})"

    @property
    def is_dynamic(self) -> bool:
        return any(t.is_dynamic for t in self.child_types)


class _TupleMeta(type(_ABIEncoded), typing.Generic[typing.Unpack[_TTuple]]):  # type: ignore  # noqa: PGH003
    __concrete__: typing.ClassVar[dict[tuple, type]] = {}  # type: ignore[type-arg]

    def __getitem__(cls, key_t: tuple[type[_ABIEncoded], ...]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        cache[key_t] = c = _new_parameterized_class(
            cls, key_t, _TupleTypeInfo([t._type_info for t in key_t])
        )
        return c


class Tuple(
    _ABIEncoded,
    MutableBytes,
    tuple[typing.Unpack[_TTuple]],
    typing.Generic[typing.Unpack[_TTuple]],
    metaclass=_TupleMeta,
):
    """An ARC4 ABI tuple, containing other ARC4 ABI types."""

    __slots__ = ()  # to satisfy SLOT001
    _type_info: _TupleTypeInfo

    def __new__(
        cls,
        items: tuple[typing.Unpack[_TTuple]] = (),  # type: ignore[assignment]
    ) -> typing.Self:
        try:
            assert cls._type_info
        except AttributeError:
            if not items:
                raise TypeError("empty tuple not supported") from None
            cls = _parameterize_type(cls, *map(type, items))
        instance = super().__new__(cls)
        return instance

    def __init__(self, _items: tuple[typing.Unpack[_TTuple]] = (), /):  # type: ignore[assignment]
        super().__init__()
        items = _check_is_arc4(_items)
        if items:
            for item, expected_type in zip(items, self._type_info.child_types, strict=True):
                item_type_info = item._type_info
                if expected_type != item_type_info:
                    raise TypeError(
                        f"item must be of type {self._type_info!r}, not {item_type_info!r}"
                    )
        self._value = _encode(items)

    def __len__(self) -> int:
        return len(self.native)

    def __getitem__(self, index: int) -> object:  # type: ignore[override]
        value = self.native[index]

        # can't mutate tuple, but can re-encode underlying _value
        def _set_value(updated_value: object) -> None:
            items = self.native
            new_items = items[:index] + (updated_value, items[index + 1 :])
            self._value = _encode(new_items)

        return add_mutable_callback(_set_value, value)

    def __iter__(self) -> typing.Iterator[_ABIEncoded]:
        return iter(self.native)  # type: ignore[arg-type]

    @property
    def native(self) -> tuple[typing.Unpack[_TTuple]]:
        return typing.cast(
            tuple[typing.Unpack[_TTuple]],
            tuple(_decode_tuple_items(self._value, self._type_info.child_types)),
        )

    def __str__(self) -> str:
        return str(self.native)

    def __repr__(self) -> str:
        return _arc4_repr(self)


class _StructTypeInfo(_TypeInfo):
    def __init__(self, struct_type: type[Struct], *, frozen: bool) -> None:
        self.struct_type = struct_type
        self.fields = dataclasses.fields(struct_type)
        self.field_names = [field.name for field in self.fields]
        self.frozen = frozen

    @property
    def typ(self) -> type:
        return self.struct_type

    @property
    def child_types(self) -> list[_TypeInfo]:
        return _tuple_type_from_struct(self.struct_type)._type_info.child_types

    @property
    def arc4_name(self) -> str:
        inner_name = ",".join([t.arc4_name for t in self.child_types])
        return f"({inner_name})"

    @property
    def is_dynamic(self) -> bool:
        return any(t.is_dynamic for t in self.child_types)


@typing.dataclass_transform(
    eq_default=False, order_default=False, kw_only_default=False, field_specifiers=()
)
class _StructMeta(type):
    pass


def _tuple_type_from_struct(struct: type[Struct]) -> type[Tuple]:  # type: ignore[type-arg]
    field_types = [f.type for f in struct._type_info.fields]
    return _parameterize_type(Tuple, *field_types)


class Struct(MutableBytes, _ABIEncoded, metaclass=_StructMeta):  # type: ignore[misc]
    """Base class for ARC4 Struct types."""

    _type_info: typing.ClassVar[_StructTypeInfo]  # type: ignore[misc]

    def __init_subclass__(cls, *args: typing.Any, **kwargs: dict[str, typing.Any]) -> None:
        # make implementation not frozen, so we can conditionally control behaviour
        dataclasses.dataclass(cls, *args, **{**kwargs, "frozen": False})
        frozen = kwargs.get("frozen", False)
        assert isinstance(frozen, bool)
        cls._type_info = _StructTypeInfo(cls, frozen=frozen)

    def __post_init__(self) -> None:
        # calling base class here to init Mutable
        # see https://docs.python.org/3/library/dataclasses.html#post-init-processing
        super().__init__()
        self._update_backing_value()

    def __getattribute__(self, name: str) -> typing.Any:
        value = super().__getattribute__(name)
        return add_mutable_callback(lambda _: self._update_backing_value(), value)

    def __setattr__(self, key: str, value: typing.Any) -> None:
        super().__setattr__(key, value)
        # don't update backing value until base class has been init'd
        if hasattr(self, "_on_mutate") and key in self._type_info.field_names:
            if self._type_info.frozen:
                raise dataclasses.FrozenInstanceError(
                    f"{type(self)} is frozen and cannot be modified"
                )
            self._update_backing_value()

    def _update_backing_value(self) -> None:
        self._value = self._as_tuple._value

    @classmethod
    def from_bytes(cls, value: algopy.Bytes | bytes, /) -> typing.Self:
        tuple_type = _tuple_type_from_struct(cls)
        tuple_value = tuple_type.from_bytes(value)
        return cls(*tuple_value.native)

    @property
    def bytes(self) -> algopy.Bytes:
        """Get the underlying bytes[]"""
        return self._as_tuple.bytes

    @property
    def _as_tuple(self) -> Tuple:  # type: ignore[type-arg]
        # can't use dataclass.astuple here as that processes all dataclasses
        # in the object graph, not just immediate fields
        tuple_items = tuple(getattr(self, field.name) for field in dataclasses.fields(self))
        return Tuple(tuple_items)

    def _replace(self, **kwargs: typing.Any) -> typing.Self:
        copy = self.copy()
        for field, value in kwargs.items():
            setattr(copy, field, value)
        return copy


class ARC4Client:
    pass


class _ABICall:
    def __init__(self, func_name: str) -> None:
        self.func_name = func_name

    def __call__(
        self,
        _method: typing.Callable[..., typing.Any] | str,
        /,
        *_args: typing.Any,
        **_kwargs: typing.Any,
    ) -> typing.Any:
        # Implement the actual abi_call logic here
        raise_mocked_function_error(self.func_name)

    def __getitem__(self, return_type: type) -> typing.Any:
        return self


# TODO: Implement these when calling other puya contracts
abi_call = _ABICall("abi_call")
arc4_create = _ABICall("arc4_create")
arc4_update = _ABICall("arc4_update")


def emit(event: str | Struct, /, *args: object) -> None:
    from _algopy_testing.utilities.log import log

    if isinstance(event, str):
        arc4_args = tuple(_cast_arg_as_arc4(arg) for arg in args)
        struct = Tuple(arc4_args)
        arg_types = struct._type_info.arc4_name
        if event.find("(") == -1:
            event += arg_types
        elif event.find(arg_types) == -1:
            raise ValueError(f"Event signature {event} does not match arg types {arg_types}")
        event_str = event
        event_data = struct.bytes
    elif isinstance(event, Struct):
        event_str = type(event).__name__ + event._type_info.arc4_name
        event_data = event.bytes
    else:
        raise TypeError("expected str or Struct for event")

    event_hash = SHA512.new(event_str.encode(), truncate="256").digest()
    log(event_hash[:4] + event_data.value)


def _cast_arg_as_arc4(arg: object) -> _ABIEncoded:
    from _algopy_testing.serialize import native_to_arc4

    if isinstance(arg, int) and not isinstance(arg, bool):
        return UInt64(arg) if arg <= MAX_UINT64 else UInt512(arg)
    if isinstance(arg, bytes):
        return DynamicBytes(arg)
    if isinstance(arg, str):
        return String(arg)
    return native_to_arc4(arg)


def _find_bool(
    values: (
        StaticArray[typing.Any, typing.Any]
        | DynamicArray[typing.Any]
        | Tuple[typing.Any]
        | tuple[typing.Any, ...]
        | list[typing.Any]
    ),
    index: int,
    delta: int,
) -> int:
    """Helper function to find consecutive booleans from current index in a tuple."""
    until = 0
    is_looking_forward = delta > 0
    is_looking_backward = delta < 0
    values_length = len(values) if isinstance(values, tuple | list) else values.length.value
    while True:
        curr = index + delta * until
        is_curr_at_end = curr == values_length - 1
        is_curr_at_start = curr == 0
        if isinstance(values[curr], Bool):
            if (is_looking_forward and not is_curr_at_end) or (
                is_looking_backward and not is_curr_at_start
            ):
                until += 1
            else:
                break
        else:
            until -= 1
            break
    return until


def _find_bool_types(values: typing.Sequence[_TypeInfo], index: int, delta: int) -> int:
    """Helper function to find consecutive booleans from current index in a tuple."""
    until = 0
    is_looking_forward = delta > 0
    is_looking_backward = delta < 0
    values_length = len(values)
    while True:
        curr = index + delta * until
        is_curr_at_end = curr == values_length - 1
        is_curr_at_start = curr == 0
        if isinstance(values[curr], _BoolTypeInfo):
            if (is_looking_forward and not is_curr_at_end) or (
                is_looking_backward and not is_curr_at_start
            ):
                until += 1
            else:
                break
        else:
            until -= 1
            break
    return until


def _compress_multiple_bool(value_list: list[Bool]) -> int:
    """Compress consecutive boolean values into a byte for a Tuple/Array."""
    result = 0
    if len(value_list) > 8:
        raise ValueError("length of list should not be greater than 8")
    for i, value in enumerate(value_list):
        assert isinstance(value, Bool)
        bool_val = value.native
        if bool_val:
            result |= 1 << (7 - i)
    return result


def _get_max_bytes_len(type_info: _TypeInfo) -> int:
    size = 0
    if isinstance(type_info, _DynamicArrayTypeInfo):
        size += _ABI_LENGTH_SIZE
    elif isinstance(type_info, _TupleTypeInfo | _StructTypeInfo | _StaticArrayTypeInfo):
        i = 0
        if isinstance(type_info, _TupleTypeInfo | _StructTypeInfo):
            child_types = type_info.child_types
        else:
            typing.assert_type(type_info, _StaticArrayTypeInfo)
            child_types = [type_info.item_type] * type_info.size
        while i < len(child_types):
            if isinstance(child_types[i], _BoolTypeInfo):
                after = _find_bool_types(child_types, i, 1)
                i += after
                bool_num = after + 1
                size += bool_num // 8
                if bool_num % 8 != 0:
                    size += 1
            else:
                child_byte_size = _get_max_bytes_len(child_types[i])
                size += child_byte_size
            i += 1
    elif isinstance(type_info, _UIntTypeInfo):
        size = type_info.max_bytes_len

    return size


def _encode(  # noqa: PLR0912
    values: (
        StaticArray[typing.Any, typing.Any]
        | DynamicArray[typing.Any]
        | Tuple[typing.Any]
        | Struct
        | Sequence[typing.Any]
    ),
) -> bytes:
    heads = []
    tails = []
    is_dynamic_index = []
    i = 0
    if isinstance(values, Struct):
        values = values._as_tuple
    match values:
        case (StaticArray() | DynamicArray()) as has_length:
            values_length = has_length.length.value
        case tuple() | list() as can_len:
            values_length = len(can_len)
        case _:
            raise TypeError("expected sized type")
    values_length_bytes = (
        _encode_length(values_length) if isinstance(values, DynamicArray) else b""
    )
    while i < values_length:
        value = values[i]
        assert isinstance(value, _ABIEncoded), "expected ARC4 value"
        is_dynamic_index.append(value._type_info.is_dynamic)
        if is_dynamic_index[-1]:
            heads.append(b"\x00\x00")
            assert isinstance(
                value, StaticArray | DynamicArray | Tuple | String | Struct
            ), f"expected dynamic type: {value}"
            tail_encoding = value.bytes.value if isinstance(value, String) else _encode(value)
            tails.append(tail_encoding)
        else:
            if isinstance(value, Bool):
                before = _find_bool(values, i, -1)
                after = _find_bool(values, i, 1)

                # Pack bytes to heads and tails
                if before % 8 != 0:
                    raise ValueError(
                        "expected before index should have number of bool mod 8 equal 0"
                    )
                after = min(7, after)
                consecutive_bool_list = [values[i] for i in range(i, i + after + 1)]
                compressed_int = _compress_multiple_bool(consecutive_bool_list)
                heads.append(bytes([compressed_int]))
                i += after
            else:
                heads.append(value.bytes.value)
            tails.append(b"")
        i += 1

    # Adjust heads for dynamic types
    head_length = 0
    for head_element in heads:
        # If the element is not a placeholder, append the length of the element
        head_length += len(head_element)

    # Correctly encode dynamic types and replace placeholder
    tail_curr_length = 0
    for i in range(len(heads)):
        if is_dynamic_index[i]:
            head_value = as_int16(head_length + tail_curr_length)
            heads[i] = int_to_bytes(head_value, _ABI_LENGTH_SIZE)

        tail_curr_length += len(tails[i])

    # Concatenate bytes
    return values_length_bytes + b"".join(heads) + b"".join(tails)


def _decode_tuple_items(  # noqa: PLR0912
    value: bytes, child_types: list[_TypeInfo]
) -> list[typing.Any]:
    dynamic_segments: list[list[int]] = []  # Store the start and end of a dynamic element
    value_partitions: list[bytes] = []
    i = 0
    array_index = 0

    while i < len(child_types):
        child_type = child_types[i]
        if child_type.is_dynamic:
            # Decode the size of the dynamic element
            dynamic_index = int.from_bytes(value[array_index : array_index + _ABI_LENGTH_SIZE])
            if dynamic_segments:
                dynamic_segments[-1][1] = dynamic_index

            # Since we do not know where the current dynamic element ends,
            # put a placeholder and update later
            dynamic_segments.append([dynamic_index, -1])
            value_partitions.append(b"")
            array_index += _ABI_LENGTH_SIZE
        elif isinstance(child_type, _BoolTypeInfo):
            before = _find_bool_types(child_types, i, -1)
            after = _find_bool_types(child_types, i, 1)

            if before % 8 != 0:
                raise ValueError("expected before index should have number of bool mod 8 equal 0")
            after = min(7, after)
            bits = int.from_bytes(value[array_index : array_index + 1])
            # Parse bool values into multiple byte strings
            for bool_i in range(after + 1):
                mask = 128 >> bool_i
                if mask & bits:
                    value_partitions.append(b"\x80")
                else:
                    value_partitions.append(b"\x00")
            i += after
            array_index += 1
        else:
            curr_len = _get_max_bytes_len(child_type)
            value_partitions.append(value[array_index : array_index + curr_len])
            array_index += curr_len

        if array_index >= len(value) and i != len(child_types) - 1:
            raise ValueError(f"input string is not long enough to be decoded: {value!r}")

        i += 1

    if len(dynamic_segments) > 0:
        dynamic_segments[len(dynamic_segments) - 1][1] = len(value)
        array_index = len(value)
    if array_index < len(value):
        raise ValueError(f"input string was not fully consumed: {value!r}")

    # Check dynamic element partitions
    segment_index = 0
    for i, child_type in enumerate(child_types):
        if child_type.is_dynamic:
            segment_start, segment_end = dynamic_segments[segment_index]
            value_partitions[i] = value[segment_start:segment_end]
            segment_index += 1

    # Decode individual tuple elements
    values = []
    for child_type, child_value in zip(child_types, value_partitions, strict=False):
        cls = child_type.typ
        assert issubclass(cls, _ABIEncoded | Struct), "expected ARC4 type"
        assert child_value is not None, "expected ARC4 value"
        val = cls.from_bytes(child_value)
        values.append(val)
    return values


def _encode_length(length: int) -> bytes:
    return length.to_bytes(_ABI_LENGTH_SIZE)


def _read_length(value: bytes) -> tuple[int, bytes]:
    length = int.from_bytes(value[:_ABI_LENGTH_SIZE])
    data = value[_ABI_LENGTH_SIZE:]
    return length, data


def _arc4_repr(value: object) -> str:
    return f"{_arc4_type_repr(type(value))}({value!s})"


def _arc4_type_repr(value: type) -> str:
    return f"arc4.{value.__name__}"
