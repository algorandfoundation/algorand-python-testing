from collections.abc import Generator
from pathlib import Path

import _algopy_testing
import algokit_utils
import algopy
import algosdk
import pytest
from algokit_utils.beta.algorand_client import AlgorandClient, AssetCreateParams, PayParams
from algopy import arc4
from algosdk.atomic_transaction_composer import TransactionWithSigner
from algosdk.v2client.algod import AlgodClient

from tests.artifacts.Arc4ABIMethod.contract import (
    AnotherStruct,
    MyStruct,
    SignaturesContract,
    UInt8Array,
)
from tests.common import AVMInvoker, create_avm_invoker

ARTIFACTS_DIR = Path(__file__).parent / ".." / "artifacts"
APP_SPEC = ARTIFACTS_DIR / "Arc4ABIMethod" / "data" / "SignaturesContract.arc32.json"
_FUNDED_ACCOUNT_SPENDING = 1234


@pytest.fixture()
def get_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(APP_SPEC, algod_client)


@pytest.fixture()
def context() -> Generator[_algopy_testing.AlgopyTestContext, None, None]:
    with _algopy_testing.algopy_testing_context() as ctx:
        yield ctx


@pytest.fixture()
def funded_account(algod_client: AlgodClient, context: _algopy_testing.AlgopyTestContext) -> str:
    pk, address = algosdk.account.generate_account()
    assert isinstance(address, str)
    algokit_utils.ensure_funded(
        algod_client,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=address,
            min_spending_balance_micro_algos=_FUNDED_ACCOUNT_SPENDING,
        ),
    )

    # ensure context has the same account with matching balance
    context.any.account(address, balance=algopy.Global.min_balance + _FUNDED_ACCOUNT_SPENDING)
    return address


@pytest.fixture()
def other_app_id(algod_client: AlgodClient, context: _algopy_testing.AlgopyTestContext) -> int:
    second_invoker = create_avm_invoker(APP_SPEC, algod_client)
    client = second_invoker.client
    app_id = client.app_id

    # ensure context also has app with this id
    context.any.application(app_id)
    return app_id


def test_app_args_is_correct_with_simple_args(
    get_avm_result: AVMInvoker,
    context: _algopy_testing.AlgopyTestContext,
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
    context: _algopy_testing.AlgopyTestContext,
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
    context: _algopy_testing.AlgopyTestContext,
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
    context: _algopy_testing.AlgopyTestContext,
    localnet_creator_address: str,
    algorand: AlgorandClient,
    get_avm_result: AVMInvoker,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    asa_id = algorand.send.asset_create(
        AssetCreateParams(
            sender=localnet_creator_address,
            total=123,
        )
    )["confirmation"]["asset-index"]

    # act
    get_avm_result("with_asset", value="hello", asset=asa_id, arr=[1, 2])
    contract.with_asset(
        arc4.String("hello"),
        context.any.asset(total=algopy.UInt64(123)),
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
    context: _algopy_testing.AlgopyTestContext,
    funded_account: str,
    get_avm_result: AVMInvoker,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    # act
    contract.with_acc(
        arc4.String("hello"),
        context.ledger.get_account(funded_account),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )
    get_avm_result(
        "with_acc",
        value="hello",
        acc=funded_account,
        arr=[1, 2],
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
    context: _algopy_testing.AlgopyTestContext,
    other_app_id: int,
    get_avm_result: AVMInvoker,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    self_app = context.ledger.get_app(contract)

    # act
    get_avm_result(
        "with_app",
        value="hello",
        app=other_app_id,
        app_id=other_app_id,
        arr=[1, 2],
    )
    contract.with_app(
        arc4.String("hello"),
        context.ledger.get_app(other_app_id),
        arc4.UInt64(other_app_id),
        UInt8Array(arc4.UInt8(1), arc4.UInt8(2)),
    )

    # assert
    txn = context.txn.last_active
    app_args = [txn.app_args(i) for i in range(int(txn.num_app_args))]
    app_foreign_apps = [txn.apps(i).id for i in range(int(txn.num_apps))]
    assert app_args == [
        algosdk.abi.Method.from_signature(
            "with_app(string,application,uint64,uint8[])void"
        ).get_selector(),
        b"\x00\x05hello",
        b"\x01",  # 0th index is the app being called
        other_app_id.to_bytes(length=8),  # app id as bytes
        b"\x00\x02\x01\x02",
    ]
    assert app_foreign_apps == [
        self_app.id,
        other_app_id,
    ]


def test_app_args_is_correct_with_complex(
    context: _algopy_testing.AlgopyTestContext,
    funded_account: str,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    account = context.ledger.get_account(funded_account)
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
    context: _algopy_testing.AlgopyTestContext,
    get_avm_result: AVMInvoker,
    algorand: AlgorandClient,
    localnet_creator_address: str,
    funded_account: str,
) -> None:
    # arrange
    contract = SignaturesContract()
    contract.create()

    account = context.ledger.get_account(funded_account)
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
    get_avm_result(
        "complex_sig",
        struct1=((1, "2"), (1, "2"), 3, 4),
        txn=TransactionWithSigner(
            txn=algorand.transactions.payment(
                PayParams(
                    sender=localnet_creator_address,
                    receiver=localnet_creator_address,
                    amount=123,
                )
            ),
            signer=algorand.account.get_signer("default"),
        ),
        acc=funded_account,
        five=[5],
    )
    with context.txn.create_group(
        gtxns=[context.any.txn.payment(), deferred_app_call, context.any.txn.payment()]
    ):
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
