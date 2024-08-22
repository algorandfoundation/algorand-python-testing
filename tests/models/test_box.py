import typing
from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context, arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.op.pure import itob
from _algopy_testing.primitives.biguint import BigUInt
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.state.box import Box
from _algopy_testing.utils import as_bytes, as_string

from tests.artifacts.BoxContract.contract import BoxContract

BOX_NOT_CREATED_ERROR = "Box has not been created"


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
    ("value_type", "value"),
    [
        (UInt64, UInt64(100)),
        (Bytes, Bytes(b"Test")),
        (String, String("Test")),
        (BigUInt, BigUInt(100)),
        (arc4.String, arc4.String("Test")),
        (arc4.DynamicArray[arc4.UInt64], arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)])),
    ],
)
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


@pytest.mark.parametrize(
    ("value_type", "value"),
    [
        (UInt64, UInt64(100)),
        (Bytes, Bytes(b"Test")),
        (String, String("Test")),
        (BigUInt, BigUInt(100)),
        (arc4.String, arc4.String("Test")),
        (arc4.DynamicArray[arc4.UInt64], arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)])),
    ],
)
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


@pytest.mark.parametrize(
    ("value_type", "value"),
    [
        (UInt64, UInt64(100)),
        (Bytes, Bytes(b"Test")),
        (String, String("Test")),
        (BigUInt, BigUInt(100)),
        (arc4.String, arc4.String("Test")),
        (arc4.DynamicArray[arc4.UInt64], arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)])),
    ],
)
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


@pytest.mark.parametrize(
    ("value_type", "value"),
    [
        (UInt64, UInt64(100)),
        (Bytes, Bytes(b"Test")),
        (String, String("Test")),
        (BigUInt, BigUInt(100)),
        (arc4.String, arc4.String("Test")),
        (arc4.DynamicArray[arc4.UInt64], arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)])),
    ],
)
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
        assert box_content == op_box_content


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
