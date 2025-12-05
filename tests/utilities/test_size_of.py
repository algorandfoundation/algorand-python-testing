import typing

import pytest
from algopy import (
    Account,
    Application,
    Array,
    Asset,
    Bytes,
    FixedArray,
    FixedBytes,
    ImmutableArray,
    ImmutableFixedArray,
    String,
    Struct,
    UInt64,
    arc4,
    size_of,
)


class SwappedArc4(arc4.Struct):
    a: arc4.UInt64
    b: arc4.Bool
    c: arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Bool]
    d: arc4.StaticArray[arc4.Bool, typing.Literal[10]]
    e: arc4.Tuple[arc4.UInt64, arc4.StaticArray[arc4.UInt64, typing.Literal[3]]]


class Swapped(Struct):
    a: UInt64
    b: bool
    c: tuple[UInt64, bool, bool]
    d: FixedArray[bool, typing.Literal[10]]
    e: tuple[UInt64, ImmutableFixedArray[UInt64, typing.Literal[3]]]
    f: FixedBytes[typing.Literal[5]]


class WhatsMySize(typing.NamedTuple):
    foo: UInt64
    bar: bool
    bax: Swapped
    baz: SwappedArc4


class MyTuple(typing.NamedTuple):
    foo: UInt64
    bar: bool
    baz: bool


class MyDynamicSizedTuple(typing.NamedTuple):
    foo: UInt64
    bar: String


def test_size_of() -> None:
    x = arc4.UInt64(0)
    assert size_of(x) == 8
    assert size_of(arc4.UInt64) == 8
    assert size_of(UInt64) == 8
    assert size_of(arc4.Address) == 32
    assert size_of(Account) == 32
    assert size_of(Application) == 8
    assert size_of(Asset) == 8
    assert size_of(bool) == 8
    assert size_of(tuple[bool]) == 1
    assert size_of(tuple[bool, bool, bool, bool, bool, bool, bool, bool]) == 1
    assert size_of(tuple[bool, bool, bool, bool, bool, bool, bool, bool, bool]) == 2
    assert size_of(tuple[arc4.UInt64, UInt64, bool, arc4.Bool]) == 17
    assert size_of(arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Bool] == 9)
    assert size_of(MyTuple) == 9
    assert size_of(SwappedArc4) == 52
    assert size_of(Swapped) == 57
    assert size_of(WhatsMySize) == 118
    assert size_of(arc4.StaticArray[arc4.Byte, typing.Literal[7]]) == 7
    assert size_of(arc4.StaticArray(arc4.Byte(), arc4.Byte())) == 2
    assert size_of(FixedArray[bool, typing.Literal[10]]) == 2
    assert size_of(ImmutableFixedArray[bool, typing.Literal[10]]) == 2


@pytest.mark.parametrize(
    "typ",
    [
        arc4.StaticArray[arc4.DynamicBytes, typing.Literal[7]],
        tuple[arc4.DynamicBytes, Bytes],
        arc4.Tuple[arc4.UInt64, arc4.String],
        MyDynamicSizedTuple,
        Array[UInt64],
        ImmutableArray[UInt64],
    ],
)
def test_size_of_dynamic(typ: type) -> None:
    with pytest.raises(ValueError, match="is dynamically sized"):
        size_of(typ)
