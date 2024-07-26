from algopy import ARC4Contract, Box, OnCompleteAction, TransactionType, UInt64, arc4, op


class BoxContract(ARC4Contract):
    def __init__(self) -> None:
        self.oca = Box(UInt64)
        self.txn = Box(UInt64)

    @arc4.abimethod()
    def store_enums(self) -> None:
        self.oca.value = OnCompleteAction.OptIn
        self.txn.value = TransactionType.ApplicationCall

    @arc4.abimethod()
    def read_enums(self) -> tuple[UInt64, UInt64]:
        assert op.Box.get(b"oca")[0] == op.itob(self.oca.value)
        assert op.Box.get(b"txn")[0] == op.itob(self.txn.value)

        return self.oca.value, self.txn.value
