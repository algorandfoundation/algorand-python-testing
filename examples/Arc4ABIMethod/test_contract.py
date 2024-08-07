from collections.abc import Generator

import algopy
import algopy_testing
import algosdk
import pytest
from algopy import arc4

from .contract import SignaturesContract, UInt8Array

# TODO: execute this on AVM too


@pytest.fixture()
def context() -> Generator[algopy_testing.AlgopyTestContext, None, None]:
    with algopy_testing.algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


def test_app_args_is_correct_with_simple_args(context: algopy_testing.AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    contract.sink(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.last_active_txn
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("sink(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_alias(context: algopy_testing.AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    contract.sink2(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.last_active_txn
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("alias(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_txn(context: algopy_testing.AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    contract.with_txn(
        arc4.String("hello"),
        context.any_asset_config_transaction(total=algopy.UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # asset
    txn = context.last_active_txn
    app_args = [txn.app_args(i) for i in range(3)]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_txn(string,acfg,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_asset(
    context: algopy_testing.AlgopyTestContext,
) -> None:  # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    contract.with_asset(
        arc4.String("hello"),
        context.any_asset(total=algopy.UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.last_active_txn
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_asset(string,asset,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_application(context: algopy_testing.AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    self_app = context.get_application_for_contract(contract)
    other_app = context.any_application(id=1234)

    # act
    contract.with_app(
        arc4.String("hello"),
        other_app,
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.last_active_txn
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    app_foreign_apps = [txn.apps(i) for i in range(int(txn.num_apps))]
    assert app_args == [
        algosdk.abi.Method.from_signature(
            "with_app(string,application,uint8[])void"
        ).get_selector(),
        b"\x00\x05hello",
        b"\x01",  # 0th index is the app being called
        b"\x00\x02\x01\x02",
    ]
    assert app_foreign_apps == [
        self_app,
        other_app,
    ]
