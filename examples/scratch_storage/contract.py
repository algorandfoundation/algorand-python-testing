from algopy import ARC4Contract, Bytes, Contract, UInt64, op, urange
from algopy.arc4 import abimethod

TWO = 2
TWENTY = 20


class ScratchSlotsContract(ARC4Contract, scratch_slots=(1, TWO, urange(3, TWENTY))):
    @abimethod
    def store_data(self) -> bool:
        op.Scratch.store(1, UInt64(5))
        op.Scratch.store(2, Bytes(b"Hello World"))
        assert op.Scratch.load_uint64(1) == UInt64(5)
        assert op.Scratch.load_bytes(2) == b"Hello World"
        return True


class SimpleScratchSlotsContract(Contract, scratch_slots=(1, TWO, urange(3, TWENTY))):
    def approval_program(self) -> UInt64:
        assert op.Scratch.load_uint64(1) == UInt64(5)
        assert op.Scratch.load_bytes(2) == b"Hello World"
        return UInt64(1)

    def clear_state_program(self) -> UInt64:
        return UInt64(1)
