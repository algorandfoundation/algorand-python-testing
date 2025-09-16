import typing

import algosdk
import pytest
from _algopy_testing.constants import MAX_UINT512
from algopy import ImmutableArray, String, UInt64, arc4
from algopy_testing import AlgopyTestContext, algopy_testing_context

from tests.artifacts.Arrays.immutable import (
    DynamicArrayInitContract,
    ImmutableArrayContract,
    MyDynamicSizedTuple,
    MyStruct,
    MyTuple,
)
from tests.artifacts.Arrays.static_size import More, StaticSizeContract
from tests.artifacts.Arrays.uint64 import Contract as UInt64Contract


@pytest.fixture()
def context() -> typing.Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


# tests are based on puyapy compiler tests for array
def test_array_uint64(context: AlgopyTestContext) -> None:  # noqa: ARG001
    contract = UInt64Contract()

    contract.test_array()
    contract.test_array_extend()
    contract.test_array_multiple_append()
    contract.test_iteration()
    contract.test_array_copy_and_extend()
    contract.test_array_evaluation_order()

    contract.test_allocations(UInt64(255))
    contract.test_array_too_long()

    contract.test_quicksort()

    contract.test_array_assignment_maximum_cursage()
    contract.test_unobserved_write()


def test_array_static_size(context: AlgopyTestContext) -> None:
    contract = StaticSizeContract()

    x1, y1 = 3, 4
    x2, y2 = 6, 8
    sender = context.default_sender.public_key
    assert (
        contract.test_array(arc4.UInt64(x1), arc4.UInt64(y1), arc4.UInt64(x2), arc4.UInt64(y2))
        == 15
    )

    assert context.ledger.box_exists(contract, b"a")
    assert context.ledger.get_box(contract, b"a") == _get_arc4_bytes(
        "(uint64,uint64,(uint64,uint64,address,(uint64,uint64),uint512))[]",
        [
            (0, 0, (5, 1, sender, (2, 1), 1)),
            (x1, y1, (5, 2, sender, (3, 4), 2)),
            (x2, y2, (5, 3, sender, (4, 9), 3)),
        ],
    )

    arr_1_to_5 = arc4.DynamicArray(*(arc4.UInt64(i + 1) for i in range(5)))
    assert contract.test_arc4_conversion(UInt64(5)) == arr_1_to_5
    assert contract.sum_array(arr_1_to_5) == 15

    assert contract.test_bool_array(UInt64(5)) == 2
    assert contract.test_bool_array(UInt64(4)) == 2
    assert contract.test_bool_array(UInt64(6)) == 3

    more_a = More(arc4.UInt64(1), arc4.UInt64(2))
    more_b = More(arc4.UInt64(3), arc4.UInt64(4))
    response = contract.test_extend_from_tuple((more_a, more_b))
    assert list(response) == [
        More(arc4.UInt64(1), arc4.UInt64(2)),
        More(arc4.UInt64(3), arc4.UInt64(4)),
    ]

    response = contract.test_extend_from_arc4_tuple(arc4.Tuple((more_a, more_b)))
    assert list(response) == [
        More(arc4.UInt64(1), arc4.UInt64(2)),
        More(arc4.UInt64(3), arc4.UInt64(4)),
    ]

    arc4_bool = contract.test_arc4_bool()
    assert list(arc4_bool) == [arc4.Bool(False), arc4.Bool(True)]


def test_immutable_array(context: AlgopyTestContext) -> None:
    app = ImmutableArrayContract()

    app.test_uint64_array()
    assert context.ledger.get_global_state(app, b"a") == _get_arc4_bytes(
        "uint64[]", [42, 0, 23, 2, *range(10), 44]
    )

    app.test_biguint_array()
    assert context.ledger.get_box(app, b"biguint") == _get_arc4_bytes(
        "uint512[]", [0, 0, 1, 2, 3, 4, MAX_UINT512 - 1, MAX_UINT512]
    )

    app.test_fixed_size_tuple_array()
    assert context.ledger.get_global_state(app, b"c") == _get_arc4_bytes(
        "(uint64,uint64)[]", [(i + 1, i + 2) for i in range(4)]
    )

    app.test_fixed_size_named_tuple_array()
    assert context.ledger.get_global_state(app, b"d") == _get_arc4_bytes(
        "(uint64,bool,bool)[]", [(i, i % 2 == 0, i * 3 % 2 == 0) for i in range(5)]
    )

    app.test_dynamic_sized_tuple_array()
    assert context.ledger.get_global_state(app, b"e") == _get_arc4_bytes(
        "(uint64,byte[])[]", [(i + 1, b"\x00" * i) for i in range(4)]
    )

    app.test_dynamic_sized_named_tuple_array()
    assert context.ledger.get_global_state(app, b"f") == _get_arc4_bytes(
        "(uint64,string)[]", [(i + 1, " " * i) for i in range(4)]
    )

    app.test_bit_packed_tuples()
    assert context.ledger.get_global_state(app, b"bool2") == _get_arc4_bytes(
        "(bool,bool)[]", [(i == 0, i == 1) for i in range(5)]
    )
    assert context.ledger.get_global_state(app, b"bool7") == _get_arc4_bytes(
        "(uint64,bool,bool,bool,bool,bool,bool,bool,uint64)[]",
        [(i, i == 0, i == 1, i == 2, i == 3, i == 4, i == 5, i == 6, i + 1) for i in range(5)],
    )
    assert context.ledger.get_global_state(app, b"bool8") == _get_arc4_bytes(
        "(uint64,bool,bool,bool,bool,bool,bool,bool,bool,uint64)[]",
        [
            (i, i == 0, i == 1, i == 2, i == 3, i == 4, i == 5, i == 6, i == 7, i + 1)
            for i in range(5)
        ],
    )
    assert context.ledger.get_global_state(app, b"bool9") == _get_arc4_bytes(
        "(uint64,bool,bool,bool,bool,bool,bool,bool,bool,bool,uint64)[]",
        [
            (i, i == 0, i == 1, i == 2, i == 3, i == 4, i == 5, i == 6, i == 7, i == 8, i + 1)
            for i in range(5)
        ],
    )

    append = 5
    arr = [MyTuple(UInt64(i), i % 2 == 0, i % 3 == 0) for i in range(append)]
    response = app.test_convert_to_array_and_back(arr=ImmutableArray(arr), append=UInt64(append))
    assert list(response) == [*arr, *arr]

    response = app.test_concat_with_arc4_tuple(arc4.Tuple((arc4.UInt64(3), arc4.UInt64(4))))
    assert list(response) == list(map(arc4.UInt64, [1, 2, 3, 4]))

    response = app.test_concat_with_native_tuple((arc4.UInt64(3), arc4.UInt64(4)))
    assert list(response) == list(map(arc4.UInt64, [1, 2, 3, 4]))

    one = MyDynamicSizedTuple(UInt64(1), String("one"))
    two = MyDynamicSizedTuple(UInt64(2), String("foo"))
    three = MyDynamicSizedTuple(UInt64(3), String("tree"))
    four = MyDynamicSizedTuple(UInt64(4), String("floor"))
    response = app.test_concat_immutable_dynamic(
        ImmutableArray((one, two)), ImmutableArray((three, four))
    )
    assert list(response) == [one, two, three, four]

    immutable_arc4_input = ImmutableArray(
        (
            MyStruct(arc4.UInt64(1), arc4.UInt64(2)),
            MyStruct(arc4.UInt64(3), arc4.UInt64(4)),
            MyStruct(arc4.UInt64(5), arc4.UInt64(6)),
        )
    )
    immutable_arc4_result = app.test_immutable_arc4(immutable_arc4_input)
    assert list(immutable_arc4_result) == [
        MyStruct(arc4.UInt64(1), arc4.UInt64(2)),
        MyStruct(arc4.UInt64(3), arc4.UInt64(4)),
        MyStruct(arc4.UInt64(1), arc4.UInt64(2)),
    ]
    assert list(immutable_arc4_input) == [
        MyStruct(arc4.UInt64(1), arc4.UInt64(2)),
        MyStruct(arc4.UInt64(3), arc4.UInt64(4)),
        MyStruct(arc4.UInt64(5), arc4.UInt64(6)),
    ]

    imm_fixed_arr = app.test_imm_fixed_arr()
    assert len(imm_fixed_arr) == 3


def test_dynamic_array_init(context: AlgopyTestContext) -> None:  # noqa: ARG001
    app = DynamicArrayInitContract()

    app.test_immutable_array_init()

    app.test_immutable_array_init_without_type_generic()

    app.test_reference_array_init()

    app.test_immutable_array_init_without_type_generic()


_EXPECTED_LENGTH_20 = [False, False, True, *(False,) * 17]


@pytest.mark.parametrize("length", [0, 1, 2, 3, 4, 7, 8, 9, 15, 16, 17])
def test_immutable_bool_array(context: AlgopyTestContext, length: int) -> None:
    app = ImmutableArrayContract()

    app.test_bool_array(UInt64(length))
    expected = _EXPECTED_LENGTH_20[:length]
    assert context.ledger.get_global_state(app, b"g") == _get_arc4_bytes("bool[]", expected)


def test_immutable_routing(context: AlgopyTestContext) -> None:  # noqa: ARG001
    app = ImmutableArrayContract()

    response = app.sum_uints_and_lengths_and_trues(
        arr1=ImmutableArray([*map(UInt64, range(5))]),
        arr2=ImmutableArray([i % 2 == 0 for i in range(6)]),
        arr3=ImmutableArray([MyTuple(UInt64(i), i % 2 == 0, i % 3 == 0) for i in range(7)]),
        arr4=ImmutableArray([MyDynamicSizedTuple(UInt64(i), String(" " * i)) for i in range(8)]),
    )
    assert response == tuple(map(UInt64, (10, 3, 21 + 4 + 3, 28 * 2)))

    append = 4
    response = app.test_uint64_return(UInt64(append))
    assert list(response) == list(map(UInt64, [1, 2, 3, *range(append)]))

    append = 5
    response = app.test_bool_return(UInt64(append))
    assert list(response) == [
        *[True, False, True, False, True],
        *(i % 2 == 0 for i in range(append)),
    ]

    append = 6
    response = app.test_tuple_return(UInt64(append))
    assert list(response) == [
        MyTuple(UInt64(0), True, False),
        *(MyTuple(UInt64(i), i % 2 == 0, i % 3 == 0) for i in range(append)),
    ]

    append = 3
    response = app.test_dynamic_tuple_return(UInt64(append))
    assert list(response) == [
        MyDynamicSizedTuple(UInt64(0), String("Hello")),
        *(MyDynamicSizedTuple(UInt64(i), String(" " * i)) for i in range(append)),
    ]


def test_nested_immutable(context: AlgopyTestContext) -> None:  # noqa: ARG001
    app = ImmutableArrayContract()

    response = app.test_nested_array(
        arr_to_add=UInt64(5),
        arr=ImmutableArray([ImmutableArray([UInt64(i * j) for i in range(5)]) for j in range(3)]),
    )
    assert list(response) == list(
        map(
            UInt64,
            (
                0,
                10,
                20,
                0,
                0,
                1,
                3,
                6,
            ),
        )
    )


def _get_arc4_bytes(arc4_type: str, value: object) -> bytes:
    return algosdk.abi.ABIType.from_string(arc4_type).encode(value)
