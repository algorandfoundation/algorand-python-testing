import typing

from algopy import (
    Account,
    Application,
    ARC4Contract,
    Array,
    Asset,
    BigUInt,
    Bytes,
    FixedArray,
    ImmutableArray,
    ImmutableFixedArray,
    String,
    Struct,
    UInt64,
    arc4,
    subroutine,
)


class Arc4PrimitiveOpsContract(ARC4Contract):
    @arc4.abimethod()
    def verify_uintn_uintn_eq(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) == arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_eq(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) == arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_eq(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) == arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_eq(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) == arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_uintn_ne(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) != arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_ne(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) != arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_ne(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) != arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_ne(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) != arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_uintn_lt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) < arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_lt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) < arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_lt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) < arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_lt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) < arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_uintn_le(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) <= arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_le(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) <= arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_le(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) <= arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_le(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) <= arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_uintn_gt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) > arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_gt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) > arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_gt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) > arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_gt(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) > arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_uintn_ge(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) >= arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_uintn_ge(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) >= arc4.UInt64(b_biguint)

    @arc4.abimethod()
    def verify_uintn_biguintn_ge(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt64(a_biguint) >= arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_biguintn_biguintn_ge(self, a: Bytes, b: Bytes) -> bool:
        a_biguint = BigUInt.from_bytes(a)
        b_biguint = BigUInt.from_bytes(b)
        return arc4.UInt512(a_biguint) >= arc4.UInt512(b_biguint)

    @arc4.abimethod()
    def verify_uintn_init(self, a: Bytes) -> arc4.UInt32:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt32(a_biguint)

    @arc4.abimethod()
    def verify_biguintn_init(self, a: Bytes) -> arc4.UInt256:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt256(a_biguint)

    @arc4.abimethod()
    def verify_uintn_from_bytes(self, a: Bytes) -> arc4.UInt32:
        return arc4.UInt32.from_bytes(a)

    @arc4.abimethod()
    def verify_biguintn_from_bytes(self, a: Bytes) -> arc4.UInt256:
        return arc4.UInt256.from_bytes(a)

    @arc4.abimethod()
    def verify_uintn_from_log(self, a: Bytes) -> arc4.UInt32:
        return arc4.UInt32.from_log(a)

    @arc4.abimethod()
    def verify_biguintn_from_log(self, a: Bytes) -> arc4.UInt256:
        return arc4.UInt256.from_log(a)

    @arc4.abimethod()
    def verify_biguintn_as_uint64(self, a: Bytes) -> UInt64:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt256(a_biguint).as_uint64()

    @arc4.abimethod()
    def verify_biguintn_as_biguint(self, a: Bytes) -> BigUInt:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt256(a_biguint).as_biguint()

    @arc4.abimethod()
    def verify_uintn64_as_uint64(self, a: Bytes) -> UInt64:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt64(a_biguint).as_uint64()

    @arc4.abimethod()
    def verify_uintn64_as_biguint(self, a: Bytes) -> BigUInt:
        a_biguint = BigUInt.from_bytes(a)
        return arc4.UInt64(a_biguint).as_biguint()

    @arc4.abimethod()
    def verify_ufixednxm_bytes(
        self, a: arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]]
    ) -> Bytes:
        return a.bytes

    @arc4.abimethod()
    def verify_bigufixednxm_bytes(
        self, a: arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]
    ) -> Bytes:
        return a.bytes

    @arc4.abimethod()
    def verify_ufixednxm_from_bytes(
        self, a: Bytes
    ) -> arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]]:
        return arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]].from_bytes(a)

    @arc4.abimethod()
    def verify_bigufixednxm_from_bytes(
        self, a: Bytes
    ) -> arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]:
        return arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]].from_bytes(a)

    @arc4.abimethod()
    def verify_ufixednxm_from_log(
        self, a: Bytes
    ) -> arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]]:
        return arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]].from_log(a)

    @arc4.abimethod()
    def verify_bigufixednxm_from_log(
        self, a: Bytes
    ) -> arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]:
        return arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]].from_log(a)

    @arc4.abimethod
    def verify_string_init(self, a: String) -> arc4.String:
        result = arc4.String(String("Hello, ") + a)
        return result

    @arc4.abimethod
    def verify_string_add(self, a: arc4.String, b: arc4.String) -> arc4.String:
        result = a + b
        return result

    @arc4.abimethod()
    def verify_string_eq(self, a: arc4.String, b: arc4.String) -> bool:
        return a == b

    @arc4.abimethod()
    def verify_string_bytes(self, a: String) -> Bytes:
        result = arc4.String(a)
        return result.bytes

    @arc4.abimethod()
    def verify_string_from_bytes(self, a: Bytes) -> arc4.String:
        return arc4.String.from_bytes(a)

    @arc4.abimethod()
    def verify_string_from_log(self, a: Bytes) -> arc4.String:
        return arc4.String.from_log(a)

    @arc4.abimethod()
    def verify_bool_bytes(self, a: arc4.Bool) -> Bytes:
        return a.bytes

    @arc4.abimethod()
    def verify_bool_from_bytes(self, a: Bytes) -> arc4.Bool:
        return arc4.Bool.from_bytes(a)

    @arc4.abimethod()
    def verify_bool_from_log(self, a: Bytes) -> arc4.Bool:
        return arc4.Bool.from_log(a)

    @arc4.abimethod()
    def verify_emit(  # noqa: PLR0913
        self,
        a: arc4.String,
        b: arc4.UInt512,
        c: arc4.UInt64,
        d: arc4.DynamicBytes,
        e: arc4.UInt64,
        f: arc4.Bool,
        g: arc4.DynamicBytes,
        h: arc4.String,
        m: arc4.UIntN[typing.Literal[64]],
        n: arc4.BigUIntN[typing.Literal[256]],
        o: arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]],
        p: arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]],
        q: arc4.Bool,
        r: Bytes,
        s: Bytes,
        t: Bytes,
    ) -> None:
        arc4_r = arc4.StaticArray[arc4.UInt8, typing.Literal[3]].from_bytes(r)
        arc4_s = arc4.DynamicArray[arc4.UInt16].from_bytes(s)
        arc4_t = arc4.Tuple[arc4.UInt32, arc4.UInt64, arc4.String].from_bytes(t)

        arc4.emit(SwappedArc4(m, n, o, p, q, arc4_r, arc4_s, arc4_t))
        arc4.emit(
            "Swapped",
            a,
            b,
            c,
            d.copy(),
            e,
            f,
            g.copy(),
            h,
            m,
            n,
            o,
            p,
            q,
            arc4_r.copy(),
            arc4_s.copy(),
            arc4_t,
        )
        arc4.emit(
            "Swapped(string,uint512,uint64,byte[],uint64,bool,byte[],string,uint64,uint256,ufixed32x8,ufixed256x16,bool,uint8[3],uint16[],(uint32,uint64,string))",
            a,
            b,
            c,
            d.copy(),
            e,
            f,
            g.copy(),
            h,
            m,
            n,
            o,
            p,
            q,
            arc4_r.copy(),
            arc4_s.copy(),
            arc4_t,
        )

    @arc4.abimethod()
    def verify_encode_decode(self) -> None:
        test_native_struct()
        test_arc4_native_struct()
        test_arc4_struct()
        test_uint64()
        test_biguint()
        test_string()
        test_bytes()
        test_bool()
        test_account()
        test_asset()
        test_application()
        test_arc4_uint64()
        test_arc4_string()
        test_tuple()
        test_named_tuple()
        test_arc4_dynamic_array()
        test_arc4_static_array()
        test_array()
        test_immutable_array()
        test_fixed_array()
        test_immutable_fixed_array()


class SwappedArc4(arc4.Struct):
    m: arc4.UIntN[typing.Literal[64]]
    n: arc4.BigUIntN[typing.Literal[256]]
    o: arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]]
    p: arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]
    q: arc4.Bool
    r: arc4.StaticArray[arc4.UInt8, typing.Literal[3]]
    s: arc4.DynamicArray[arc4.UInt16]
    t: arc4.Tuple[arc4.UInt32, arc4.UInt64, arc4.String]


class NativeStruct(Struct):
    a: UInt64
    b: bool


class Arc4NativeStruct(arc4.Struct):
    a: UInt64
    b: bool


class Arc4Struct(arc4.Struct):
    x: arc4.UInt64
    y: arc4.String


class MyNamedTuple(typing.NamedTuple):
    x: UInt64
    y: String


@subroutine()
def test_native_struct() -> None:
    original = NativeStruct(a=UInt64(1), b=True)
    encoded = arc4.encode(original)
    assert encoded == Bytes.from_hex("000000000000000180")
    decoded = arc4.decode(NativeStruct, encoded)
    assert decoded == original


@subroutine()
def test_arc4_native_struct() -> None:
    original = Arc4NativeStruct(a=UInt64(1), b=True)
    encoded = arc4.encode(original)
    assert encoded == Bytes.from_hex("000000000000000180")
    decoded = arc4.decode(Arc4NativeStruct, encoded)
    assert decoded == original


@subroutine()
def test_arc4_struct() -> None:
    original = Arc4Struct(x=arc4.UInt64(42), y=arc4.String("hello"))
    encoded = arc4.encode(original)
    decoded = arc4.decode(Arc4Struct, encoded)
    assert decoded == original


@subroutine()
def test_uint64() -> None:
    value = UInt64(42)
    encoded = arc4.encode(value)
    # UInt64 encodes as 8-byte big-endian
    assert encoded == Bytes.from_hex("000000000000002A")
    decoded = arc4.decode(UInt64, encoded)
    assert decoded == value


@subroutine()
def test_biguint() -> None:
    value = BigUInt(42)
    encoded = arc4.encode(value)
    decoded = arc4.decode(BigUInt, encoded)
    assert decoded == value


@subroutine()
def test_string() -> None:
    value = String("hello")
    encoded = arc4.encode(value)
    # 16 bit len + UTF-8 string
    assert encoded == Bytes.from_hex("000568656C6C6F")
    decoded = arc4.decode(String, encoded)
    assert decoded == value


@subroutine()
def test_bytes() -> None:
    value = Bytes(b"\x01\x02\x03")
    encoded = arc4.encode(value)
    # 16 bit len + bytes
    assert encoded == Bytes.from_hex("0003010203")
    decoded = arc4.decode(Bytes, encoded)
    assert decoded == value


@subroutine()
def test_bool() -> None:
    encoded_true = arc4.encode(True)
    assert encoded_true == Bytes.from_hex("80")
    decoded_true = arc4.decode(bool, encoded_true)
    assert decoded_true

    encoded_false = arc4.encode(False)
    assert encoded_false == Bytes.from_hex("00")
    decoded_false = arc4.decode(bool, encoded_false)
    assert not decoded_false


@subroutine()
def test_account() -> None:
    value = Account("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ")
    encoded = arc4.encode(value)
    decoded = arc4.decode(Account, encoded)
    assert decoded == value


@subroutine()
def test_asset() -> None:
    value = Asset(42)
    encoded = arc4.encode(value)
    assert encoded == Bytes.from_hex("000000000000002A")
    decoded = arc4.decode(Asset, encoded)
    assert decoded == value


@subroutine()
def test_application() -> None:
    value = Application(123)
    encoded = arc4.encode(value)
    assert encoded == Bytes.from_hex("000000000000007B")
    decoded = arc4.decode(Application, encoded)
    assert decoded == value


@subroutine()
def test_arc4_uint64() -> None:
    value = arc4.UInt64(42)
    encoded = arc4.encode(value)
    assert encoded == Bytes.from_hex("000000000000002A")
    decoded = arc4.decode(arc4.UInt64, encoded)
    assert decoded == value


@subroutine()
def test_arc4_string() -> None:
    value = arc4.String("hello")
    encoded = arc4.encode(value)
    assert encoded == Bytes.from_hex("000568656C6C6F")
    decoded = arc4.decode(arc4.String, encoded)
    assert decoded == value


@subroutine()
def test_tuple() -> None:
    value = (UInt64(1), UInt64(2))
    encoded = arc4.encode(value)
    assert encoded == Bytes.from_hex("00000000000000010000000000000002")
    decoded = arc4.decode(tuple[UInt64, UInt64], encoded)
    assert decoded == value


@subroutine()
def test_named_tuple() -> None:
    value = MyNamedTuple(x=UInt64(5), y=String("test"))
    encoded = arc4.encode(value)
    decoded = arc4.decode(MyNamedTuple, encoded)
    assert decoded == value


@subroutine()
def test_arc4_dynamic_array() -> None:
    value = arc4.DynamicArray(arc4.UInt64(1), arc4.UInt64(2), arc4.UInt64(3))
    encoded = arc4.encode(value)
    decoded = arc4.decode(arc4.DynamicArray[arc4.UInt64], encoded)
    assert decoded == value


@subroutine()
def test_arc4_static_array() -> None:
    value = arc4.StaticArray(arc4.UInt64(10), arc4.UInt64(20))
    encoded = arc4.encode(value)
    decoded = arc4.decode(arc4.StaticArray[arc4.UInt64, typing.Literal[2]], encoded)
    assert decoded == value


@subroutine()
def test_array() -> None:
    value = Array((UInt64(10), UInt64(20)))
    encoded = arc4.encode(value)
    decoded = arc4.decode(Array[UInt64], encoded)
    assert decoded == value


@subroutine()
def test_immutable_array() -> None:
    value = ImmutableArray((UInt64(10), UInt64(20)))
    encoded = arc4.encode(value)
    decoded = arc4.decode(ImmutableArray[UInt64], encoded)
    assert decoded == value


@subroutine()
def test_fixed_array() -> None:
    value = FixedArray[UInt64, typing.Literal[2]]((UInt64(10), UInt64(20)))
    encoded = arc4.encode(value)
    decoded = arc4.decode(FixedArray[UInt64, typing.Literal[2]], encoded)
    assert decoded == value


@subroutine()
def test_immutable_fixed_array() -> None:
    value = ImmutableFixedArray[UInt64, typing.Literal[2]]((UInt64(10), UInt64(20)))
    encoded = arc4.encode(value)
    decoded = arc4.decode(ImmutableFixedArray[UInt64, typing.Literal[2]], encoded)
    assert decoded == value
