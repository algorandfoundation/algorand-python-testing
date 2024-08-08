from collections.abc import Generator

import pytest
from algopy import op
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import BoxContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_enums(context: AlgopyTestContext) -> None:
    # Arrange
    contract = BoxContract()

    # Act
    contract.store_enums()
    oca, txn = contract.read_enums()

    # Assert
    assert context.ledger.get_box(b"oca") == op.itob(oca.native)
    assert context.ledger.get_box(b"txn") == op.itob(txn.native)
