from algopy import (
    Application,
    ARC4Contract,
    Array,
    Global,
    arc4,
    gtxn,
    itxn,
    urange,
)


class DynamicItxnGroup(ARC4Contract):
    @arc4.abimethod
    def test_firstly(
        self, addresses: Array[arc4.Address], funds: gtxn.PaymentTransaction, verifier: Application
    ) -> None:
        assert funds.receiver == Global.current_application_address, "Funds must be sent to app"

        assert addresses.length, "must provide some accounts"

        share = funds.amount // addresses.length

        itxn.Payment(amount=share, receiver=addresses[0].native).stage(begin_group=True)

        for i in urange(1, addresses.length):
            addr = addresses[i]
            itxn.Payment(amount=share, receiver=addr.native).stage()

        itxn.ApplicationCall(
            app_id=verifier.id, app_args=(arc4.arc4_signature("verify()void"),)
        ).stage()

        itxn.AssetConfig(asset_name="abc").stage()

        itxn.submit_staged()

    @arc4.abimethod
    def test_looply(
        self,
        addresses: Array[arc4.Address],
        funds: gtxn.PaymentTransaction,
        verifier: Application,
    ) -> None:
        assert funds.receiver == Global.current_application_address, "Funds must be sent to app"

        assert addresses.length, "must provide some accounts"

        share = funds.amount // addresses.length

        is_first = True
        for addr in addresses:
            my_txn = itxn.Payment(amount=share, receiver=addr.native)
            my_txn.stage(begin_group=is_first)
            is_first = False

        itxn.ApplicationCall(
            app_id=verifier.id, app_args=(arc4.arc4_signature("verify()void"),)
        ).stage()

        itxn.AssetConfig(asset_name="abc").stage()

        itxn.submit_staged()
