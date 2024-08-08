from collections.abc import Generator

import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import ScratchSlotsContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


def test_approval_program(context: AlgopyTestContext) -> None:
    # Arrange
    contract = ScratchSlotsContract()

    # Act
    result = contract.store_data()

    # Assert
    assert result
    last_txn = context.txn.last_active_txn
    scratch_space = context.get_scratch_space(last_txn)
    assert scratch_space[1] == 5
    assert scratch_space[2] == b"Hello World"
