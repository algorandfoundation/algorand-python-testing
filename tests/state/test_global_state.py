from collections.abc import Generator
from typing import Any

import pytest
from _algopy_testing import arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.context_helpers.context_storage import algopy_testing_context
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.state.global_state import GlobalState


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


@pytest.mark.usefixtures("context")
class TestGlobalState:
    @pytest.mark.parametrize(
        ("type_or_value", "expected_type", "expected_value"),
        [
            (arc4.UInt64, arc4.UInt64, None),
            (arc4.String("Hello"), arc4.String, "Hello"),
            (arc4.Bool(True), arc4.Bool, True),
            (
                arc4.Address("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ"),
                arc4.Address,
                "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
            ),
            (Bytes(b"test"), Bytes, b"test"),
        ],
    )
    def test_initialization(
        self,
        context: AlgopyTestContext,
        type_or_value: Any,
        expected_type: type[Any],
        expected_value: Any,
    ) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(type_or_value, key="test_key")
            assert gs.type_ == expected_type
            assert gs.key == Bytes(b"test_key")
            if expected_value is not None:
                response = gs.value.native if hasattr(gs.value, "native") else gs.value
                assert response == expected_value

    @pytest.mark.parametrize(
        ("key", "expected_bytes"),
        [
            (b"bytes_key", b"bytes_key"),
            ("str_key", b"str_key"),
            (Bytes(b"bytes_obj_key"), b"bytes_obj_key"),
            ("", b""),  # Test empty string
        ],
    )
    def test_set_key(self, context: AlgopyTestContext, key: Any, expected_bytes: bytes) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64)
            gs.set_key(key)
            assert gs.key == Bytes(expected_bytes)

    def test_set_key_invalid(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64)
            with pytest.raises(KeyError, match="Key must be bytes or str"):
                gs.set_key(123)  # type: ignore[arg-type]

    @pytest.mark.parametrize(
        ("type_", "value"),
        [
            (arc4.UInt64, 42),
            (arc4.String, "test"),
            (arc4.Bool, True),
            (Bytes, b"test"),
        ],
    )
    def test_value_operations(self, context: AlgopyTestContext, type_: Any, value: Any) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(type_, key="test_key")

            gs.value = type_(value)
            response = gs.value.native if hasattr(gs.value, "native") else gs.value
            assert response == value
            assert isinstance(gs.value, type_)

            del gs.value
            with pytest.raises(ValueError, match="Value is not set"):
                _ = gs.value

    def test_get_method(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64, key="test_uint64")

            assert gs.get(default=arc4.UInt64(0)) == 0
            assert gs.get() == 0  # Default initialization

            gs.value = arc4.UInt64(42)
            assert gs.get() == 42

    def test_maybe_method(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64, key="test_uint64")

            value, exists = gs.maybe()
            assert value is None
            assert exists is False

            gs.value = arc4.UInt64(42)
            value, exists = gs.maybe()
            assert value == 42
            assert exists is True

    def test_pending_value(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64(100))
            assert gs._pending_value == 100

            gs.set_key("test_key")
            assert gs.value == 100
            assert gs._pending_value is None

    def test_description(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64, key="test_key", description="Test description")
            assert gs.description == "Test description"

    def test_app_id(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(arc4.UInt64, key="test_key")

        assert gs.app_id == context.txn.last_active.app_id.id
