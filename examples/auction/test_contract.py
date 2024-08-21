import time
from collections.abc import Generator

import algopy
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import AuctionContract


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_opt_into_asset(context: AlgopyTestContext) -> None:
    # Arrange
    asset = context.any.asset()
    contract = AuctionContract()

    # Act
    contract.opt_into_asset(asset)

    # Assert
    assert contract.asa.id == asset.id
    inner_txn = context.txn.last_group.last_itxn.asset_transfer
    assert (
        inner_txn.asset_receiver == context.ledger.get_app(contract).address
    ), "Asset receiver does not match"
    assert inner_txn.xfer_asset == asset, "Transferred asset does not match"


def test_start_auction(
    context: AlgopyTestContext,
) -> None:
    # Arrange
    contract = AuctionContract()
    app = context.ledger.get_app(contract)
    latest_timestamp = context.any.uint64(1, 1000)
    starting_price = context.any.uint64()
    auction_duration = context.any.uint64(100, 1000)
    axfer_txn = context.any.txn.asset_transfer(
        asset_receiver=app.address,
        asset_amount=starting_price,
    )
    contract.asa_amount = starting_price
    context.ledger.patch_global_fields(
        latest_timestamp=latest_timestamp,
    )

    # Act
    contract.start_auction(
        starting_price,
        auction_duration,
        axfer_txn,
    )

    # Assert
    assert contract.auction_end == latest_timestamp + auction_duration
    assert contract.previous_bid == starting_price
    assert contract.asa_amount == starting_price


def test_bid(context: AlgopyTestContext) -> None:
    # Arrange
    account = context.default_sender
    auction_end = context.any.uint64(min_value=int(time.time()) + 10_000)
    previous_bid = context.any.uint64(1, 100)
    pay_amount = context.any.uint64()

    contract = AuctionContract()
    contract.auction_end = auction_end
    contract.previous_bid = previous_bid
    pay = context.any.txn.payment(sender=account, amount=pay_amount)

    # Act
    contract.bid(pay=pay)

    # Assert
    assert contract.previous_bid == pay_amount
    assert contract.previous_bidder == account
    assert contract.claimable_amount[account] == pay_amount


def test_claim_bids(
    context: AlgopyTestContext,
) -> None:
    # Arrange
    account = context.any.account()
    contract = AuctionContract()
    claimable_amount = context.any.uint64()
    contract.claimable_amount[account] = claimable_amount
    contract.previous_bidder = account
    previous_bid = context.any.uint64(max_value=int(claimable_amount))
    contract.previous_bid = previous_bid

    # Act
    with context.txn.create_group(active_txn_overrides={"sender": account}):
        contract.claim_bids()

    # Assert
    expected_payment = claimable_amount - previous_bid
    last_inner_txn = context.txn.last_group.last_itxn.payment

    assert last_inner_txn.amount == expected_payment
    assert last_inner_txn.receiver == account
    assert contract.claimable_amount[account] == claimable_amount - expected_payment


def test_claim_asset(context: AlgopyTestContext) -> None:
    # Arrange
    context.ledger.patch_global_fields(latest_timestamp=context.any.uint64())
    contract = AuctionContract()
    contract.auction_end = context.any.uint64(1, 100)
    contract.previous_bidder = context.default_sender
    asa_amount = context.any.uint64(1000, 2000)
    contract.asa_amount = asa_amount
    asset = context.any.asset()

    # Act
    contract.claim_asset(asset)

    # Assert
    last_inner_txn = context.txn.last_group.last_itxn.asset_transfer
    assert last_inner_txn.xfer_asset == asset
    assert last_inner_txn.asset_close_to == context.default_sender
    assert last_inner_txn.asset_receiver == context.default_sender
    assert last_inner_txn.asset_amount == asa_amount


def test_delete_application(
    context: AlgopyTestContext,
) -> None:
    # Arrange
    account = context.any.account()

    # Act
    # setting sender will determine creator
    with context.txn.create_group(active_txn_overrides={"sender": account}):
        contract = AuctionContract()

    with context.txn.create_group(
        active_txn_overrides={"on_completion": algopy.OnCompleteAction.DeleteApplication}
    ):
        contract.delete_application()

    # Assert
    inner_transactions = context.txn.last_group.last_itxn.payment
    assert inner_transactions
    assert inner_transactions.type == algopy.TransactionType.Payment
    assert inner_transactions.receiver == account
    assert inner_transactions.close_remainder_to == account


@pytest.mark.usefixtures("context")
def test_clear_state_program() -> None:
    contract = AuctionContract()
    assert contract.clear_state_program()
