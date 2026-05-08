import typing
from collections.abc import Generator
from dataclasses import FrozenInstanceError

import _algopy_testing
import pytest
from _algopy_testing import arc4
from algokit_utils.applications import abi
from algopy import Account, Application, Asset, BigUInt, Bytes, String, UInt64

from tests.artifacts.Arc4PrimitiveOps.contract import Arc4PrimitiveOpsContract
from tests.common import AVMInvoker


class Arc4Struct(arc4.Struct):
    x: arc4.UInt64
    y: arc4.String


class NativeStruct(arc4.Struct):
    a: UInt64
    b: bool


class MixedStruct(arc4.Struct):
    native_u: UInt64
    arc4_u: arc4.UInt64
    native_s: String
    arc4_s: arc4.String
    flag: bool


class NativeStructWithAccount(arc4.Struct):
    owner: Account
    balance: UInt64


class NativeStructWithResources(arc4.Struct):
    asset: Asset
    app: Application
    owner: Account


class OuterStruct(arc4.Struct):
    tag: UInt64
    inner: NativeStruct


class FrozenNativeStruct(arc4.Struct, frozen=True):
    x: UInt64
    y: bool


class MyNamedTuple(typing.NamedTuple):
    x: UInt64
    y: String


@pytest.fixture()
def context() -> Generator[_algopy_testing.AlgopyTestContext, None, None]:
    with _algopy_testing.algopy_testing_context() as ctx:
        yield ctx


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


def test_encode_decode_native_struct() -> None:
    # arc4.Struct with native-typed fields: serialized via native_to_arc4
    # on the way in, and arc4_to_native on the way out, so the decoded fields
    # retain their declared native types.
    original = NativeStruct(a=UInt64(1), b=True)
    encoded = arc4.encode(original)
    # 8-byte UInt64 + 1-byte bool (0x80 = True)
    assert encoded == bytes.fromhex("000000000000000180")
    decoded = arc4.decode(NativeStruct, encoded)
    assert decoded == original
    # ensure the decoded field types match the declared native annotations
    assert isinstance(decoded.a, UInt64)
    assert isinstance(decoded.b, bool)


def test_encode_decode_struct_with_mixed_native_and_arc4_fields() -> None:
    original = MixedStruct(
        native_u=UInt64(5),
        arc4_u=arc4.UInt64(6),
        native_s=String("native"),
        arc4_s=arc4.String("arc4"),
        flag=True,
    )
    encoded = arc4.encode(original)
    decoded = arc4.decode(MixedStruct, encoded)
    assert decoded == original
    # declared types are preserved per-field after round-trip
    assert isinstance(decoded.native_u, UInt64)
    assert isinstance(decoded.arc4_u, arc4.UInt64)
    assert isinstance(decoded.native_s, String)
    assert isinstance(decoded.arc4_s, arc4.String)
    assert isinstance(decoded.flag, bool)


def test_encode_decode_native_struct_with_account_field() -> None:
    # covers a native field whose serializer goes through Account<->Address
    original = NativeStructWithAccount(
        owner=Account("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"),
        balance=UInt64(1000),
    )
    encoded = arc4.encode(original)
    decoded = arc4.decode(NativeStructWithAccount, encoded)
    assert decoded == original
    assert isinstance(decoded.owner, Account)
    assert isinstance(decoded.balance, UInt64)


def test_native_struct_bytes_match_tuple_bytes() -> None:
    # the struct's encoded bytes must match the canonical ABI tuple encoding
    struct_val = NativeStruct(a=UInt64(1), b=True)
    tuple_bytes = abi.ABIType.from_string("(uint64,bool)").encode((1, True))
    assert arc4.encode(struct_val).value == tuple_bytes


def test_encode_decode_nested_native_struct() -> None:
    # a struct field whose type is itself an arc4.Struct with native fields —
    # exercises the recursive serializer path through Struct → Struct
    original = OuterStruct(tag=UInt64(7), inner=NativeStruct(a=UInt64(1), b=True))
    encoded = arc4.encode(original)
    decoded = arc4.decode(OuterStruct, encoded)
    assert decoded == original
    assert isinstance(decoded.tag, UInt64)
    assert isinstance(decoded.inner, NativeStruct)
    assert isinstance(decoded.inner.a, UInt64)
    assert isinstance(decoded.inner.b, bool)


def test_encode_decode_native_struct_with_resource_fields() -> None:
    # Asset and Application are UInt64Backed natives — the per-field
    # arc4_to_native path routes through `from_int` rather than the simple map
    original = NativeStructWithResources(
        asset=Asset(42),
        app=Application(123),
        owner=Account("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"),
    )
    encoded = arc4.encode(original)
    decoded = arc4.decode(NativeStructWithResources, encoded)
    assert decoded == original
    assert isinstance(decoded.asset, Asset)
    assert isinstance(decoded.app, Application)
    assert isinstance(decoded.owner, Account)


def test_frozen_native_struct_round_trip_and_mutation_guard() -> None:
    original = FrozenNativeStruct(x=UInt64(9), y=True)
    encoded = arc4.encode(original)
    decoded = arc4.decode(FrozenNativeStruct, encoded)
    assert decoded == original
    # frozen-mutation detection must still fire when native-wrapping is in play
    with pytest.raises(FrozenInstanceError):
        decoded.x = UInt64(10)  # type: ignore[misc]


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


def test_verify_encode_decode_avm_parity(
    get_avm_result: AVMInvoker,
    context: _algopy_testing.AlgopyTestContext,  # noqa: ARG001
) -> None:
    # ensure the same encode/decode cases also succeed on the AVM
    get_avm_result("verify_encode_decode")
    contract = Arc4PrimitiveOpsContract()
    contract.verify_encode_decode()
