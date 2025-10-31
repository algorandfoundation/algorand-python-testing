import base64
import typing

import pytest
from _algopy_testing.constants import MAX_BYTES_SIZE
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.fixed_bytes import FixedBytes
from _algopy_testing.primitives.uint64 import UInt64

from tests.util import int_to_bytes


def test_fixed_bytes_init_default() -> None:
    """Test FixedBytes initialization with default values (all zeros)."""
    fb8 = FixedBytes[typing.Literal[8]]()
    assert fb8 == b"\x00" * 8
    assert len(fb8) == 8

    fb32 = FixedBytes[typing.Literal[32]]()
    assert fb32 == b"\x00" * 32
    assert len(fb32) == 32


def test_fixed_bytes_init_with_bytes() -> None:
    """Test FixedBytes initialization with bytes value."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)
    assert fb8 == value
    assert len(fb8) == 8
    assert fb8.length == 8


def test_fixed_bytes_init_with_bytes_object() -> None:
    """Test FixedBytes initialization with Bytes object."""
    value = Bytes(b"12345678")
    fb8 = FixedBytes[typing.Literal[8]](value)
    assert fb8 == value.value
    assert len(fb8) == 8
    assert fb8.length == 8


def test_fixed_bytes_init_wrong_length() -> None:
    """Test FixedBytes initialization raises TypeError for wrong length."""
    with pytest.raises(TypeError, match="expected value of length 8, not 5"):
        FixedBytes[typing.Literal[8]](b"12345")

    with pytest.raises(TypeError, match="expected value of length 32, not 10"):
        FixedBytes[typing.Literal[32]](Bytes(b"0123456789"))


@pytest.mark.parametrize(
    "value",
    [
        b"\x00\x00\x00\x00",
        b"\x01\x00\x00\x00",
        b"test",
        b"\xff\xff\xff\xff",
    ],
)
def test_fixed_bytes_bool(value: bytes) -> None:
    fb = FixedBytes[typing.Literal[4]](value)
    assert bool(fb) == bool(value)


def test_fixed_bytes_bool_all_zeros() -> None:
    a = FixedBytes[typing.Literal[8]]()
    assert bool(a) is True

    b = FixedBytes[typing.Literal[0]]()
    assert bool(b) is False


@pytest.mark.parametrize(
    "index",
    [-1, -2, -7, -8, 0, 1, 4, 7],
)
def test_fixed_bytes_getitem_int(index: int) -> None:
    """Test FixedBytes __getitem__ with int index."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)
    result = fb8[index]
    assert isinstance(result, Bytes)
    assert result == int_to_bytes(value[index])


def test_fixed_bytes_getitem_uint64() -> None:
    """Test FixedBytes __getitem__ with UInt64 index."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)
    result = fb8[UInt64(3)]
    assert isinstance(result, Bytes)
    assert result == int_to_bytes(value[3])


@pytest.mark.parametrize(
    "slice_obj",
    [
        slice(0, 4),
        slice(2, 6),
        slice(0, 8),
        slice(4, 8),
        slice(1, 3),
    ],
)
def test_fixed_bytes_getitem_slice(slice_obj: slice) -> None:
    """Test FixedBytes __getitem__ with slice."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)
    result = fb8[slice_obj]
    assert isinstance(result, Bytes)
    assert result == value[slice_obj]


def test_fixed_bytes_iter() -> None:
    """Test FixedBytes iteration."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)

    result = Bytes()
    for byte in fb8:
        assert isinstance(byte, Bytes)
        result += byte

    assert len(result) == len(value)
    assert result == value

    for i, byte in enumerate(result):
        assert byte == int_to_bytes(value[i])


def test_fixed_bytes_reversed() -> None:
    """Test FixedBytes reverse iteration."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)

    result = Bytes()
    for byte in reversed(fb8):
        assert isinstance(byte, Bytes)
        result += byte

    assert len(result) == len(value)
    assert result == value[::-1]
    for i, byte in enumerate(result):
        assert byte == int_to_bytes(value[len(value) - 1 - i])


def test_fixed_bytes_from_base32() -> None:
    """Test FixedBytes.from_base32 static method."""
    base32_str = "GEZDGNBV"  # "12345" in base32
    expected = base64.b32decode(base32_str)

    result = FixedBytes[typing.Literal[5]].from_base32(base32_str)
    assert result.value == expected
    assert len(result) == 5

    with pytest.raises(TypeError, match="expected value of length 4, not 5"):
        FixedBytes[typing.Literal[4]].from_base32(base32_str)


def test_fixed_bytes_from_base64() -> None:
    """Test FixedBytes.from_base64 static method."""
    base64_str = "MTIzNDU2Nzg="  # "12345678" in base64
    expected = base64.b64decode(base64_str)

    result = FixedBytes[typing.Literal[8]].from_base64(base64_str)
    assert result.value == expected
    assert len(result) == 8

    with pytest.raises(TypeError, match="expected value of length 4, not 8"):
        FixedBytes[typing.Literal[4]].from_base64(base64_str)


def test_fixed_bytes_from_hex() -> None:
    """Test FixedBytes.from_hex static method."""
    hex_str = "0102030405060708"
    expected = base64.b16decode(hex_str)

    result = FixedBytes[typing.Literal[8]].from_hex(hex_str)
    assert result.value == expected
    assert len(result) == 8

    with pytest.raises(TypeError, match="expected value of length 4, not 8"):
        FixedBytes[typing.Literal[4]].from_hex(hex_str)


def test_fixed_bytes_from_bytes_method() -> None:
    """Test FixedBytes.from_bytes class method."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]].from_bytes(value)
    assert fb8 == value
    assert len(fb8) == 8

    # no validation of input length
    fb7 = FixedBytes[typing.Literal[7]].from_bytes(value)
    assert fb7 == value
    assert len(fb7) == 8
    assert fb7.length == 8


def test_fixed_bytes_from_bytes_method_with_bytes_object() -> None:
    """Test FixedBytes.from_bytes class method with Bytes object."""
    value = Bytes(b"12345678")
    fb8 = FixedBytes[typing.Literal[8]].from_bytes(value)
    assert fb8 == value.value
    assert len(fb8) == 8

    # no validation of input length
    fb7 = FixedBytes[typing.Literal[7]].from_bytes(value)
    assert fb7 == value.value
    assert len(fb7) == 8


def test_fixed_bytes_bytes_property() -> None:
    """Test FixedBytes.bytes property."""
    value = b"12345678"
    fb = FixedBytes[typing.Literal[8]](value)
    result = fb.bytes
    assert isinstance(result, Bytes)
    assert result == value


def test_fixed_bytes_single_byte_iteration() -> None:
    """Test iterating over FixedBytes with minimal length."""
    fb1 = FixedBytes[typing.Literal[1]](b"x")
    items = list(fb1)
    assert len(items) == 1
    assert items[0] == int_to_bytes(ord(b"x"))


def test_fixed_bytes_slice_edge_cases() -> None:
    """Test edge cases for FixedBytes slicing."""
    value = b"12345678"
    fb8 = FixedBytes[typing.Literal[8]](value)

    # Empty slice
    assert fb8[0:0] == b""

    # Slice beyond bounds
    assert fb8[0:100] == value

    # Reverse slice (empty result)
    assert fb8[5:2] == b""

    # Slice with step (Python slices support this)
    assert fb8[::2] == value[::2]


@pytest.mark.parametrize(
    ("other", "expected", "expected_len"),
    [
        (FixedBytes[typing.Literal[5]](b"world"), b"testworld", 9),
        (Bytes(b"data"), b"testdata", 8),
        (b"123", b"test123", 7),
        (b"", b"test", 4),
    ],
)
def test_fixed_bytes_add(
    other: FixedBytes[typing.Any] | Bytes | bytes, expected: bytes, expected_len: int
) -> None:
    """Test FixedBytes __add__ with various types."""
    fb4 = FixedBytes[typing.Literal[4]](b"test")

    result = fb4 + other
    assert isinstance(result, Bytes)
    assert result == expected
    assert len(result) == expected_len


def test_fixed_bytes_radd_with_bytes_literal() -> None:
    """Test FixedBytes __radd__ with bytes literal."""
    fb4 = FixedBytes[typing.Literal[4]](b"test")

    result = b"123" + fb4
    assert isinstance(result, Bytes)
    assert result == b"123test"
    assert len(result) == 7


def test_fixed_bytes_add_overflow() -> None:
    """Test FixedBytes __add__ raises OverflowError when result exceeds MAX_BYTES_SIZE."""
    # Create a FixedBytes that's close to MAX_BYTES_SIZE
    fb_large = FixedBytes[typing.Literal[4096]](b"x" * 4096)

    # Try to add bytes that would exceed MAX_BYTES_SIZE (4096 bytes)
    with pytest.raises(OverflowError, match=r"\+ overflows"):
        _ = fb_large + (b"y" * (MAX_BYTES_SIZE - 4095))


@pytest.mark.parametrize(
    ("other", "expected_equal"),
    [
        (FixedBytes[typing.Literal[4]](b"test"), True),
        (FixedBytes[typing.Literal[4]](b"diff"), False),
        (Bytes(b"test"), True),
        (Bytes(b"diff"), False),
        (b"test", True),
        (b"diff", False),
        (b"testtest", False),  # different length
        (FixedBytes[typing.Literal[8]](b"testtest"), False),  # different length
        ("test", False),  # invalid type
        (123, False),  # invalid type
        ([1, 2, 3, 4], False),  # invalid type
    ],
)
def test_fixed_bytes_eq(other: typing.Any, *, expected_equal: bool) -> None:
    """Test FixedBytes __eq__ and __ne__ with various types and values."""
    fb = FixedBytes[typing.Literal[4]](b"test")

    # Test __eq__
    assert (fb == other) is expected_equal
    # Test __ne__
    assert (fb != other) is not expected_equal


@pytest.mark.parametrize(
    ("a_value", "b_value", "expected"),
    [
        (b"\xff\xff\xff\xff", b"\x0f\x0f\x0f\x0f", b"\x0f\x0f\x0f\x0f"),
        (b"\xaa\xaa\xaa\xaa", b"\x55\x55\x55\x55", b"\x00\x00\x00\x00"),
        (b"\xff\x00\xff\x00", b"\x0f\xf0\x0f\xf0", b"\x0f\x00\x0f\x00"),
        (b"\x00\x00\x00\x00", b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"),
    ],
)
def test_fixed_bytes_and(a_value: bytes, b_value: bytes, expected: bytes) -> None:
    """Test FixedBytes __and__ (bitwise AND) with same length FixedBytes."""
    fb_a = FixedBytes[typing.Literal[4]](a_value)
    fb_b = FixedBytes[typing.Literal[4]](b_value)

    result = fb_a & fb_b
    # Same length should return FixedBytes
    assert isinstance(result, FixedBytes)
    assert result == expected


def test_fixed_bytes_and_with_bytes() -> None:
    """Test FixedBytes __and__ with bytes literal."""
    fb = FixedBytes[typing.Literal[4]](b"\xff\xff\xff\xff")

    result = fb & b"\x0f\x0f\x0f\x0f"
    assert isinstance(result, Bytes)
    assert result == b"\x0f\x0f\x0f\x0f"


def test_fixed_bytes_and_different_lengths() -> None:
    """Test FixedBytes __and__ with different length operands."""
    fb4 = FixedBytes[typing.Literal[4]](b"\xff\xff\xff\xff")
    fb2 = FixedBytes[typing.Literal[2]](b"\x0f\x0f")

    result = fb4 & fb2
    assert isinstance(result, Bytes)
    # Shorter operand is zero-padded on the left
    assert result == b"\x00\x00\x0f\x0f"


def test_fixed_bytes_rand() -> None:
    """Test FixedBytes __rand__ (reverse AND)."""
    fb = FixedBytes[typing.Literal[4]](b"\xff\x00\xff\x00")

    result = b"\x0f\xf0\x0f\xf0" & fb
    assert isinstance(result, Bytes)
    assert result == b"\x0f\x00\x0f\x00"


@pytest.mark.parametrize(
    ("a_value", "b_value", "expected"),
    [
        (b"\xff\xff\xff\xff", b"\x0f\x0f\x0f\x0f", b"\xff\xff\xff\xff"),
        (b"\xaa\xaa\xaa\xaa", b"\x55\x55\x55\x55", b"\xff\xff\xff\xff"),
        (b"\xff\x00\xff\x00", b"\x0f\xf0\x0f\xf0", b"\xff\xf0\xff\xf0"),
        (b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"),
    ],
)
def test_fixed_bytes_or(a_value: bytes, b_value: bytes, expected: bytes) -> None:
    """Test FixedBytes __or__ (bitwise OR) with same length FixedBytes."""
    fb_a = FixedBytes[typing.Literal[4]](a_value)
    fb_b = FixedBytes[typing.Literal[4]](b_value)

    result = fb_a | fb_b
    # Same length should return FixedBytes
    assert isinstance(result, FixedBytes)
    assert result == expected


def test_fixed_bytes_or_with_bytes() -> None:
    """Test FixedBytes __or__ with bytes literal."""
    fb = FixedBytes[typing.Literal[4]](b"\x0f\x0f\x0f\x0f")

    result = fb | b"\xf0\xf0\xf0\xf0"
    assert isinstance(result, Bytes)
    assert result == b"\xff\xff\xff\xff"


def test_fixed_bytes_or_different_lengths() -> None:
    """Test FixedBytes __or__ with different length operands."""
    fb4 = FixedBytes[typing.Literal[4]](b"\xff\xff\x00\x00")
    fb2 = FixedBytes[typing.Literal[2]](b"\x0f\x0f")

    result = fb4 | fb2
    assert isinstance(result, Bytes)
    # Shorter operand is zero-padded on the left
    assert result == b"\xff\xff\x0f\x0f"


def test_fixed_bytes_ror() -> None:
    """Test FixedBytes __ror__ (reverse OR)."""
    fb = FixedBytes[typing.Literal[4]](b"\x0f\x0f\x0f\x0f")

    result = b"\xf0\xf0\xf0\xf0" | fb
    assert isinstance(result, Bytes)
    assert result == b"\xff\xff\xff\xff"


@pytest.mark.parametrize(
    ("a_value", "b_value", "expected"),
    [
        (b"\xff\xff\xff\xff", b"\x0f\x0f\x0f\x0f", b"\xf0\xf0\xf0\xf0"),
        (b"\xaa\xaa\xaa\xaa", b"\x55\x55\x55\x55", b"\xff\xff\xff\xff"),
        (b"\xff\x00\xff\x00", b"\x0f\xf0\x0f\xf0", b"\xf0\xf0\xf0\xf0"),
        (b"\x00\x00\x00\x00", b"\x00\x00\x00\x00", b"\x00\x00\x00\x00"),
    ],
)
def test_fixed_bytes_xor(a_value: bytes, b_value: bytes, expected: bytes) -> None:
    """Test FixedBytes __xor__ (bitwise XOR) with same length FixedBytes."""
    fb_a = FixedBytes[typing.Literal[4]](a_value)
    fb_b = FixedBytes[typing.Literal[4]](b_value)

    result = fb_a ^ fb_b
    # Same length should return FixedBytes
    assert isinstance(result, FixedBytes)
    assert result == expected


def test_fixed_bytes_xor_with_bytes() -> None:
    """Test FixedBytes __xor__ with bytes literal."""
    fb = FixedBytes[typing.Literal[4]](b"\xff\xff\xff\xff")

    result = fb ^ b"\x0f\x0f\x0f\x0f"
    assert isinstance(result, Bytes)
    assert result == b"\xf0\xf0\xf0\xf0"


def test_fixed_bytes_xor_different_lengths() -> None:
    """Test FixedBytes __xor__ with different length operands."""
    fb4 = FixedBytes[typing.Literal[4]](b"\xff\xff\x00\x00")
    fb2 = FixedBytes[typing.Literal[2]](b"\x0f\x0f")

    result = fb4 ^ fb2
    assert isinstance(result, Bytes)
    # Shorter operand is zero-padded on the left
    assert result == b"\xff\xff\x0f\x0f"


def test_fixed_bytes_rxor() -> None:
    """Test FixedBytes __rxor__ (reverse XOR)."""
    fb = FixedBytes[typing.Literal[4]](b"\xff\xff\xff\xff")

    result = b"\x0f\x0f\x0f\x0f" ^ fb
    assert isinstance(result, Bytes)
    assert result == b"\xf0\xf0\xf0\xf0"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (b"\xff\xff\xff\xff", b"\x00\x00\x00\x00"),
        (b"\x00\x00\x00\x00", b"\xff\xff\xff\xff"),
        (b"\xaa\xaa\xaa\xaa", b"\x55\x55\x55\x55"),
        (b"\x0f\xf0\x0f\xf0", b"\xf0\x0f\xf0\x0f"),
    ],
)
def test_fixed_bytes_invert(value: bytes, expected: bytes) -> None:
    """Test FixedBytes __invert__ (bitwise NOT)."""
    fb = FixedBytes[typing.Literal[4]](value)

    result = ~fb
    assert isinstance(result, FixedBytes)
    assert result == expected


@pytest.mark.parametrize(
    ("haystack", "needle", "expected_contains"),
    [
        (b"hello world", b"world", True),
        (b"hello world", b"hello", True),
        (b"hello world", b"o w", True),
        (b"hello world", b"", True),  # empty bytes is always contained
        (b"hello world", b"x", False),
        (b"hello world", b"Hello", False),  # case sensitive
        (b"hello world", b"worldx", False),  # longer than substring
        (b"\x00\x01\x02\x03" + b"\00" * 7, b"\x01\x02", True),
        (b"\x00\x01\x02\x03" + b"\00" * 7, b"\x02\x03", True),
        (b"\x00\x01\x02\x03" + b"\00" * 7, b"\x03\x04", False),
    ],
)
def test_fixed_bytes_contains_with_bytes(
    haystack: bytes, needle: bytes, *, expected_contains: bool
) -> None:
    """Test FixedBytes __contains__ with bytes literal."""
    fb = FixedBytes[typing.Literal[11]](haystack)

    assert (needle in fb) is expected_contains


def test_fixed_bytes_contains_with_bytes_object() -> None:
    """Test FixedBytes __contains__ with Bytes object."""
    fb = FixedBytes[typing.Literal[11]](b"hello world")

    assert Bytes(b"world") in fb
    assert Bytes(b"hello") in fb
    assert Bytes(b"xyz") not in fb


def test_fixed_bytes_contains_with_fixed_bytes() -> None:
    """Test FixedBytes __contains__ with another FixedBytes."""
    fb = FixedBytes[typing.Literal[11]](b"hello world")

    assert FixedBytes[typing.Literal[5]](b"world") in fb
    assert FixedBytes[typing.Literal[5]](b"hello") in fb
    assert FixedBytes[typing.Literal[3]](b"xyz") not in fb


def test_fixed_bytes_contains_edge_cases() -> None:
    """Test FixedBytes __contains__ edge cases."""
    fb = FixedBytes[typing.Literal[4]](b"test")

    # Full match
    assert b"test" in fb

    # Single byte
    assert b"t" in fb
    assert b"e" in fb
    assert b"s" in fb

    # Not present
    assert b"x" not in fb
    assert b"testing" not in fb  # longer than haystack
