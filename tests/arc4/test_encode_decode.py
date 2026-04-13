import typing

import pytest
from _algopy_testing import arc4
from algokit_utils.applications import abi
from algopy import Account, Application, Asset, BigUInt, Bytes, String, UInt64

from tests.common import AVMInvoker


class Arc4Struct(arc4.Struct):
    x: arc4.UInt64
    y: arc4.String


class MyNamedTuple(typing.NamedTuple):
    x: UInt64
    y: String


@pytest.mark.parametrize(
    ("native_value", "expected_hex"),
    [
        pytest.param(UInt64(42), "000000000000002a", id="uint64"),
        pytest.param(
            BigUInt(42),
            # BigUInt encodes as ARC-4 UInt512 (64 bytes big-endian)
            "00" * 63 + "2a",
            id="biguint",
        ),
        pytest.param(String("hello"), "000568656c6c6f", id="string"),
        pytest.param(Bytes(b"\x01\x02\x03"), "0003010203", id="bytes"),
        pytest.param(True, "80", id="bool-true"),
        pytest.param(False, "00", id="bool-false"),
        pytest.param(Asset(42), "000000000000002a", id="asset"),
        pytest.param(Application(123), "000000000000007b", id="application"),
    ],
)
def test_encode_native_value_bytes(native_value: object, expected_hex: str) -> None:
    encoded = arc4.encode(native_value)
    assert encoded == bytes.fromhex(expected_hex)


@pytest.mark.parametrize(
    ("native_type", "value"),
    [
        pytest.param(UInt64, UInt64(42), id="uint64-42"),
        pytest.param(UInt64, UInt64(0), id="uint64-0"),
        pytest.param(UInt64, UInt64(2**64 - 1), id="uint64-max"),
        pytest.param(BigUInt, BigUInt(0), id="biguint-0"),
        pytest.param(BigUInt, BigUInt(42), id="biguint-42"),
        pytest.param(BigUInt, BigUInt(2**256), id="biguint-large"),
        pytest.param(String, String(""), id="string-empty"),
        pytest.param(String, String("hello"), id="string-hello"),
        pytest.param(Bytes, Bytes(b""), id="bytes-empty"),
        pytest.param(Bytes, Bytes(b"\x01\x02\x03"), id="bytes-three"),
        pytest.param(bool, True, id="bool-true"),
        pytest.param(bool, False, id="bool-false"),
        pytest.param(Asset, Asset(42), id="asset"),
        pytest.param(Application, Application(123), id="application"),
    ],
)
def test_encode_decode_round_trip_native(native_type: type, value: object) -> None:
    encoded = arc4.encode(value)
    decoded = arc4.decode(native_type, encoded)  # type: ignore[var-annotated]
    assert decoded == value
    assert isinstance(decoded, native_type)


@pytest.mark.parametrize(
    "value",
    [
        arc4.Bool(True),
        arc4.Bool(False),
        arc4.UInt8(7),
        arc4.UInt64(42),
        arc4.UInt256(2**200),
        arc4.UInt512(2**500),
        arc4.String(""),
        arc4.String("hello"),
        arc4.DynamicBytes(b""),
        arc4.DynamicBytes(b"\x01\x02\x03"),
        arc4.StaticArray(arc4.UInt8(1), arc4.UInt8(2), arc4.UInt8(3)),
        arc4.DynamicArray(arc4.String("a"), arc4.String("bc")),
        arc4.Tuple((arc4.UInt64(1), arc4.String("hi"), arc4.Bool(True))),
    ],
)
def test_encode_arc4_value_reinterprets_bytes(value: arc4._ABIEncoded) -> None:
    # passing an already-ARC-4-encoded value just returns its underlying bytes
    assert arc4.encode(value) == value.bytes


@pytest.mark.parametrize(
    ("arc4_type", "value"),
    [
        pytest.param(arc4.Bool, arc4.Bool(True), id="bool"),
        pytest.param(arc4.UInt8, arc4.UInt8(7), id="uint8"),
        pytest.param(arc4.UInt64, arc4.UInt64(42), id="uint64"),
        pytest.param(arc4.UInt256, arc4.UInt256(2**200), id="uint256"),
        pytest.param(arc4.String, arc4.String("hello"), id="string"),
        pytest.param(arc4.DynamicBytes, arc4.DynamicBytes(b"\x01\x02\x03"), id="dynamic-bytes"),
        pytest.param(
            arc4.DynamicArray[arc4.UInt64],
            arc4.DynamicArray(arc4.UInt64(1), arc4.UInt64(2), arc4.UInt64(3)),
            id="dynamic-array",
        ),
        pytest.param(
            arc4.StaticArray[arc4.UInt64, typing.Literal[2]],
            arc4.StaticArray(arc4.UInt64(10), arc4.UInt64(20)),
            id="static-array",
        ),
    ],
)
def test_decode_returns_arc4_type_when_typ_is_arc4(
    arc4_type: type[arc4._ABIEncoded], value: arc4._ABIEncoded
) -> None:
    decoded = arc4.decode(arc4_type, arc4.encode(value))
    assert isinstance(decoded, arc4_type)
    assert decoded == value


def test_encode_decode_mixed_tuple() -> None:
    value = (UInt64(1), String("hi"), True)
    encoded = arc4.encode(value)
    # parity with the canonical ABI encoder
    expected = abi.ABIType.from_string("(uint64,string,bool)").encode((1, "hi", True))
    assert encoded.value == expected

    decoded = arc4.decode(tuple[UInt64, String, bool], encoded)
    assert decoded == value


def test_encode_decode_named_tuple() -> None:
    value = MyNamedTuple(x=UInt64(5), y=String("test"))
    encoded = arc4.encode(value)
    decoded = arc4.decode(MyNamedTuple, encoded)
    assert decoded == value


def test_encode_decode_arc4_struct() -> None:
    original = Arc4Struct(x=arc4.UInt64(42), y=arc4.String("hello"))
    encoded = arc4.encode(original)
    decoded = arc4.decode(Arc4Struct, encoded)
    assert decoded == original


def test_encode_decode_account() -> None:
    value = Account("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ")
    encoded = arc4.encode(value)
    decoded = arc4.decode(Account, encoded)
    assert decoded == value


def test_decode_accepts_raw_bytes_and_algopy_bytes() -> None:
    encoded = arc4.encode(UInt64(123))
    from_algopy_bytes = arc4.decode(UInt64, encoded)
    from_raw_bytes = arc4.decode(UInt64, encoded.value)
    assert from_algopy_bytes == from_raw_bytes == UInt64(123)


def test_encode_rejects_unsupported_type() -> None:
    with pytest.raises(TypeError, match="unserializable type"):
        arc4.encode(object())


@pytest.mark.parametrize(
    "value",
    [
        pytest.param(42, id="int"),
        pytest.param(b"hi", id="bytes"),
        pytest.param("hi", id="str"),
    ],
)
def test_encode_rejects_raw_python_primitives(value: object) -> None:
    # raw Python int/bytes/str are intentionally unsupported — callers must wrap them
    # in the corresponding algopy/arc4 type (e.g. UInt64(42), Bytes(b"hi"), String("hi"))
    # so the intended ABI type is explicit.
    with pytest.raises(TypeError, match="unserializable type"):
        arc4.encode(value)


def test_decode_rejects_unsupported_type() -> None:
    with pytest.raises(TypeError, match="unserializable type"):
        arc4.decode(list, b"\x00" * 8)


def test_verify_encode_decode_avm_parity(get_avm_result: AVMInvoker) -> None:
    # ensure the same encode/decode cases also succeed on the AVM
    get_avm_result("verify_encode_decode")
