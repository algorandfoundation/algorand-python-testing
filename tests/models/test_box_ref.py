from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context
from _algopy_testing.constants import MAX_BOX_SIZE, MAX_BYTES_SIZE
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String
from _algopy_testing.state.box import BoxRef
from _algopy_testing.utils import as_bytes, as_string

TEST_BOX_KEY = b"test_key"
BOX_NOT_CREATED_ERROR = "Box has not been created"


class ATestContract(algopy.ARC4Contract):
    def __init__(self) -> None:
        self.uint_64_box_ref = algopy.BoxRef()


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:  # noqa: SIM117
        with ctx.txn.create_group([ctx.any.txn.application_call()]):
            yield ctx


def test_init_without_key() -> None:
    with algopy_testing_context():
        contract = ATestContract()
        assert contract.uint_64_box_ref.key == b"uint_64_box_ref"


@pytest.mark.parametrize(
    "key",
    [
        "key",
        b"key",
        Bytes(b"key"),
        String("key"),
    ],
)
def test_init_with_key(
    context: AlgopyTestContext,  # noqa: ARG001
    key: bytes | str | Bytes | String,
) -> None:
    box = BoxRef(key=key)
    assert not box
    assert len(box.key) > 0

    key_bytes = (
        String(as_string(key)).bytes if isinstance(key, str | String) else Bytes(as_bytes(key))
    )
    assert box.key == key_bytes

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.length


@pytest.mark.parametrize(
    "size",
    [
        0,
        1,
        10,
        MAX_BOX_SIZE,
    ],
)
def test_create(
    context: AlgopyTestContext,  # noqa: ARG001
    size: int,
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=size)

    assert box.length == size

    _assert_box_value(box, b"\x00" * size)


def test_create_overflow(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    with pytest.raises(ValueError, match=f"Box size cannot exceed {MAX_BOX_SIZE}"):
        box.create(size=MAX_BOX_SIZE + 1)


def test_delete(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=MAX_BOX_SIZE)
    assert box.length == MAX_BOX_SIZE

    box_existed = box.delete()
    assert box_existed
    assert not box

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        _ = box.length

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        box.resize(10)

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        box.replace(0, b"\x11")

    assert not box.delete()


@pytest.mark.parametrize(
    ("size", "new_size"),
    [
        (1, 0),
        (10, 1),
        (MAX_BYTES_SIZE, 10),
        (MAX_BOX_SIZE, MAX_BYTES_SIZE),
    ],
)
def test_resize_to_smaller(
    context: AlgopyTestContext,  # noqa: ARG001
    size: int,
    new_size: int,
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=size)
    _initialise_box_value(box, b"\x11" * size)

    box.resize(new_size)
    assert box.length == new_size
    _assert_box_value(box, b"\x11" * new_size)


@pytest.mark.parametrize(
    ("size", "new_size"),
    [
        (0, 1),
        (1, 10),
        (10, MAX_BYTES_SIZE),
        (MAX_BYTES_SIZE, MAX_BOX_SIZE),
    ],
)
def test_resize_to_bigger(
    context: AlgopyTestContext,  # noqa: ARG001
    size: int,
    new_size: int,
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=size)
    _initialise_box_value(box, b"\x11" * size)

    box.resize(new_size)
    assert box.length == new_size

    _assert_box_value(box, b"\x00" * new_size, new_size - 1)


def test_resize_overflow(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=10)

    with pytest.raises(ValueError, match=f"Box size cannot exceed {MAX_BOX_SIZE}"):
        box.resize(MAX_BOX_SIZE + 1)


def test_replace_extract(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=MAX_BOX_SIZE)
    box_value = b"\x01\x02" * int(MAX_BOX_SIZE / 2)

    _initialise_box_value(box, box_value)

    _assert_box_value(box, box_value)


def test_replace_when_box_does_not_exists(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        box.replace(0, b"\x11")


@pytest.mark.parametrize(
    ("start", "replacement"),
    [
        (0, b"\x11" * 11),
        (10, b"\x11"),
        (9, b"\x11" * 2),
    ],
)
def test_replace_overflow(
    context: AlgopyTestContext,  # noqa: ARG001
    start: int,
    replacement: bytes,
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    box.create(size=10)

    with pytest.raises(ValueError, match="Replacement content exceeds box size"):
        box.replace(start, replacement)


def test_maybe(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    key = b"test_key"

    box = BoxRef(key=key)
    box.create(size=10)
    box_value = b"\x01\x02" * 5
    box.put(box_value)

    box_content, box_exists = box.maybe()

    op_box_content, op_box_exists = algopy.op.Box.get(key)

    assert box_exists
    assert op_box_exists
    assert box_content == op_box_content
    assert box_content == Bytes(box_value)


def test_maybe_when_box_does_not_exist(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    key = b"test_key"

    box = BoxRef(key=key)
    box.create(size=10)
    box_value = b"\x01\x02" * 5
    box.put(box_value)
    box.delete()

    box_content, box_exists = box.maybe()
    assert not box_content
    assert not box_exists

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert not op_box_content
    assert not op_box_exists


@pytest.mark.parametrize(
    ("size", "value"),
    [
        (0, b""),
        (10, b"\x11" * 10),
        (MAX_BYTES_SIZE, b"\x11" * MAX_BYTES_SIZE),
    ],
)
def test_put_get(
    context: AlgopyTestContext,  # noqa: ARG001
    size: int,
    value: bytes,
) -> None:
    key = b"test_key"

    box = BoxRef(key=key)
    box.create(size=size)

    box.put(value)

    box_content = box.get(default=b"\x00" * size)
    assert box_content == Bytes(value)

    op_box_content, op_box_exists = algopy.op.Box.get(key)
    assert op_box_exists
    assert box_content == op_box_content


def test_put_when_box_does_not_exist(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    key = b"test_key"

    box = BoxRef(key=key)
    box_value = b"\x01\x02" * 5
    box.put(box_value)

    box_content = box.get(default=b"\x00" * 10)
    assert box_content == Bytes(box_value)


def test_get_when_box_does_not_exist(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    key = b"test_key"
    box = BoxRef(key=key)

    default_value = b"\x00" * 10
    box_content = box.get(default=default_value)
    assert box_content == Bytes(default_value)


def test_put_get_overflow(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    key = b"test_key"

    box = BoxRef(key=key)
    box.create(size=MAX_BOX_SIZE)

    with pytest.raises(ValueError, match=f"expected value length <= {MAX_BYTES_SIZE}"):
        box.put(b"\x11" * MAX_BOX_SIZE)
    with pytest.raises(ValueError, match=f"expected value length <= {MAX_BYTES_SIZE}"):
        box.get(default=b"\x00" * MAX_BOX_SIZE)


def test_splice_when_new_value_is_longer(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    size = 10
    box = BoxRef(key=TEST_BOX_KEY)
    box.create(size=size)
    box_value = b"\x01\x02" * 5
    replacement_value = b"\x11" * 2
    box.put(box_value)

    box.splice(1, 1, replacement_value)
    box_content = box.get(default=b"\x00" * size)

    op_box_key = b"another_key"
    algopy.op.Box.create(op_box_key, size)
    algopy.op.Box.put(op_box_key, box_value)
    algopy.op.Box.splice(op_box_key, 1, 1, replacement_value)
    op_box_content, _ = algopy.op.Box.get(op_box_key)
    op_box_length, _ = algopy.op.Box.length(op_box_key)
    assert box_content == Bytes(b"\x01" + replacement_value + b"\x01\x02" * 3 + b"\x01")
    assert box_content == op_box_content
    assert box.length == size
    assert box.length == op_box_length


def test_splice_when_new_value_is_shorter(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    size = 10
    box = BoxRef(key=TEST_BOX_KEY)
    box.create(size=size)
    box_value = b"\x01\x02" * 5
    replacement_value = b"\x11" * 2
    box.put(box_value)

    box.splice(1, 5, replacement_value)
    box_content = box.get(default=b"\x00" * size)

    op_box_key = b"another_key"
    algopy.op.Box.create(op_box_key, size)
    algopy.op.Box.put(op_box_key, box_value)
    algopy.op.Box.splice(op_box_key, 1, 5, replacement_value)
    op_box_content, _ = algopy.op.Box.get(op_box_key)
    op_box_length, _ = algopy.op.Box.length(op_box_key)
    assert box_content == Bytes(b"\x01" + replacement_value + b"\x01\x02" * 2 + b"\x00" * 3)
    assert box_content == op_box_content
    assert box.length == size
    assert box.length == op_box_length


def test_splice_when_box_does_not_exist(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)

    with pytest.raises(RuntimeError, match=BOX_NOT_CREATED_ERROR):
        box.splice(0, 1, b"\x11")


def test_splice_out_of_bounds(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    box = BoxRef(key=TEST_BOX_KEY)
    box.create(size=10)

    with pytest.raises(ValueError, match="Start index exceeds box size"):
        box.splice(11, 1, b"\x11")


def _initialise_box_value(box: BoxRef, value: bytes) -> None:
    index = 0
    size = len(value)
    while index < size:
        length = min((size - index), MAX_BYTES_SIZE)
        box.replace(index, value[index : index + length])
        index += length


def _assert_box_value(box: BoxRef, expected_value: bytes, start: int = 0) -> None:
    index = start
    size = len(expected_value)
    while index < size:
        length = min((size - index), MAX_BYTES_SIZE)
        box_content = box.extract(index, length)
        op_box_content = algopy.op.Box.extract(box.key, index, length)
        assert box_content == op_box_content
        assert box_content == Bytes(expected_value[index : index + length])
        index += length
