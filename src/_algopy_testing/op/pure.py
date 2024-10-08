from __future__ import annotations

import base64
import enum
import json
import math
import typing

from _algopy_testing import BigUInt, Bytes, UInt64
from _algopy_testing.constants import BITS_IN_BYTE, MAX_BYTES_SIZE, MAX_UINT64
from _algopy_testing.utils import as_bytes, as_int, as_int8, as_int64, as_int512, int_to_bytes


def addw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    result = a + b
    return _int_to_uint128(result)


def bitlen(a: Bytes | UInt64 | bytes | int, /) -> UInt64:
    int_value = int.from_bytes(as_bytes(a)) if (isinstance(a, Bytes | bytes)) else as_int64(a)
    return UInt64(int_value.bit_length())


def bsqrt(a: BigUInt | int, /) -> BigUInt:
    a = as_int512(a)
    return BigUInt(math.isqrt(a))


def btoi(a: Bytes | bytes, /) -> UInt64:
    a_bytes = as_bytes(a)
    if len(a_bytes) > 8:
        raise ValueError(f"btoi arg too long, got [{len(a_bytes)}]bytes")
    return UInt64(int.from_bytes(a_bytes))


def bzero(a: UInt64 | int, /) -> Bytes:
    a = as_int64(a)
    if a > MAX_BYTES_SIZE:
        raise ValueError("bzero attempted to create a too large string")
    return Bytes(b"\x00" * a)


def divmodw(
    a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, d: UInt64 | int, /
) -> tuple[UInt64, UInt64, UInt64, UInt64]:
    i = _uint128_to_int(a, b)
    j = _uint128_to_int(c, d)
    d = i // j
    m = i % j
    return _int_to_uint128(d) + _int_to_uint128(m)


def divw(a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, /) -> UInt64:
    i = _uint128_to_int(a, b)
    c = as_int64(c)
    return UInt64(i // c)


def exp(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int64(b)
    if a == b and a == 0:
        raise ArithmeticError("0^0 is undefined")
    return UInt64(a**b)


def expw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    if a == b and a == 0:
        raise ArithmeticError("0^0 is undefined")
    result = a**b
    return _int_to_uint128(result)


def extract(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    start = as_int64(b)
    stop = start + as_int64(c)

    if isinstance(b, int) and isinstance(c, int) and c == 0:
        stop = len(a)

    if start > len(a):
        raise ValueError(f"extraction start {start} is beyond length")
    if stop > len(a):
        raise ValueError(f"extraction end {stop} is beyond length")

    return Bytes(a)[slice(start, stop)]


def extract_uint16(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 2)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def extract_uint32(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 4)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def extract_uint64(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 8)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def getbit(a: Bytes | UInt64 | bytes | int, b: UInt64 | int, /) -> UInt64:
    if isinstance(a, Bytes | bytes):
        return _getbit_bytes(a, b)
    if isinstance(a, UInt64 | int):
        a_bytes = _uint64_to_bytes(a)
        return _getbit_bytes(a_bytes, b, "little")
    raise TypeError("Unknown type for argument a")


def getbyte(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    a = as_bytes(a)
    int_list = list(a)

    max_index = len(int_list) - 1
    b = as_int(b, max=max_index)

    return UInt64(int_list[b])


def itob(a: UInt64 | int, /) -> Bytes:
    return Bytes(_uint64_to_bytes(a))


def mulw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    result = a * b
    return _int_to_uint128(result)


def replace(a: Bytes | bytes, b: UInt64 | int, c: Bytes | bytes, /) -> Bytes:
    a = a if (isinstance(a, Bytes)) else Bytes(a)
    b = as_int64(b)
    c = as_bytes(c)
    if b + len(c) > len(a):
        raise ValueError(f"expected value <= {len(a)}, got: {b + len(c)}")
    return a[slice(0, b)] + c + a[slice(b + len(c), len(a))]


def select_bytes(a: Bytes | bytes, b: Bytes | bytes, c: bool | UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    b = as_bytes(b)
    c = int(c) if (isinstance(c, bool)) else as_int64(c)
    return Bytes(b if c != 0 else a)


def select_uint64(a: UInt64 | int, b: UInt64 | int, c: bool | UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int64(b)
    c = int(c) if (isinstance(c, bool)) else as_int64(c)
    return UInt64(b if c != 0 else a)


def setbit_bytes(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    return _setbit_bytes(a, b, c)


def setbit_uint64(a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, /) -> UInt64:
    a_bytes = _uint64_to_bytes(a)
    result = _setbit_bytes(a_bytes, b, c, "little")
    return UInt64(int.from_bytes(result.value))


def setbyte(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    int_list = list(a)

    max_index = len(int_list) - 1
    b = as_int(b, max=max_index)
    c = as_int8(c)

    int_list[b] = c
    return Bytes(_int_list_to_bytes(int_list))


def shl(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int(b, max=63)
    result = (a * (2**b)) % (2**64)
    return UInt64(result)


def shr(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int(b, max=63)
    result = a // (2**b)
    return UInt64(result)


def sqrt(a: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    return UInt64(math.isqrt(a))


def substring(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    c = as_int(c, max=len(a))
    b = as_int(b, max=c)
    return Bytes(a)[slice(b, c)]


def concat(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
    a = a if (isinstance(a, Bytes)) else Bytes(a)
    b = b if (isinstance(b, Bytes)) else Bytes(b)
    return a + b


def _int_to_uint128(a: int) -> tuple[UInt64, UInt64]:
    cf, rest = a >> 64, a & MAX_UINT64
    return (
        UInt64(cf),
        UInt64(rest),
    )


def _uint128_to_int(a: UInt64 | int, b: UInt64 | int) -> int:
    a = as_int64(a)
    b = as_int64(b)
    return (a << 64) + b


def _uint64_to_bytes(a: UInt64 | int) -> bytes:
    a = as_int64(a)
    return a.to_bytes(8)


def _int_list_to_bytes(a: list[int]) -> bytes:
    return b"".join([b"\x00" if i == 0 else int_to_bytes(i) for i in a])


def _getbit_bytes(
    a: Bytes | bytes, b: UInt64 | int, byteorder: typing.Literal["little", "big"] = "big"
) -> UInt64:
    a = as_bytes(a)
    if byteorder != "big":  # reverse bytes if NOT big endian
        a = bytes(reversed(a))

    int_list = list(a)
    max_index = len(int_list) * BITS_IN_BYTE - 1
    b = as_int(b, max=max_index)

    byte_index = b // BITS_IN_BYTE
    bit_index = b % BITS_IN_BYTE
    if byteorder == "big":
        bit_index = 7 - bit_index
    bit = _get_bit(int_list[byte_index], bit_index)

    return UInt64(bit)


def _setbit_bytes(
    a: Bytes | bytes,
    b: UInt64 | int,
    c: UInt64 | int,
    byteorder: typing.Literal["little", "big"] = "big",
) -> Bytes:
    a = as_bytes(a)
    if byteorder != "big":  # reverse bytes if NOT big endian
        a = bytes(reversed(a))

    int_list = list(a)
    max_index = len(int_list) * BITS_IN_BYTE - 1
    b = as_int(b, max=max_index)
    c = as_int(c, max=1)

    byte_index = b // BITS_IN_BYTE
    bit_index = b % BITS_IN_BYTE
    if byteorder == "big":
        bit_index = 7 - bit_index
    int_list[byte_index] = _set_bit(int_list[byte_index], bit_index, c)

    # reverse int array if NOT big endian before casting it to Bytes
    if byteorder != "big":
        int_list = list(reversed(int_list))

    return Bytes(_int_list_to_bytes(int_list))


def _get_bit(v: int, index: int) -> int:
    return (v >> index) & 1


def _set_bit(v: int, index: int, x: int) -> int:
    """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new
    value."""
    mask = 1 << index  # Compute mask, an integer with just bit 'index' set.
    v &= ~mask  # Clear the bit indicated by the mask (if x is False)
    if x:
        v |= mask  # If x was True, set the bit indicated by the mask.
    return v


class Base64(enum.Enum):
    URLEncoding = 0
    StdEncoding = 1


def _bytes_to_string(a: Bytes | bytes, err_msg: str) -> str:
    a = as_bytes(a)
    try:
        return a.decode()
    except UnicodeDecodeError:
        raise ValueError(err_msg) from None


class _MultiKeyDict(dict[typing.Any, typing.Any]):
    def __init__(self, items: list[typing.Any]):
        self[""] = ""
        items = [
            (
                (i[0], _MultiKeyDict(i[1]))
                if isinstance(i[1], list) and all(isinstance(j, tuple) for j in i[1])
                else i
            )
            for i in items
        ]
        self._items = items

    def items(self) -> typing.Any:
        return self._items


class JsonRef:
    @staticmethod
    def _load_json(a: Bytes | bytes) -> dict[typing.Any, typing.Any]:
        a = as_bytes(a)
        try:
            # load the whole json payload as an array of key value pairs
            pairs = json.loads(a, object_pairs_hook=lambda x: x)
        except json.JSONDecodeError:
            raise ValueError("error while parsing JSON text, invalid json text") from None

        # turn the pairs into the dictionay for the top level,
        # all other levels remain as key value pairs
        # e.g.
        # input bytes: b'{"key0": 1,"key1": {"key2":2,"key2":"10"}, "key2": "test"}'
        # output dict: {'key0': 1, 'key1': [('key2', 2), ('key2', '10')], 'key2': 'test'}
        result = dict(pairs)
        if len(pairs) != len(result):
            raise ValueError(
                "error while parsing JSON text, invalid json text, duplicate keys found"
            )

        return result

    @staticmethod
    def _raise_key_error(key: str) -> None:
        raise ValueError(f"key {key} not found in JSON text")

    @staticmethod
    def json_string(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, str):
            raise TypeError(f"value must be a string type, not {type(result).__name__!r}")

        # encode with `surrogatepass` to allow sequences such as `\uD800`
        # decode with `replace` to replace with official replacement character `U+FFFD`
        # encode with default settings to get the final bytes result
        result = result.encode("utf-16", "surrogatepass").decode("utf-16", "replace").encode()
        return Bytes(result)

    @staticmethod
    def json_uint64(a: Bytes | bytes, b: Bytes | bytes, /) -> UInt64:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        result = as_int(result, max=MAX_UINT64)
        return UInt64(result)

    @staticmethod
    def json_object(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None
        try:
            # using a custom dict object to allow duplicate keys which is essentially a list
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, list) or not all(isinstance(i, tuple) for i in result):
            raise TypeError(f"value must be an object type, not {type(result).__name__!r}")

        result = _MultiKeyDict(result)
        result_string = json.dumps(result, separators=(",", ":"))
        return Bytes(result_string.encode())


def base64_decode(e: Base64, a: Bytes | bytes, /) -> Bytes:
    a_str = _bytes_to_string(a, "illegal base64 data")
    a_str = a_str + "="  # append padding to ensure there is at least one

    result = (
        base64.urlsafe_b64decode(a_str) if e == Base64.URLEncoding else base64.b64decode(a_str)
    )
    return Bytes(result)
