from collections.abc import Generator

import pytest
from algopy import Account, Bytes, UInt64
from algopy_testing import AlgopyTestContext, algopy_testing_context
from algopy_testing.models.asset import Asset, AssetFields


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as context:
        yield context


def test_asset_initialization() -> None:
    asset = Asset()
    assert asset.id == UInt64(0)

    asset = Asset(123)
    assert asset.id == UInt64(123)

    asset = Asset(UInt64(456))
    assert asset.id == UInt64(456)


def test_asset_int_property() -> None:
    asset = Asset(789)
    assert asset.int_ == 789


def test_asset_from_int() -> None:
    asset = Asset.from_int(101112)
    assert isinstance(asset, Asset)
    assert asset.id == UInt64(101112)


def test_asset_balance(context: AlgopyTestContext) -> None:
    account = context.any.account()
    asset = context.any.asset()
    context.ledger.update_account(
        account.public_key, opted_asset_balances={asset.id.value: UInt64(1000)}
    )

    assert asset.balance(account) == UInt64(1000)


def test_asset_balance_not_opted_in(context: AlgopyTestContext) -> None:
    account = context.any.account()
    asset = context.any.asset()

    with pytest.raises(ValueError, match="The asset is not opted into the account!"):
        asset.balance(account)


def test_asset_frozen() -> None:
    asset = Asset(1)
    account = Account()

    with pytest.raises(
        NotImplementedError,
        match="The 'frozen' method is being executed in a python testing context",
    ):
        asset.frozen(account)


def test_asset_attributes(context: AlgopyTestContext) -> None:
    asset_fields: AssetFields = {
        "total": UInt64(1000000),
        "decimals": UInt64(6),
        "default_frozen": False,
        "unit_name": Bytes(b"TEST"),
        "name": Bytes(b"Test Asset"),
        "url": Bytes(b"https://test.com"),
        "metadata_hash": Bytes(b"\x00" * 32),
        "manager": Account(),
        "reserve": Account(),
        "freeze": Account(),
        "clawback": Account(),
        "creator": Account(),
    }

    asset = context.any.asset(**asset_fields)

    for field, value in asset_fields.items():
        assert getattr(asset, field) == value


def test_asset_attribute_error(context: AlgopyTestContext) -> None:
    asset = context.any.asset()

    with pytest.raises(
        AttributeError, match="The value for 'non_existent' in the test context is None"
    ):
        asset.non_existent  # noqa: B018


def test_asset_not_in_context() -> None:
    asset = Asset(999)
    with pytest.raises(ValueError, match="Test context is not initialized!"):
        asset.total  # noqa: B018


def test_asset_equality() -> None:
    asset1 = Asset(1)
    asset2 = Asset(1)
    asset3 = Asset(2)

    assert asset1 == asset2
    assert asset1 != asset3
    assert asset1 == 1
    assert asset1 != 2


def test_asset_bool() -> None:
    assert bool(Asset(1)) is True
    assert bool(Asset(0)) is False


def test_asset_hash() -> None:
    asset1 = Asset(1)
    asset2 = Asset(1)
    asset3 = Asset(2)

    assert hash(asset1) == hash(asset2)
    assert hash(asset1) != hash(asset3)

    # Test that assets can be used as dictionary keys
    asset_dict = {asset1: "Asset 1", asset3: "Asset 3"}
    assert asset_dict[asset2] == "Asset 1"
    assert asset_dict[asset3] == "Asset 3"
