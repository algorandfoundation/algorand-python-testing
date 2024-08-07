from __future__ import annotations

import copy
import decimal
import types
import typing
from collections import ChainMap

import algosdk
from Cryptodome.Hash import SHA512

from algopy_testing._context_storage import get_test_context
from algopy_testing.constants import (
    ARC4_RETURN_PREFIX,
    BITS_IN_BYTE,
    MAX_UINT64,
    UINT64_SIZE,
    UINT512_SIZE,
)
from algopy_testing.decorators.arc4 import abimethod, baremethod
from algopy_testing.models.account import Account
from algopy_testing.primitives import Bytes
from algopy_testing.protocols import BytesBacked
from algopy_testing.utils import (
    as_bytes,
    as_int,
    as_int16,
    as_int64,
    as_int512,
    as_string,
    int_to_bytes,
)

if typing.TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    import algopy

__all__ = [
    "ARC4Client",
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
    "UInt128",
    "UInt16",
    "UInt256",
    "UInt32",
    "UInt512",
    "UInt64",
    "UInt8",
    "UIntN",
    "abi_call",
    "abimethod",
    "arc4_signature",
    "baremethod",
    "emit",
]

_ABI_LENGTH_SIZE = 2
_TBitSize = typing.TypeVar("_TBitSize", bound=int)


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
        return self.typ.__name__


def _get_int_literal(literal_type: type) -> int:
    type_args = typing.get_args(literal_type)
    try:
        (int_arg,) = type_args
    except ValueError:
        int_arg = 0
    return int(int_arg)


class _ABIEncoded(BytesBacked):
    type_info: _TypeInfo
    _value: bytes

    def __init__(self, *, type_info: _TypeInfo | None = None):
        if type_info:
            self.type_info = type_info
        else:
            try:
                self.type_info = self.type_info
            except AttributeError:
                self.type_info = None  # type: ignore[assignment]

    @classmethod
    def from_bytes(
        cls, value: algopy.Bytes | bytes, /, *, type_info: _TypeInfo | None = None
    ) -> typing.Self:
        """Construct an instance from the underlying bytes (no validation)"""
        instance = cls(type_info=type_info)
        instance._value = as_bytes(value)
        return instance

    @classmethod
    def from_log(cls, log: algopy.Bytes, /) -> typing.Self:
        """Load an ABI type from application logs, checking for the ABI return
        prefix `0x151f7c75`"""
        if log[:4] == ARC4_RETURN_PREFIX:
            return cls.from_bytes(log[4:])
        raise ValueError("ABI return prefix not found")

    @property
    def bytes(self) -> algopy.Bytes:
        """Get the underlying Bytes."""
        import algopy

        return algopy.Bytes(self._value)


def arc4_signature(signature: str, /) -> algopy.Bytes:
    """Convert a signature to ARC4 bytes."""
    import algopy

    hashed_signature = SHA512.new(truncate="256")
    hashed_signature.update(signature.encode("utf-8"))
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

    type_info = _StringTypeInfo()
    _value: bytes

    def __init__(
        self, value: algopy.String | str = "", /, *, type_info: _TypeInfo | None = None
    ) -> None:
        super().__init__(type_info=type_info)
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

        self._value = len(bytes_value).to_bytes(_ABI_LENGTH_SIZE) + bytes_value

    @property
    def native(self) -> algopy.String:
        """Return the String representation of the UTF8 string after ARC4
        decoding."""
        import algopy

        return algopy.String.from_bytes(self._value[_ABI_LENGTH_SIZE:])

    def __add__(self, other: String | str) -> String:
        return String(self.native + as_string(other))

    def __radd__(self, other: String | str) -> String:
        return String(as_string(other) + self.native)

    def __eq__(self, other: String | str) -> bool:  # type: ignore[override]
        return self.native == as_string(other)

    def __bool__(self) -> bool:
        """Returns `True` if length is not zero."""
        return bool(self.native)


class _UIntTypeInfo(_TypeInfo):

    def __init__(self, size: int, alias: str | None = None) -> None:
        self.bit_size = size
        if size <= UINT64_SIZE:
            self.max_bits_len = UINT64_SIZE
            self._type: type = UIntN
        else:
            self.max_bits_len = UINT512_SIZE
            self._type = BigUIntN
        self.max_int = 2**self.bit_size - 1
        self.max_bytes_len = self.bit_size // BITS_IN_BYTE
        self.alias = alias

    @property
    def typ(self) -> type:
        return self._type

    @property
    def arc4_name(self) -> str:
        return self.alias or f"uint{self.bit_size}"


# https://stackoverflow.com/a/75395800
class _UIntNMeta(type(_ABIEncoded), typing.Generic[_TBitSize]):  # type: ignore[misc]
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    def __getitem__(cls, key_t: type[_TBitSize]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c
        size = _get_int_literal(key_t)
        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{key_t.__name__}]",
            (cls,),
            {},
            lambda ns: ns.update(
                _t=key_t,
                type_info=_UIntTypeInfo(size),
            ),
        )
        return c


class _UIntN(_ABIEncoded, typing.Generic[_TBitSize], metaclass=_UIntNMeta):
    type_info: _UIntTypeInfo
    _value: bytes  # underlying 'bytes' value representing the UIntN

    def __init__(
        self,
        value: algopy.BigUInt | algopy.UInt64 | int = 0,
        /,
        *,
        type_info: _TypeInfo | None = None,
    ) -> None:
        super().__init__(type_info=type_info)
        value = as_int(value, max=self.type_info.max_int)
        bytes_value = int_to_bytes(value, self.type_info.max_bytes_len)
        self._value = as_bytes(bytes_value)

    # ~~~ https://docs.python.org/3/reference/datamodel.html#basic-customization ~~~
    # TODO: mypy suggests due to Liskov below should be other: object
    #       need to consider ramifications here, ignoring it for now
    def __eq__(  # type: ignore[override]
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __ne__(  # type: ignore[override]
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __le__(
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __lt__(
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __ge__(
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __gt__(
        self,
        other: UIntN[_TBitSize] | BigUIntN[_TBitSize] | algopy.UInt64 | algopy.BigUInt | int,
    ) -> bool:
        raise NotImplementedError

    def __bool__(self) -> bool:
        """Returns `True` if not equal to zero."""
        raise NotImplementedError


class UIntN(_UIntN, typing.Generic[_TBitSize]):  # type: ignore[type-arg]
    """An ARC4 UInt consisting of the number of bits specified.

    Max Size: 64 bits
    """

    @property
    def native(self) -> algopy.UInt64:
        """Return the UInt64 representation of the value after ARC4
        decoding."""
        import algopy

        return algopy.UInt64(int.from_bytes(self._value))

    def __eq__(self, other: object) -> bool:
        return as_int64(self.native) == as_int(other, max=None)

    def __ne__(self, other: object) -> bool:
        return as_int64(self.native) != as_int(other, max=None)

    def __le__(self, other: object) -> bool:
        return as_int64(self.native) <= as_int(other, max=None)

    def __lt__(self, other: object) -> bool:
        return as_int64(self.native) < as_int(other, max=None)

    def __ge__(self, other: object) -> bool:
        return as_int64(self.native) >= as_int(other, max=None)

    def __gt__(self, other: object) -> bool:
        return as_int64(self.native) > as_int(other, max=None)

    def __bool__(self) -> bool:
        return bool(self.native)


class BigUIntN(_UIntN, typing.Generic[_TBitSize]):  # type: ignore[type-arg]
    """An ARC4 UInt consisting of the number of bits specified.

    Max size: 512 bits
    """

    @property
    def native(self) -> algopy.BigUInt:
        """Return the UInt64 representation of the value after ARC4
        decoding."""
        import algopy

        return algopy.BigUInt.from_bytes(self._value)

    def __eq__(self, other: object) -> bool:
        return as_int512(self.native) == as_int(other, max=None)

    def __ne__(self, other: object) -> bool:
        return as_int512(self.native) != as_int(other, max=None)

    def __le__(self, other: object) -> bool:
        return as_int512(self.native) <= as_int(other, max=None)

    def __lt__(self, other: object) -> bool:
        return as_int512(self.native) < as_int(other, max=None)

    def __ge__(self, other: object) -> bool:
        return as_int512(self.native) >= as_int(other, max=None)

    def __gt__(self, other: object) -> bool:
        return as_int512(self.native) > as_int(other, max=None)

    def __bool__(self) -> bool:
        return bool(self.native)


_TDecimalPlaces = typing.TypeVar("_TDecimalPlaces", bound=int)
_MAX_M_SIZE = 160


class _UFixedTypeInfo(_UIntTypeInfo):

    def __init__(self, size: int, precision: int) -> None:
        super().__init__(size)
        self.precision = precision

    @property
    def typ(self) -> type:
        return _UFixedNxM

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
        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{size_t.__name__}, {precision_t.__name__}]",
            (cls,),
            {},
            lambda ns: ns.update(
                type_info=_UFixedTypeInfo(
                    size=size,
                    precision=precision,
                )
            ),
        )
        return c


class _UFixedNxM(
    _ABIEncoded, typing.Generic[_TBitSize, _TDecimalPlaces], metaclass=_UFixedNxMMeta
):
    type_info: _UFixedTypeInfo
    _value: bytes  # underlying 'bytes' value representing the UFixedNxM

    def __init__(self, value: str = "0.0", /, *, type_info: _TypeInfo | None = None) -> None:
        """Construct an instance of UFixedNxM where value (v) is determined
        from the original decimal value (d) by the formula v = round(d *
        (10^M))"""
        super().__init__(type_info=type_info)
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
                q = d.quantize(decimal.Decimal(f"1e-{self.type_info.precision}"))
            except ArithmeticError as ex:
                raise ValueError(
                    f"Too many decimals, expected max of {self.type_info.precision}"
                ) from ex

            int_value = round(q * (10**self.type_info.precision))
            int_value = as_int(int_value, max=self.type_info.max_int)
            bytes_value = int_to_bytes(int_value, self.type_info.max_bytes_len)
            self._value = as_bytes(bytes_value, max_size=self.type_info.max_bytes_len)

    def __bool__(self) -> bool:
        """Returns `True` if not equal to zero."""
        return bool(int.from_bytes(self._value))


# implementations are effectively the same for these types
UFixedNxM = _UFixedNxM
BigUFixedNxM = _UFixedNxM


class Byte(UIntN[typing.Literal[8]]):
    """An ARC4 alias for a UInt8."""

    type_info = _UIntTypeInfo(size=8, alias="byte")


UInt8: typing.TypeAlias = UIntN[typing.Literal[8]]
"""An ARC4 UInt8."""

UInt16: typing.TypeAlias = UIntN[typing.Literal[16]]
"""An ARC4 UInt16."""

UInt32: typing.TypeAlias = UIntN[typing.Literal[32]]
"""An ARC4 UInt32."""

UInt64: typing.TypeAlias = UIntN[typing.Literal[64]]
"""An ARC4 UInt64."""

UInt128: typing.TypeAlias = BigUIntN[typing.Literal[128]]
"""An ARC4 UInt128."""

UInt256: typing.TypeAlias = BigUIntN[typing.Literal[256]]
"""An ARC4 UInt256."""

UInt512: typing.TypeAlias = BigUIntN[typing.Literal[512]]
"""An ARC4 UInt512."""


class _BoolTypeInfo(_TypeInfo):

    @property
    def typ(self) -> type:
        return Bool

    @property
    def arc4_name(self) -> str:
        return "bool"


class Bool(_ABIEncoded):
    """An ARC4 encoded bool."""

    type_info = _BoolTypeInfo()
    _value: bytes

    # True value is encoded as having a 1 on the most significant bit (0x80 = 128)
    _true_int_value = 128
    _false_int_value = 0

    def __init__(
        self,
        value: bool = False,  # noqa: FBT001, FBT002
        /,
        *,
        type_info: _TypeInfo | None = None,
    ) -> None:
        super().__init__(type_info=type_info)
        self._value = int_to_bytes(self._true_int_value if value else self._false_int_value, 1)

    def __bool__(self) -> bool:
        """Allow Bool to be used in boolean contexts."""
        return self.native

    @property
    def native(self) -> bool:
        """Return the bool representation of the value after ARC4 decoding."""
        int_value = int.from_bytes(self._value)
        return int_value == self._true_int_value


_TArrayItem = typing.TypeVar("_TArrayItem", bound=_ABIEncoded)
_TArrayLength = typing.TypeVar("_TArrayLength", bound=int)


class _StaticArrayTypeInfo(_TypeInfo):

    def __init__(self, item_type: _TypeInfo, size: int, alias: str | None = None):
        self.item_type = item_type
        self.size = size
        self.alias = alias

    @property
    def typ(self) -> type:
        return StaticArray

    @property
    def arc4_name(self) -> str:
        return self.alias or f"{self.item_type.arc4_name}[{self.size}]"

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
        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{','.join([k.__name__ for k in key_t])}]",
            (cls,),
            {},
            lambda ns: ns.update(
                type_info=_StaticArrayTypeInfo(
                    item_type=item_t.type_info,
                    size=size,
                ),
            ),
        )
        return c


class StaticArray(
    _ABIEncoded,
    typing.Generic[_TArrayItem, _TArrayLength],
    metaclass=_StaticArrayMeta,
):
    """A fixed length ARC4 Array of the specified type and length."""

    type_info: _StaticArrayTypeInfo
    _value: bytes

    def __init__(self, *items: _TArrayItem, type_info: _TypeInfo | None = None):
        super().__init__(type_info=type_info)
        type_info = self.type_info  # from class
        if not type_info and items:
            item_type = items[0].type_info
            self.type_info = type_info = _StaticArrayTypeInfo(item_type=item_type, size=len(items))
        if self.type_info != type_info:
            raise TypeError(f"expected type {self.type_info!r}, not {type_info!r}")
        for item in items:
            if self.type_info.item_type != item.type_info:
                raise TypeError(
                    f"item must be of type {self.type_info.item_type!r}, not {item.type_info!r}"
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

        return algopy.UInt64(self.type_info.size)

    @typing.overload
    def __getitem__(self, value: algopy.UInt64 | int, /) -> _TArrayItem: ...

    @typing.overload
    def __getitem__(self, value: slice, /) -> list[_TArrayItem]: ...

    def __getitem__(self, index: algopy.UInt64 | int | slice) -> _TArrayItem | list[_TArrayItem]:
        return self._list()[index]

    def __setitem__(self, index: algopy.UInt64 | int, item: _TArrayItem) -> _TArrayItem:
        if item.type_info != self.type_info.item_type:
            raise TypeError(
                f"item must be of type {self.type_info.item_type!r}, not {item.type_info!r}"
            )
        x = self._list()
        x[index] = item
        self._value = _encode(x)
        return item

    def copy(self) -> typing.Self:
        # """Create a copy of this array"""
        return copy.deepcopy(self)

    def _list(self) -> list[_TArrayItem]:
        return _decode_tuple_items(self._value, [self.type_info.item_type] * self.type_info.size)


class Address(StaticArray[Byte, typing.Literal[32]]):
    """An alias for an array containing 32 bytes representing an Algorand
    address."""

    type_info = _StaticArrayTypeInfo(Byte.type_info, size=32, alias="address")

    def __init__(
        self,
        value: Account | str | algopy.Bytes = algosdk.constants.ZERO_ADDRESS,
        *,
        type_info: _TypeInfo | None = None,
    ):
        """If `value` is a string, it should be a 58 character base32 string,

        ie a base32 string-encoded 32 bytes public key + 4 bytes checksum.
        If `value` is a Bytes, it's length checked to be 32 bytes - to avoid this
        check, use `Address.from_bytes(...)` instead.
        Defaults to the zero-address.
        """
        super().__init__(type_info=type_info)
        if isinstance(value, str):
            try:
                bytes_value = algosdk.encoding.decode_address(value)
            except Exception as e:
                raise ValueError(f"cannot encode the following address: {value!r}") from e
        else:
            bytes_value = (
                value.bytes.value if isinstance(value, Account) else as_bytes(value, max_size=32)
            )
        if len(bytes_value) != 32:
            raise ValueError(f"expected 32 bytes, got: {len(bytes_value)}")
        self._value = bytes_value

    @property
    def native(self) -> Account:
        # """Return the Account representation of the address after ARC4 decoding"""
        return Account(self.bytes)

    def __bool__(self) -> bool:
        # """Returns `True` if not equal to the zero address"""
        zero_bytes = algosdk.encoding.decode_address(algosdk.constants.ZERO_ADDRESS)
        return self.bytes != zero_bytes if isinstance(zero_bytes, bytes) else False

    def __eq__(self, other: Address | Account | str) -> bool:  # type: ignore[override]
        """Address equality is determined by the address of another
        `arc4.Address`, `Account` or `str`"""
        if isinstance(other, Address | Account):
            return self.bytes == other.bytes
        other_bytes = algosdk.encoding.decode_address(other)
        return self.bytes == other_bytes if isinstance(other_bytes, bytes) else False


class _DynamicArrayTypeInfo(_TypeInfo):
    def __init__(self, item_type: _TypeInfo):
        self.item_type = item_type

    @property
    def typ(self) -> type:
        return DynamicArray

    @property
    def arc4_name(self) -> str:
        return f"{self.item_type.arc4_name}[]"

    @property
    def is_dynamic(self) -> bool:
        return True


class _DynamicArrayMeta(type(_ABIEncoded), typing.Generic[_TArrayItem, _TArrayLength]):  # type: ignore  # noqa: PGH003
    __concrete__: typing.ClassVar[dict[type, type]] = {}

    def __getitem__(cls, key_t: type[_TArrayItem]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{key_t.__name__}]",
            (cls,),
            {},
            lambda ns: ns.update(
                type_info=_DynamicArrayTypeInfo(key_t.type_info),
            ),
        )
        return c


class DynamicArray(  # TODO: inherit from StaticArray?
    _ABIEncoded,
    typing.Generic[_TArrayItem],
    metaclass=_DynamicArrayMeta,
):
    """A dynamically sized ARC4 Array of the specified type."""

    type_info: _DynamicArrayTypeInfo
    _value: bytes

    def __init__(self, *items: _TArrayItem, type_info: _TypeInfo | None = None):
        super().__init__(type_info=type_info)
        type_info = self.type_info
        if not type_info and items:
            item_type = items[0].type_info
            self.type_info = type_info = _DynamicArrayTypeInfo(
                item_type=item_type,
            )
        if self.type_info != type_info:
            raise TypeError(f"expected type {self.type_info!r}, not {type_info!r}")
        for item in items:
            if self.type_info.item_type != item.type_info:
                raise TypeError(
                    f"item must be of type {self.type_info.item_type!r}, not {item.type_info!r}"
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

    @typing.overload
    def __getitem__(self, value: algopy.UInt64 | int, /) -> _TArrayItem: ...

    @typing.overload
    def __getitem__(self, value: slice, /) -> list[_TArrayItem]: ...
    def __getitem__(self, index: algopy.UInt64 | int | slice) -> _TArrayItem | list[_TArrayItem]:
        return self._list()[index]

    def __setitem__(self, index: algopy.UInt64 | int, item: _TArrayItem) -> _TArrayItem:
        if item.type_info != self.type_info.item_type:
            raise TypeError(
                f"item must be of type {self.type_info.item_type!r}, not {item.type_info!r}"
            )
        x = self._list()
        x[index] = item
        self._value = self._encode_with_length(x)
        return item

    def append(self, item: _TArrayItem, /) -> None:
        """Append items to this array."""
        if item.type_info != self.type_info.item_type:
            raise TypeError(
                f"item must be of type {self.type_info.item_type!r}, not {item.type_info!r}"
            )
        x = self._list()
        x.append(item)
        self._value = self._encode_with_length(x)

    def extend(self, other: Iterable[_TArrayItem], /) -> None:
        """Extend this array with the contents of another array."""
        if any(o.type_info != self.type_info.item_type for o in other):
            raise TypeError(f"items must be of type {self.type_info.item_type!r}")
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

    def copy(self) -> typing.Self:
        """Create a copy of this array."""
        return copy.deepcopy(self)

    def __bool__(self) -> bool:
        """Returns `True` if not an empty array."""
        return bool(self._list())

    def _list(self) -> list[_TArrayItem]:
        length, data = _read_length(self._value)
        return _decode_tuple_items(data, [self.type_info.item_type] * length)

    def _encode_with_length(self, items: list[_TArrayItem] | tuple[_TArrayItem, ...]) -> bytes:
        return _encode_length(len(items)) + _encode(items)


class DynamicBytes(DynamicArray[Byte]):
    """A variable sized array of bytes."""

    @typing.overload
    def __init__(self, *values: Byte | UInt8 | int): ...

    @typing.overload
    def __init__(self, value: algopy.Bytes | bytes, /): ...

    def __init__(
        self, *value: algopy.Bytes | bytes | Byte | UInt8 | int, type_info: _TypeInfo | None = None
    ):
        items = []
        for x in value:
            if isinstance(x, int):
                items.append(Byte(x))
            elif isinstance(x, Byte):
                items.append(x)
            elif isinstance(x, UInt8):  # type: ignore[misc]
                items.append(Byte(x.native))
            elif isinstance(x, Bytes | bytes):
                if len(value) > 1:
                    raise ValueError("expected single Bytes value")
                items.extend([Byte(b) for b in as_bytes(x)])

        super().__init__(*items, type_info=type_info)

    @property
    def native(self) -> algopy.Bytes:
        """Return the Bytes representation of the address after ARC4
        decoding."""
        return self.bytes


_TTuple = typing.TypeVarTuple("_TTuple")


class _TupleTypeInfo(_TypeInfo):

    def __init__(self, child_types: list[_TypeInfo]) -> None:
        self.child_types = child_types

    @property
    def typ(self) -> type:
        return Tuple

    @property
    def arc4_name(self) -> str:
        inner_name = ",".join([t.arc4_name for t in self.child_types])
        return f"({inner_name})"

    @property
    def is_dynamic(self) -> bool:
        return any(t.is_dynamic for t in self.child_types)


class _TupleMeta(type(_ABIEncoded), typing.Generic[typing.Unpack[_TTuple]]):  # type: ignore  # noqa: PGH003
    __concrete__: typing.ClassVar[dict[tuple, type]] = {}  # type: ignore[type-arg]

    def __getitem__(cls, key_t: tuple[_ABIEncoded, ...]) -> type:
        cache = cls.__concrete__
        if c := cache.get(key_t, None):
            return c

        cache[key_t] = c = types.new_class(
            f"{cls.__name__}[{key_t}]",
            (cls,),
            {},
            lambda ns: ns.update(
                type_info=_TupleTypeInfo([t.type_info for t in key_t]),
            ),
        )
        return c


class Tuple(
    _ABIEncoded,
    tuple[*_TTuple],
    typing.Generic[typing.Unpack[_TTuple]],
    metaclass=_TupleMeta,
):
    """An ARC4 ABI tuple, containing other ARC4 ABI types."""

    __slots__ = ()  # to satisfy SLOT001
    type_info: _TupleTypeInfo
    _value: bytes

    def __init__(
        self,
        items: tuple[typing.Unpack[_TTuple]] = (),  # type: ignore[assignment]
        /,
        *,
        type_info: _TypeInfo | None = None,
    ):
        """Construct an ARC4 tuple from a python tuple."""
        super().__init__(type_info=type_info)
        type_info = self.type_info  # from class
        if not type_info:
            child_types = []
            for item in items:
                assert isinstance(item, _ABIEncoded), "expected ARC4 type"
                assert item.type_info is not None
                child_types.append(item.type_info)
            self.type_info = type_info = _TupleTypeInfo(child_types)
        if self.type_info != type_info:
            raise TypeError(f"item must be of type {self.type_info!r}, not {type_info!r}")
        if items:
            for item, expected_type in zip(items, type_info.child_types, strict=True):  # type: ignore[arg-type]
                assert isinstance(item, _ABIEncoded), "expected ARC4 type"
                item_type_info = item.type_info  # type: ignore[attr-defined]
                if expected_type != item_type_info:
                    raise TypeError(
                        f"item must be of type {self.type_info!r}, not {item_type_info!r}"
                    )
        self._value = _encode(items)

    def __len__(self) -> int:
        return len(self.native)

    def __getitem__(self, index: typing.SupportsIndex | slice) -> object:  # type: ignore[override]
        return self.native[index]

    def __iter__(self) -> typing.Iterator[_ABIEncoded]:
        return iter(self.native)  # type: ignore[arg-type]

    @property
    def native(self) -> tuple[typing.Unpack[_TTuple]]:
        """Return the Bytes representation of the address after ARC4
        decoding."""
        return typing.cast(
            tuple[typing.Unpack[_TTuple]],
            tuple(_decode_tuple_items(self._value, self.type_info.child_types)),
        )


@typing.dataclass_transform(
    eq_default=False, order_default=False, kw_only_default=False, field_specifiers=()
)
class _StructMeta(type):
    def __new__(
        cls,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, object],
    ) -> _StructMeta:
        return super().__new__(cls, name, bases, namespace)


class Struct(metaclass=_StructMeta):
    """Base class for ARC4 Struct types."""

    def __init__(self, *args: typing.Any, type_info: _TypeInfo | None = None):
        self._value = Tuple(args)
        # TODO: does Struct need it's own TypeInfo?
        self.type_info = type_info or self._value.type_info

    @classmethod
    def from_bytes(
        cls, value: algopy.Bytes | bytes, /, *, type_info: _TypeInfo | None = None
    ) -> typing.Self:
        annotations = _all_annotations(cls)

        result = cls(type_info=type_info)
        tuple_value = Tuple[tuple(v for k, v in annotations.items())].from_bytes(value)  # type: ignore[misc, attr-defined]
        result._value = tuple_value

        return result

    @property
    def bytes(self) -> algopy.Bytes:
        """Get the underlying bytes[]"""
        return self._value.bytes

    def copy(self) -> typing.Self:
        """Create a copy of this struct."""
        return copy.deepcopy(self)


class ARC4Client(typing.Protocol): ...


if typing.TYPE_CHECKING:
    _TABIArg: typing.TypeAlias = (
        algopy.String
        | algopy.BigUInt
        | algopy.UInt64
        | algopy.Bytes
        | algopy.Asset
        | algopy.Account
        | algopy.Application
        | UIntN[typing.Any]
        | BigUIntN[typing.Any]
        | UFixedNxM[typing.Any, typing.Any]
        | BigUFixedNxM[typing.Any, typing.Any]
        | Bool
        | String
        | StaticArray[typing.Any, typing.Any]
        | DynamicArray[typing.Any]
        | Tuple  # type: ignore[type-arg]
        | int
        | bool
        | bytes
        | str
    )


_TABIResult_co = typing.TypeVar("_TABIResult_co", covariant=True)


class _ABICallWithReturnProtocol(typing.Protocol[_TABIResult_co]):
    def __call__(  # noqa: PLR0913
        self,
        method: str,
        /,
        *args: _TABIArg,
        app_id: algopy.Application | algopy.UInt64 | int = ...,
        on_completion: algopy.OnCompleteAction = ...,
        approval_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        clear_state_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        global_num_uint: UInt64 | int = ...,
        global_num_bytes: UInt64 | int = ...,
        local_num_uint: UInt64 | int = ...,
        local_num_bytes: UInt64 | int = ...,
        extra_program_pages: UInt64 | int = ...,
        fee: algopy.UInt64 | int = 0,
        sender: algopy.Account | str = ...,
        note: algopy.Bytes | bytes | str = ...,
        rekey_to: algopy.Account | str = ...,
    ) -> tuple[_TABIResult_co, algopy.itxn.ApplicationCallInnerTransaction]: ...


class _ABICallProtocolType(typing.Protocol):
    @typing.overload
    def __call__(
        self,
        method: typing.Callable[..., None] | str,
        /,
        *args: _TABIArg,
        app_id: algopy.Application | algopy.UInt64 | int = ...,
        on_completion: algopy.OnCompleteAction = ...,
        approval_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        clear_state_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        global_num_uint: UInt64 | int = ...,
        global_num_bytes: UInt64 | int = ...,
        local_num_uint: UInt64 | int = ...,
        local_num_bytes: UInt64 | int = ...,
        extra_program_pages: UInt64 | int = ...,
        fee: algopy.UInt64 | int = 0,
        sender: algopy.Account | str = ...,
        note: algopy.Bytes | bytes | str = ...,
        rekey_to: algopy.Account | str = ...,
    ) -> algopy.itxn.ApplicationCallInnerTransaction: ...

    @typing.overload
    def __call__(  # type: ignore[misc, unused-ignore]
        self,
        method: typing.Callable[..., _TABIResult_co],
        /,
        *args: _TABIArg,
        app_id: algopy.Application | algopy.UInt64 | int = ...,
        on_completion: algopy.OnCompleteAction = ...,
        approval_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        clear_state_program: algopy.Bytes | bytes | tuple[algopy.Bytes, ...] = ...,
        global_num_uint: UInt64 | int = ...,
        global_num_bytes: UInt64 | int = ...,
        local_num_uint: UInt64 | int = ...,
        local_num_bytes: UInt64 | int = ...,
        extra_program_pages: UInt64 | int = ...,
        fee: algopy.UInt64 | int = 0,
        sender: algopy.Account | str = ...,
        note: algopy.Bytes | bytes | str = ...,
        rekey_to: algopy.Account | str = ...,
    ) -> tuple[_TABIResult_co, algopy.itxn.ApplicationCallInnerTransaction]: ...

    def __getitem__(
        self, _: type[_TABIResult_co]
    ) -> _ABICallWithReturnProtocol[_TABIResult_co]: ...


class _ABICall:
    def __call__(
        self,
        method: typing.Callable[..., typing.Any] | str,
        /,
        *args: _TABIArg,
        **kwargs: typing.Any,
    ) -> typing.Any:
        # Implement the actual abi_call logic here
        raise NotImplementedError(
            "'abi_call' is not available in test context. "
            "Mock using your preferred testing framework."
        )

    def __getitem__(
        self, return_type: type[_TABIResult_co]
    ) -> _ABICallWithReturnProtocol[_TABIResult_co]:
        return self


# TODO: Implement abi_call
abi_call: _ABICallProtocolType = _ABICall()


@typing.overload
def emit(event: Struct, /) -> None: ...
@typing.overload
def emit(event: str, /, *args: _TABIArg) -> None: ...
def emit(event: str | Struct, /, *args: _TABIArg) -> None:
    """Emit an ARC-28 event for the provided event signature or name, and
    provided args.

    :param event: Either an ARC4 Struct, an event name, or event signature.
        * If event is an ARC4 Struct, the event signature will be determined from the Struct name and fields
        * If event is a signature, then the following args will be typed checked to ensure they match.
        * If event is just a name, the event signature will be inferred from the name and following arguments

    :param args: When event is a signature or name, args will be used as the event data.
    They will all be encoded as single ARC4 Tuple

    Example:
    ```
    from algopy import ARC4Contract, arc4


    class Swapped(arc4.Struct):
        a: arc4.UInt64
        b: arc4.UInt64


    class EventEmitter(ARC4Contract):
        @arc4.abimethod
        def emit_swapped(self, a: arc4.UInt64, b: arc4.UInt64) -> None:
            arc4.emit(Swapped(b, a))
            arc4.emit("Swapped(uint64,uint64)", b, a)
            arc4.emit("Swapped", b, a)
    ```
    """  # noqa: E501
    import algopy

    context = get_test_context()
    active_txn = context.get_active_transaction()

    if active_txn.type != algopy.TransactionType.ApplicationCall:
        raise ValueError("Cannot emit events outside of application call context!")
    if not active_txn.app_id:
        raise ValueError("Cannot emit event: missing `app_id` in associated call transaction!")

    if isinstance(event, str):
        arc4_args = [_cast_arg_as_arc4(arg) for arg in args]
        arg_types = "(" + ",".join(a.type_info.arc4_name for a in arc4_args) + ")"
        if event.find("(") == -1:
            event += arg_types
        elif event.find(arg_types) == -1:
            raise ValueError(f"Event signature {event} does not match args {args}")

        event_hash = algopy.Bytes(SHA512.new(event.encode(), truncate="256").digest())
        context.add_application_logs(
            app_id=active_txn.app_id,
            logs=(event_hash[:4] + Struct(*arc4_args).bytes).value,
        )
    elif isinstance(event, Struct):
        arg_types = "(" + ",".join(a.type_info.arc4_name for a in event._value) + ")"
        event_str = event.__class__.__name__ + arg_types
        event_hash = algopy.Bytes(SHA512.new(event_str.encode(), truncate="256").digest())
        context.add_application_logs(
            app_id=active_txn.app_id,
            logs=(event_hash[:4] + event.bytes).value,
        )


def _cast_arg_as_arc4(arg: object) -> _ABIEncoded:  # noqa: PLR0911
    import algopy

    if isinstance(arg, _ABIEncoded):
        return arg
    if isinstance(arg, bool):
        return Bool(arg)
    if isinstance(arg, algopy.UInt64):
        return UInt64(arg)
    if isinstance(arg, algopy.BigUInt):
        return UInt512(arg)
    if isinstance(arg, int):
        return UInt64(arg) if arg <= MAX_UINT64 else UInt512(arg)
    if isinstance(arg, algopy.Bytes | bytes):
        return DynamicBytes(arg)
    if isinstance(arg, algopy.String | str):
        return String(arg)
    # TODO: check these against puya, as they don't seem correct for emit
    if isinstance(arg, algopy.Asset):
        return UInt64(arg.id)
    if isinstance(arg, algopy.Account):
        return Address(arg)
    if isinstance(arg, algopy.Application):
        return UInt64(arg.id)
    raise ValueError(f"Unsupported type {type(arg)}")


# https://stackoverflow.com/a/72037059
def _all_annotations(cls: type) -> ChainMap[str, type]:
    """Returns a dictionary-like ChainMap that includes annotations for all
    attributes defined in cls or inherited from superclasses."""
    return ChainMap(*(c.__annotations__ for c in cls.__mro__ if "__annotations__" in c.__dict__))


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
    """Helper function to find consecutive booleans from current index in a
    tuple."""
    until = 0
    values_length = len(values) if isinstance(values, tuple | list) else values.length.value
    while True:
        curr = index + delta * until
        if isinstance(values[curr], Bool):
            if curr != values_length - 1 and delta > 0 or curr > 0 and delta < 0:
                until += 1
            else:
                break
        else:
            until -= 1
            break
    return until


def _find_bool_types(values: typing.Sequence[_TypeInfo], index: int, delta: int) -> int:
    """Helper function to find consecutive booleans from current index in a
    tuple."""
    until = 0
    values_length = len(values)
    while True:
        curr = index + delta * until
        if isinstance(values[curr], _BoolTypeInfo):
            if curr != values_length - 1 and delta > 0 or curr > 0 and delta < 0:
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
    elif isinstance(type_info, _TupleTypeInfo | _StaticArrayTypeInfo):
        i = 0
        child_types = (
            type_info.child_types
            if isinstance(type_info, _TupleTypeInfo)
            else [type_info.item_type] * type_info.size
        )
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


def _encode(
    values: (
        StaticArray[typing.Any, typing.Any]
        | DynamicArray[typing.Any]
        | Tuple[typing.Any]
        | tuple[typing.Any, ...]
        | list[typing.Any]
    ),
) -> bytes:
    heads = []
    tails = []
    is_dynamic_index = []
    i = 0
    values_length = len(values) if hasattr(values, "__len__") else values.length.value
    values_length_bytes = (
        _encode_length(values_length) if isinstance(values, DynamicArray) else b""
    )
    while i < values_length:
        value = values[i]
        assert isinstance(value, _ABIEncoded), "expected ARC4 value"
        is_dynamic_index.append(value.type_info.is_dynamic)
        if is_dynamic_index[-1]:
            heads.append(b"\x00\x00")
            assert isinstance(
                value, StaticArray | DynamicArray | Tuple | String
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
                consecutive_bool_list = typing.cast(list[Bool], values[i : i + after + 1])
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
    value_partitions: list[bytes | None] = []
    i = 0
    array_index = 0

    while i < len(child_types):
        child_type = child_types[i]
        if child_type.is_dynamic:
            # Decode the size of the dynamic element
            dynamic_index = int.from_bytes(value[array_index : array_index + _ABI_LENGTH_SIZE])
            if len(dynamic_segments) > 0:
                dynamic_segments[-1][1] = dynamic_index

            # Since we do not know where the current dynamic element ends,
            # put a placeholder and update later
            dynamic_segments.append([dynamic_index, -1])
            value_partitions.append(None)
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
        assert issubclass(cls, _ABIEncoded), "expected ARC4 type"
        assert child_value is not None, "expected ARC4 value"
        val = cls.from_bytes(child_value, type_info=child_type)
        values.append(val)
    return values


def _encode_length(length: int) -> bytes:
    return length.to_bytes(_ABI_LENGTH_SIZE)


def _read_length(value: bytes) -> tuple[int, bytes]:
    length = int.from_bytes(value[:_ABI_LENGTH_SIZE])
    data = value[_ABI_LENGTH_SIZE:]
    return length, data
