import typing
from collections.abc import Generator

import pytest
from algopy import BigUInt, Bytes, String, UInt64, arc4
from algopy_testing import AlgopyTestContext, algopy_testing_context

from tests.artifacts.LogicSignature.lsig_args_complex import (
    NestedStruct,
    OverwriteStruct,
    SimpleNamedTuple,
    SimpleStruct,
    args_complex,
    args_complex_no_validation,
)


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def _build_args() -> tuple[
    UInt64,
    Bytes,
    BigUInt,
    String,
    bool,
    arc4.UInt8,
    arc4.UInt64,
    arc4.UInt128,
    arc4.Address,
    arc4.Bool,
    arc4.String,
    arc4.DynamicBytes,
    arc4.StaticArray[arc4.Byte, typing.Literal[4]],
    SimpleStruct,
    NestedStruct,
    arc4.Tuple[arc4.UInt8, arc4.UInt64],
    SimpleNamedTuple,
    tuple[UInt64, Bytes],
    tuple[UInt64, tuple[Bytes, UInt64]],
    OverwriteStruct,
    arc4.DynamicArray[arc4.UInt8],
]:
    return (
        UInt64(42),
        Bytes(b"hello"),
        BigUInt(999),
        String("world"),
        True,
        arc4.UInt8(10),
        arc4.UInt64(100),
        arc4.UInt128(1000),
        arc4.Address("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"),
        arc4.Bool(True),
        arc4.String("test"),
        arc4.DynamicBytes(b"\x01\x02\x03"),
        arc4.StaticArray(arc4.Byte(0x01), arc4.Byte(0x02), arc4.Byte(0x03), arc4.Byte(0x04)),
        SimpleStruct(x=arc4.UInt64(1), y=arc4.UInt64(2)),
        NestedStruct(
            header=arc4.UInt8(5),
            data=SimpleStruct(x=arc4.UInt64(10), y=arc4.UInt64(20)),
        ),
        arc4.Tuple((arc4.UInt8(7), arc4.UInt64(77))),
        SimpleNamedTuple(a=arc4.UInt8(3), b=arc4.UInt64(33)),
        (UInt64(50), Bytes(b"data")),
        (UInt64(60), (Bytes(b"nested"), UInt64(70))),
        OverwriteStruct(value=arc4.UInt8(9), dont_overwrite_me=arc4.Bool(False)),
        arc4.DynamicArray(arc4.UInt8(1), arc4.UInt8(2)),
    )


def test_args_complex(context: AlgopyTestContext) -> None:
    args = _build_args()
    result = context.execute_logicsig(args_complex, *args)
    # arg9 = arc4.Bool(True) -> mutated to arc4.Bool(not True) = False
    assert result is False


def test_args_complex_returns_true(context: AlgopyTestContext) -> None:
    args = list(_build_args())
    args[9] = arc4.Bool(False)  # arg9: after `not arg9.native` becomes True
    result = context.execute_logicsig(args_complex, *args)
    assert result is True


def test_args_complex_no_validation(context: AlgopyTestContext) -> None:
    args = _build_args()
    result = context.execute_logicsig(args_complex_no_validation, *args)
    assert result is False
