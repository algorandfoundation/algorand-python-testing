from collections.abc import Generator

import algopy
import algosdk
import pytest
from algopy import arc4, gtxn
from algopy_testing.context import AlgopyTestContext, algopy_testing_context
from algopy_testing.models.contract import ARC4Contract

UInt8Array = arc4.DynamicArray[arc4.UInt8]


class SignaturesContract(ARC4Contract):
    @arc4.abimethod
    def sink(self, value: arc4.String, arr: UInt8Array) -> None:
        assert value
        assert arr

    @arc4.abimethod(name="alias")
    def sink2(self, value: arc4.String, arr: UInt8Array) -> None:
        assert value
        assert arr

    @arc4.abimethod
    def with_txn(
        self, value: arc4.String, acfg: gtxn.AssetConfigTransaction, arr: UInt8Array
    ) -> None:
        assert value
        assert arr
        assert acfg.total == 123

    @arc4.abimethod
    def with_asset(self, value: arc4.String, asset: algopy.Asset, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert asset.total == 123

    @arc4.abimethod
    def with_app(self, value: arc4.String, app: algopy.Application, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert app.id == 1234

    @arc4.abimethod
    def with_acc(self, value: arc4.String, acc: algopy.Account, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert acc.total_apps_created == 123


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


def test_app_args_is_correct_with_simple_args(context: AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()

    # act
    contract.sink(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.get_active_transaction()
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("sink(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_alias(context: AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()

    # act
    contract.sink2(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.get_active_transaction()
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("alias(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_txn(context: AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()

    # act
    contract.with_txn(
        arc4.String("hello"),
        context.any_asset_config_transaction(total=algopy.UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # asset
    txn = context.get_active_transaction()
    app_args = [txn.app_args(i) for i in range(3)]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_txn(string,acfg,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_asset(context: AlgopyTestContext) -> None:  # arrange
    contract = SignaturesContract()

    # act
    contract.with_asset(
        arc4.String("hello"),
        context.any_asset(total=algopy.UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.get_active_transaction()
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_asset(string,asset,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_application(context: AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    self_app = context.get_application_for_contract(contract)
    other_app = context.any_application(id=1234)

    # act
    contract.with_app(
        arc4.String("hello"),
        other_app,
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.get_active_transaction()
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
