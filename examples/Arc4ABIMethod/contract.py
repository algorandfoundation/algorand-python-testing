from algopy import Account, Application, ARC4Contract, Asset, Txn, arc4, gtxn, op

UInt8Array = arc4.DynamicArray[arc4.UInt8]

# TODO: move out of examples
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
