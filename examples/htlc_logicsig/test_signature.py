from collections.abc import Generator

import algopy
import algosdk
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .signature import hashed_time_locked_lsig


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_seller_receives_payment(context: AlgopyTestContext) -> None:
    # Arrange
    with context.txn.create_group(
        [
            context.any.txn.payment(
                fee=algopy.UInt64(500),
                first_valid=algopy.UInt64(1000),
                close_remainder_to=algopy.Account(algosdk.constants.ZERO_ADDRESS),
                rekey_to=algopy.Account(algosdk.constants.ZERO_ADDRESS),
                receiver=algopy.Account(
                    "6ZHGHH5Z5CTPCF5WCESXMGRSVK7QJETR63M3NY5FJCUYDHO57VTCMJOBGY"
                ),
            ),
        ],
    ):
        # Act
        result = context.execute_logicsig(hashed_time_locked_lsig, algopy.Bytes(b"secret"))

    # Assert
    assert result is True
