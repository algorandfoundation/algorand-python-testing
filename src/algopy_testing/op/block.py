from __future__ import annotations

from typing import TYPE_CHECKING

from algopy_testing._context_storage import get_test_context
from algopy_testing.op.misc import itob
from algopy_testing.primitives import UInt64

if TYPE_CHECKING:
    import algopy


class Block:
    @staticmethod
    def blk_seed(a: algopy.UInt64 | int, /) -> algopy.Bytes:
        context = get_test_context()

        try:
            index = int(a)
            return itob(context._blocks[index]["seed"])
        except KeyError as e:
            raise KeyError(f"Block {a} not set") from e

    @staticmethod
    def blk_timestamp(a: algopy.UInt64 | int, /) -> algopy.UInt64:
        context = get_test_context()

        try:
            index = int(a)
            return UInt64(context._blocks[index]["timestamp"])
        except KeyError as e:
            raise KeyError(f"Block {a} not set") from e
