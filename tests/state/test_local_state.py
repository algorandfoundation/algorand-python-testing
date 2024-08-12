import contextlib
from collections.abc import Generator

import algopy_testing
import algosdk
import pytest
from algokit_utils import Account
from algopy_testing._context_helpers.context_storage import algopy_testing_context
from algopy_testing.context import AlgopyTestContext

from tests.artifacts.StateOps.contract import LocalStateContract
from tests.common import AVMInvoker


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


@pytest.mark.parametrize(
    ("method_name", "expected_type"),
    [
        ("get_implicit_key_arc4_uint", algopy_testing.arc4.UInt64),
        ("get_implicit_key_arc4_string", algopy_testing.arc4.String),
    ],
)
def test_get_local_arc4_value(
    get_local_state_avm_result: AVMInvoker,
    context: AlgopyTestContext,
    localnet_creator: Account,
    method_name: str,
    expected_type: type,
) -> None:
    import algopy

    with contextlib.suppress(algosdk.error.AlgodHTTPError):
        get_local_state_avm_result("opt_in", on_complete=algosdk.transaction.OnComplete.OptInOC)
    avm_result = get_local_state_avm_result(method_name, a=localnet_creator.public_key)
    contract = LocalStateContract()

    with context.txn.scoped_execution(
        txn_op_fields={"on_completion": algopy.OnCompleteAction.OptIn}
    ):
        contract.opt_in()
    test_result = getattr(contract, method_name)(context.default_sender)
    assert isinstance(test_result, expected_type)
    assert test_result.native == avm_result  # type: ignore[attr-defined]
