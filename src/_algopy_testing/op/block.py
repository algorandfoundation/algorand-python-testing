from __future__ import annotations

import typing
from typing import TYPE_CHECKING

from _algopy_testing import op
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.models.account import Account
from _algopy_testing.primitives import Bytes, UInt64

if TYPE_CHECKING:
    from collections.abc import Callable

    import algopy


_T = typing.TypeVar("_T")


def _make_block_method(
    field: str, conv: Callable[[typing.Any], _T]
) -> Callable[[algopy.UInt64 | int], _T]:
    def _read_block(index: algopy.UInt64 | int) -> _T:
        try:
            return conv(lazy_context.ledger.get_block_content(int(index), field))
        except KeyError as e:
            raise KeyError(f"Block {index} not set") from e

    return _read_block


class Block:
    @staticmethod
    def blk_seed(index: algopy.UInt64 | int) -> Bytes:
        try:
            value = lazy_context.ledger.get_block_content(int(index), "seed")
        except KeyError as e:
            raise KeyError(f"Block {index} not set") from e
        else:
            assert isinstance(value, int), "expected int for blk_seed"
            return op.itob(value)

    blk_timestamp = _make_block_method("timestamp", UInt64)
    blk_bonus = _make_block_method("bonus", UInt64)
    blk_proposer = _make_block_method("proposer", Account)
    blk_fees_collected = _make_block_method("fees_collected", UInt64)
    blk_txn_counter = _make_block_method("txn_counter", UInt64)
    blk_proposer_payout = _make_block_method("proposer_payout", UInt64)
    blk_branch = _make_block_method("branch", Bytes)
    blk_protocol = _make_block_method("protocol", Bytes)
    blk_fee_sink = _make_block_method("fee_sink", Account)
