import secrets
from pathlib import Path

import pytest
from algokit_utils import AlgorandClient, AppClientMethodCallParams

from tests.common import AVMInvoker, create_avm_invoker

ARTIFACTS_DIR = Path(__file__).parent / ".." / "artifacts"
GLOBAL_STATE_APP_SPEC = ARTIFACTS_DIR / "StateOps" / "data" / "GlobalStateContract.arc56.json"
LOCAL_STATE_APP_SPEC = ARTIFACTS_DIR / "StateOps" / "data" / "LocalStateContract.arc56.json"


@pytest.fixture(scope="module")
def get_global_state_avm_result(algorand: AlgorandClient) -> AVMInvoker:
    return create_avm_invoker(GLOBAL_STATE_APP_SPEC, algorand)


@pytest.fixture(scope="module")
def get_local_state_avm_result(algorand: AlgorandClient) -> AVMInvoker:
    invoker = create_avm_invoker(LOCAL_STATE_APP_SPEC, algorand)
    invoker.client.send.opt_in(
        AppClientMethodCallParams(method="opt_in", note=secrets.token_bytes(8))
    )

    return invoker
