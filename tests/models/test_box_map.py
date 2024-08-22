import typing
from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context, arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.primitives.biguint import BigUInt
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.state.box import BoxMap
from _algopy_testing.utils import as_bytes, as_string

BOX_NOT_CREATED_ERROR = "Box has not been created"


class ATestContract(algopy.Contract):
    def __init__(self) -> None:
        self.uint_64_box_map = algopy.BoxMap(algopy.UInt64, algopy.Bytes)


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:  # noqa: SIM117
        with ctx.txn.create_group([ctx.any.txn.application_call()]):
            yield ctx


def test_init_without_key_prefix() -> None:
    with algopy_testing_context():
        contract = ATestContract()
        assert contract.uint_64_box_map.key_prefix == b"uint_64_box_map"


@pytest.mark.parametrize(
    ("key_type", "value_type", "key_prefix"),
    [
        (Bytes, UInt64, "key_prefix"),
        (String, Bytes, b"key_prefix"),
        (BigUInt, String, Bytes(b"key_prefix")),
        (arc4.String, BigUInt, String("key_prefix")),
        (UInt64, arc4.String, "key_prefix"),
        (String, arc4.DynamicArray[arc4.DynamicBytes], b"key_prefix"),
    ],
)
def test_init_with_key_prefix(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key_prefix: bytes | str | Bytes | String,
) -> None:
    box = BoxMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    assert len(box.key_prefix) > 0

    key_prefix_bytes = (
        String(as_string(key_prefix)).bytes
        if isinstance(key_prefix, str | String)
        else Bytes(as_bytes(key_prefix))
    )
    assert box.key_prefix == key_prefix_bytes

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box[key_type()]

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.length(key_type())


@pytest.mark.parametrize(
    ("key_type", "value_type", "key", "value"),
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (BigUInt, String, BigUInt(123), String("Test")),
        (arc4.String, BigUInt, arc4.String("ghi"), BigUInt(100)),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
        (
            String,
            arc4.DynamicArray[arc4.UInt64],
            String("jkl"),
            arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)]),
        ),
    ],
)
def test_value_setter(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_pefix"
    box = BoxMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    box[key] = value
    box_content = box[key]

    full_key = box._full_key(key)
    op_box_content, op_box_exists = algopy.op.Box.get(full_key)
    op_box_length, _ = algopy.op.Box.length(full_key)
    assert op_box_exists
    assert box.length(key) == op_box_length

    _assert_box_content_equality(value, box_content, op_box_content)


@pytest.mark.parametrize(
    ("key_type", "value_type", "key", "value"),
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (BigUInt, String, BigUInt(123), String("Test")),
        (arc4.String, BigUInt, arc4.String("ghi"), BigUInt(100)),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
        (
            String,
            arc4.DynamicArray[arc4.UInt64],
            String("jkl"),
            arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)]),
        ),
    ],
)
def test_value_deleter(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_pefix"
    box = BoxMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    box[key] = value

    del box[key]

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box[key]

    full_key = box._full_key(key)

    op_box_content, op_box_exists = algopy.op.Box.get(full_key)
    assert not op_box_exists
    assert not op_box_content


@pytest.mark.parametrize(
    ("key_type", "value_type", "key", "value"),
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (BigUInt, String, BigUInt(123), String("Test")),
        (arc4.String, BigUInt, arc4.String("ghi"), BigUInt(100)),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
        (
            String,
            arc4.DynamicArray[arc4.UInt64],
            String("jkl"),
            arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)]),
        ),
    ],
)
def test_maybe(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_pefix"
    box = BoxMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    box[key] = value

    box_content, box_exists = box.maybe(key)

    full_key = box._full_key(key)
    op_box_content, op_box_exists = algopy.op.Box.get(full_key)
    op_box_length, _ = algopy.op.Box.length(full_key)
    assert box_exists
    assert op_box_exists
    assert box.length(key) == op_box_length

    _assert_box_content_equality(value, box_content, op_box_content)


@pytest.mark.parametrize(
    ("key_type", "value_type", "key", "value"),
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (BigUInt, String, BigUInt(123), String("Test")),
        (arc4.String, BigUInt, arc4.String("ghi"), BigUInt(100)),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
        (
            String,
            arc4.DynamicArray[arc4.UInt64],
            String("jkl"),
            arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)]),
        ),
    ],
)
def test_maybe_when_box_does_not_exists(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_pefix"
    box = BoxMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    box[key] = value

    del box[key]

    box_content, box_exists = box.maybe(key)
    assert not box_content
    assert not box_exists

    full_key = box._full_key(key)

    op_box_content, op_box_exists = algopy.op.Box.get(full_key)
    assert not op_box_exists
    assert not op_box_content


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
