import typing
from collections.abc import Generator
from typing import Any

import algopy
import pytest
from _algopy_testing import arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.context_helpers.context_storage import algopy_testing_context
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.serialize import compare_type, type_of
from _algopy_testing.state.local_state import LocalState
from _algopy_testing.state.utils import cast_to_bytes

from tests.artifacts.StateOps.contract import LocalStateContract
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
class TestLocalState:
    test_data_array = (
        [
            (arc4.UInt64, arc4.UInt64(42)),
            (arc4.String, arc4.String("test")),
            (arc4.Bool, arc4.Bool(True)),
            (Bytes, Bytes(b"test")),
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
            ),
            (
                Swapped,
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
            ),
        ],
    )

    @pytest.mark.parametrize(("type_", "value"), *test_data_array)
    def test_initialization(
        self,
        context: AlgopyTestContext,
        type_: Any,
        value: type[Any],
    ) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            ls = LocalState(type_, key="test_key")
            ls[context.default_sender] = value
            assert ls.type_ == type_
            assert ls.key == Bytes(b"test_key")
            assert ls[context.default_sender] == value

    @pytest.mark.parametrize(("type_", "value"), *test_data_array)
    def test_value_operations(self, context: AlgopyTestContext, type_: Any, value: Any) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            ls = LocalState(type_, key="test_key")

            ls[context.default_sender] = value

            assert ls[context.default_sender] == value
            assert compare_type(type_of(ls[context.default_sender]), type_) or isinstance(
                ls[context.default_sender], type_
            )

            del ls[context.default_sender]
            with pytest.raises(KeyError):
                _ = ls[context.default_sender]

    @pytest.mark.parametrize(("type_", "value"), *test_data_array)
    def test_get_method(self, context: AlgopyTestContext, type_: Any, value: Any) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            ls = LocalState(type_, key="test_uint64")

            assert ls.get(context.default_sender, default=None) is None

            ls[context.default_sender] = value
            assert ls.get(context.default_sender, default=None) == value

    @pytest.mark.parametrize(("type_", "value"), *test_data_array)
    def test_maybe_method(self, context: AlgopyTestContext, type_: Any, value: Any) -> None:
        with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
            ls = LocalState(type_, key="test_uint64")

            maybe_value, exists = ls.maybe(context.default_sender)
            assert maybe_value is None
            assert exists is False

            ls[context.default_sender] = value
            maybe_value, exists = ls.maybe(context.default_sender)
            assert maybe_value == value
            assert exists is True


@pytest.mark.parametrize(
    ("method_name", "expected_type"),
    [
        ("get_implicit_key_arc4_uint", algopy.arc4.UInt64),
        ("get_implicit_key_arc4_string", algopy.arc4.String),
        ("get_implicit_key_arc4_byte", algopy.arc4.Byte),
        ("get_implicit_key_arc4_bool", algopy.arc4.Bool),
        ("get_implicit_key_arc4_address", algopy.arc4.Address),
        ("get_implicit_key_arc4_uint128", algopy.arc4.UInt128),
        ("get_implicit_key_arc4_dynamic_bytes", algopy.arc4.DynamicBytes),
        ("get_implicit_key_tuple", tuple[UInt64, Bytes, bool]),
        ("get_arc4_uint", algopy.arc4.UInt64),
        ("get_arc4_string", algopy.arc4.String),
        ("get_arc4_byte", algopy.arc4.Byte),
        ("get_arc4_bool", algopy.arc4.Bool),
        ("get_arc4_address", algopy.arc4.Address),
        ("get_arc4_uint128", algopy.arc4.UInt128),
        ("get_arc4_dynamic_bytes", algopy.arc4.DynamicBytes),
    ],
)
def test_get_local_arc4_value(
    get_local_state_avm_result: AVMInvoker,
    localnet_creator_address: str,
    method_name: str,
    expected_type: type,
) -> None:
    avm_result = get_local_state_avm_result(
        method_name, a=localnet_creator_address, return_raw=True
    )

    with algopy_testing_context(default_sender=localnet_creator_address) as ctx:
        contract = LocalStateContract()

        with ctx.txn.create_group(
            active_txn_overrides={"on_completion": algopy.OnCompleteAction.OptIn}
        ):
            contract.opt_in()
        test_result = getattr(contract, method_name)(ctx.default_sender)
        assert compare_type(type_of(test_result), expected_type) or isinstance(
            test_result, expected_type
        )
        assert cast_to_bytes(test_result) == avm_result
