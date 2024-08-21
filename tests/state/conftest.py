from pathlib import Path

import pytest
from algosdk.v2client.algod import AlgodClient

from tests.common import AVMInvoker, create_avm_invoker

ARTIFACTS_DIR = Path(__file__).parent / ".." / "artifacts"
GLOBAL_STATE_APP_SPEC = ARTIFACTS_DIR / "StateOps" / "data" / "GlobalStateContract.arc32.json"
LOCAL_STATE_APP_SPEC = ARTIFACTS_DIR / "StateOps" / "data" / "LocalStateContract.arc32.json"


@pytest.fixture(scope="module")
def get_global_state_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(GLOBAL_STATE_APP_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_local_state_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    invoker = create_avm_invoker(LOCAL_STATE_APP_SPEC, algod_client)
    invoker.client.opt_in()

    return invoker
