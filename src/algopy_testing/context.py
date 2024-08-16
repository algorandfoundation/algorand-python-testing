from __future__ import annotations

import typing

import algosdk

from algopy_testing._context_helpers import LedgerContext, TransactionContext
from algopy_testing._value_generators import AlgopyValueGenerator

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

    def __init__(
        self,
        *,
        default_sender: str | None = None,
        template_vars: dict[str, typing.Any] | None = None,
    ) -> None:
        """Initialize the AlgopyTestContext.

        :param default_sender: The default sender account address,
            defaults to None
        :type default_sender: str | None, optional
        :param template_vars: Dictionary of template variables, defaults
            to None
        :type template_vars: dict[str, typing.Any] | None, optional
        """
        import algopy

        self._default_sender = algopy.Account(
            default_sender or algosdk.account.generate_account()[1]
        )
        self._template_vars: dict[str, typing.Any] = template_vars or {}

        self._active_lsig_args: Sequence[algopy.Bytes] = ()
        self._ledger_context = LedgerContext()
        self._txn_context = TransactionContext()
        self._value_generator = AlgopyValueGenerator()

    @property
    def default_sender(self) -> algopy.Account:
        """Get the default sender account.

        :return: The default sender account
        :rtype: algopy.Account
        """
        return self._default_sender

    @property
    def any(self) -> AlgopyValueGenerator:
        """Access the value generators.

        :return: The value generator
        :rtype: AlgopyValueGenerator
        """
        return self._value_generator

    @property
    def ledger(self) -> LedgerContext:
        """Access the ledger context.

        :return: The ledger context
        :rtype: LedgerContext
        """
        return self._ledger_context

    @property
    def txn(self) -> TransactionContext:
        """Access the transaction context.

        :return: The transaction context
        :rtype: TransactionContext
        """
        return self._txn_context

    def get_app_for_contract(
        self, contract: algopy.Contract | algopy.ARC4Contract
    ) -> algopy.Application:
        """Get the application for a given contract.

        :param contract: The contract to get the application for
        :type contract: algopy.Contract | algopy.ARC4Contract
        :return: The application associated with the contract
        :rtype: algopy.Application
        """
        return self.ledger.get_app(contract.__app_id__)

    def set_template_var(self, name: str, value: typing.Any) -> None:
        """Set a template variable for the current context.

        :param name: The name of the template variable
        :type name: str
        :param value: The value to assign to the template variable
        :type value: Any
        """
        self._template_vars[name] = value

    def execute_logicsig(self, lsig: algopy.LogicSig, *args: algopy.Bytes) -> bool | algopy.UInt64:
        """Execute a logic signature using provided args.

        :param lsig: The logic signature to execute
        :type lsig: algopy.LogicSig
        :param args: The logic signature arguments to use
        :type args: algopy.Bytes
        :return: The result of executing the logic signature function
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
        self._template_vars.clear()
        self._txn_context = TransactionContext()
        self._ledger_context = LedgerContext()
