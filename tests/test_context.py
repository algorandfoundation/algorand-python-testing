import typing
from contextlib import ExitStack

import algopy.itxn
import algosdk
import pytest
from _algopy_testing import algopy_testing_context, arc4
from _algopy_testing.constants import MAX_UINT8, MAX_UINT16, MAX_UINT32, MAX_UINT64, MAX_UINT512
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.context_helpers.txn_context import TransactionGroup
from _algopy_testing.itxn import PaymentInnerTransaction
from algopy import Bytes, TransactionType, UInt64

from tests.artifacts.Arc4InnerTxns.contract import Arc4InnerTxnsContract
from tests.artifacts.GlobalStateValidator.contract import GlobalStateValidator

_ARC4_PREFIX_LEN = 2


@pytest.fixture()
def context() -> typing.Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_patch_global_fields() -> None:
    with algopy_testing_context() as context:
        context.ledger.patch_global_fields(min_txn_fee=UInt64(100), min_balance=UInt64(10))
        assert context.ledger._global_fields["min_txn_fee"] == 100
        assert context.ledger._global_fields["min_balance"] == 10

        with pytest.raises(ValueError, match="InvalidField"):
            context.ledger.patch_global_fields(InvalidField=123)  # type: ignore   # noqa: PGH003


def test_account_management() -> None:
    with algopy_testing_context() as context:
        address: str = algosdk.account.generate_account()[1]
        account = context.any.account(address=address, balance=UInt64(1000))
        assert context.ledger.get_account(account.public_key).balance == 1000

        context.ledger.update_account(account.public_key, balance=UInt64(2000))
        assert context.ledger.get_account(account.public_key).balance == 2000

        with pytest.raises(AssertionError, match="Invalid Algorand address"):
            context.ledger.update_account("invalid_address", balance=UInt64(2000))


def test_asset_management() -> None:
    with algopy_testing_context() as context:
        asset = context.any.asset(name=Bytes(b"TestAsset"), total=UInt64(1000))
        assert context.ledger.get_asset(int(asset.id)).name == b"TestAsset"

        context.ledger.update_asset(int(asset.id), name=Bytes(b"UpdatedAsset"))
        assert context.ledger.get_asset(int(asset.id)).name == b"UpdatedAsset"

        with pytest.raises(ValueError, match="Asset not found"):
            context.ledger.update_asset(9999, name=Bytes(b"NonExistentAsset"))


def test_application_management() -> None:
    with algopy_testing_context() as context:
        app = context.any.application(
            approval_program=Bytes(b"TestApp"),
            clear_state_program=Bytes(b"TestClear"),
        )

        application = context.ledger.get_app(app.id)

        assert application.approval_program == b"TestApp"
        assert application.clear_state_program == b"TestClear"


def test_transaction_group_management() -> None:
    with algopy_testing_context() as context:
        txn1 = context.any.txn.payment(
            sender=context.default_sender,
            receiver=context.default_sender,
            amount=UInt64(1000),
        )
        txn2 = context.any.txn.payment(
            sender=context.default_sender,
            receiver=context.default_sender,
            amount=UInt64(2000),
        )
        with context.txn.create_group([txn1, txn2]):
            assert context.txn._active_group is not None
            assert len(context.txn._active_group.txns) == 2
        assert context.txn._active_group is None
        assert len(context.txn.last_group.txns) == 2

        context.clear_transaction_context()
        with pytest.raises(ValueError, match="No group transactions"):
            assert context.txn.last_group


def test_last_itxn_access() -> None:
    with algopy_testing_context() as context:
        contract = Arc4InnerTxnsContract()
        dummy_asset = context.any.asset()
        contract.opt_in_dummy_asset(dummy_asset)

        assert len(context.txn.last_group.get_itxn_group(0)) == 1
        itxn: algopy.itxn.AssetTransferInnerTransaction = (
            context.txn.last_group.last_itxn.asset_transfer
        )
        app = context.ledger.get_app(contract)
        assert itxn.asset_sender == app.address
        assert itxn.asset_receiver == app.address
        assert itxn.asset_amount == UInt64(0)
        assert itxn.type == TransactionType.AssetTransfer


def test_context_reset() -> None:
    with algopy_testing_context() as context:
        context.any.account(balance=UInt64(1000))
        context.any.asset(name=Bytes(b"TestAsset"), total=UInt64(1000))
        context.any.application(
            approval_program=Bytes(b"TestApp"),
            clear_state_program=Bytes(b"TestClear"),
        )
        context.reset()
        assert len(context.ledger._account_data) == 0
        assert len(context.ledger._asset_data) == 0
        assert len(context.ledger._app_data) == 0
        with pytest.raises(ValueError, match="No group transactions found"):
            assert context.txn.last_group
        assert len(context.txn._groups) == 0
        assert context.ledger._get_next_asset_id() == 1001
        assert context.ledger._get_next_app_id() == 1001


def test_algopy_testing_context() -> None:
    with algopy_testing_context() as context:
        assert isinstance(context, AlgopyTestContext)
        assert context.ledger.get_account(
            context.default_sender.public_key
        )  # reserved for default creator
        account = context.any.account(balance=UInt64(1000))
        assert context.ledger.get_account(account.public_key)

    # When accessed outside of a context manager, it should raise an error
    with pytest.raises(ValueError, match="Test context is not initialized!"):
        context = lazy_context.value


def test_get_last_submitted_itxn_loader() -> None:
    with algopy_testing_context() as context:
        itxn1 = PaymentInnerTransaction(
            sender=context.default_sender,
            receiver=context.default_sender,
            amount=UInt64(1000),
        )
        itxn2 = PaymentInnerTransaction(
            sender=context.default_sender,
            receiver=context.default_sender,
            amount=UInt64(2000),
        )
        group = TransactionGroup([], 0)
        group._add_itxn_group([itxn1, itxn2])
        last_itxn = group.last_itxn.payment
        assert last_itxn.amount == 2000


def test_misc_global_state_access() -> None:
    with algopy_testing_context() as _:
        contract = GlobalStateValidator()
        contract.validate_g_args(arc4.UInt64(1), arc4.String("TestAsset"))


@pytest.mark.parametrize(
    ("method", "type_", "min_val", "max_val"),
    [
        ("uint8", arc4.UInt8, 0, MAX_UINT8),
        ("uint16", arc4.UInt16, 0, MAX_UINT16),
        ("uint32", arc4.UInt32, 0, MAX_UINT32),
        ("uint64", arc4.UInt64, 0, MAX_UINT64),
        ("biguint128", arc4.UInt128, 0, (1 << 128) - 1),
        ("biguint256", arc4.UInt256, 0, (1 << 256) - 1),
        ("biguint512", arc4.UInt512, 0, MAX_UINT512),
    ],
)
def test_arc4_uint_methods(method: str, type_: type, min_val: int, max_val: int) -> None:
    with algopy_testing_context() as context:
        func = getattr(context.any.arc4, method)
        value = func(min_val, max_val)
        assert isinstance(value, type_)
        assert min_val <= value.native <= max_val  # type: ignore[attr-defined]

        with pytest.raises(ValueError):  # noqa: PT011
            func(max_val + 1)


def test_arc4_any_address() -> None:
    with algopy_testing_context() as context:
        address = context.any.arc4.address()
        assert isinstance(address, arc4.Address)
        assert len(address.bytes) == 32


@pytest.mark.parametrize(
    ("method", "type_", "bit_length", "expected_length"),
    [
        ("dynamic_bytes", arc4.DynamicBytes, 64, 8),
        ("dynamic_bytes", arc4.DynamicBytes, 20, 3),
        ("string", arc4.String, 32, 4),
        ("string", arc4.String, 20, 3),
    ],
)
def test_arc4_variable_length_methods(
    method: str, type_: type, bit_length: int, expected_length: int
) -> None:
    with algopy_testing_context() as context:
        func = getattr(context.any.arc4, method)
        value = func(bit_length)
        assert isinstance(value, type_)
        assert len(value.bytes) == expected_length + _ARC4_PREFIX_LEN  # type: ignore[attr-defined]


def test_nested_contexts_exception() -> None:
    with ExitStack() as stack:
        _ = stack.enter_context(algopy_testing_context())
        with pytest.raises(
            RuntimeError, match="Nested `algopy_testing_context`s are not allowed."
        ):
            __ = stack.enter_context(algopy_testing_context())


def test_nested_create_group(context: AlgopyTestContext) -> None:
    with (
        pytest.raises(RuntimeError, match="Nested `create_group` calls are not allowed."),
        context.txn.create_group(),
        context.txn.create_group(),
    ):
        pass


def test_sequential_create_group(context: AlgopyTestContext) -> None:
    with context.txn.create_group(gtxns=[context.any.txn.payment()]):
        pass

    with context.txn.create_group(gtxns=[context.any.txn.application_call()]):
        pass

    assert len(context.txn._groups) == 2
