import typing
from collections.abc import Generator

import algopy
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context, arc4_prefix

from .contract import ZkWhitelistContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


@pytest.fixture()
def contract(context: AlgopyTestContext) -> ZkWhitelistContract:
    contract = ZkWhitelistContract()
    contract.create(name=context.any.arc4.string(10))
    return contract


def test_add_address_to_whitelist(
    context: AlgopyTestContext, contract: ZkWhitelistContract
) -> None:
    # Arrange
    address = algopy.arc4.Address(context.default_sender)
    proof = algopy.arc4.DynamicArray[
        algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]]
    ](
        algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]](
            *[algopy.arc4.Byte(0) for _ in range(32)]
        )
    )

    dummy_verifier_app = context.any.application(logs=[arc4_prefix(b"\x80")])
    context.set_template_var("VERIFIER_APP_ID", dummy_verifier_app.id)

    # Act
    result = contract.add_address_to_whitelist(address, proof)

    # Assert
    assert result == algopy.arc4.String("")
    assert contract.whitelist[context.default_sender]


def test_add_address_to_whitelist_invalid_proof(
    context: AlgopyTestContext, contract: ZkWhitelistContract
) -> None:
    # Arrange
    address = context.any.arc4.address()
    proof = algopy.arc4.DynamicArray[
        algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]]
    ](
        algopy.arc4.StaticArray[algopy.arc4.Byte, typing.Literal[32]](
            *[algopy.arc4.Byte(0) for _ in range(32)]
        )
    )
    dummy_verifier_app = context.any.application(logs=[arc4_prefix(b"")])
    context.set_template_var("VERIFIER_APP_ID", dummy_verifier_app.id)

    # Act
    result = contract.add_address_to_whitelist(address, proof)

    # Assert
    assert result == algopy.arc4.String("Proof verification failed")


@pytest.mark.usefixtures("context")
def test_is_on_whitelist(context: AlgopyTestContext, contract: ZkWhitelistContract) -> None:
    # Arrange
    dummy_account = context.any.account(opted_apps=[context.ledger.get_app(contract)])
    contract.whitelist[dummy_account] = True

    # Act
    result = contract.is_on_whitelist(algopy.arc4.Address(dummy_account))

    # Assert
    assert result.native


@pytest.mark.usefixtures("context")
def test_is_not_on_whitelist(context: AlgopyTestContext, contract: ZkWhitelistContract) -> None:
    # Arrange
    dummy_account = context.any.account(opted_apps=[context.ledger.get_app(contract)])
    contract.whitelist[dummy_account] = False

    # Act
    result = contract.is_on_whitelist(algopy.arc4.Address(dummy_account))

    # Assert
    assert not result.native
