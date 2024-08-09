from __future__ import annotations

import contextlib
import typing

import algosdk

if typing.TYPE_CHECKING:
    from collections.abc import Iterator

    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType

from algopy_testing import gtxn
from algopy_testing._itxn_loader import ITxnGroupLoader, ITxnLoader
from algopy_testing.itxn import InnerTransaction, submit_txns
from algopy_testing.models import Application
from algopy_testing.primitives import UInt64


class TransactionContext:
    def __init__(self) -> None:
        self._groups: list[TransactionGroup] = []
        self._active_group: TransactionGroup | None = None
        # active group is for use by implementations to get the current active group.
        # Once an app call is complete the active group is added to the list of groups.
        # It should not be accessed directly by user code, and should be None when
        # not executing an app call.
        # User code should use the "last" group properties to do assertions about a recently
        # executed app call

        # TODO: move the following on to TransactionGroup, to be accessed via _active_group
        self._active_txn_fields: dict[str, typing.Any] = {}
        self._inner_txn_groups: list[typing.Sequence[InnerTransactionResultType]] = []
        self._constructing_itxn_group: list[InnerTransaction] = []

    @contextlib.contextmanager
    def _maybe_implicit_txn_group(
        self,
        gtxns: typing.Sequence[algopy.gtxn.TransactionBase],
        active_transaction_index: int | None = None,
    ) -> Iterator[None]:
        """Only creates a group if there isn't one already active."""
        if self._active_group is None:
            ctx: typing.ContextManager[None] = self.enter_txn_group(
                gtxns, active_transaction_index=active_transaction_index
            )
        else:
            ctx = contextlib.nullcontext()
        with ctx:
            yield

    @contextlib.contextmanager
    def enter_txn_group(
        self,
        gtxns: typing.Sequence[algopy.gtxn.TransactionBase],
        active_transaction_index: int | None = None,
    ) -> Iterator[None]:
        """Adds a new transaction group using a list of transactions and an
        optional index to indicate the active transaction within the group.

        :param gtxns: List of transactions.
        :type gtxns: list[algopy.gtxn.TransactionBase]
        :param active_transaction_index: Index of the active
            transaction.
        :type active_transaction_index: int
        :param active_transaction_index: Index of the active
            transaction. Defaults to None.
        :type active_transaction_index: int
        :param gtxn: list[algopy.gtxn.TransactionBase]:
        :param active_transaction_index: int | None: (Default value =
            None)
        """
        if self._active_group is not None:
            raise RuntimeError("Existing active group")
        if not all(isinstance(txn, gtxn.TransactionBase) for txn in gtxns):
            raise ValueError("All transactions must be instances of TransactionBase")

        if len(gtxns) > algosdk.constants.TX_GROUP_LIMIT:
            raise ValueError(
                f"Transaction group can have at most {algosdk.constants.TX_GROUP_LIMIT} "
                "transactions, as per AVM limits."
            )

        for i, txn in enumerate(gtxns):
            txn.fields["group_index"] = UInt64(i)

        previous_group = self._active_group
        self._active_group = TransactionGroup(
            transactions=gtxns,
            active_transaction_index=active_transaction_index,
        )
        try:
            yield
        finally:
            self._groups.append(self._active_group)
            self._active_group = previous_group

    def add_inner_txn_group(self, group: typing.Sequence[InnerTransactionResultType]) -> None:
        self._inner_txn_groups.append(group)

    def get_submitted_itxn_group(self, index: int) -> ITxnGroupLoader:
        try:
            return ITxnGroupLoader(self._inner_txn_groups[index])
        except IndexError as e:
            raise ValueError(f"No inner transaction group at index {index}!") from e

    # TODO: make these private and move onto active group
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

    @contextlib.contextmanager
    def scoped_txn_fields(self, **fields: typing.Any) -> Iterator[None]:
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

    def get_txn(self, index: int | algopy.UInt64) -> algopy.gtxn.Transaction:
        try:
            return self.transactions[int(index)]  # type: ignore[return-value]
        except IndexError:
            raise ValueError("invalid group index") from None

    @property
    def active_app_id(self) -> int:
        # this should return the true app_id and not 0 if the app is in the creation phase
        app_id = self.active_txn.fields["app_id"]
        assert isinstance(app_id, Application)
        return int(app_id.id)

    @property
    def active_txn(self) -> algopy.gtxn.Transaction:
        return self.transactions[self.active_transaction_index]  # type: ignore[return-value]
