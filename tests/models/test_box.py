import re
import typing
from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context, arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.models.account import Account
from _algopy_testing.models.application import Application
from _algopy_testing.models.asset import Asset
from _algopy_testing.op.pure import itob
from _algopy_testing.primitives.biguint import BigUInt
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.state.box import Box
from _algopy_testing.state.utils import cast_to_bytes
from _algopy_testing.utils import as_bytes, as_string

from tests.artifacts.BoxContract.contract import BoxContract

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
        assert context.ledger.get_box(contract, b"oca") == itob(oca.native)
        assert context.ledger.get_box(contract, b"txn") == itob(txn.native)
