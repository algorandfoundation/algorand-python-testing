import re
import typing
from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context, arc4, op
from _algopy_testing.constants import MAX_BYTES_SIZE
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.models.account import Account
from _algopy_testing.models.application import Application
from _algopy_testing.models.asset import Asset
from _algopy_testing.op.pure import itob
from _algopy_testing.primitives.array import (
    Array,
    FixedArray,
    ImmutableArray,
    ImmutableFixedArray,
    Struct,
)
from _algopy_testing.primitives.biguint import BigUInt
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.fixed_bytes import FixedBytes
from _algopy_testing.primitives.string import String
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.state.box import Box
from _algopy_testing.state.utils import cast_to_bytes
from _algopy_testing.utils import as_bytes, as_string

from tests.artifacts.BoxContract.contract import (
    BoxContract,
    InnerStruct,
    LargeNestedStruct,
    NestedStruct,
)

BOX_NOT_CREATED_ERROR = "Box has not been created"


class Swapped(arc4.Struct):
    b: arc4.UInt64
    c: arc4.Bool
    d: arc4.Address


class MyStruct(typing.NamedTuple):
    a: UInt64
    b: bool
    c: arc4.Bool
    d: arc4.UInt64
    e: Swapped


class ATestContract(algopy.Contract):
    def __init__(self) -> None:
        self.uint_64_box = algopy.Box(algopy.UInt64)


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:  # noqa: SIM117
        with ctx.txn.create_group([ctx.any.txn.application_call()]):
            yield ctx


def test_init_without_key() -> None:
    with algopy_testing_context():
        contract = ATestContract()
        assert contract.uint_64_box.key == b"uint_64_box"


@pytest.mark.parametrize(
    ("value_type", "key"),
    [
        (UInt64, "key"),
        (Bytes, b"key"),
        (String, Bytes(b"key")),
        (BigUInt, String("key")),
        (arc4.String, "Key"),
        (arc4.DynamicArray, b"Key"),
        (Swapped, b"key"),
        (
            tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address],
            "key",
        ),
        (
            arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Address],
            "key",
        ),
        (MyStruct, b"key"),
    ],
)
def test_init_with_key(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    key: bytes | str | Bytes | String,
) -> None:
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    assert not box
    assert len(box.key) > 0

    key_bytes = (
        String(as_string(key)).bytes if isinstance(key, str | String) else Bytes(as_bytes(key))
    )
    assert box.key == key_bytes

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.value

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.length


@pytest.mark.parametrize(
    ("value_type", "expected_size"),
    [
        (arc4.UInt64, 8),
        (UInt64, 8),
        (arc4.Address, 32),
        (Account, 32),
        (Application, 8),
        (Asset, 8),
        (bool, 8),
        (arc4.StaticArray[arc4.Byte, typing.Literal[7]], 7),
        (Swapped, 41),
        (tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address], 41),
        (arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Address], 41),
        (MyStruct, 58),
    ],
)
def test_create_for_static_value_type(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    expected_size: int,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    assert not box

    box.create()
    assert box

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert op_box_exists
    assert op_box_content == b"\x00" * expected_size

    box_content, box_exists = box.maybe()
    assert box_exists
    assert cast_to_bytes(box_content) == b"\x00" * expected_size

    assert box.length == expected_size


@pytest.mark.parametrize(
    ("value_type", "size", "expected_size"),
    [
        (arc4.UInt64, 7, 8),
        (UInt64, 0, 8),
        (arc4.Address, 16, 32),
        (Account, 31, 32),
        (Application, 1, 8),
        (Asset, 0, 8),
        (bool, 1, 8),
        (arc4.StaticArray[arc4.Byte, typing.Literal[7]], 2, 7),
        (Swapped, 40, 41),
        (tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address], 12, 41),
        (arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Address], 12, 41),
        (MyStruct, 1, 58),
    ],
)
def test_create_smaller_box_for_static_value_type(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    size: int,
    expected_size: int,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    assert not box

    with pytest.warns(UserWarning, match=f"Box size should not be less than {expected_size}"):
        box.create(size=size)


@pytest.mark.parametrize(
    ("value_type", "size"),
    [
        (arc4.String, 7),
        (arc4.DynamicArray[arc4.UInt64], 0),
        (arc4.DynamicArray[arc4.Address], 16),
        (Bytes, 31),
        (arc4.StaticArray[arc4.String, typing.Literal[7]], 2),
    ],
)
def test_create_box_for_dynamic_value_type(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    size: int,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    assert not box

    box.create(size=size)

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert op_box_exists
    assert op_box_content == b"\x00" * size

    assert box.length == size


@pytest.mark.parametrize(
    "value_type",
    [
        arc4.String,
        arc4.DynamicArray[arc4.UInt64],
        arc4.DynamicArray[arc4.Address],
        Bytes,
        arc4.StaticArray[arc4.String, typing.Literal[7]],
    ],
)
def test_create_box_for_dynamic_value_type_with_no_size(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    assert not box

    with pytest.raises(
        ValueError,
        match=re.compile("does not have a fixed byte size. Please specify a size argument"),
    ):
        box.create()


test_data_array = (
    [
        (UInt64, UInt64(100)),
        (Bytes, Bytes(b"Test")),
        (String, String("Test")),
        (BigUInt, BigUInt(100)),
        (arc4.String, arc4.String("Test")),
        (arc4.DynamicArray[arc4.UInt64], arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)])),
        (
            Swapped,
            Swapped(arc4.UInt64(100), arc4.Bool(True), arc4.Address(algopy.Bytes(b"\x00" * 32))),
        ),
        (
            tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address],
            (arc4.UInt64(100), arc4.Bool(True), True, arc4.Address(algopy.Bytes(b"\x00" * 32))),
        ),
        (
            arc4.Tuple[arc4.UInt64, arc4.Bool, arc4.Address],
            arc4.Tuple(
                (arc4.UInt64(100), arc4.Bool(True), arc4.Address(algopy.Bytes(b"\x00" * 32)))
            ),
        ),
        (
            MyStruct,
            MyStruct(
                UInt64(100),
                True,
                arc4.Bool(True),
                arc4.UInt64(100),
                Swapped(
                    arc4.UInt64(100), arc4.Bool(True), arc4.Address(algopy.Bytes(b"\x00" * 32))
                ),
            ),
        ),
    ],
)


@pytest.mark.parametrize(("value_type", "value"), *test_data_array)
def test_value_setter(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    value: typing.Any,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    box.value = value

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    op_box_length, _ = algopy.op.Box.length(key)
    assert op_box_exists
    assert box.length == op_box_length

    _assert_box_content_equality(value, box.value, op_box_content)


@pytest.mark.parametrize(("value_type", "value"), *test_data_array)
def test_value_deleter(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    value: typing.Any,
) -> None:
    key = b"test_key"
    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    box.value = value

    del box.value
    assert not box

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.value

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert not op_box_exists
    assert not op_box_content


@pytest.mark.parametrize(("value_type", "value"), *test_data_array)
def test_maybe(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    value: typing.Any,
) -> None:
    key = b"test_key"

    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    box.value = value
    box_content, box_exists = box.maybe()

    op_box_content, op_box_exists = algopy.op.Box.get(key)

    assert box_exists
    assert op_box_exists
    _assert_box_content_equality(value, box_content, op_box_content)


@pytest.mark.parametrize(("value_type", "value"), *test_data_array)
def test_maybe_when_box_does_not_exist(
    context: AlgopyTestContext,  # noqa: ARG001
    value_type: type,
    value: typing.Any,
) -> None:
    key = b"test_key"

    box = Box(value_type, key=key)  # type: ignore[var-annotated]
    box.value = value
    del box.value

    box_content, box_exists = box.maybe()
    assert not box_content
    assert not box_exists

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert not op_box_content
    assert not op_box_exists


def _assert_box_content_equality(
    expected_value: typing.Any, box_content: typing.Any, op_box_content: Bytes
) -> None:
    if hasattr(expected_value, "bytes"):
        assert box_content.bytes == expected_value.bytes
        assert box_content.bytes == op_box_content
    elif isinstance(expected_value, UInt64):
        assert box_content == expected_value
        assert box_content == algopy.op.btoi(op_box_content)
    else:
        assert box_content == expected_value
        assert cast_to_bytes(box_content) == op_box_content


def test_enums_in_boxes() -> None:
    # Arrange
    with algopy_testing_context() as context:
        contract = BoxContract()

        # Act
        defered_store = context.txn.defer_app_call(contract.store_enums)
        defered_read = context.txn.defer_app_call(contract.read_enums)
        with context.txn.create_group([defered_store, defered_read]):
            defered_store.submit()
            oca, txn = defered_read.submit()

        # Assert
        assert context.ledger.get_box(contract, b"oca") == itob(oca.as_uint64())
        assert context.ledger.get_box(contract, b"txn") == itob(txn.as_uint64())


class Swapped2(Struct):
    a: Array[UInt64]
    b: Array[UInt64]


def test_arrays_and_struct_in_boxes(context: AlgopyTestContext) -> None:  # noqa: ARG001, PLR0915
    # Array
    arr1 = Array([UInt64(1), UInt64(2), UInt64(3)])
    arr2 = Array([UInt64(4), UInt64(5), UInt64(6)])
    nested_arr1 = Array([arr1, arr2])
    box1 = Box(Array[Array[UInt64]], key=b"test_array_1")
    box1.value = nested_arr1
    _op_box_content, op_box_exists = algopy.op.Box.get(b"test_array_1")
    op_box_length, _ = algopy.op.Box.length(b"test_array_1")
    assert op_box_exists
    assert box1.length == op_box_length

    box1.value[0][1] = UInt64(20)
    assert list(box1.value[0]) == [UInt64(1), UInt64(20), UInt64(3)]

    # FixedArray
    arr3 = FixedArray[UInt64, typing.Literal[3]]([UInt64(1), UInt64(2), UInt64(3)])
    arr4 = FixedArray[UInt64, typing.Literal[3]]([UInt64(4), UInt64(5), UInt64(6)])
    nested_arr2 = FixedArray[FixedArray[UInt64, typing.Literal[3]], typing.Literal[2]](
        [arr3, arr4]
    )
    box2 = Box(
        FixedArray[FixedArray[UInt64, typing.Literal[3]], typing.Literal[2]], key=b"test_array_2"
    )
    box2.value = nested_arr2
    _op_box_content, op_box_exists = algopy.op.Box.get(b"test_array_2")
    op_box_length, _ = algopy.op.Box.length(b"test_array_2")
    assert op_box_exists
    assert box2.length == op_box_length

    box2.value[0][1] = UInt64(20)
    assert list(box2.value[0]) == [UInt64(1), UInt64(20), UInt64(3)]

    # ImmutableArray
    nested_arr3 = ImmutableArray[ImmutableArray[UInt64]](
        (ImmutableArray(arr1), ImmutableArray(arr2))
    )
    box3 = Box(ImmutableArray[ImmutableArray[UInt64]], key=b"test_array_3")
    box3.value = nested_arr3
    _op_box_content, op_box_exists = algopy.op.Box.get(b"test_array_3")
    op_box_length, _ = algopy.op.Box.length(b"test_array_3")
    assert op_box_exists
    assert box3.length == op_box_length

    # ImmutableFixedArray
    nested_arr4 = ImmutableFixedArray[
        ImmutableFixedArray[UInt64, typing.Literal[3]], typing.Literal[2]
    ]([ImmutableFixedArray(arr3), ImmutableFixedArray(arr4)])
    box4 = Box(
        ImmutableFixedArray[ImmutableFixedArray[UInt64, typing.Literal[3]], typing.Literal[2]],
        key=b"test_array_4",
    )
    box4.value = nested_arr4
    _op_box_content, op_box_exists = algopy.op.Box.get(b"test_array_4")
    op_box_length, _ = algopy.op.Box.length(b"test_array_4")
    assert op_box_exists
    assert box4.length == op_box_length

    # Struct
    struct1 = Swapped2(arr1, arr2)
    box5 = Box(
        Swapped2,
        key=b"test_struct_1",
    )
    box5.value = struct1
    _op_box_content, op_box_exists = algopy.op.Box.get(b"test_struct_1")
    op_box_length, _ = algopy.op.Box.length(b"test_struct_1")
    assert op_box_exists
    assert box5.length == op_box_length

    box5.value.a[1] = UInt64(20)
    assert list(box5.value.a) == [UInt64(1), UInt64(20), UInt64(3)]

    # FixedBytes in FixedArray
    box6 = Box(
        FixedArray[FixedBytes[typing.Literal[1024]], typing.Literal[10]], key=b"test_array_6"
    )
    box6.value = FixedArray(
        [FixedBytes[typing.Literal[1024]].from_hex(f"0{x}" * 1024) for x in range(10)]
    )
    assert box6.length == 10 * 1024
    assert box6.value[0].bytes == b"\x00" * 1024
    assert box6.value[9].bytes == b"\x09" * 1024
    box6.value[1] = FixedBytes[typing.Literal[1024]].from_hex("11" * 1024)
    assert box6.value[1].bytes == b"\x11" * 1024


def test_box() -> None:
    with algopy_testing_context():
        contract = BoxContract()

        (a_exist, b_exist, c_exist, large_exist) = contract.boxes_exist()
        assert not a_exist
        assert not b_exist
        assert not c_exist
        assert not large_exist

        contract.set_boxes(a=UInt64(56), b=arc4.DynamicBytes(b"Hello"), c=arc4.String("World"))

        (a_exist, b_exist, c_exist, large_exist) = contract.boxes_exist()
        assert a_exist
        assert b_exist
        assert c_exist
        assert large_exist

        contract.check_keys()

        (a, b, c, large) = contract.read_boxes()

        assert (a, b, c, large) == (59, b"Hello", "World", 42)

        contract.indirect_extract_and_replace()

        contract.delete_boxes()

        (a_exist, b_exist, c_exist, large_exist) = contract.boxes_exist()

        assert not a_exist
        assert not b_exist
        assert not c_exist
        assert not large_exist

        contract.slice_box()

        contract.arc4_box()

        contract.create_many_ints()

        contract.set_many_ints(index=UInt64(1), value=UInt64(1))
        contract.set_many_ints(index=UInt64(2), value=UInt64(2))
        contract.set_many_ints(index=UInt64(256), value=UInt64(256))
        contract.set_many_ints(index=UInt64(511), value=UInt64(511))
        contract.set_many_ints(index=UInt64(512), value=UInt64(512))

        sum_many_ints = contract.sum_many_ints()
        assert sum_many_ints == (1 + 2 + 256 + 511 + 512)


def test_nested_struct_box() -> None:
    with algopy_testing_context() as ctx:
        contract = BoxContract()
        r = iter(range(1, 256))

        def n() -> UInt64:
            return UInt64(next(r))

        def inner() -> object:
            c, arr, d = (n() for _ in range(3))
            return InnerStruct(c=c, arr_arr=Array([Array([arr] * 4) for _ in range(3)]), d=d)

        struct = NestedStruct(a=n(), inner=inner(), woah=Array([inner() for _ in range(3)]), b=n())
        assert n() < 100, "too many ints"
        contract.set_nested_struct(struct=struct)
        response = contract.nested_read(i1=UInt64(1), i2=UInt64(2), i3=UInt64(3))
        assert response == 33, "expected sum to be correct"

        contract.nested_write(index=UInt64(1), value=UInt64(10))
        response = contract.nested_read(i1=UInt64(1), i2=UInt64(2), i3=UInt64(3))
        assert response == 60, "expected sum to be correct"

        # verify box contents
        with ctx.txn.create_group(
            [ctx.any.txn.application_call(app_id=ctx.ledger.get_app(contract))]
        ):
            box_length = op.Box.length(b"box")[0]
            padding_bytes = op.Box.extract(b"box", 0, MAX_BYTES_SIZE)
            struct_bytes = op.Box.extract(b"box", MAX_BYTES_SIZE, box_length - MAX_BYTES_SIZE)
            box_bytes = padding_bytes.value + struct_bytes.value
            large_nested_struct = LargeNestedStruct.from_bytes(box_bytes)
            assert list(large_nested_struct.padding) == [
                arc4.Byte(b) for b in b"\x00" * MAX_BYTES_SIZE
            ]
            assert large_nested_struct.nested.a == 10
            assert large_nested_struct.nested.b == 11
            assert large_nested_struct.nested.inner.arr_arr[1][1] == 12
            assert large_nested_struct.nested.inner.c == 13
            assert large_nested_struct.nested.inner.d == 14
            assert large_nested_struct.nested.woah[1].arr_arr[1][1] == 15


def test_too_many_bools() -> None:
    with algopy_testing_context():
        contract = BoxContract()

        contract.create_bools()

        contract.set_bool(index=UInt64(0), value=True)
        contract.set_bool(index=UInt64(42), value=True)
        contract.set_bool(index=UInt64(500), value=True)
        contract.set_bool(index=UInt64(32_999), value=True)

        total = contract.sum_bools(stop_at_total=UInt64(3))
        expected_sum = 3
        assert total == expected_sum, f"expected sum to be {expected_sum}"

        box_response = contract.too_many_bools.value
        assert box_response[0]
        assert box_response[42]
        assert box_response[500]
        assert box_response[32_999]

        too_many_bools = [False] * 33_000
        too_many_bools[0] = True
        too_many_bools[42] = True
        too_many_bools[500] = True
        too_many_bools[32_999] = True
        # encode bools into bytes (as SDK is too slow)
        expected_bytes = sum(
            val << shift for shift, val in enumerate(reversed(too_many_bools))
        ).to_bytes(length=33_000 // 8)

        assert box_response._value == expected_bytes, "expected box contents to be correct"
