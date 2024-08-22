from __future__ import annotations

from typing import TYPE_CHECKING

from _algopy_testing import op
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.primitives import UInt64

if TYPE_CHECKING:
    import algopy


class Block:
    @staticmethod
    def blk_seed(a: algopy.UInt64 | int, /) -> algopy.Bytes:
        try:
            index = int(a)
            return op.itob(lazy_context.ledger.get_block_content(index, "seed"))
        except KeyError as e:
            raise KeyError(f"Block {a} not set") from e

    @staticmethod
    def blk_timestamp(a: algopy.UInt64 | int, /) -> algopy.UInt64:
        try:
            index = int(a)
            return UInt64(lazy_context.ledger.get_block_content(index, "timestamp"))
        except KeyError as e:
            raise KeyError(f"Block {a} not set") from e
