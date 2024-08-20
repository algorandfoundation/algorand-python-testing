from collections.abc import Generator

import algopy
import algosdk
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

from .contract import ProofOfAttendance


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


@pytest.fixture()
def contract(context: AlgopyTestContext) -> ProofOfAttendance:
    contract = ProofOfAttendance()
    contract.init(context.any.uint64(1, 100))

    return contract


def test_init(context: AlgopyTestContext) -> None:
    # Arrange
    contract = ProofOfAttendance()
    max_attendees = context.any.uint64(1, 100)

    # Act
    contract.init(max_attendees)

    # Assert
    assert contract.max_attendees == max_attendees


@pytest.mark.parametrize(
    ("confirm_attendance", "key_prefix"),
    [
        ("confirm_attendance", b""),
        ("confirm_attendance_with_box", b""),
        ("confirm_attendance_with_box_ref", b""),
        ("confirm_attendance_with_box_map", b"box_map"),
    ],
)
def test_confirm_attendance(
    context: AlgopyTestContext,
    contract: ProofOfAttendance,
    confirm_attendance: str,
    key_prefix: bytes,
) -> None:
    # Arrange

    # Act
    confirm = getattr(contract, confirm_attendance)
    confirm()

    # Assert
    assert context.ledger.get_box(
        contract, key_prefix + context.default_sender.bytes
    ) == algopy.op.itob(1001)


@pytest.mark.parametrize(
    ("claim_poa", "key_prefix"),
    [
        ("claim_poa", b""),
        ("claim_poa_with_box", b""),
        ("claim_poa_with_box_ref", b""),
        ("claim_poa_with_box_map", b"box_map"),
    ],
)
def test_claim_poa(
    context: AlgopyTestContext,
    contract: ProofOfAttendance,
    claim_poa: str,
    key_prefix: bytes,
) -> None:
    # Arrange
    dummy_poa = context.any.asset()
    opt_in_txn = context.any.txn.asset_transfer(
        sender=context.default_sender,
        asset_receiver=context.default_sender,
        asset_close_to=algopy.Account(algosdk.constants.ZERO_ADDRESS),
        rekey_to=algopy.Account(algosdk.constants.ZERO_ADDRESS),
        xfer_asset=dummy_poa,
        fee=algopy.UInt64(0),
        asset_amount=algopy.UInt64(0),
    )
    context.ledger.set_box(
        contract, key_prefix + context.default_sender.bytes, algopy.op.itob(dummy_poa.id)
    )

    # Act
    claim = getattr(contract, claim_poa)
    claim(opt_in_txn)

    # Assert
    axfer_itxn = context.txn.last_group.get_itxn_group(-1).asset_transfer(0)
    assert axfer_itxn.asset_receiver == context.default_sender
    assert axfer_itxn.asset_amount == algopy.UInt64(1)
