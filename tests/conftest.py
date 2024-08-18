import algopy
import pytest
from algokit_utils import (
    get_algod_client,
    get_default_localnet_config,
    get_indexer_client,
    get_localnet_default_account,
    is_localnet,
)
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.network_clients import AlgoClientConfigs
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

# config.config.configure(debug=True)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client(get_default_localnet_config("algod"))

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client(get_default_localnet_config("indexer"))


@pytest.fixture()
def localnet_creator_address(algod_client: AlgodClient) -> str:
    return get_localnet_default_account(algod_client).address


@pytest.fixture()
def algorand(algod_client: AlgodClient) -> AlgorandClient:
    client = AlgorandClient(
        AlgoClientConfigs(
            algod_config=get_default_localnet_config("algod"),
            indexer_config=get_default_localnet_config("indexer"),
            kmd_config=get_default_localnet_config("kmd"),
        )
    )
    creator = get_localnet_default_account(algod_client)
    client.set_default_signer(creator.signer)
    return client


@pytest.fixture()
def localnet_creator(localnet_creator_address: str) -> algopy.Account:
    return algopy.Account(localnet_creator_address)
