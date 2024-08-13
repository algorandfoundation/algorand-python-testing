from .arc4 import ARC4ValueGenerator
from .avm import AVMValueGenerator
from .txn import TxnValueGenerator


class AlgopyValueGenerator(AVMValueGenerator):
    """Proxy class holding refs to all value generators."""

    def __init__(self) -> None:
        self._txn = TxnValueGenerator()
        self._arc4 = ARC4ValueGenerator()

    @property
    def txn(self) -> TxnValueGenerator:
        return self._txn

    @property
    def arc4(self) -> ARC4ValueGenerator:
        return self._arc4


__all__ = ["TxnValueGenerator", "ARC4ValueGenerator", "AlgopyValueGenerator"]
