import typing
from collections.abc import Generator
from typing import Any

import pytest
from _algopy_testing import arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.context_helpers.context_storage import algopy_testing_context
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.serialize import compare_type, type_of
from _algopy_testing.state.global_state import GlobalState
from _algopy_testing.state.utils import cast_to_bytes

from tests.artifacts.StateOps.contract import GlobalStateContract
from tests.common import AVMInvoker


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


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
            (
                tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address],
                tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address],
                None,
            ),
            (
                (
                    arc4.UInt64(100),
                    arc4.Bool(True),
                    True,
                    arc4.Address(Bytes(b"\x00" * 32)),
                ),
                tuple[arc4.UInt64, arc4.Bool, bool, arc4.Address],
                (
                    arc4.UInt64(100),
                    arc4.Bool(True),
                    True,
                    arc4.Address(Bytes(b"\x00" * 32)),
                ),
            ),
            (
                Swapped,
                Swapped,
                None,
            ),
            (
                Swapped(arc4.UInt64(1), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                Swapped,
                Swapped(arc4.UInt64(1), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
            ),
            (MyStruct, MyStruct, None),
            (
                MyStruct(
                    UInt64(1),
                    True,
                    arc4.Bool(True),
                    arc4.UInt64(2),
                    Swapped(arc4.UInt64(3), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                ),
                MyStruct,
                MyStruct(
                    UInt64(1),
                    True,
                    arc4.Bool(True),
                    arc4.UInt64(2),
                    Swapped(arc4.UInt64(3), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                ),
            ),
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

    test_data_array = (
        [
            (arc4.UInt64, arc4.UInt64(42), 42),
            (arc4.String, arc4.String("test"), "test"),
            (arc4.Bool, arc4.Bool(True), True),
            (Bytes, Bytes(b"test"), b"test"),
            (
                tuple[
                    arc4.UInt64,
                    arc4.Bool,
                    bool,
                    arc4.Address,
                    Bytes,
                    arc4.DynamicBytes,
                    arc4.DynamicArray[arc4.Byte],
                ],
                (
                    arc4.UInt64(100),
                    arc4.Bool(True),
                    True,
                    arc4.Address(Bytes(b"\x00" * 32)),
                    Bytes(b"hello"),
                    arc4.DynamicBytes(b"world"),
                    arc4.DynamicArray[arc4.Byte](*[arc4.Byte(i) for i in b"testing"]),
                ),
                (
                    arc4.UInt64(100),
                    arc4.Bool(True),
                    True,
                    arc4.Address(Bytes(b"\x00" * 32)),
                    Bytes(b"hello"),
                    arc4.DynamicBytes(b"world"),
                    arc4.DynamicArray[arc4.Byte](*[arc4.Byte(i) for i in b"testing"]),
                ),
            ),
            (
                Swapped,
                Swapped(arc4.UInt64(1), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                Swapped(arc4.UInt64(1), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
            ),
            (
                MyStruct,
                MyStruct(
                    UInt64(1),
                    True,
                    arc4.Bool(True),
                    arc4.UInt64(2),
                    Swapped(arc4.UInt64(3), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                ),
                MyStruct(
                    UInt64(1),
                    True,
                    arc4.Bool(True),
                    arc4.UInt64(2),
                    Swapped(arc4.UInt64(3), arc4.Bool(True), arc4.Address(Bytes(b"\x00" * 32))),
                ),
            ),
        ],
    )

    @pytest.mark.parametrize(("type_", "value", "expected_value"), *test_data_array)
    def test_value_operations(
        self, context: AlgopyTestContext, type_: Any, value: Any, expected_value: Any | None
    ) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(type_, key="test_key")

            gs.value = value
            response = gs.value.as_uint64() if hasattr(gs.value, "as_uint64") else gs.value
            assert response == expected_value
            assert compare_type(type_of(gs.value), type_) or isinstance(gs.value, type_)

            del gs.value
            with pytest.raises(ValueError, match="Value is not set"):
                _ = gs.value

    @pytest.mark.parametrize(("type_", "value", "expected_value"), *test_data_array)
    def test_get_method(
        self,
        context: AlgopyTestContext,
        type_: Any,
        value: Any,
        expected_value: Any,  # noqa: ARG002
    ) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(type_, key="test_uint64")

            assert gs.get(default=None) is None

            gs.value = value
            assert gs.get(default=None) == value

    @pytest.mark.parametrize(("type_", "value", "expected_value"), *test_data_array)
    def test_maybe_method(
        self,
        context: AlgopyTestContext,
        type_: Any,
        value: Any,
        expected_value: Any,  # noqa: ARG002
    ) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            gs = GlobalState(type_, key="test_uint64")

            maybe_value, exists = gs.maybe()
            assert maybe_value is None
            assert exists is False

            gs.value = value
            maybe_value, exists = gs.maybe()
            assert maybe_value == value
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


@pytest.mark.parametrize(
    ("method_name", "expected_type"),
    [
        ("get_implicit_key_arc4_uint", arc4.UInt64),
        ("get_implicit_key_arc4_string", arc4.String),
        ("get_implicit_key_arc4_byte", arc4.Byte),
        ("get_implicit_key_arc4_bool", arc4.Bool),
        ("get_implicit_key_arc4_address", arc4.Address),
        ("get_implicit_key_arc4_uint128", arc4.UInt128),
        ("get_implicit_key_arc4_dynamic_bytes", arc4.DynamicBytes),
        ("get_implicit_key_tuple", tuple[UInt64, Bytes, bool]),
        ("get_arc4_uint", arc4.UInt64),
        ("get_arc4_string", arc4.String),
        ("get_arc4_byte", arc4.Byte),
        ("get_arc4_bool", arc4.Bool),
        ("get_arc4_address", arc4.Address),
        ("get_arc4_uint128", arc4.UInt128),
        ("get_arc4_dynamic_bytes", arc4.DynamicBytes),
    ],
)
def test_get_global_value(
    get_global_state_avm_result: AVMInvoker,
    localnet_creator_address: str,
    method_name: str,
    expected_type: type,
) -> None:
    avm_result = get_global_state_avm_result(method_name, return_raw=True)

    with algopy_testing_context(default_sender=localnet_creator_address):
        contract = GlobalStateContract()

        test_result = getattr(contract, method_name)()
        assert compare_type(type_of(test_result), expected_type) or isinstance(
            test_result, expected_type
        )
        assert compare_type(type_of(test_result), expected_type) or isinstance(
            test_result, expected_type
        )
        assert cast_to_bytes(test_result) == avm_result
