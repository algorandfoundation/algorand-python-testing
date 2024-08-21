from collections.abc import Generator

import pytest
from algopy import Asset, UInt64, arc4
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import (
    DigitalMarketplace,
    ListingKey,
    ListingValue,
)

TEST_DECIMALS = 6


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


@pytest.fixture()
def contract(context: AlgopyTestContext) -> DigitalMarketplace:  # noqa: ARG001
    return DigitalMarketplace()


@pytest.fixture()
def test_asset(context: AlgopyTestContext) -> Asset:
    return context.any.asset(decimals=UInt64(TEST_DECIMALS))


@pytest.fixture()
def test_nonce(context: AlgopyTestContext) -> arc4.UInt64:
    return context.any.arc4.uint64()


def test_first_deposit(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    test_app = context.ledger.get_app(contract)

    # Act
    contract.first_deposit(
        mbr_pay=context.any.txn.payment(receiver=test_app.address, amount=UInt64(50500)),
        xfer=context.any.txn.asset_transfer(
            xfer_asset=test_asset,
            asset_receiver=test_app.address,
            asset_amount=UInt64(10),
        ),
        unitary_price=context.any.arc4.uint64(),
        nonce=test_nonce,
    )

    # Assert
    listing_key = ListingKey(
        owner=arc4.Address(str(context.default_sender)),
        asset=arc4.UInt64(test_asset.id),
        nonce=test_nonce,
    )
    listing_value = ListingValue.from_bytes(
        context.ledger.get_box(contract, b"listings" + listing_key.bytes)
    )
    assert listing_value.deposited == UInt64(10)


def test_deposit(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    test_app = context.ledger.get_app(contract)
    listing_key = ListingKey(
        owner=arc4.Address(str(context.default_sender)),
        asset=arc4.UInt64(test_asset.id),
        nonce=test_nonce,
    )
    contract.listings[listing_key] = ListingValue(
        deposited=arc4.UInt64(10),
        unitary_price=arc4.UInt64(10),
        bidder=arc4.Address(str(context.default_sender)),
        bid=arc4.UInt64(10),
        bid_unitary_price=arc4.UInt64(10),
    )

    # Act
    contract.deposit(
        xfer=context.any.txn.asset_transfer(
            xfer_asset=test_asset,
            asset_receiver=test_app.address,
            asset_amount=UInt64(10),
        ),
        nonce=test_nonce,
    )

    # Assert
    assert context.ledger.box_exists(contract, b"listings" + listing_key.bytes)


def test_set_price(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    test_unitary_price = context.any.arc4.uint64()
    listing_key = ListingKey(
        owner=arc4.Address(str(context.default_sender)),
        asset=arc4.UInt64(test_asset.id),
        nonce=test_nonce,
    )
    contract.listings[listing_key] = ListingValue(
        deposited=arc4.UInt64(10),
        unitary_price=arc4.UInt64(10),
        bidder=arc4.Address(str(context.default_sender)),
        bid=arc4.UInt64(10),
        bid_unitary_price=arc4.UInt64(10),
    )

    # Act
    contract.set_price(asset=test_asset, nonce=test_nonce, unitary_price=test_unitary_price)

    # Assert
    updated_listing = ListingValue.from_bytes(
        context.ledger.get_box(contract, b"listings" + listing_key.bytes)
    )
    assert updated_listing.unitary_price == test_unitary_price


def test_buy(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    test_owner = arc4.Address(str(context.default_sender))
    test_unitary_price = context.any.arc4.uint64(max_value=int(10e6))
    initial_deposit = context.any.arc4.uint64()
    test_buy_quantity = context.any.arc4.uint64(max_value=int(1e6))

    listing_key = ListingKey(owner=test_owner, asset=arc4.UInt64(test_asset.id), nonce=test_nonce)
    contract.listings[listing_key] = ListingValue(
        deposited=initial_deposit,
        unitary_price=test_unitary_price,
        bidder=arc4.Address(),
        bid=arc4.UInt64(0),
        bid_unitary_price=arc4.UInt64(0),
    )

    # Act
    contract.buy(
        owner=test_owner,
        asset=test_asset,
        nonce=test_nonce,
        buy_pay=context.any.txn.payment(
            receiver=context.default_sender,
            amount=contract.quantity_price(
                quantity=test_buy_quantity.native,
                price=test_unitary_price.native,
                asset_decimals=test_asset.decimals,
            ),
        ),
        quantity=test_buy_quantity.native,
    )

    # Assert
    updated_listing = ListingValue.from_bytes(
        context.ledger.get_box(contract, b"listings" + listing_key.bytes)
    )
    assert updated_listing.deposited == initial_deposit.native - test_buy_quantity.native
    assert (
        context.txn.last_group.get_itxn_group(0).asset_transfer(0).asset_receiver
        == context.default_sender
    )


def test_withdraw(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    test_owner = arc4.Address(str(context.default_sender))
    initial_deposit = context.any.arc4.uint64(min_value=1)
    test_unitary_price = context.any.arc4.uint64()

    listing_key = ListingKey(owner=test_owner, asset=arc4.UInt64(test_asset.id), nonce=test_nonce)
    contract.listings[listing_key] = ListingValue(
        deposited=initial_deposit,
        unitary_price=test_unitary_price,
        bidder=arc4.Address(),
        bid=arc4.UInt64(0),
        bid_unitary_price=arc4.UInt64(0),
    )

    # Act
    contract.withdraw(asset=test_asset, nonce=test_nonce)

    # Assert
    assert not context.ledger.box_exists(contract, b"listings" + listing_key.bytes)
    assert len(context.txn.last_group.itxn_groups) == 2

    payment_txn = context.txn.last_group.get_itxn_group(0).payment(0)
    assert payment_txn.receiver == test_owner.native
    assert payment_txn.amount == contract.listings_box_mbr()

    asset_transfer_txn = context.txn.last_group.get_itxn_group(1).asset_transfer(0)
    assert asset_transfer_txn.xfer_asset == test_asset
    assert asset_transfer_txn.asset_receiver == test_owner.native
    assert asset_transfer_txn.asset_amount == initial_deposit.native


def test_bid(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    app = context.ledger.get_app(contract)
    owner = arc4.Address(str(context.default_sender))
    initial_price = context.any.arc4.uint64(max_value=int(10e6))
    initial_deposit = context.any.arc4.uint64(max_value=int(1e6))

    listing_key = ListingKey(owner=owner, asset=arc4.UInt64(test_asset.id), nonce=test_nonce)
    contract.listings[listing_key] = ListingValue(
        deposited=initial_deposit,
        unitary_price=initial_price,
        bidder=arc4.Address(),
        bid=arc4.UInt64(0),
        bid_unitary_price=arc4.UInt64(0),
    )

    bidder = context.any.account()
    bid_quantity = context.any.arc4.uint64(max_value=int(initial_deposit.native))
    bid_price = context.any.arc4.uint64(
        min_value=int(initial_price.native) + 1, max_value=int(10e6)
    )
    bid_amount = contract.quantity_price(
        bid_quantity.native, bid_price.native, test_asset.decimals
    )

    # Act
    with context.txn.create_group(active_txn_overrides={"sender": bidder}):
        contract.bid(
            owner=owner,
            asset=test_asset,
            nonce=test_nonce,
            bid_pay=context.any.txn.payment(
                sender=bidder, receiver=app.address, amount=bid_amount
            ),
            quantity=bid_quantity,
            unitary_price=bid_price,
        )

    # Assert
    updated_listing = contract.listings[listing_key]
    assert updated_listing.bidder == arc4.Address(str(bidder))
    assert updated_listing.bid == bid_quantity
    assert updated_listing.bid_unitary_price == bid_price


def test_accept_bid(
    context: AlgopyTestContext,
    contract: DigitalMarketplace,
    test_asset: Asset,
    test_nonce: arc4.UInt64,
) -> None:
    # Arrange
    owner = context.default_sender
    initial_deposit = context.any.arc4.uint64(min_value=1, max_value=int(1e6))
    bid_quantity = context.any.arc4.uint64(max_value=int(initial_deposit.native))
    bid_price = context.any.arc4.uint64(max_value=int(10e6))
    bidder = context.any.account()

    listing_key = ListingKey(
        owner=arc4.Address(str(owner)),
        asset=arc4.UInt64(test_asset.id),
        nonce=test_nonce,
    )
    contract.listings[listing_key] = ListingValue(
        deposited=initial_deposit,
        unitary_price=context.any.arc4.uint64(),
        bidder=arc4.Address(str(bidder)),
        bid=bid_quantity,
        bid_unitary_price=bid_price,
    )

    min_quantity = min(initial_deposit.native, bid_quantity.native)
    expected_payment = contract.quantity_price(
        min_quantity,
        bid_price.native,
        asset_decimals=test_asset.decimals,
    )

    # Act
    contract.accept_bid(asset=test_asset, nonce=test_nonce)

    # Assert
    updated_listing = contract.listings[listing_key]
    assert updated_listing.deposited == initial_deposit.native - min_quantity

    assert len(context.txn.last_group.itxn_groups) == 2

    payment_txn = context.txn.last_group.get_itxn_group(0).payment(0)
    assert payment_txn.receiver == owner
    assert payment_txn.amount == expected_payment

    asset_transfer_txn = context.txn.last_group.get_itxn_group(1).asset_transfer(0)
    assert asset_transfer_txn.xfer_asset == test_asset
    assert asset_transfer_txn.asset_receiver == bidder
    assert asset_transfer_txn.asset_amount == min_quantity
