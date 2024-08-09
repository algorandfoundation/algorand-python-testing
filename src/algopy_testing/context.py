from __future__ import annotations

import typing
from collections import defaultdict

import algosdk

import algopy_testing
from algopy_testing._context_helpers import LedgerContext, TransactionContext
from algopy_testing._value_generators import (
    AlgopyValueGenerator,
    ARC4ValueGenerator,
)
from algopy_testing.constants import (
    ARC4_RETURN_PREFIX,
)
from algopy_testing.utils import (
    convert_native_to_stack,
    get_new_scratch_space,
)

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    import algopy


class AlgopyTestContext:
    """Manages the testing context for Algorand Python SDK (algopy)
    applications.

    This class provides methods and properties to simulate various
    aspects of the Algorand blockchain environment, including accounts,
    assets, applications, transactions, and global state. It allows for
    easy setup and manipulation of test scenarios for algopy-based smart
    contracts and applications.
    """

    _arc4: ARC4ValueGenerator

    def __init__(
        self,
        *,
        default_sender: algopy.Account | None = None,
        template_vars: dict[str, typing.Any] | None = None,
    ) -> None:
        import algopy

        # TODO: remove direct reads of data mappings outside of context_storage
        self._default_sender = default_sender or algopy.Account(
            algosdk.account.generate_account()[1]
        )
        self._template_vars: dict[str, typing.Any] = template_vars or {}

        # TODO: this map is a global mapping of app_id to logs
        #       should instead be a mapping within a txn group
        self._application_logs: dict[int, list[bytes]] = {}
        # TODO: move onto TransactionGroup
        self._scratch_spaces = defaultdict[
            algopy_testing.gtxn.TransactionBase, list[algopy.Bytes | algopy.UInt64]
        ](get_new_scratch_space)
        self._active_lsig_args: Sequence[algopy.Bytes] = ()
        self._ledger_context = LedgerContext()
        self._txn_context = TransactionContext()
        self._value_generator = AlgopyValueGenerator(self)

    @property
    def arc4(self) -> ARC4ValueGenerator:
        return self._arc4

    @property
    def default_sender(self) -> algopy.Account:
        return self._default_sender

    @property
    def any(self) -> AlgopyValueGenerator:
        return self._value_generator

    @property
    def ledger(self) -> LedgerContext:
        return self._ledger_context

    @property
    def txn(self) -> TransactionContext:
        return self._txn_context

    def get_application_for_contract(
        self, contract: algopy.Contract | algopy.ARC4Contract
    ) -> algopy.Application:
        return self.ledger.get_application(contract.__app_id__)

    def set_scratch_space(
        self,
        txn: algopy.gtxn.TransactionBase,
        scratch_space: Sequence[algopy.Bytes | algopy.UInt64 | bytes | int],
    ) -> None:
        new_scratch_space = get_new_scratch_space()
        # insert values to list at specific indexes, use key as index and value as value to set
        for index, value in enumerate(scratch_space):
            new_scratch_space[index] = convert_native_to_stack(value)

        self._scratch_spaces[txn] = new_scratch_space

    def set_scratch_slot(
        self,
        txn: algopy.gtxn.TransactionBase,
        index: algopy.UInt64 | int,
        value: algopy.Bytes | algopy.UInt64 | bytes | int,
    ) -> None:
        slots = self._scratch_spaces[txn]
        try:
            slots[int(index)] = convert_native_to_stack(value)
        except IndexError:
            raise ValueError("invalid scratch slot") from None

    def get_scratch_slot(
        self,
        txn: algopy.gtxn.TransactionBase,
        index: algopy.UInt64 | int,
    ) -> algopy.UInt64 | algopy.Bytes:
        slots = self._scratch_spaces[txn]
        try:
            return slots[int(index)]
        except IndexError:
            raise ValueError("invalid scratch slot") from None

    def get_scratch_space(
        self, txn: algopy.gtxn.TransactionBase
    ) -> Sequence[algopy.Bytes | algopy.UInt64]:
        """Retrieves scratch space for a transaction.

        :param txn: Transaction identifier.
        :param txn: algopy.gtxn.TransactionBase:
        :returns: List of scratch space values.
        """
        return self._scratch_spaces[txn]

    def set_template_var(self, name: str, value: typing.Any) -> None:
        """Set a template variable for the current context.

        :param name: The name of the template variable.
        :type name: str
        :param value: The value to assign to the template variable.
        :type value: Any
        :param name: str:
        :param value: Any:
        :returns: None
        """
        self._template_vars[name] = value

    def add_application_logs(
        self,
        *,
        app_id: algopy.UInt64 | algopy.Application | int,
        logs: bytes | list[bytes],
        prepend_arc4_prefix: bool = False,
    ) -> None:
        """Add logs for an application.

        :param app_id: The ID of the application.
        :type app_id: int
        :param logs: A single log entry or a list of log entries.
        :type logs: bytes | list[bytes]
        :param prepend_arc4_prefix: Whether to prepend ARC4 prefix to
            the logs.
        :type prepend_arc4_prefix: bool :param *:
        :param app_id: algopy.UInt64 | algopy.Application | int:
        :param logs: bytes | list[bytes]:
        :param prepend_arc4_prefix: bool:  (Default value = False)
        """
        import algopy

        raw_app_id = (
            int(app_id)
            if isinstance(app_id, algopy.UInt64)
            else int(app_id.id) if isinstance(app_id, algopy.Application) else app_id
        )

        if isinstance(logs, bytes):
            logs = [logs]

        if prepend_arc4_prefix:
            logs = [ARC4_RETURN_PREFIX + log for log in logs]

        if raw_app_id in self._application_logs:
            self._application_logs[raw_app_id].extend(logs)
        else:
            self._application_logs[raw_app_id] = logs

    def get_application_logs(self, app_id: algopy.UInt64 | int) -> list[bytes]:
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

        if app_id not in self._application_logs:
            raise ValueError(
                f"No application logs available for app ID {app_id} in testing context!"
            )

        return self._application_logs[app_id]

    def execute_logicsig(self, lsig: algopy.LogicSig, *args: algopy.Bytes) -> bool | algopy.UInt64:
        """Execute a logic signature using provided args.

        :param lsig: The logic signature to execute.
        :type lsig: algopy.LogicSig
        :param args: The logic signature arguments to use
        :type args: algopy.Bytes
        :return: The result of executing the logic signature function.
        :rtype: bool | algopy.UInt64
        """
        self._active_lsig_args = args
        try:
            return lsig.func()
        finally:
            self._active_lsig_args = ()

    def clear_transaction_context(self) -> None:
        """Clear the transaction context."""
        self._txn_context = TransactionContext()

    def reset(self) -> None:
        """Reset the test context to its initial state, clearing all data and
        resetting ID counters."""

        self._application_logs.clear()
        self._scratch_spaces.clear()
        self._template_vars.clear()
        self._txn_context = TransactionContext()
        self._ledger_context = LedgerContext()
