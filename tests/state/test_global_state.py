from collections.abc import Generator

import algopy_testing
import pytest
from algopy_testing._context_helpers.context_storage import algopy_testing_context
from algopy_testing.context import AlgopyTestContext

from tests.artifacts.StateOps.contract import GlobalStateContract
from tests.common import AVMInvoker


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    ("method_name", "expected_type"),
    [
        ("get_implicit_key_arc4_uint", algopy_testing.arc4.UInt64),
        ("get_implicit_key_arc4_string", algopy_testing.arc4.String),
    ],
)
def test_get_global_arc4_value(
    get_global_state_avm_result: AVMInvoker,
    method_name: str,
    expected_type: type,
) -> None:
    avm_result = get_global_state_avm_result(method_name)
    contract = GlobalStateContract()

    test_result = getattr(contract, method_name)()
    assert isinstance(test_result, expected_type)
    assert test_result.native == avm_result  # type: ignore[attr-defined]
