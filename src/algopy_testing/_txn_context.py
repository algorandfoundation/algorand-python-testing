from __future__ import annotations

import typing
from contextlib import contextmanager

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType

from algopy_testing._itxn_loader import ITxnGroupLoader, ITxnLoader
from algopy_testing.itxn import InnerTransaction, submit_txns


class TransactionContext:
    def __init__(self) -> None:
        self._groups: list[TransactionGroup] = []
        self._active_txn_fields: dict[str, typing.Any] = {}
        self._inner_txn_groups: list[typing.Sequence[InnerTransactionResultType]] = []
        self._constructing_itxn_group: list[InnerTransaction] = []

    def get_txn(self, index: int) -> algopy.gtxn.Transaction:
        import algopy

        return typing.cast(algopy.gtxn.Transaction, self.last_txn_group.transactions[index])

    def add_txn_group(self, group: TransactionGroup) -> None:
        self._groups.append(group)

    def add_inner_txn_group(self, group: typing.Sequence[InnerTransactionResultType]) -> None:
        self._inner_txn_groups.append(group)

    def get_submitted_itxn_group(self, index: int) -> ITxnGroupLoader:
        try:
            return ITxnGroupLoader(self._inner_txn_groups[index])
        except IndexError as e:
            raise ValueError(f"No inner transaction group at index {index}!") from e

    @property
    def constructing_itxn(self) -> InnerTransaction:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn field without itxn begin")
        return self._constructing_itxn_group[-1]

    def begin_itxn_group(self) -> None:
        if self._constructing_itxn_group:
            raise RuntimeError("itxn begin without itxn submit")
        # TODO: raise error if active txn is clear state
        self._constructing_itxn_group.append(InnerTransaction())

    def append_itxn_group(self) -> None:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn next without itxn begin")
        self._constructing_itxn_group.append(InnerTransaction())

    def submit_itxn_group(self) -> None:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn submit without itxn begin")
        submit_txns(*self._constructing_itxn_group)
        self._constructing_itxn_group = []

    def clear(self, *, group_txns: bool = False, inner_txns: bool = False) -> None:
        if group_txns:
            self._groups.clear()
            self._active_txn_fields.clear()

        if inner_txns:
            self._inner_txn_groups.clear()
            self._constructing_itxn_group.clear()

    @property
    def last_txn_group(self) -> TransactionGroup:
        if not self._groups:
            raise ValueError("No group transactions found!")
        return self._groups[-1]

    @property
    def last_active_txn(self) -> algopy.gtxn.Transaction:
        return self.last_txn_group.active_txn

    @property
    def inner_txn_groups(self) -> list[typing.Sequence[InnerTransactionResultType]]:
        return self._inner_txn_groups

    @property
    def last_submitted_itxn(self) -> ITxnLoader:
        if not self._inner_txn_groups or not self._inner_txn_groups[-1]:
            raise ValueError("No inner transactions in the last group!")
        return ITxnLoader(self._inner_txn_groups[-1][-1])

    @contextmanager
    def scoped_txn_fields(self, **fields: typing.Any) -> typing.Generator[None, None, None]:
        last_txn = self._active_txn_fields
        self._active_txn_fields = fields
        try:
            yield
        finally:
            self._active_txn_fields = last_txn


class TransactionGroup:
    def __init__(
        self,
        transactions: typing.Sequence[algopy.gtxn.TransactionBase],
        active_transaction_index: int | None = None,
    ):
        self.transactions = transactions
        self.active_transaction_index = (
            len(transactions) - 1 if active_transaction_index is None else active_transaction_index
        )

    @property
    def active_txn(self) -> algopy.gtxn.Transaction:
        return self.transactions[self.active_transaction_index]  # type: ignore[return-value]
