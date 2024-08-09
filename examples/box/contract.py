from algopy import ARC4Contract, Box, OnCompleteAction, TransactionType, arc4, op


class BoxContract(ARC4Contract):
    def __init__(self) -> None:
        self.oca = Box(OnCompleteAction)
        self.txn = Box(TransactionType)

    @arc4.abimethod()
    def store_enums(self) -> None:
        self.oca.value = OnCompleteAction.OptIn
        self.txn.value = TransactionType.ApplicationCall

    @arc4.abimethod()
    def read_enums(self) -> arc4.Tuple[arc4.UInt64, arc4.UInt64]:
        assert op.Box.get(b"oca")[0] == op.itob(self.oca.value)
        assert op.Box.get(b"txn")[0] == op.itob(self.txn.value)

        return arc4.Tuple((arc4.UInt64(self.oca.value), arc4.UInt64(self.txn.value)))
