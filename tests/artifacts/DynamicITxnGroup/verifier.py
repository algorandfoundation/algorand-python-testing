from algopy import (
    ARC4Contract,
    TransactionType,
    Txn,
    arc4,
    gtxn,
    urange,
)


class VerifierContract(ARC4Contract):
    @arc4.abimethod
    def verify(self) -> None:
        for i in urange(Txn.group_index):
            txn = gtxn.Transaction(i)
            assert txn.type == TransactionType.Payment, "Txn must be pay"
