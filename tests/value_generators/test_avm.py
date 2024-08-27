from collections.abc import Iterator

import algopy
import algosdk
import pytest
from _algopy_testing import algopy_testing_context
from _algopy_testing.constants import MAX_BYTES_SIZE, MAX_UINT64
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String


@pytest.fixture()
def context() -> Iterator[AlgopyTestContext]:
    with algopy_testing_context() as ctx:
        yield ctx


def assert_value_in_range(value: int | object, min_val: int, max_val: int) -> None:
    assert min_val <= value <= max_val  # type: ignore[operator]


def assert_length(value: bytes | str | String | Bytes, expected_length: int) -> None:
    if isinstance(value, bytes | Bytes):
        assert len(value) == expected_length
    else:
        assert len(str(value)) == expected_length


@pytest.mark.parametrize(
    ("method", "type_", "min_val", "max_val"),
    [
        ("uint64", algopy.UInt64, 0, MAX_UINT64),
    ],
)
def test_avm_uint64_generator(
    context: AlgopyTestContext, method: str, type_: type, min_val: int, max_val: int
) -> None:
    func = getattr(context.any, method)
    value = func(min_val, max_val)
    assert isinstance(value, type_)
    assert_value_in_range(value, min_val, max_val)

    with pytest.raises(ValueError, match="max_value must be less than or equal to MAX_UINT64"):
        func(max_value=max_val + 1)

    with pytest.raises(ValueError, match="min_value must be less than or equal to max_value"):
        func(min_value=max_val + 1)

    with pytest.raises(
        ValueError, match="min_value and max_value must be greater than or equal to 0"
    ):
        func(min_value=-1)


@pytest.mark.parametrize("length", [None, 10, MAX_BYTES_SIZE])
def test_avm_bytes_generator(context: AlgopyTestContext, length: int | None) -> None:
    value = context.any.bytes(length) if length else context.any.bytes()
    assert isinstance(value, algopy.Bytes)
    assert_length(value, length or MAX_BYTES_SIZE)


@pytest.mark.parametrize("length", [None, 10, MAX_BYTES_SIZE])
def test_avm_string_generator(context: AlgopyTestContext, length: int | None) -> None:
    value = context.any.string(length) if length else context.any.string()
    assert isinstance(value, algopy.String)
    assert_length(value, length or MAX_BYTES_SIZE)


def test_avm_account_generator(context: AlgopyTestContext) -> None:
    # funded
    account = context.any.account(balance=algopy.UInt64(123))
    assert isinstance(account, algopy.Account)
    assert context.ledger.account_is_funded(account.public_key)

    # unfunded
    custom_address = algosdk.account.generate_account()[1]
    account = context.any.account(address=custom_address)
    assert isinstance(account, algopy.Account)
    assert account.public_key == custom_address
    assert not context.ledger.account_is_funded(custom_address)

    # duplicate
    with pytest.raises(ValueError, match="Account with such address already exists"):
        context.any.account(address=custom_address)


def test_avm_asset_generator(context: AlgopyTestContext) -> None:
    asset = context.any.asset()
    assert isinstance(asset, algopy.Asset)
    assert context.ledger.asset_exists(int(asset.id))

    custom_id = 1000
    asset = context.any.asset(asset_id=custom_id)
    assert isinstance(asset, algopy.Asset)
    assert int(asset.id) == custom_id
    assert context.ledger.asset_exists(custom_id)

    with pytest.raises(ValueError, match="Asset with such ID already exists"):
        context.any.asset(asset_id=custom_id)


def test_avm_application_generator(context: AlgopyTestContext) -> None:
    app = context.any.application()
    assert isinstance(app, algopy.Application)
    assert context.ledger.app_exists(int(app.id))

    custom_id = 1000
    app = context.any.application(id=custom_id)
    assert isinstance(app, algopy.Application)
    assert int(app.id) == custom_id
    assert context.ledger.app_exists(custom_id)

    with pytest.raises(ValueError, match="Application id .* has already been configured"):
        context.any.application(id=custom_id)
