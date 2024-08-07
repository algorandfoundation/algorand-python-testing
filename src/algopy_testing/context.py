from __future__ import annotations

import secrets
import string
import typing
from collections import defaultdict
from contextlib import contextmanager
from typing import Unpack

import algosdk

import algopy_testing
from algopy_testing._arc4_factory import ARC4Factory
from algopy_testing._context_storage import get_app_data
from algopy_testing._ledger_context import LedgerContext
from algopy_testing._txn_context import TransactionContext, TransactionGroup
from algopy_testing.constants import (
    ARC4_RETURN_PREFIX,
    MAX_BYTES_SIZE,
    MAX_UINT64,
)
from algopy_testing.gtxn import TransactionBase
from algopy_testing.models.txn_fields import get_txn_defaults
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import (
    convert_native_to_stack,
    generate_random_int,
)

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType, ITxnGroupLoader, ITxnLoader
    from algopy_testing.models.account import (
        AccountFields,
    )
    from algopy_testing.models.application import ApplicationFields
    from algopy_testing.models.asset import AssetFields
    from algopy_testing.models.txn_fields import (
        ApplicationCallFields,
        AssetConfigFields,
        AssetFreezeFields,
        AssetTransferFields,
        KeyRegistrationFields,
        PaymentFields,
        TransactionFields,
    )
    from algopy_testing.op.global_values import GlobalFields

_TGlobalTxn = typing.TypeVar("_TGlobalTxn", bound=TransactionBase)


class AlgopyTestContext:
    """Manages the testing context for Algorand Python SDK (algopy)
    applications.

    This class provides methods and properties to simulate various
    aspects of the Algorand blockchain environment, including accounts,
    assets, applications, transactions, and global state. It allows for
    easy setup and manipulation of test scenarios for algopy-based smart
    contracts and applications.
    """

    _arc4: ARC4Factory

    def __init__(
        self,
        *,
        default_sender: algopy.Account | None = None,
        template_vars: dict[str, typing.Any] | None = None,
    ) -> None:
        import algopy

        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

        self._active_contract: algopy_testing.Contract | None = None
        self._scratch_spaces = defaultdict[
            algopy_testing.gtxn.TransactionBase, list[algopy.Bytes | algopy.UInt64]
        ](_get_scratch_slots)
        # TODO: remove direct reads of data mappings outside of context_storage
        self._contract_app_ids = dict[algopy.Contract, int]()
        # TODO: this map is from app_id to logs, should probably instead be stored against
        #       the appropriate txn
        self._ledger_context = LedgerContext(default_sender=default_sender)
        self._application_logs: dict[int, list[bytes]] = {}
        self._txn_context = TransactionContext()
        self._active_lsig_args: Sequence[algopy.Bytes] = []
        self._arc4 = ARC4Factory(context=self)
        self._template_vars: dict[str, typing.Any] = template_vars or {}
        self._lsigs: dict[algopy.LogicSig, Callable[[], algopy.UInt64 | bool]] = {}

    @property
    def arc4(self) -> ARC4Factory:
        return self._arc4

    @property
    def default_sender(self) -> algopy.Account:
        return self._ledger_context.default_sender

    def patch_global_fields(self, **global_fields: Unpack[GlobalFields]) -> None:
        """Patch 'Global' fields in the test context.

        :param **global_fields: Key-value pairs for global fields.
        :param **global_fields: Unpack[GlobalFields]:
        :raises AttributeError: If a key is invalid.
        """
        self._ledger_context.patch_global_fields(**global_fields)

    def get_application_for_contract(
        self, contract: algopy.Contract | algopy.ARC4Contract
    ) -> algopy.Application:
        try:
            app_id = self._contract_app_ids[contract]
        except KeyError:
            raise ValueError("Contract not found in testing context!") from None
        return self.get_application(app_id)

    def get_contract_for_app(self, app: algopy.Application) -> algopy.Contract | None:
        app_data = get_app_data(int(app.id))
        return app_data.contract

    def set_scratch_space(
        self,
        txn: algopy.gtxn.TransactionBase,
        scratch_space: Sequence[algopy.Bytes | algopy.UInt64 | bytes | int],
    ) -> None:
        new_scratch_space = _get_scratch_slots()
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

    def set_active_contract(self, contract: algopy.Contract | algopy.ARC4Contract) -> None:
        """Set the active contract for the current context. By default, invoked
        automatically as part of invocation of any app calls against instances
        of Contract or ARC4Contract classes.

        :param contract: The contract to set as active.
        :type contract: algopy.Contract | algopy.ARC4Contract
        :param contract: algopy.Contract | algopy.ARC4Contract:
        :returns: None
        """
        self._active_contract = contract

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

    def get_account(self, address: str) -> algopy.Account:
        """Retrieve an account by address.

        :param address: Account address.
        :type address: str
        :param address: str:
        :returns: The account associated with the address.
        :rtype: algopy.Account
        """
        return self._ledger_context.get_account(address)

    def update_account(self, address: str, **account_fields: Unpack[AccountFields]) -> None:
        """Update an existing account.

        :param address: Account address.
        :type address: str
        :param **account_fields: New account data.
        :param address: str:
        :param **account_fields: Unpack[AccountFields]:
        :raises TypeError: If the provided object is not an instance of `Account`.
        """
        self._ledger_context.update_account(address, **account_fields)

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        """Retrieve an asset by its ID.

        :param asset_id: The ID of the asset to retrieve.
        :type asset_id: int
        :returns: The asset associated with the given ID.
        :rtype: algopy.Asset
        :raises ValueError: If the asset is not found in the testing
            context.
        """
        return self._ledger_context.get_asset(asset_id)

    def update_asset(self, asset_id: int, **asset_fields: Unpack[AssetFields]) -> None:
        """Update an existing asset.

        :param asset_id: Asset ID.
        :type asset_id: int :param **asset_fields: New asset data.
        :param asset_id: int: :param **asset_fields:
            Unpack[AssetFields]:
        """
        self._ledger_context.update_asset(asset_id, **asset_fields)

    @property
    def inner_txn_groups(self) -> list[Sequence[InnerTransactionResultType]]:
        """Retrieve all groups of inner transactions that have been submitted.

        :returns: A list of inner transaction groups, where each group
            is a sequence of inner transaction results.
        :rtype: list[Sequence[InnerTransactionResultType]]
        """
        return self._txn_context.inner_txn_groups

    @property
    def last_txn_group(self) -> TransactionGroup:
        return self._txn_context.last_txn_group

    @property
    def last_active_txn(self) -> algopy.gtxn.Transaction:
        return self._txn_context.last_active_txn

    def get_submitted_itxn_group(self, index: int) -> ITxnGroupLoader:
        """Retrieve the last group of inner transactions. Returns a loader
        instance that allows access to generic inner transaction fields or
        specific inner transaction types with implicit type checking. Will
        implicitly assert that at least one inner transaction group has been
        submitted.

        :param index: int:
        :returns: The last group of inner transactions.
        :rtype: Sequence[algopy.itxn.InnerTransactionResult]
        :raises ValueError: If no inner transaction groups have been
            submitted yet.
        """

        return self._txn_context.get_submitted_itxn_group(index)

    @property
    def last_submitted_itxn(self) -> ITxnLoader:
        """Retrieve the last submitted inner transaction from the last inner
        transaction group (if both exist).

        :returns: The last submitted inner transaction loader.
        :rtype: ITxnLoader
        :raises ValueError: If no inner transactions exist in the last
            inner transaction group.
        """

        return self._txn_context.last_submitted_itxn

    def get_application(self, app_id: algopy.UInt64 | int) -> algopy.Application:
        """Retrieve an application by ID.

        :param app_id: Application ID.
        :type app_id: int
        :param app_id: algopy.UInt64 | int:
        :returns: The application associated with the ID.
        :rtype: algopy.Application
        """
        return self._ledger_context.get_application(app_id)

    def update_application(
        self, app_id: int, **application_fields: Unpack[ApplicationFields]
    ) -> None:
        """Update an existing application.

        :param app_id: Application ID.
        :type app_id: int :param **application_fields: New application
            data.
        :param app_id: int: :param **application_fields:
            Unpack[ApplicationFields]:
        """
        self._ledger_context.update_application(app_id, **application_fields)

    def any_account(
        self,
        address: str | None = None,
        opted_asset_balances: dict[algopy.UInt64, algopy.UInt64] | None = None,
        opted_apps: Sequence[algopy.Application] = (),
        **account_fields: Unpack[AccountFields],
    ) -> algopy.Account:
        """Generate and add a new account with a random address.

        :param address: Optional account address. If not provided, a new
            address will
        :type address: str | None
        :param address: Optional account address. If not provided, a new
            address will be generated.
        :type address: str | None
        :param opted_asset_balances: Optional asset
        :type opted_asset_balances: dict[algopy.UInt64
        :param opted_asset_balances: Optional asset balances.
        :type opted_asset_balances: dict[algopy.UInt64
        :param opted_apps: Optional applications.
        :type opted_apps: Sequence[algopy.Application] :param
            **account_fields: Additional account fields.
        :param address: str | None:  (Default value = None)
        :param opted_asset_balances: dict[algopy.UInt64: :param
            algopy.UInt64] | None: (Default value = None)
        :param opted_apps: Sequence[algopy.Application]: (Default value
            = ()) :param **account_fields: Unpack[AccountFields]:
        :returns: The newly generated account.
        :rtype: algopy.Account
        """

        return self._ledger_context.any_account(
            address, opted_asset_balances, opted_apps, **account_fields
        )

    def any_asset(
        self, asset_id: int | None = None, **asset_fields: Unpack[AssetFields]
    ) -> algopy.Asset:
        """Generate and add a new asset with a unique ID.

        :param asset_id: Optional asset ID. If not provided, a new ID
            will be generated.
        :type asset_id: int | None :param **asset_fields: Additional
            asset fields.
        :param asset_id: int | None: (Default value = None) :param
            **asset_fields: Unpack[AssetFields]:
        :returns: The newly generated asset.
        :rtype: algopy.Asset
        """
        return self._ledger_context.any_asset(asset_id, **asset_fields)

    def any_application(  # type: ignore[misc]
        self,
        id: int | None = None,
        address: algopy.Account | None = None,
        **application_fields: Unpack[ApplicationFields],
    ) -> algopy.Application:
        """Generate and add a new application with a unique ID.

        :param id: Optional application ID. If not provided, a new ID
            will be generated.
        :type id: int | None
        :param address: Optional application address. If not provided,
        :type address: algopy.Account | None
        :param address: Optional application address. If not provided,
            it will be generated.
        :type address: algopy.Account | None :param
            **application_fields: Additional application fields. :param
            # type: ignore[misc]self:
        :param id: int | None:  (Default value = None)
        :param address: algopy.Account | None: (Default value = None)
            :param **application_fields: Unpack[ApplicationFields]:
        :returns: The newly generated application.
        :rtype: algopy.Application
        """
        return self._ledger_context.any_application(id, address, **application_fields)

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

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        """Set the content of a box.

        :param name: algopy.Bytes | bytes:
        :param content: algopy.Bytes | bytes:
        """
        self._ledger_context.set_box(name, content)

    def get_box(self, name: algopy.Bytes | bytes) -> bytes:
        """Get the content of a box.

        :param name: The name of the box.
        :type name: algopy.Bytes | bytes
        :returns: The content of the box. If the box doesn't exist,
            returns an empty bytes object.
        :rtype: bytes
        """
        return self._ledger_context.get_box(name)

    def set_block(
        self, index: int, seed: algopy.UInt64 | int, timestamp: algopy.UInt64 | int
    ) -> None:
        """Set the block seed and timestamp for block at index `index`.

        :param index: int:
        :param seed: algopy.UInt64 | int:
        :param timestamp: algopy.UInt64 | int:
        """
        self._ledger_context.set_block(index, seed, timestamp)

    def set_transaction_group(
        self,
        gtxns: Sequence[algopy.gtxn.TransactionBase],
        active_transaction_index: int | None = None,
    ) -> None:
        """Set the transaction group using a list of transactions.

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
        if not all(isinstance(txn, algopy_testing.gtxn.TransactionBase) for txn in gtxns):
            raise ValueError("All transactions must be instances of TransactionBase")

        if len(gtxns) > algosdk.constants.TX_GROUP_LIMIT:
            raise ValueError(
                f"Transaction group can have at most {algosdk.constants.TX_GROUP_LIMIT} "
                "transactions, as per AVM limits."
            )

        for i, txn in enumerate(gtxns):
            txn.fields["group_index"] = UInt64(i)

        txn_group = TransactionGroup(
            transactions=gtxns,
            active_transaction_index=active_transaction_index,
        )
        self._txn_context.add_txn_group(txn_group)

    # TODO: should not expose this to the user, "active" transactions/apps should only
    #       be while a function is executing
    def get_active_application(self) -> algopy.Application:
        """Gets the Application associated with the active contract.

        :returns: The Application instance for the active contract.
        :rtype: algopy.Application
        :raises ValueError: If no active contract is set.
        """
        if self._active_contract is None:
            raise ValueError("No active contract")
        return self.get_application_for_contract(self._active_contract)

    def get_transaction(self, index: int) -> algopy.gtxn.Transaction:
        return self._txn_context.get_txn(index)

    def any_uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.UInt64:
        """Generate a random UInt64 value within a specified range.

        :param min_value: Minimum value. Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value. Defaults to MAX_UINT64.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT64)
        :returns: The randomly generated UInt64 value.
        :rtype: algopy.UInt64
        :raises ValueError: If `max_value` exceeds MAX_UINT64 or `min_value` exceeds `max_value`.
        """
        if max_value > MAX_UINT64:
            raise ValueError("max_value must be less than or equal to MAX_UINT64")
        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")

        return algopy_testing.UInt64(generate_random_int(min_value, max_value))

    def any_bytes(self, length: int = MAX_BYTES_SIZE) -> algopy.Bytes:
        """Generate a random byte sequence of a specified length.

        :param length: Length of the byte sequence. Defaults to
            MAX_BYTES_SIZE.
        :type length: int
        :param length: int:  (Default value = MAX_BYTES_SIZE)
        :returns: The randomly generated byte sequence.
        :rtype: algopy.Bytes
        """
        return algopy_testing.Bytes(secrets.token_bytes(length))

    def any_string(self, length: int = MAX_BYTES_SIZE) -> algopy.String:
        """Generate a random string of a specified length.

        :param length: int:  (Default value = MAX_BYTES_SIZE)
        """
        return algopy_testing.String(
            "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
        )

    def any_application_call_transaction(
        self,
        scratch_space: Sequence[algopy.Bytes | algopy.UInt64 | int | bytes] | None = None,
        **fields: Unpack[ApplicationCallFields],
    ) -> algopy.gtxn.ApplicationCallTransaction:
        """Generate a new application call transaction.

        :param scratch_space: Scratch space data. :param **fields:
            Fields to be set in the transaction. :type **fields:
            Unpack[ApplicationCallFields]
        :param scratch_space: Sequence[algopy.Bytes | algopy.UInt64 |
            int | bytes] | None: (Default value = None) :param **fields:
            Unpack[ApplicationCallFields]:
        :returns: New application call transaction.
        """
        try:
            app = fields["app_id"]
        except KeyError:
            app = fields["app_id"] = self.any_application()

        if not isinstance(app, algopy_testing.Application):
            raise TypeError("`app_id` must be an instance of algopy.Application")
        if not get_app_data(int(app.id)):
            raise ValueError(f"algopy.Application with ID {app.id} not found in testing context!")

        new_txn = self._new_gtxn(algopy_testing.gtxn.ApplicationCallTransaction, **fields)
        self.set_scratch_space(new_txn, scratch_space or [])

        return new_txn

    def any_asset_transfer_transaction(
        self, **fields: Unpack[AssetTransferFields]
    ) -> algopy.gtxn.AssetTransferTransaction:
        """Generate a new asset transfer transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[AssetTransferFields] :param **fields:
        Unpack[AssetTransferFields]:
        :returns: The newly generated asset transfer transaction.
        :rtype: algopy.gtxn.AssetTransferTransaction
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetTransferTransaction, **fields)

    def any_payment_transaction(
        self, **fields: Unpack[PaymentFields]
    ) -> algopy.gtxn.PaymentTransaction:
        """Generate a new payment transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[PaymentFields] :param **fields:
        Unpack[PaymentFields]:
        :returns: The newly generated payment transaction.
        :rtype: algopy.gtxn.PaymentTransaction
        """
        return self._new_gtxn(algopy_testing.gtxn.PaymentTransaction, **fields)

    def any_asset_config_transaction(
        self, **fields: Unpack[AssetConfigFields]
    ) -> algopy.gtxn.AssetConfigTransaction:
        """Generate a new ACFG transaction with specified fields.

        :param **fields: Unpack[AssetConfigFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetConfigTransaction, **fields)

    def any_key_registration_transaction(
        self, **fields: Unpack[KeyRegistrationFields]
    ) -> algopy.gtxn.KeyRegistrationTransaction:
        """Generate a new key registration transaction with specified fields.

        :param **fields: Unpack[KeyRegistrationFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.KeyRegistrationTransaction, **fields)

    def any_asset_freeze_transaction(
        self, **fields: Unpack[AssetFreezeFields]
    ) -> algopy.gtxn.AssetFreezeTransaction:
        """Generate a new asset freeze transaction with specified fields.

        :param **fields: Unpack[AssetFreezeFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetFreezeTransaction, **fields)

    def any_transaction(
        self,
        **fields: Unpack[TransactionFields],
    ) -> algopy.gtxn.Transaction:
        """Generate a new transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[TransactionFields] :param **fields:
        Unpack[TransactionFields]:
        :returns: The newly generated transaction.
        :rtype: algopy.gtxn.Transaction
        """
        return self._new_gtxn(algopy_testing.gtxn.Transaction, **fields)

    @contextmanager
    def scoped_txn_fields(
        self, **fields: Unpack[TransactionFields]
    ) -> Generator[None, None, None]:
        """Create a scoped context for transaction fields.

        This context manager allows setting temporary transaction fields
        that will be restored to their previous values when exiting the
        context.

        :param **fields: Transaction fields to be set within the scope.
        :type **fields: Unpack[TransactionFields]
        :return: A generator that yields None.
        :rtype: Generator[None, None, None]
        """
        with self._txn_context.scoped_txn_fields(**fields):
            yield

    def _new_gtxn(self, txn_type: type[_TGlobalTxn], **fields: object) -> _TGlobalTxn:
        # TODO: check reference types are known?
        fields.setdefault("type", txn_type.type_enum)
        fields.setdefault("sender", self.default_sender)  # TODO: have a default sender too?

        fields = {**get_txn_defaults(), **fields}
        return txn_type(fields)

    def delete_box(self, name: algopy.Bytes | bytes) -> bool:
        """Delete a box from the test context.

        :param name: The name of the box to delete.
        :type name: algopy.Bytes | bytes
        :returns: True if the box was successfully deleted, False if the
            box didn't exist.
        :rtype: bool
        """
        return self._ledger_context.delete_box(name)

    def box_exists(self, name: algopy.Bytes | bytes) -> bool:
        """Check if a box exists in the test context.

        :param name: The name of the box to check.
        :type name: algopy.Bytes | bytes
        :returns: True if the box exists, False otherwise.
        :rtype: bool
        """
        return self._ledger_context.box_exists(name)

    @contextmanager
    def scoped_lsig_args(
        self, lsig_args: Sequence[algopy.Bytes] | None = None
    ) -> Generator[None, None, None]:
        """Temporarily set the active logic signature arguments within a
        context.

        This context manager allows you to set logic signature arguments
        for the duration of a specific block of code. When the context
        is exited, the previous arguments are restored.

        :param lsig_args: The logic signature arguments to set. If None,
            an empty list will be used.
        :type lsig_args: Sequence[algopy.Bytes] | None
        :yield: None
        :rtype: Generator[None, None, None]
        """
        last_lsig_args = self._active_lsig_args
        self._active_lsig_args = lsig_args or []
        try:
            yield
        finally:
            self._active_lsig_args = last_lsig_args

    def execute_logicsig(
        self,
        lsig: algopy.LogicSig,
    ) -> bool | algopy.UInt64:
        """Execute a logic signature.

        This method executes the given logic signature. If the logic
        signature is not already in the context's list of logic
        signatures, it adds it before execution.

        :param lsig: The logic signature to execute.
        :type lsig: algopy.LogicSig
        :return: The result of executing the logic signature function.
        :rtype: bool | algopy.UInt64
        """
        if lsig not in self._lsigs:
            self._lsigs[lsig] = lsig.func
        return lsig.func()

    def add_logicsig(self, lsig: algopy.LogicSig) -> None:
        """Add a logic signature to the context.

        This method adds the given logic signature to the context's list of logic signatures.

        :param lsig: The logic signature to add.
        :type lsig: algopy.LogicSig
        :return: None
        :raises TypeError: If `lsig` is not an instance of `algopy.LogicSig`.
        """
        if not isinstance(lsig, algopy_testing.LogicSig):
            raise TypeError("lsig must be an instance of algopy.LogicSig")
        if lsig in self._lsigs:
            raise ValueError(f"Logic signature {lsig} already exists in the context!")
        self._lsigs[lsig] = lsig.func

    def clear_active_contract(self) -> None:
        """Clear the active contract."""
        self._active_contract = None

    def clear_transaction_context(
        self, *, group_txns: bool = True, inner_txns: bool = True
    ) -> None:
        """Clear the transaction context.

        This method clears the transaction context, optionally including
        group transactions and inner transactions.

        :param group_txns: If False, skip clearing group transactions.
            Defaults to True.
        :type group_txns: bool
        :param inner_txns: If False, skip clearing inner transactions.
            Defaults to True.
        :type inner_txns: bool
        :return: None
        """
        self._txn_context.clear(group_txns=group_txns, inner_txns=inner_txns)

    def clear_ledger_context(self) -> None:
        """Clear the ledger context."""
        self._ledger_context.clear()

    def clear(self) -> None:
        """Clear all data, including accounts, applications, assets, inner
        transactions, transaction groups, and application_logs."""
        self._application_logs.clear()
        self._scratch_spaces.clear()
        self._active_contract = None
        self._lsigs.clear()
        self._template_vars.clear()
        self.clear_transaction_context()
        self.clear_ledger_context()

    def reset(self) -> None:
        """Reset the test context to its initial state, clearing all data and
        resetting ID counters."""

        self.clear()
        self._txn_context = TransactionContext()
        self._ledger_contex = LedgerContext()


def _get_scratch_slots() -> list[algopy.Bytes | algopy.UInt64]:
    return [UInt64(0)] * 256
