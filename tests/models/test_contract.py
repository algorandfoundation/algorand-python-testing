from __future__ import annotations

import typing

import algopy
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

if typing.TYPE_CHECKING:
    from collections.abc import Iterator


class ContractTxnInit(algopy.Contract):

    def __init__(self) -> None:
        self.arg1 = algopy.Txn.app_args(0) if algopy.Txn.num_app_args else algopy.Bytes()
        self.creator = algopy.Txn.sender

    def approval_program(self) -> bool:
        return True

    def clear_state_program(self) -> bool:
        return True


class ContractARC4Create(algopy.ARC4Contract):

    def __init__(self) -> None:
        self.creator = algopy.Txn.sender

    @algopy.arc4.abimethod(create="require")
    def create(self, val: algopy.UInt64) -> None:
        self.arg1 = val


@pytest.fixture()
def context() -> Iterator[AlgopyTestContext]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_contract_with_txn_in_init(context: AlgopyTestContext) -> None:
    # arrange
    arg1 = context.any.bytes(5)
    sender = context.any.account()

    # act
    with context.txn.create_group(
        active_txn_overrides={
            "app_args": [arg1],
            "sender": sender,
        }
    ):
        contract = ContractTxnInit()

    # assert
    assert contract.arg1 == arg1
    assert contract.creator == sender


def test_contract_with_txn_in_init_no_overrides(context: AlgopyTestContext) -> None:
    # act
    contract = ContractTxnInit()

    # assert
    assert contract.arg1 == b""
    assert contract.creator == context.default_sender


def test_contract_with_arc4_create(context: AlgopyTestContext) -> None:
    # arrange
    arg1 = context.any.uint64()
    sender = context.any.account()

    # act
    with context.txn.create_group(
        active_txn_overrides={
            "sender": sender,
        }
    ):
        contract = ContractARC4Create()
        contract.create(arg1)

    # assert
    assert contract.arg1 == arg1
    assert contract.creator == sender


def test_contract_with_arc4_create_no_overrides(context: AlgopyTestContext) -> None:
    from _algopy_testing.context_helpers import lazy_context

    # arrange
    arg1 = context.any.uint64()

    # act
    contract = ContractARC4Create()

    # assert
    app_data = lazy_context.get_app_data(contract)
    assert app_data.is_creating

    # act
    contract.create(arg1)

    # assert
    assert not app_data.is_creating
    assert contract.arg1 == arg1
    assert contract.creator == context.default_sender
