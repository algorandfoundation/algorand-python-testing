from algopy import (
    ARC4Contract,
    UInt64,
    arc4,
)


class TuplesContract(ARC4Contract, avm_version=11):
    @arc4.abimethod()
    def test_tuple_with_primitive_type(self) -> tuple[UInt64, bool]:
        return (UInt64(0), True)
