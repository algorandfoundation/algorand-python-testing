from collections.abc import Generator
from pathlib import Path

import algopy
import algopy_testing
import algosdk
import pytest
from algokit_utils.beta.algorand_client import AlgorandClient, AssetCreateParams, PayParams
from algopy import arc4
from algopy_testing.primitives.uint64 import UInt64
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.v2client.algod import AlgodClient

from tests.artifacts.Arc4ABIMethod.contract import (
    AnotherStruct,
    MyStruct,
    SignaturesContract,
    UInt8Array,
)
from tests.common import AVMInvoker, create_avm_invoker

# TODO: 1.0 execute this on AVM too

ARTIFACTS_DIR = Path(__file__).parent / ".." / "artifacts"
APP_SPEC = ARTIFACTS_DIR / "Arc4ABIMethod" / "data" / "SignaturesContract.arc32.json"


@pytest.fixture()
def get_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(APP_SPEC, algod_client)


@pytest.fixture()
def context() -> Generator[algopy_testing.AlgopyTestContext, None, None]:
    with algopy_testing.algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


def test_app_args_is_correct_with_simple_args(
    get_avm_result: AVMInvoker,
    context: algopy_testing.AlgopyTestContext,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act

    # ensure same execution in AVM runs without errors
    get_avm_result("sink", value="hello", arr=[1, 2])
    # then run inside emulator
    contract.sink(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("sink(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_alias(
    get_avm_result: AVMInvoker,
    context: algopy_testing.AlgopyTestContext,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    # ensure same execution in AVM runs without errors
    get_avm_result("alias", value="hello", arr=[1, 2])
    # then run inside emulator
    contract.sink2(arc4.String("hello"), UInt8Array(arc4.UInt8(1), arc4.UInt8(2)))

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("alias(string,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_txn(
    context: algopy_testing.AlgopyTestContext,
    get_avm_result: AVMInvoker,
    localnet_creator_address: str,
    algorand: AlgorandClient,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act

    get_avm_result(
        "with_txn",
        value="hello",
        pay=TransactionWithSigner(
            txn=algorand.transactions.payment(
                PayParams(
                    sender=localnet_creator_address,
                    receiver=localnet_creator_address,
                    amount=123,
                )
            ),
            signer=algorand.account.get_signer("default"),
        ),
        arr=[1, 2],
    )
    contract.with_txn(
        arc4.String("hello"),
        context.any.txn.payment(amount=algopy.UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # asset
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(3)]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_txn(string,pay,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_asset(
    context: algopy_testing.AlgopyTestContext,
    localnet_creator_address: str,
    algorand: AlgorandClient,
    get_avm_result: AVMInvoker,
) -> None:  # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    asa_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=localnet_creator_address,
            total=123,
        )
    )["confirmation"]["asset-index"]
    get_avm_result("with_asset", value="hello", asset=asa_id, arr=[1, 2])
    contract.with_asset(
        arc4.String("hello"),
        context.any.asset(total=UInt64(123)),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_asset(string,asset,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x00",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_account(
    context: algopy_testing.AlgopyTestContext,
    localnet_creator_address: str,
    get_avm_result: AVMInvoker,
) -> None:  # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    test_account = context.any.account(total_apps_created=UInt64(1))
    contract.with_acc(
        arc4.String("hello"),
        test_account,
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )
    get_avm_result(
        "with_acc",
        value="hello",
        acc=localnet_creator_address,
        arr=[1, 2],
        accounts=[localnet_creator_address, localnet_creator_address],
    )

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature("with_acc(string,account,uint8[])void").get_selector(),
        b"\x00\x05hello",
        b"\x01",
        b"\x00\x02\x01\x02",
    ]


def test_app_args_is_correct_with_application(
    context: algopy_testing.AlgopyTestContext,
    get_avm_result: AVMInvoker,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    self_app = context.get_app_for_contract(contract)
    other_app = context.any.application(id=1234)

    # act
    get_avm_result(
        "with_app",
        value="hello",
        app=get_avm_result.client.app_id,
        arr=[1, 2],
        foreign_apps=[get_avm_result.client.app_id, get_avm_result.client.app_id],
    )
    contract.with_app(
        arc4.String("hello"),
        other_app,
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.txn.last_active
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


def test_app_args_is_correct_with_complex(context: algopy_testing.AlgopyTestContext) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    account = context.any.account(balance=algopy.UInt64(123))
    txn = context.any.txn.transaction()
    struct = MyStruct(
        three=arc4.UInt128(3),
        four=arc4.UInt128(4),
        another_struct=AnotherStruct(one=arc4.UInt64(1), two=arc4.String("2")),
        another_struct_alias=AnotherStruct(one=arc4.UInt64(1), two=arc4.String("2")),
    )
    five = UInt8Array(arc4.UInt8(5))

    # act
    result = contract.complex_sig(struct, txn, account, five)

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature(
            "complex_sig(((uint64,string),(uint64,string),uint128,uint128),txn,account,uint8[])((uint64,string),((uint64,string),(uint64,string),uint128,uint128))"
        ).get_selector(),
        b"\x00$\x001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\n\x00\x012\x00\x00\x00\x00\x00\x00\x00\x01\x00\n\x00\x012",
        b"\x01",  # 0th index is the sender
        b"\x00\x01\x05",
    ]
    assert result[0].bytes == struct.another_struct.bytes
    assert result[1].bytes == struct.bytes


def test_prepare_txns_with_complex(
    context: algopy_testing.AlgopyTestContext,
    # get_avm_result: AVMInvoker,
    # algorand: AlgorandClient,
    # localnet_creator_address: str,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    account = context.any.account(balance=algopy.UInt64(123))
    txn = context.any.txn.transaction()
    struct = MyStruct(
        three=arc4.UInt128(3),
        four=arc4.UInt128(4),
        another_struct=AnotherStruct(one=arc4.UInt64(1), two=arc4.String("2")),
        another_struct_alias=AnotherStruct(one=arc4.UInt64(1), two=arc4.String("2")),
    )
    five = UInt8Array(arc4.UInt8(5))
    deferred_app_call = context.txn.defer_app_call(
        contract.complex_sig, struct, txn, account, five
    )

    # act
    # TODO: 1.0 Figure out proper way to pass encoded struct
    # get_avm_result(
    #     "complex_sig",
    #     struct1=struct.bytes.value,
    #     txn=TransactionWithSigner(
    #         txn=algorand.transactions.payment(
    #             PayParams(
    #                 sender=localnet_creator_address,
    #                 receiver=localnet_creator_address,
    #                 amount=123,
    #             )
    #         ),
    #         signer=algorand.account.get_signer("default"),
    #     ),
    #     acc=localnet_creator_address,
    #     five=[5],
    # )
    with context.txn.create_group(gtxns=[deferred_app_call]):
        result = deferred_app_call.submit()

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    assert app_args == [
        algosdk.abi.Method.from_signature(
            "complex_sig(((uint64,string),(uint64,string),uint128,uint128),txn,account,uint8[])((uint64,string),((uint64,string),(uint64,string),uint128,uint128))"
        ).get_selector(),
        b"\x00$\x001\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x03\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x04\x00\x00\x00\x00\x00\x00\x00\x01\x00\n\x00\x012\x00\x00\x00\x00\x00\x00\x00\x01\x00\n\x00\x012",
        b"\x01",  # 0th index is the sender
        b"\x00\x01\x05",
    ]
    assert result[0].bytes == struct.another_struct.bytes
    assert result[1].bytes == struct.bytes
