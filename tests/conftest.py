import algopy
import pytest
from algokit_utils import (
    AlgorandClient,
)

# config.config.configure(debug=True)


@pytest.fixture(scope="session")
def algorand() -> AlgorandClient:
    client = AlgorandClient.default_localnet()
    client.set_suggested_params_cache_timeout(0)
    return client


@pytest.fixture()
def localnet_creator_address(algorand: AlgorandClient) -> str:
    return algorand.account.localnet_dispenser().address


@pytest.fixture()
def localnet_creator(localnet_creator_address: str) -> algopy.Account:
    return algopy.Account(localnet_creator_address)
