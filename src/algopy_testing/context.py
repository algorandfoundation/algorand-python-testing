from __future__ import annotations

import secrets
import string
import typing
from collections import ChainMap, defaultdict
from contextlib import contextmanager
from typing import Unpack

import algosdk

import algopy_testing
from algopy_testing._arc4_factory import ARC4Factory
from algopy_testing._itxn_loader import ITxnGroupLoader, ITxnLoader
from algopy_testing.constants import (
    ALWAYS_APPROVE_TEAL_PROGRAM,
    ARC4_RETURN_PREFIX,
    DEFAULT_ACCOUNT_MIN_BALANCE,
    DEFAULT_ASSET_CREATE_MIN_BALANCE,
    DEFAULT_ASSET_OPT_IN_MIN_BALANCE,
    DEFAULT_GLOBAL_GENESIS_HASH,
    DEFAULT_MAX_TXN_LIFE,
    MAX_BYTES_SIZE,
    MAX_UINT64,
)
from algopy_testing.gtxn import TransactionBase
from algopy_testing.models.account import (
    Account,
    AccountContextData,
    AccountFields,
    get_empty_account,
)
from algopy_testing.models.asset import AssetFields
from algopy_testing.models.txn_fields import get_txn_defaults
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import convert_native_to_stack, generate_random_int

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

    import algopy

    from algopy_testing._itxn_loader import InnerTransactionResultType
    from algopy_testing.models.application import ApplicationContextData, ApplicationFields
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


class TransactionGroup:

    def __init__(
        self,
        transactions: Sequence[algopy.gtxn.TransactionBase],
        active_transaction_index: int | None = None,
    ):
        # TODO: add TransactionContext and combine with logs and scratch space
        self.transactions = transactions
        self.active_transaction_index = (
            len(transactions) - 1 if active_transaction_index is None else active_transaction_index
        )

    @property
    def active_txn(self) -> algopy.gtxn.Transaction:
        return self.transactions[self.active_transaction_index]  # type: ignore[return-value]


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
        self._active_txn_fields = dict[str, typing.Any]()
        self._groups = list[TransactionGroup]()
        # TODO: remove direct reads of data mappings outside of context_storage
        self._application_data: dict[int, ApplicationContextData] = {}
        self._contract_app_ids = dict[algopy.Contract, int]()
        # TODO: this map is from app_id to logs, should probably instead be stored against
        #       the appropriate txn
        self._application_logs: dict[int, list[bytes]] = {}
        self._asset_data: dict[int, AssetFields] = {}
        self._inner_transaction_groups: list[Sequence[InnerTransactionResultType]] = []
        self._constructing_inner_transaction_group: list[InnerTransactionResultType] = []
        self._constructing_inner_transaction: InnerTransactionResultType | None = None
        self._template_vars: dict[str, typing.Any] = template_vars or {}
        self._blocks: dict[int, dict[str, int]] = {}
        self._boxes: dict[bytes, bytes] = {}
        self._lsigs: dict[algopy.LogicSig, Callable[[], algopy.UInt64 | bool]] = {}
        self._active_lsig_args: Sequence[algopy.Bytes] = []
        # using defaultdict here because there should be an AccountContextData for any
        # account, it defaults to an account with no balance
        self._account_data = defaultdict[str, AccountContextData](get_empty_account)
        self.default_sender: algopy.Account = default_sender or algopy.Account(
            algosdk.account.generate_account()[1]
        )
        self._account_data[self.default_sender.public_key] = get_empty_account()

        self._global_fields: GlobalFields = {
            "min_txn_fee": algopy.UInt64(algosdk.constants.MIN_TXN_FEE),
            "min_balance": algopy.UInt64(DEFAULT_ACCOUNT_MIN_BALANCE),
            "max_txn_life": algopy.UInt64(DEFAULT_MAX_TXN_LIFE),
            "zero_address": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "creator_address": self.default_sender,
            "asset_create_min_balance": algopy.UInt64(DEFAULT_ASSET_CREATE_MIN_BALANCE),
            "asset_opt_in_min_balance": algopy.UInt64(DEFAULT_ASSET_OPT_IN_MIN_BALANCE),
            "genesis_hash": algopy.Bytes(DEFAULT_GLOBAL_GENESIS_HASH),
        }

        self._arc4 = ARC4Factory(context=self)

    @property
    def arc4(self) -> ARC4Factory:
        return self._arc4

    def patch_global_fields(self, **global_fields: Unpack[GlobalFields]) -> None:
        """Patch 'Global' fields in the test context.

        :param **global_fields: Key-value pairs for global fields.
        :param **global_fields: Unpack[GlobalFields]:
        :raises AttributeError: If a key is invalid.
        """
        from algopy_testing.op.global_values import GlobalFields

        invalid_keys = global_fields.keys() - GlobalFields.__annotations__.keys()

        if invalid_keys:
            raise AttributeError(
                f"Invalid field(s) found during patch for `Global`: {', '.join(invalid_keys)}"
            )

        self._global_fields.update(global_fields)

    def get_application_for_contract(
        self, contract: algopy.Contract | algopy.ARC4Contract
    ) -> algopy.Application:
        try:
            app_id = self._contract_app_ids[contract]
        except KeyError:
            raise ValueError("Contract not found in testing context!") from None
        return self.get_application(app_id)

    def get_contract_for_app(self, app: algopy.Application) -> algopy.Contract | None:
        app_data = self._application_data[int(app.id)]
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
        return Account(address)

    def get_account_data(self) -> dict[str, AccountContextData]:
        """Retrieve all account data.

        :returns: The account data.
        :rtype: dict[str, AccountContextData]
        """
        return self._account_data

    def get_asset_data(self) -> dict[int, AssetFields]:
        """Retrieve all asset data.

        :returns: The asset data.
        :rtype: dict[int, AssetFields]
        """
        return self._asset_data

    def get_application_data(self) -> dict[int, ApplicationFields]:
        """Retrieve all application data.

        :returns: The application data.
        :rtype: dict[int, ApplicationFields]
        """
        return self._application_data  # type: ignore[return-value]

    def update_account(self, address: str, **account_fields: Unpack[AccountFields]) -> None:
        """Update an existing account.

        :param address: Account address.
        :type address: str
        :param **account_fields: New account data.
        :param address: str:
        :param **account_fields: Unpack[AccountFields]:
        :raises TypeError: If the provided object is not an instance of `Account`.
        """
        _assert_address_is_valid(address)
        self._account_data[address].fields.update(account_fields)

    def get_opted_asset_balance(
        self, account: algopy.Account, asset_id: algopy.UInt64
    ) -> algopy.UInt64 | None:
        """Retrieve the opted asset balance for an account and asset ID.

        :param account: Account to retrieve the balance for.
        :type account: algopy.Account
        :param asset_id: Asset ID.
        :type asset_id: algopy.UInt64
        :param account: algopy.Account:
        :param asset_id: algopy.UInt64:
        :returns: The opted asset balance or None if not opted in.
        :rtype: algopy.UInt64 | None
        """

        response = self._account_data[account.public_key].opted_asset_balances.get(asset_id, None)

        return response

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        """Retrieve an asset by ID.

        :param asset_id: Asset ID.
        :type asset_id: int
        :param asset_id: algopy.UInt64 | int:
        :returns: The asset associated with the ID.
        :rtype: algopy.Asset
        """
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id

        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")

        return algopy.Asset(asset_id)

    def update_asset(self, asset_id: int, **asset_fields: Unpack[AssetFields]) -> None:
        """Update an existing asset.

        :param asset_id: Asset ID.
        :type asset_id: int :param **asset_fields: New asset data.
        :param asset_id: int: :param **asset_fields:
            Unpack[AssetFields]:
        """
        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")

        self._asset_data[asset_id].update(asset_fields)

    def get_application(self, app_id: algopy.UInt64 | int) -> algopy.Application:
        """Retrieve an application by ID.

        :param app_id: Application ID.
        :type app_id: int
        :param app_id: algopy.UInt64 | int:
        :returns: The application associated with the ID.
        :rtype: algopy.Application
        """
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id

        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        return algopy.Application(app_id)

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
        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        self._application_data[app_id].fields.update(application_fields)

    def _append_inner_transaction_group(
        self,
        itxns: Sequence[object],
    ) -> None:
        """Append a group of inner transactions to the context.

        :param itxn: The group of inner transactions to append.
        :type itxn: Sequence[InnerTransactionResultType]
        :param itxns: Sequence[object]:
        """
        self._inner_transaction_groups.append(itxns)  # type: ignore[arg-type]

    def get_submitted_itxn_groups(self) -> list[Sequence[InnerTransactionResultType]]:
        """Retrieve the group of inner transactions at the specified index.
        Returns a loader instance that allows access to generic inner
        transaction fields or specific inner transaction types with implicit
        type checking.

        :param index: The index of the inner transaction group.
        :type index: int
        :returns: The loader for the inner transaction group.
        :rtype: ITxnGroupLoader
        :raises ValueError: If no inner transaction groups have been
            submitted yet or the index
        :raises ValueError: If no inner transaction groups have been
            submitted yet or the index is out of range.
        """
        return self._inner_transaction_groups

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

        if not self._inner_transaction_groups:
            raise ValueError("No inner transaction groups submitted yet!")

        try:
            return ITxnGroupLoader(self._inner_transaction_groups[index])
        except IndexError as err:
            raise ValueError(f"No inner transaction group available at index {index}!") from err

    @property
    def last_submitted_itxn(self) -> ITxnLoader:
        """Retrieve the last submitted inner transaction from the last inner
        transaction group (if both exist).

        :returns: The last submitted inner transaction loader.
        :rtype: ITxnLoader
        :raises ValueError: If no inner transactions exist in the last
            inner transaction group.
        """

        if not self._inner_transaction_groups or not self._inner_transaction_groups[-1]:
            raise ValueError("No inner transactions in the last inner transaction group!")

        try:
            last_itxn = self._inner_transaction_groups[-1][-1]
            return ITxnLoader(last_itxn)
        except IndexError as err:
            raise ValueError("No inner transactions in the last inner transaction group!") from err

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

        import algopy

        if address is not None:
            _assert_address_is_valid(address)

        # TODO: ensure passed fields are valid names and types
        if address in self._account_data:
            raise ValueError(
                "Account with such address already exists in testing context! "
                "Use `context.get_account(address)` to retrieve the existing account."
            )

        for key in account_fields:
            if key not in AccountFields.__annotations__:
                raise AttributeError(f"Invalid field '{key}' for Account")

        new_account_address = address or algosdk.account.generate_account()[1]
        new_account = algopy.Account(new_account_address)
        new_account_fields = AccountFields(**account_fields)
        new_account_data = AccountContextData(
            fields=new_account_fields,
            opted_asset_balances=opted_asset_balances or {},
            opted_apps={app.id: app for app in opted_apps},
        )

        self._account_data[new_account_address] = new_account_data

        return new_account

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
        import algopy

        if asset_id and asset_id in self._asset_data:
            raise ValueError("Asset with such ID already exists in testing context!")

        # TODO: ensure passed fields are valid names and types
        new_asset = algopy.Asset(asset_id or next(self._asset_id))
        default_asset_fields = {
            "total": self.any_uint64(),
            "decimals": self.any_uint64(1, 6),
            "default_frozen": False,
            "unit_name": self.any_bytes(4),
            "name": self.any_bytes(32),
            "url": self.any_bytes(10),
            "metadata_hash": self.any_bytes(32),
            "manager": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "freeze": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "clawback": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "creator": self.default_sender,
            "reserve": algopy.Account(algosdk.constants.ZERO_ADDRESS),
        }
        merged_fields = dict(ChainMap(asset_fields, default_asset_fields))  # type: ignore[arg-type]
        self._asset_data[int(new_asset.id)] = AssetFields(**merged_fields)  # type: ignore[typeddict-item]
        return new_asset

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
        from algopy_testing.models.application import ApplicationContextData

        new_app_id = id if id is not None else next(self._app_id)

        if new_app_id in self._application_data:
            raise ValueError(
                f"Application id {new_app_id} has already been configured in test context!"
            )

        new_app = algopy_testing.Application(new_app_id)

        # Set sensible defaults
        app_fields: ApplicationFields = {
            "approval_program": algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "clear_state_program": algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "global_num_uint": algopy_testing.UInt64(0),
            "global_num_bytes": algopy_testing.UInt64(0),
            "local_num_uint": algopy_testing.UInt64(0),
            "local_num_bytes": algopy_testing.UInt64(0),
            "extra_program_pages": algopy_testing.UInt64(0),
            "creator": self.default_sender,
            "address": address
            or algopy_testing.Account(algosdk.logic.get_application_address(new_app_id)),
        }

        # Merge provided fields with defaults, prioritizing provided fields
        for field, value in application_fields.items():
            try:
                default_value = app_fields[field]  # type: ignore[literal-required]
            except KeyError:
                raise ValueError(f"invalid field: {field!r}") from None
            if not issubclass(type(value), type(default_value)):
                raise TypeError(f"incorrect type for {field!r}")
            app_fields[field] = value  # type: ignore[literal-required]

        self._application_data[new_app_id] = ApplicationContextData(
            fields=app_fields,
            app_id=new_app_id,
        )

        return new_app

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

    def set_block(
        self, index: int, seed: algopy.UInt64 | int, timestamp: algopy.UInt64 | int
    ) -> None:
        """Set the block seed and timestamp for block at index `index`.

        :param index: int:
        :param seed: algopy.UInt64 | int:
        :param timestamp: algopy.UInt64 | int:
        """
        self._blocks[index] = {"seed": int(seed), "timestamp": int(timestamp)}

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
        self._groups.append(
            TransactionGroup(
                transactions=gtxns,
                active_transaction_index=active_transaction_index,
            )
        )

    @property
    def last_group(self) -> TransactionGroup:
        if not self._groups:
            raise ValueError("No group transactions found in the context!")

        return self._groups[-1]

    @property
    def last_active_txn(self) -> algopy.gtxn.Transaction:
        return self.last_group.active_txn

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
        try:
            active_txn = self.last_group.transactions[index]
        except IndexError:
            raise ValueError("invalid group index") from None

        return typing.cast(algopy_testing.gtxn.Transaction, active_txn)

    def get_active_transaction(self) -> algopy.gtxn.Transaction:
        """Retrieve the active transaction.

        :returns: The active transaction.
        :rtype: algopy.gtxn.Transaction
        :raises ValueError: If no active transaction is found.
        """
        # TODO: should only be valid during execution?
        return self.last_active_txn

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
            app_id = fields["app_id"]
        except KeyError:
            app_id = fields["app_id"] = self.any_application()

        if not isinstance(app_id, algopy_testing.Application):
            raise TypeError("`app_id` must be an instance of algopy.Application")
        if int(app_id.id) not in self._application_data:
            raise ValueError(
                f"algopy.Application with ID {app_id.id} not found in testing context!"
            )

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
        last_txn = self._active_txn_fields
        self._active_txn_fields = fields  # type: ignore[assignment]
        try:
            yield
        finally:
            self._active_txn_fields = last_txn

    def _new_gtxn(self, txn_type: type[_TGlobalTxn], **fields: object) -> _TGlobalTxn:
        # TODO: check reference types are known?
        fields.setdefault("type", txn_type.type_enum)
        fields.setdefault("sender", self.default_sender)  # TODO: have a default sender too?

        fields = {**get_txn_defaults(), **fields}
        return txn_type(fields)

    def does_box_exist(self, name: algopy.Bytes | bytes) -> bool:
        """

        :param name: algopy.Bytes | bytes:

        """
        name_bytes = name if isinstance(name, bytes) else name.value
        return name_bytes in self._boxes

    def get_box(self, name: algopy.Bytes | bytes) -> bytes:
        """Get the content of a box.

        :param name: The name of the box.
        :type name: algopy.Bytes | bytes
        :returns: The content of the box. If the box doesn't exist,
            returns an empty bytes object.
        :rtype: bytes
        """

        name_bytes = name if isinstance(name, bytes) else name.value
        return self._boxes.get(name_bytes, b"")

    def get_box_map(self, name: algopy.Bytes | bytes) -> bytes:
        """Get the content of a box map.

        :param name: The name of the box map.
        :type name: algopy.Bytes | bytes
        :returns: The content of the box map.
        :rtype: bytes
        """

        name_bytes = name if isinstance(name, bytes) else name.value
        prefix = b"box_map"
        return self.get_box(name=prefix + name_bytes)

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        """Set the content of a box.

        :param name: algopy.Bytes | bytes:
        :param content: algopy.Bytes | bytes:
        """

        name_bytes = name if isinstance(name, bytes) else name.value
        content_bytes = content if isinstance(content, bytes) else content.value
        self._boxes[name_bytes] = content_bytes

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

    def clear_box(self, name: algopy.Bytes | bytes) -> bool:
        """Clear all data, including accounts, applications, assets, inner
        transactions, transaction groups, and application logs.

        :param name: algopy.Bytes | bytes:
        """

        name_bytes = name if isinstance(name, bytes) else name.value
        if name_bytes in self._boxes:
            del self._boxes[name_bytes]
            return True
        return False

    def clear_all_boxes(self) -> None:
        """Clear all boxes."""
        self._boxes.clear()

    def clear_inner_transaction_groups(self) -> None:
        """Clear all inner transactions."""
        self._inner_transaction_groups.clear()

    def clear_transaction_group(self) -> None:
        """Clear the transaction group."""
        self._groups.clear()

    def clear_accounts(self) -> None:
        """Clear all accounts."""
        self._account_data.clear()

    def clear_applications(self) -> None:
        """Clear all applications."""
        self._application_data.clear()

    def clear_assets(self) -> None:
        """Clear all assets."""
        self._asset_data.clear()

    def clear_application_logs(self) -> None:
        """Clear all application logs."""
        self._application_logs.clear()

    def clear_scratch_spaces(self) -> None:
        """Clear all scratch spaces."""
        self._scratch_spaces.clear()

    def clear_active_contract(self) -> None:
        """Clear the active contract."""
        self._active_contract = None

    def clear_boxes(self) -> None:
        """Clear all boxes."""
        self._boxes.clear()

    def clear_blocks(self) -> None:
        """Clear all blocks."""
        self._blocks.clear()

    def clear_lsigs(self) -> None:
        """Clear all logic signatures."""
        self._lsigs.clear()
        self._active_lsig_args = []

    def clear_template_vars(self) -> None:
        """Clear all template variables."""
        self._template_vars.clear()

    def clear(self) -> None:
        """Clear all data, including accounts, applications, assets, inner
        transactions, transaction groups, and application_logs."""
        self.clear_accounts()
        self.clear_applications()
        self.clear_assets()
        self.clear_inner_transaction_groups()
        self.clear_transaction_group()
        self.clear_application_logs()
        self.clear_scratch_spaces()
        self.clear_active_contract()
        self.clear_boxes()
        self.clear_blocks()
        self.clear_lsigs()
        self.clear_template_vars()

    def reset(self) -> None:
        """Reset the test context to its initial state, clearing all data and
        resetting ID counters."""

        self._account_data = defaultdict(AccountContextData)
        self._application_data = {}
        self._asset_data = {}
        self._active_transaction_index = None
        self._scratch_spaces = defaultdict(_get_scratch_slots)
        self._inner_transaction_groups = []
        self._groups = []
        self._global_fields = {}
        self._application_logs = {}
        self._asset_id = iter(range(1, 2**64))
        self._app_id = iter(range(1, 2**64))


def _assert_address_is_valid(address: str) -> None:
    assert algosdk.encoding.is_valid_address(address), "Invalid Algorand address supplied!"


def _get_scratch_slots() -> list[algopy.Bytes | algopy.UInt64]:
    return [UInt64(0)] * 256
