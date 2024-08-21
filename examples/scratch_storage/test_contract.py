from collections.abc import Generator

import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import ScratchSlotsContract, SimpleScratchSlotsContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_arc4_contract(context: AlgopyTestContext) -> None:
    # Arrange
    contract = ScratchSlotsContract()

    # Act
    result = contract.store_data()

    # Assert
    assert result
    scratch_space = context.txn.last_group.get_scratch_space()
    assert scratch_space[1] == 5
    assert scratch_space[2] == b"Hello World"


def test_simple_contract(context: AlgopyTestContext) -> None:
    # Arrange

    contract = SimpleScratchSlotsContract()

    # Act
    with context.txn.create_group(
        gtxns=[
            context.any.txn.application_call(
                app_id=context.ledger.get_app(contract), scratch_space=[0, 5, b"Hello World"]
            )
        ]
    ):
        result = contract.approval_program()

    # Assert
    assert result
