import typing

import algopy.gtxn
from algopy import Account, Application, ARC4Contract, Asset, Txn, arc4, gtxn, op

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
        assert op.Global.current_application_id == 0
        assert app_txn.app_id == 0
        assert Txn.application_id == 0

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
        assert acfg.group_index == 0
        assert Txn.group_index == 1
        assert acfg.total == 123

    @arc4.abimethod
    def with_asset(self, value: arc4.String, asset: Asset, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert asset.total == 123
        assert Txn.assets(0) == asset

    @arc4.abimethod
    def with_app(self, value: arc4.String, app: Application, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert app.id == 1234
        app_txn = gtxn.ApplicationCallTransaction(0)
        assert app_txn.apps(0) == op.Global.current_application_id
        assert Txn.applications(0) == op.Global.current_application_id
        assert app_txn.apps(1) == app
        assert Txn.applications(1) == app

    @arc4.abimethod
    def with_acc(self, value: arc4.String, acc: Account, arr: UInt8Array) -> None:
        assert value
        assert arr
        assert acc.total_apps_created == 123
        assert Txn.accounts(0) == Txn.sender
        assert Txn.accounts(1) == acc

    @arc4.abimethod
    def complex_sig(
        self, struct1: MyStruct, txn: algopy.gtxn.Transaction, acc: Account, five: UInt8Array
    ) -> tuple[MyStructAlias, MyStruct]:
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
        assert acc.balance == 123
        assert five[0] == 5

        return struct1.another_struct.copy(), struct1.copy()
