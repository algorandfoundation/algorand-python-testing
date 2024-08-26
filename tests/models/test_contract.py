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


class ContractARC4Create(
    algopy.ARC4Contract,
    state_totals=algopy.StateTotals(
        global_bytes=4,
        global_uints=5,
        local_bytes=6,
        local_uints=7,
    ),
):

    def __init__(self) -> None:
        self.creator = algopy.Txn.sender
        self._name = algopy.String("name")
        self._scratch_slots = algopy.UInt64()
        self._state_totals = algopy.UInt64()

    @algopy.arc4.abimethod(create="require")
    def create(self, val: algopy.UInt64) -> None:
        self.arg1 = val
        assert algopy.Global.current_application_id.global_num_bytes == 4
        assert algopy.Global.current_application_id.global_num_uint == 5
        assert algopy.Global.current_application_id.local_num_bytes == 6
        assert algopy.Global.current_application_id.local_num_uint == 7
        assert self._name == "name"
        assert self._scratch_slots == 0
        assert self._state_totals == 0


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
