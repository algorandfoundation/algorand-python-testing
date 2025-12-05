from collections.abc import Generator

import pytest
from _algopy_testing import arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.context_helpers.context_storage import algopy_testing_context
from _algopy_testing.primitives import UInt64
from _algopy_testing.primitives.array import Array

from tests.artifacts.DynamicITxnGroup.contract import DynamicItxnGroup
from tests.artifacts.DynamicITxnGroup.verifier import VerifierContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_firstly(context: AlgopyTestContext) -> None:
    verifier = VerifierContract()
    dynamic_itxn_group = DynamicItxnGroup()

    verifier_app = context.ledger.get_app(verifier)
    dynamic_itxn_group_app = context.ledger.get_app(dynamic_itxn_group)

    test_accounts = [context.any.account() for _ in range(3)]

    addresses = Array([arc4.Address(a) for a in test_accounts])
    payment = context.any.txn.payment(
        amount=UInt64(9),
        receiver=dynamic_itxn_group_app.address,
    )
    dynamic_itxn_group.test_firstly(addresses, payment, verifier_app)

    itxns = context.txn.last_group.get_itxn_group(-1)
    assert len(itxns) == 5
    for i in range(3):
        assert itxns.payment(i).amount == 3
    assert itxns.application_call(3).app_id == verifier_app
    assert itxns.asset_config(4).asset_name == b"abc"


def test_looply(
    context: AlgopyTestContext,
) -> None:
    verifier = VerifierContract()
    dynamic_itxn_group = DynamicItxnGroup()

    verifier_app = context.ledger.get_app(verifier)
    dynamic_itxn_group_app = context.ledger.get_app(dynamic_itxn_group)

    test_accounts = [context.any.account() for _ in range(3)]

    addresses = Array([arc4.Address(a) for a in test_accounts])
    payment = context.any.txn.payment(
        amount=UInt64(9),
        receiver=dynamic_itxn_group_app.address,
    )
    dynamic_itxn_group.test_looply(addresses, payment, verifier_app)

    itxns = context.txn.last_group.get_itxn_group(-1)
    assert len(itxns) == 5
    for i in range(3):
        assert itxns.payment(i).amount == 3
    assert itxns.application_call(3).app_id == verifier_app
    assert itxns.asset_config(4).asset_name == b"abc"
