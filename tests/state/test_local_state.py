import contextlib

import algopy_testing
import algosdk
import pytest
from algopy_testing._context_helpers.context_storage import algopy_testing_context
from algopy_testing.enums import OnCompleteAction

from tests.artifacts.StateOps.contract import LocalStateContract
from tests.common import AVMInvoker


@pytest.mark.parametrize(
    ("method_name", "expected_type"),
    [
        ("get_implicit_key_arc4_uint", algopy_testing.arc4.UInt64),
        ("get_implicit_key_arc4_string", algopy_testing.arc4.String),
        ("get_implicit_key_arc4_byte", algopy_testing.arc4.Byte),
        ("get_implicit_key_arc4_bool", algopy_testing.arc4.Bool),
        ("get_implicit_key_arc4_address", algopy_testing.arc4.Address),
        ("get_implicit_key_arc4_uint128", algopy_testing.arc4.UInt128),
        ("get_implicit_key_arc4_dynamic_bytes", algopy_testing.arc4.DynamicBytes),
        ("get_arc4_uint", algopy_testing.arc4.UInt64),
        ("get_arc4_string", algopy_testing.arc4.String),
        ("get_arc4_byte", algopy_testing.arc4.Byte),
        ("get_arc4_bool", algopy_testing.arc4.Bool),
        ("get_arc4_address", algopy_testing.arc4.Address),
        ("get_arc4_uint128", algopy_testing.arc4.UInt128),
        ("get_arc4_dynamic_bytes", algopy_testing.arc4.DynamicBytes),
    ],
)
def test_get_local_arc4_value(
    get_local_state_avm_result: AVMInvoker,
    localnet_creator_address: str,
    method_name: str,
    expected_type: type,
) -> None:
    with contextlib.suppress(algosdk.error.AlgodHTTPError):
        get_local_state_avm_result("opt_in", on_complete=algosdk.transaction.OnComplete.OptInOC)
    avm_result = get_local_state_avm_result(method_name, a=localnet_creator_address)

    with algopy_testing_context(default_sender=localnet_creator_address) as ctx:
        contract = LocalStateContract()

        with ctx.txn.create_group(
            gtxns=[ctx.any.txn.application_call(on_completion=OnCompleteAction.OptIn)]
        ):
            contract.opt_in()
        test_result = getattr(contract, method_name)(ctx.default_sender)
        assert isinstance(test_result, expected_type)
        if isinstance(test_result, algopy_testing.arc4.Address):
            assert test_result.native.public_key == avm_result
        else:
            assert test_result.native == avm_result  # type: ignore[attr-defined]
