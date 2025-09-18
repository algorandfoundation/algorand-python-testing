from pathlib import Path

import pytest
from algokit_utils import AlgorandClient

from tests.common import AVMInvoker, create_avm_invoker

ARTIFACTS_DIR = Path(__file__).parent / ".." / "artifacts"
APP_SPEC = ARTIFACTS_DIR / "AVM12" / "data" / "Contract.arc56.json"


@pytest.fixture(scope="module")
def get_avm_result(algorand: AlgorandClient) -> AVMInvoker:
    return create_avm_invoker(APP_SPEC, algorand)
