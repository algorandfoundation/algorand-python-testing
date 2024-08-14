from __future__ import annotations

import contextlib
import typing

import algosdk

from algopy_testing._itxn_loader import ITxnGroupLoader
from algopy_testing.decorators.arc4 import (
    check_routing_conditions,
    create_abimethod_txns,
    create_baremethod_txns,
    get_arc4_metadata,
    get_ordered_args,
)
from algopy_testing.enums import OnCompleteAction
from algopy_testing.models import ARC4Contract

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Iterator, Sequence

    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType
    from algopy_testing.models.txn_fields import TransactionBaseFields

from algopy_testing import gtxn
from algopy_testing._context_helpers import lazy_context
from algopy_testing._itxn_loader import ITxnLoader
from algopy_testing.itxn import InnerTransaction, submit_txns
from algopy_testing.models import Application
from algopy_testing.primitives import UInt64

TReturn = typing.TypeVar("TReturn")
TParamSpec = typing.ParamSpec("TParamSpec")


class DeferredAppCall(typing.Generic[TReturn]):
    _app_id: int
    _txns: list[algopy.gtxn.TransactionBase]
    _method: typing.Callable[..., TReturn]
    _args: tuple[typing.Any, ...]
    _kwargs: dict[str, typing.Any]

    def __init__(
        self,
        app_id: int,
        txns: list[algopy.gtxn.TransactionBase],
        method: Callable[..., TReturn],
        args: tuple[typing.Any, ...],
        kwargs: dict[str, typing.Any],
    ) -> None:
        self._app_id = app_id
        self._txns = txns
        self._method = method
        self._args = args
        self._kwargs = kwargs

    def submit(self) -> TReturn:
        # This method will be called to execute the prepared call
        check_routing_conditions(self._app_id, get_arc4_metadata(self._method))
        return self._method(*self._args, **self._kwargs)


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

    @contextlib.contextmanager
    def _maybe_implicit_txn_group(
        self,
        gtxns: typing.Sequence[algopy.gtxn.TransactionBase] | None = None,
        active_txn_index: int | None = None,
    ) -> Iterator[None]:
        """Only creates a group if there isn't one already active."""
        if not self._active_group or not self._active_group.txns:
            ctx: typing.ContextManager[None] = self.create_group(
                gtxns, active_txn_index=active_txn_index
            )
        else:
            ctx = contextlib.nullcontext()
        with ctx:
            yield

    def defer_app_call(
        self,
        method: Callable[TParamSpec, TReturn],
        *args: TParamSpec.args,
        **kwargs: TParamSpec.kwargs,
    ) -> DeferredAppCall[TReturn]:
        """Prepare an application call transaction group for a contract method
        without executing it.

        :param method: The decorated contract method (baremethod or
            abimethod).
        :param args: Positional arguments for the method.
        :param kwargs: Keyword arguments for the method.
        :return: A DeferredAppCall object containing the transaction
            group and method info.
        """
        arc4_metadata = get_arc4_metadata(method)
        # unwrap instance method
        try:
            wrapped = method.__wrapped__  # type: ignore[attr-defined]
        except AttributeError:
            wrapped = None

        # get instance and original cls method
        try:
            contract = wrapped.__self__
            fn = wrapped.__func__
        except AttributeError:
            contract = fn = None

        if not isinstance(contract, ARC4Contract) or fn is None:
            raise ValueError("The provided method must be an instance method of an ARC4 contract")

        app_id = contract.__app_id__
        # Handle ABI methods
        if arc4_metadata.arc4_signature:
            ordered_args = get_ordered_args(fn, args, kwargs)  # type: ignore[arg-type]
            txns = create_abimethod_txns(
                app_id=app_id,
                arc4_signature=arc4_metadata.arc4_signature,
                args=ordered_args,
            )
        # Handle bare methods
        else:
            txns = create_baremethod_txns(app_id)

        return DeferredAppCall(app_id=app_id, txns=txns, method=method, args=args, kwargs=kwargs)

    @contextlib.contextmanager
    def create_group(
        self,
        gtxns: (
            typing.Sequence[algopy.gtxn.TransactionBase | DeferredAppCall[TReturn]] | None
        ) = None,
        active_txn_index: int | None = None,
        txn_op_fields: TransactionBaseFields | None = None,
    ) -> Iterator[None]:
        """Adds a new transaction group using a list of transactions and an
        optional index to indicate the active transaction within the group.

        :param gtxns: List of transactions.
        :type gtxns: list[algopy.gtxn.TransactionBase]
        :param active_txn_index: Index of the active transaction.
        :type active_txn_index: int
        :param active_txn_index: Index of the active transaction.
            Defaults to None.
        :type active_txn_index: int
        :param gtxn: list[algopy.gtxn.TransactionBase]:
        :param active_txn_index: int | None: (Default value = None)
        :param txn_op_fields: dict[str, typing.Any] | None: (Default
            value = None)
        """

        processed_gtxns = []

        if gtxns:
            processed_gtxns = [
                txn
                for item in gtxns
                for txn in (item._txns if isinstance(item, DeferredAppCall) else [item])
            ]

            if not all(isinstance(txn, gtxn.TransactionBase) for txn in processed_gtxns):
                raise ValueError(
                    "All transactions must be instances of TransactionBase or DeferredAppCall"
                )

            if len(processed_gtxns) > algosdk.constants.TX_GROUP_LIMIT:
                raise ValueError(
                    f"Transaction group can have at most {algosdk.constants.TX_GROUP_LIMIT} "
                    "transactions, as per AVM limits."
                )

            for i, txn in enumerate(processed_gtxns):
                txn.fields["group_index"] = UInt64(i)

        previous_group = self._active_group
        self._active_group = TransactionGroup(
            txns=processed_gtxns,
            active_txn_index=active_txn_index,
            txn_op_fields=typing.cast(dict[str, typing.Any], txn_op_fields),
        )
        try:
            yield
        finally:
            if self._active_group.txns:
                self._groups.append(self._active_group)
            self._active_group = previous_group

    @property
    def last_group(self) -> TransactionGroup:
        if not self._groups:
            raise ValueError("No group transactions found!")
        return self._groups[-1]

    @property
    def last_active(
        self,
    ) -> algopy.gtxn.Transaction:
        return self.last_group.active_txn


class TransactionGroup:
    def __init__(
        self,
        txns: typing.Sequence[algopy.gtxn.TransactionBase],
        active_txn_index: int | None = None,
        txn_op_fields: dict[str, typing.Any] | None = None,
    ):
        self.txns = txns
        self.active_txn_index = len(txns) - 1 if active_txn_index is None else active_txn_index
        self._itxn_groups: list[Sequence[InnerTransactionResultType]] = []
        self._constructing_itxn_group: list[InnerTransaction] = []
        self._txn_op_fields = txn_op_fields or {}

    @property
    def active_app_id(self) -> int:
        # this should return the true app_id and not 0 if the app is in the creation phase
        if not self.txns:
            raise ValueError("No transactions in the group")
        app_id = self.active_txn.fields["app_id"]
        assert isinstance(app_id, Application)
        return int(app_id.id)

    @property
    def active_txn(self) -> algopy.gtxn.Transaction:
        if not self.txns or self.active_txn_index is None:
            raise ValueError("No active transaction in the group")
        return self.txns[self.active_txn_index]  # type: ignore[return-value]

    @property
    def itxn_groups(
        self,
    ) -> Sequence[Sequence[InnerTransactionResultType]]:
        return self._itxn_groups

    @property
    def last_itxn(self) -> ITxnLoader:
        if not self._itxn_groups or not self._itxn_groups[-1]:
            raise ValueError("No inner transactions in the last group!")
        return ITxnLoader(self._itxn_groups[-1][-1])

    @property
    def _constructing_itxn(self) -> InnerTransaction:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn field without itxn begin")
        return self._constructing_itxn_group[-1]

    def get_app_logs(self, app_id: algopy.UInt64 | int) -> list[bytes]:
        """Retrieve the application logs for a given app ID.

        :param app_id: The ID of the application.
        :type app_id: algopy.UInt64 | int
        :param app_id: algopy.UInt64 | int:
        :returns: The application logs for the given app ID.
        :rtype: list[bytes]
        :raises ValueError: If no application logs are available for the
            given app ID.
        """
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id

        app_data = lazy_context.get_app_data(app_id)
        user_supplied_logs = app_data._get_app_logs()

        if user_supplied_logs:
            # If user explicitly set logs on an app, return those
            # over logs stored within each txn
            return user_supplied_logs

        for txn in self.txns:
            if txn.fields.get("app_id", None) == app_id:
                return txn._app_logs

        raise ValueError(
            f"No logs for app with id - {app_id}. "
            "Use `context.any.txn.application_call(logs=[...])` on an app associated with app call"
            "to set custom logs, or `algopy.log()` in contracts to store logs automatically."
        )

    def get_txn(self, index: int | algopy.UInt64) -> algopy.gtxn.Transaction:
        try:
            return self.txns[int(index)]  # type: ignore[return-value]
        except IndexError:
            raise ValueError("invalid group index") from None

    def get_itxn_group(self, index: int) -> ITxnGroupLoader:
        try:
            return ITxnGroupLoader(self._itxn_groups[index])
        except IndexError as e:
            raise ValueError(f"No inner transaction group at index {index}!") from e

    def get_scratch_slot(
        self,
        index: algopy.UInt64 | int,
    ) -> algopy.UInt64 | algopy.Bytes:
        slots = self.active_txn._get_scratch_space()
        try:
            return slots[int(index)]
        except IndexError:
            raise ValueError("invalid scratch slot") from None

    def get_scratch_space(
        self,
    ) -> Sequence[algopy.Bytes | algopy.UInt64]:
        """Retrieves scratch space for the active transaction.

        :returns: List of scratch space values for the active
            transaction.
        """
        return self.active_txn._get_scratch_space()

    def _add_itxn_group(self, group: Sequence[InnerTransactionResultType]) -> None:
        self._itxn_groups.append(group)

    def _get_index(self, txn: algopy.gtxn.TransactionBase) -> int:
        try:
            return self.txns.index(txn)
        except ValueError:
            raise ValueError("Transaction is not part of this group") from None

    def _begin_itxn_group(self) -> None:
        if self._constructing_itxn_group:
            raise RuntimeError("itxn begin without itxn submit")

        if self.active_txn.on_completion == OnCompleteAction.ClearState:
            raise RuntimeError("Cannot begin inner transaction group in a clear state call")

        self._constructing_itxn_group.append(InnerTransaction())

    def _append_itxn_group(self) -> None:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn next without itxn begin")
        self._constructing_itxn_group.append(InnerTransaction())

    def _submit_itxn_group(self) -> None:
        if not self._constructing_itxn_group:
            raise RuntimeError("itxn submit without itxn begin")
        submit_txns(*self._constructing_itxn_group)
        self._constructing_itxn_group = []
