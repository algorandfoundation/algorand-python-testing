import copy
import typing

import pytest
from _algopy_testing import arc4
from _algopy_testing.primitives import BigUInt, String, UInt64
from _algopy_testing.primitives.array import FixedArray, ImmutableFixedArray
from algosdk import abi

from tests.util import int_to_bytes

_abi_bool_static_array_type = abi.ABIType.from_string("bool[10]")
_abi_bool_static_array_values = [True, True, False, True, False, True, True, False, True, False]
_arc4_bool_static_array_values = [arc4.Bool(value) for value in _abi_bool_static_array_values]
_arc4_bool_static_array: arc4.StaticArray[arc4.Bool, typing.Literal[10]] = arc4.StaticArray(
    *_arc4_bool_static_array_values
)

_abi_bool_static_array_of_array_type = abi.ABIType.from_string("bool[10][2]")
_abi_bool_static_array_of_array_values = [
    _abi_bool_static_array_values,
    _abi_bool_static_array_values,
]
_arc4_bool_static_array_of_array_values = [
    arc4.StaticArray[arc4.Bool, typing.Literal[10]](
        *[arc4.Bool(value) for value in _abi_bool_static_array_values]
    ),
    arc4.StaticArray[arc4.Bool, typing.Literal[10]](
        *[arc4.Bool(value) for value in _abi_bool_static_array_values]
    ),
]
_arc4_bool_static_array_of_array = arc4.StaticArray[
    arc4.StaticArray[arc4.Bool, typing.Literal[10]], typing.Literal[2]
](*_arc4_bool_static_array_of_array_values)

_abi_uint256_static_array_type = abi.ABIType.from_string("uint256[10]")
_abi_uint256_static_array_values = [0, 1, 2, 3, 2**8, 2**16, 2**32, 2**64, 2**128, 2**256 - 1]
_arc4_uint256_static_array_values = [
    arc4.UInt256(value) for value in _abi_uint256_static_array_values
]
_arc4_uint256_static_array = arc4.StaticArray[arc4.UInt256, typing.Literal[10]](
    *_arc4_uint256_static_array_values
)


_abi_uint256_static_array_of_array_type = abi.ABIType.from_string("uint256[10][2]")
_abi_uint256_static_array_of_array_values = [
    _abi_uint256_static_array_values,
    _abi_uint256_static_array_values,
]
_arc4_uint256_static_array_of_array_values = [
    arc4.StaticArray[arc4.UInt256, typing.Literal[10]](
        *[arc4.UInt256(value) for value in _abi_uint256_static_array_values]
    ),
    arc4.StaticArray[arc4.UInt256, typing.Literal[10]](
        *[arc4.UInt256(value) for value in _abi_uint256_static_array_values]
    ),
]
_arc4_uint256_static_array_of_array = arc4.StaticArray[
    arc4.StaticArray[arc4.UInt256, typing.Literal[10]], typing.Literal[2]
](*_arc4_uint256_static_array_of_array_values)


_abi_string_static_array_type = abi.ABIType.from_string("string[10]")
_abi_string_static_array_values = [
    "",
    "1",
    "hello",
    "World",
    str(2**8),
    str(2**16),
    str(2**32),
    str(2**64),
    str(2**128),
    str(2**256),
]
_arc4_string_static_array_values = [
    arc4.String(value) for value in _abi_string_static_array_values
]
_arc4_string_static_array: arc4.StaticArray[arc4.String, typing.Literal[10]] = arc4.StaticArray(
    *_arc4_string_static_array_values
)


_bigufixednxm_values = [
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("0"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("1"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("2"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("3"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("255"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("65536"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("4294967295"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("1844.6744073709551616"),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]](
        "340282366920938463463374.607431768211456"
    ),
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]](
        "11579208923731619542357098500868790785326998466564056403945758.4007913129639935"
    ),
]
_abi_bigufixednxm_static_array_type = abi.ABIType.from_string("ufixed256x16[10]")
_abi_bigufixednxm_static_array_values = [
    int.from_bytes(x.bytes.value) for x in _bigufixednxm_values
]
_arc4_bigufixednxm_static_array_values = _bigufixednxm_values
_arc4_bigufixednxm_static_array = arc4.StaticArray[
    arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]], typing.Literal[10]
](*_arc4_bigufixednxm_static_array_values)


_abi_string_static_array_of_array_type = abi.ABIType.from_string("string[10][2]")
_abi_string_static_array_of_array_values = [
    _abi_string_static_array_values,
    _abi_string_static_array_values,
]
_arc4_string_static_array_of_array_values = [
    arc4.StaticArray[arc4.String, typing.Literal[10]](
        *[arc4.String(value) for value in _abi_string_static_array_values]
    ),
    arc4.StaticArray[arc4.String, typing.Literal[10]](
        *[arc4.String(value) for value in _abi_string_static_array_values]
    ),
]
_arc4_string_static_array_of_array = arc4.StaticArray[
    arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[2]
](*_arc4_string_static_array_of_array_values)


_abi_string_static_array_of_array_of_array_type = abi.ABIType.from_string("string[10][3][2]")
_abi_string_static_array_of_array_of_array_values = [
    [
        _abi_string_static_array_values,
        _abi_string_static_array_values,
        _abi_string_static_array_values,
    ],
    [
        _abi_string_static_array_values,
        _abi_string_static_array_values,
        _abi_string_static_array_values,
    ],
]
_arc4_string_static_array_of_array_of_array_values = [
    arc4.StaticArray[arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[3]](
        *[
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
        ]
    ),
    arc4.StaticArray[arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[3]](
        *[
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
            arc4.StaticArray[arc4.String, typing.Literal[10]](
                *[arc4.String(value) for value in _abi_string_static_array_values]
            ),
        ]
    ),
]
_arc4_string_static_array_of_array_of_array = arc4.StaticArray[
    arc4.StaticArray[arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[3]],
    typing.Literal[2],
](*_arc4_string_static_array_of_array_of_array_values)


_abi_tuple_static_array_type = abi.ABIType.from_string(
    "(string[],(string[],string,uint256),bool,uint256[3])[2]"
)
_abi_tuple_static_array_values = [
    (
        _abi_string_static_array_values[:2],
        (
            _abi_string_static_array_values[6:8],
            _abi_string_static_array_values[9],
            _abi_uint256_static_array_values[4],
        ),
        _abi_bool_static_array_values[3],
        _abi_uint256_static_array_values[4:7],
    ),
] * 2
_arc4_tuple_static_array_values: list[
    arc4.Tuple[
        arc4.DynamicArray[arc4.String],
        arc4.Tuple[
            arc4.DynamicArray[arc4.String],
            arc4.String,
            arc4.UInt256,
        ],
        arc4.Bool,
        arc4.StaticArray[arc4.UInt256, typing.Literal[3]],
    ]
] = [
    arc4.Tuple(
        (
            arc4.DynamicArray(*_arc4_string_static_array_values[:2]),
            arc4.Tuple(
                (
                    arc4.DynamicArray(*_arc4_string_static_array_values[6:8]),
                    _arc4_string_static_array_values[9],
                    _arc4_uint256_static_array_values[4],
                )
            ),
            _arc4_bool_static_array_values[3],
            arc4.StaticArray(*_arc4_uint256_static_array_values[4:7]),
        )
    )
] * 2

_arc4_tuple_static_array: arc4.StaticArray[
    arc4.Tuple[
        arc4.DynamicArray[arc4.String],
        arc4.Tuple[
            arc4.DynamicArray[arc4.String],
            arc4.String,
            arc4.UInt256,
        ],
        arc4.Bool,
        arc4.StaticArray[arc4.UInt256, typing.Literal[3]],
    ],
    typing.Literal[2],
] = arc4.StaticArray(*_arc4_tuple_static_array_values)


@pytest.mark.parametrize(
    ("abi_type", "abi_values", "arc4_value"),
    [
        (_abi_bool_static_array_type, _abi_bool_static_array_values, _arc4_bool_static_array),
        (
            _abi_uint256_static_array_type,
            _abi_uint256_static_array_values,
            _arc4_uint256_static_array,
        ),
        (
            _abi_string_static_array_type,
            _abi_string_static_array_values,
            _arc4_string_static_array,
        ),
        (
            _abi_bigufixednxm_static_array_type,
            _abi_bigufixednxm_static_array_values,
            _arc4_bigufixednxm_static_array,
        ),
        (
            _abi_bool_static_array_of_array_type,
            _abi_bool_static_array_of_array_values,
            _arc4_bool_static_array_of_array,
        ),
        (
            _abi_uint256_static_array_of_array_type,
            _abi_uint256_static_array_of_array_values,
            _arc4_uint256_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_type,
            _abi_string_static_array_of_array_values,
            _arc4_string_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_of_array_type,
            _abi_string_static_array_of_array_of_array_values,
            _arc4_string_static_array_of_array_of_array,
        ),
        (
            _abi_tuple_static_array_type,
            _abi_tuple_static_array_values,
            _arc4_tuple_static_array,
        ),
    ],
)
def test_bytes(
    abi_type: abi.ABIType,
    abi_values: list[typing.Any],
    arc4_value: arc4.StaticArray,  # type: ignore[type-arg]
) -> None:
    abi_result = abi_type.encode(abi_values)

    arc4_result = arc4_value.bytes
    assert abi_result == arc4_result


@pytest.mark.parametrize(
    ("abi_type", "abi_values", "arc4_value"),
    [
        (_abi_bool_static_array_type, _abi_bool_static_array_values, _arc4_bool_static_array),
        (
            _abi_uint256_static_array_type,
            _abi_uint256_static_array_values,
            _arc4_uint256_static_array,
        ),
        (
            _abi_string_static_array_type,
            _abi_string_static_array_values,
            _arc4_string_static_array,
        ),
        (
            _abi_bigufixednxm_static_array_type,
            _abi_bigufixednxm_static_array_values,
            _arc4_bigufixednxm_static_array,
        ),
        (
            _abi_bool_static_array_of_array_type,
            _abi_bool_static_array_of_array_values,
            _arc4_bool_static_array_of_array,
        ),
        (
            _abi_uint256_static_array_of_array_type,
            _abi_uint256_static_array_of_array_values,
            _arc4_uint256_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_type,
            _abi_string_static_array_of_array_values,
            _arc4_string_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_of_array_type,
            _abi_string_static_array_of_array_of_array_values,
            _arc4_string_static_array_of_array_of_array,
        ),
        (
            _abi_tuple_static_array_type,
            _abi_tuple_static_array_values,
            _arc4_tuple_static_array,
        ),
    ],
)
def test_copy(
    abi_type: abi.ABIType,
    abi_values: list[typing.Any],
    arc4_value: arc4.StaticArray,  # type: ignore[type-arg]
) -> None:
    abi_result = abi_type.encode(abi_values)

    copy = arc4_value.copy()

    arc4_result = copy.bytes

    assert copy.length == arc4_value.length
    assert abi_result == arc4_result


@pytest.mark.parametrize(
    ("abi_values", "arc4_value"),
    [
        (_abi_bool_static_array_values, _arc4_bool_static_array),
        (
            _abi_uint256_static_array_values,
            _arc4_uint256_static_array,
        ),
        (
            _abi_string_static_array_values,
            _arc4_string_static_array,
        ),
        (
            _abi_bigufixednxm_static_array_values,
            _arc4_bigufixednxm_static_array,
        ),
        (
            _abi_bool_static_array_of_array_values,
            _arc4_bool_static_array_of_array,
        ),
        (
            _abi_uint256_static_array_of_array_values,
            _arc4_uint256_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_values,
            _arc4_string_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_of_array_values,
            _arc4_string_static_array_of_array_of_array,
        ),
        (
            _abi_tuple_static_array_values,
            _arc4_tuple_static_array,
        ),
    ],
)
def test_get_item(abi_values: list[typing.Any], arc4_value: arc4.StaticArray) -> None:  # type: ignore[type-arg]
    i = 0
    while i < arc4_value.length:
        _compare_abi_and_arc4_values(arc4_value[i], abi_values[i])
        i += 1

    assert len(abi_values) == arc4_value.length


@pytest.mark.parametrize(
    ("abi_type", "abi_values", "arc4_type"),
    [
        (
            _abi_bool_static_array_type,
            _abi_bool_static_array_values,
            arc4.StaticArray[arc4.Bool, typing.Literal[10]],
        ),
        (
            _abi_uint256_static_array_type,
            _abi_uint256_static_array_values,
            arc4.StaticArray[arc4.UInt256, typing.Literal[10]],
        ),
        (
            _abi_string_static_array_type,
            _abi_string_static_array_values,
            arc4.StaticArray[arc4.String, typing.Literal[10]],
        ),
        (
            _abi_bigufixednxm_static_array_type,
            _abi_bigufixednxm_static_array_values,
            arc4.StaticArray[
                arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]], typing.Literal[10]
            ],
        ),
        (
            _abi_bool_static_array_of_array_type,
            _abi_bool_static_array_of_array_values,
            arc4.StaticArray[arc4.StaticArray[arc4.Bool, typing.Literal[10]], typing.Literal[2]],
        ),
        (
            _abi_uint256_static_array_of_array_type,
            _abi_uint256_static_array_of_array_values,
            arc4.StaticArray[
                arc4.StaticArray[arc4.UInt256, typing.Literal[10]], typing.Literal[2]
            ],
        ),
        (
            _abi_string_static_array_of_array_type,
            _abi_string_static_array_of_array_values,
            arc4.StaticArray[arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[2]],
        ),
        (
            _abi_string_static_array_of_array_of_array_type,
            _abi_string_static_array_of_array_of_array_values,
            arc4.StaticArray[
                arc4.StaticArray[
                    arc4.StaticArray[arc4.String, typing.Literal[10]], typing.Literal[3]
                ],
                typing.Literal[2],
            ],
        ),
        (
            _abi_tuple_static_array_type,
            _abi_tuple_static_array_values,
            arc4.StaticArray[
                arc4.Tuple[
                    arc4.DynamicArray[arc4.String],
                    arc4.Tuple[
                        arc4.DynamicArray[arc4.String],
                        arc4.String,
                        arc4.UInt256,
                    ],
                    arc4.Bool,
                    arc4.StaticArray[arc4.UInt256, typing.Literal[3]],
                ],
                typing.Literal[2],
            ],
        ),
    ],
)
def test_from_bytes(
    abi_type: abi.ABIType,
    abi_values: list[typing.Any],
    arc4_type: type[arc4.StaticArray],  # type: ignore[type-arg]
) -> None:
    i = 0
    arc4_value = arc4_type.from_bytes(abi_type.encode(abi_values))
    while i < arc4_value.length:
        _compare_abi_and_arc4_values(arc4_value[i], abi_values[i])
        i += 1

    assert len(abi_values) == arc4_value.length


@pytest.mark.parametrize(
    ("abi_type", "abi_values", "arc4_value"),
    [
        (_abi_bool_static_array_type, _abi_bool_static_array_values, _arc4_bool_static_array),
        (
            _abi_uint256_static_array_type,
            _abi_uint256_static_array_values,
            _arc4_uint256_static_array,
        ),
        (
            _abi_string_static_array_type,
            _abi_string_static_array_values,
            _arc4_string_static_array,
        ),
        (
            _abi_bigufixednxm_static_array_type,
            _abi_bigufixednxm_static_array_values,
            _arc4_bigufixednxm_static_array,
        ),
        (
            _abi_bool_static_array_of_array_type,
            _abi_bool_static_array_of_array_values,
            _arc4_bool_static_array_of_array,
        ),
        (
            _abi_uint256_static_array_of_array_type,
            _abi_uint256_static_array_of_array_values,
            _arc4_uint256_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_type,
            _abi_string_static_array_of_array_values,
            _arc4_string_static_array_of_array,
        ),
        (
            _abi_string_static_array_of_array_of_array_type,
            _abi_string_static_array_of_array_of_array_values,
            _arc4_string_static_array_of_array_of_array,
        ),
        (
            _abi_tuple_static_array_type,
            _abi_tuple_static_array_values,
            _arc4_tuple_static_array,
        ),
    ],
)
def test_set_item(
    abi_type: abi.ABIType,
    abi_values: list[typing.Any],
    arc4_value: arc4.StaticArray,  # type: ignore[type-arg]
) -> None:
    abi = copy.deepcopy(abi_values)
    temp = abi[-1]
    abi[-1] = abi[0]
    abi[0] = temp
    abi_result = abi_type.encode(abi)

    arc4 = arc4_value.copy()
    temp = arc4[-1]
    arc4[-1] = arc4[0]
    arc4[0] = temp
    arc4_result = arc4.bytes

    assert abi_result == arc4_result


def _compare_abi_and_arc4_values(
    arc4_value: typing.Any,
    abi_value: typing.Any,
) -> None:
    if hasattr(arc4_value, "_list") or isinstance(arc4_value, tuple):
        x = list(arc4_value) if isinstance(arc4_value, tuple) else arc4_value._list()
        j = 0
        while j < len(x):
            _compare_abi_and_arc4_values(x[j], abi_value[j])
            j += 1
    elif hasattr(arc4_value, "as_biguint"):
        assert arc4_value.as_biguint() == abi_value
    elif hasattr(arc4_value, "native"):
        assert arc4_value.native == abi_value
    else:
        assert arc4_value.bytes == int_to_bytes(abi_value, len(arc4_value.bytes))


def test_to_native() -> None:
    arr1 = arc4.StaticArray[arc4.Bool, typing.Literal[10]](
        arc4.Bool(True),
        arc4.Bool(False),
        arc4.Bool(False),
        arc4.Bool(True),
        arc4.Bool(False),
        arc4.Bool(True),
        arc4.Bool(True),
        arc4.Bool(False),
        arc4.Bool(True),
        arc4.Bool(False),
    )
    native_arr1 = arr1.to_native(bool)
    assert native_arr1.length == 10
    assert list(native_arr1) == [True, False, False, True, False, True, True, False, True, False]

    arr2 = arc4.StaticArray[arc4.UInt64, typing.Literal[10]](
        *[arc4.UInt64(i) for i in range(1, 11)]
    )
    native_arr2 = arr2.to_native(UInt64)
    assert native_arr2.length == 10
    assert list(native_arr2) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    arr3 = arc4.StaticArray[arc4.UInt512, typing.Literal[10]](
        *[arc4.UInt512(i) for i in range(1, 11)]
    )
    native_arr3 = arr3.to_native(BigUInt)
    assert native_arr3.length == 10
    assert list(native_arr3) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    arr4 = arc4.StaticArray[arc4.String, typing.Literal[10]](
        *[arc4.String(f"string_{i}") for i in range(1, 11)]
    )
    native_arr4 = arr4.to_native(String)
    assert native_arr4.length == 10
    assert list(native_arr4) == [f"string_{i}" for i in range(1, 11)]

    arr5 = arc4.StaticArray[arc4.StaticArray[arc4.UInt64, typing.Literal[10]], typing.Literal[2]](
        *[
            arc4.StaticArray[arc4.UInt64, typing.Literal[10]](
                *[arc4.UInt64(i) for i in range(1, 11)]
            ),
            arc4.StaticArray[arc4.UInt64, typing.Literal[10]](
                *[arc4.UInt64(i) for i in range(21, 31)]
            ),
        ]
    )
    native_arr5 = arr5.to_native(FixedArray[UInt64, typing.Literal[10]])
    assert native_arr5.length == 2
    assert native_arr5[0].length == 10
    assert native_arr5[1].length == 10
    assert list(native_arr5[0]) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert list(native_arr5[1]) == [21, 22, 23, 24, 25, 26, 27, 28, 29, 30]

    imm_native_arr5 = arr5.to_native(ImmutableFixedArray[UInt64, typing.Literal[10]])
    assert imm_native_arr5.length == 2
    assert imm_native_arr5[0].length == 10
    assert imm_native_arr5[1].length == 10
    assert list(imm_native_arr5[0]) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    assert list(imm_native_arr5[1]) == [21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
