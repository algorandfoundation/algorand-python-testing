import typing

import algopy.gtxn
from algopy import Account, Application, ARC4Contract, Asset, FixedBytes, Txn, arc4, gtxn, op

UInt8Array = arc4.DynamicArray[arc4.UInt8]
MyAlias: typing.TypeAlias = arc4.BigUIntN[typing.Literal[128]]


class AnotherStruct(arc4.Struct):
    one: arc4.UInt64
    two: arc4.String


MyStructAlias = AnotherStruct


class MyStruct(arc4.Struct):
    another_struct: AnotherStruct
    another_struct_alias: MyStructAlias
    three: arc4.UInt128
    four: MyAlias


class SignaturesContract(ARC4Contract):
    @arc4.abimethod(create="require")
    def create(self) -> None:
        app_txn = gtxn.ApplicationCallTransaction(0)
        assert op.Global.current_application_id != 0, "expected global to have app id"
        assert (
            op.Global.current_application_address != op.Global.zero_address
        ), "expected global to have app address"
        assert app_txn.app_id == 0, "expected txn to have 0"
        assert Txn.application_id == 0, "expected txn to have 0"

    @arc4.abimethod(validate_encoding="unsafe_disabled")
    def sink(
        self, value: arc4.String, arr: UInt8Array, fixed_bytes: FixedBytes[typing.Literal[4]]
    ) -> None:
        assert value
        assert arr
        assert fixed_bytes.length == 4

    @arc4.abimethod(name="alias")
    def sink2(self, value: arc4.String, arr: UInt8Array) -> None:
        assert value
        assert arr

    @arc4.abimethod
    def with_txn(self, value: arc4.String, pay: gtxn.PaymentTransaction, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert pay.group_index == 0
        assert Txn.group_index == 1
        assert pay.amount == 123

    @arc4.abimethod(resource_encoding="index")
    def with_asset(self, value: arc4.String, asset: Asset, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert asset.total == 123
        assert Txn.assets(0) == asset

    @arc4.abimethod(resource_encoding="index")
    def with_app(
        self, value: arc4.String, app: Application, app_id: arc4.UInt64, arr: UInt8Array
    ) -> None:
        assert value
        assert arr
        assert app.id == app_id, "expected app id to match provided app id"
        assert app.creator == op.Global.creator_address, "expected other app to have same creator"
        app_txn = gtxn.ApplicationCallTransaction(0)
        assert app_txn.apps(0) == op.Global.current_application_id
        assert Txn.applications(0) == op.Global.current_application_id
        assert app_txn.apps(1) == app
        assert Txn.applications(1) == app

    @arc4.abimethod(resource_encoding="index")
    def with_acc(self, value: arc4.String, acc: Account, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert acc.balance == acc.min_balance + 1234
        assert Txn.accounts(0) == Txn.sender
        assert Txn.accounts(1) == acc

    @arc4.abimethod(resource_encoding="index")
    def complex_sig(
        self, struct1: MyStruct, txn: algopy.gtxn.Transaction, acc: Account, five: UInt8Array
    ) -> tuple[MyStructAlias, MyStruct]:
        five.validate()
        assert Txn.num_app_args == 4
        # struct
        assert struct1.another_struct.one == 1
        assert struct1.another_struct.two == "2"
        assert struct1.another_struct_alias.one == 1
        assert struct1.another_struct_alias.two == "2"
        assert struct1.three == 3
        assert struct1.four == 4

        # txn
        assert txn.group_index == Txn.group_index - 1

        # acc
        assert Txn.application_args(2) == arc4.UInt8(1).bytes  # acc array ref
        assert acc.balance == acc.min_balance + 1234
        assert five[0] == 5

        return struct1.another_struct.copy(), struct1.copy()

    @arc4.abimethod(
        resource_encoding="index",
    )
    def echo_resource_by_index(
        self, asset: Asset, app: Application, acc: Account
    ) -> tuple[Asset, Application, Account]:
        asset_idx = op.btoi(Txn.application_args(1))
        assert asset == Txn.assets(asset_idx), "expected asset to be passed by index"
        app_idx = op.btoi(Txn.application_args(2))
        assert app == Txn.applications(app_idx), "expected application to be passed by index"
        acc_idx = op.btoi(Txn.application_args(3))
        assert acc == Txn.accounts(acc_idx), "expected account to be passed by index"
        return asset, app, acc

    @arc4.abimethod(
        resource_encoding="value",
    )
    def echo_resource_by_value(
        self, asset: Asset, app: Application, acc: Account
    ) -> tuple[Asset, Application, Account]:
        acc.validate()
        asset_id = op.btoi(Txn.application_args(1))
        assert asset.id == asset_id, "expected asset to be passed by value"
        app_id = op.btoi(Txn.application_args(2))
        assert app.id == app_id, "expected application to be passed by value"
        address = Txn.application_args(3)
        assert acc.bytes == address, "expected account to be passed by value"
        return asset, app, acc
