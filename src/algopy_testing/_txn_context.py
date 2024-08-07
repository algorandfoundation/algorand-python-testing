from __future__ import annotations

import typing
from contextlib import contextmanager

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType

from algopy_testing._itxn_loader import ITxnGroupLoader, ITxnLoader


class TransactionContext:
    def __init__(self) -> None:
        self._groups: list[TransactionGroup] = []
        self._active_txn_fields: dict[str, typing.Any] = {}
        self._inner_txn_groups: list[typing.Sequence[InnerTransactionResultType]] = []
        self._constructing_itxn_group: list[InnerTransactionResultType] = []
        self._constructing_itxn: InnerTransactionResultType | None = None

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

    def begin_constructing_itxn_group(self) -> None:
        self._constructing_itxn_group = []

    def add_to_constructing_itxn_group(self) -> None:
        if self._constructing_itxn:
            self._constructing_itxn_group.append(self._constructing_itxn)
            self._constructing_itxn = None

    def submit_constructing_itxn_group(self) -> None:
        if self._constructing_itxn:
            self._constructing_itxn_group.append(self._constructing_itxn)
            self._constructing_itxn = None
        if self._constructing_itxn_group:
            self.add_inner_txn_group(self._constructing_itxn_group)
            self._constructing_itxn_group = []

    def clear(self, *, group_txns: bool = False, inner_txns: bool = False) -> None:
        if group_txns:
            self._groups.clear()
            self._active_txn_fields.clear()

        if inner_txns:
            self._inner_txn_groups.clear()
            self._constructing_itxn_group.clear()
            self._constructing_itxn = None

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

    @property
    def constructing_inner_txn(self) -> InnerTransactionResultType | None:
        return self._constructing_itxn

    @constructing_inner_txn.setter
    def constructing_inner_txn(self, value: InnerTransactionResultType | None) -> None:
        self._constructing_itxn = value

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
