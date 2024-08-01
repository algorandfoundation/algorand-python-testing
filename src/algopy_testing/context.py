from __future__ import annotations

import secrets
import string
import typing
from collections import ChainMap, defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

# Define the union type
from typing import TYPE_CHECKING, Any, TypeVar, Unpack, cast, overload

import algosdk

import algopy_testing
from algopy_testing.constants import (
    ALWAYS_APPROVE_TEAL_PROGRAM,
    ARC4_RETURN_PREFIX,
    DEFAULT_ACCOUNT_MIN_BALANCE,
    DEFAULT_ASSET_CREATE_MIN_BALANCE,
    DEFAULT_ASSET_OPT_IN_MIN_BALANCE,
    DEFAULT_GLOBAL_GENESIS_HASH,
    DEFAULT_MAX_TXN_LIFE,
    MAX_BYTES_SIZE,
    MAX_UINT8,
    MAX_UINT16,
    MAX_UINT32,
    MAX_UINT64,
    MAX_UINT512,
)
from algopy_testing.gtxn import NULL_GTXN_GROUP_INDEX
from algopy_testing.models.account import AccountContextData, AccountFields, get_empty_account
from algopy_testing.models.asset import AssetFields
from algopy_testing.models.global_values import GlobalFields
from algopy_testing.models.txn import TxnFields
from algopy_testing.utils import generate_random_int

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

    import algopy

    from algopy_testing.gtxn import (
        AssetTransferFields,
        PaymentFields,
        TransactionFields,
    )
    from algopy_testing.models.application import ApplicationFields
    from algopy_testing.models.transactions import (
        AssetConfigFields,
        AssetFreezeFields,
        KeyRegistrationFields,
        _ApplicationCallFields,
    )

    InnerTransactionResultType = (
        algopy.itxn.InnerTransactionResult
        | algopy.itxn.PaymentInnerTransaction
        | algopy.itxn.KeyRegistrationInnerTransaction
        | algopy.itxn.AssetConfigInnerTransaction
        | algopy.itxn.AssetTransferInnerTransaction
        | algopy.itxn.AssetFreezeInnerTransaction
        | algopy.itxn.ApplicationCallInnerTransaction
    )


T = TypeVar("T")


@dataclass
class ContractContextData:
    """
    Stores contract-related information.

    Attributes:
        contract (algopy.Contract | algopy.ARC4Contract): Contract instance.
        app_id (algopy.UInt64): Application ID.
    """

    contract: algopy.Contract | algopy.ARC4Contract
    app_id: algopy.UInt64


class ITxnLoader:
    """
    Stores inner transaction references.
    """

    def __init__(self, inner_txn: InnerTransactionResultType):
        self._inner_txn = inner_txn

    def _get_itxn(self, txn_type: type[T]) -> T:
        txn = self._inner_txn

        if not isinstance(txn, txn_type):
            raise TypeError(f"Last transaction is not of type {txn_type.__name__}!")

        return txn

    @property
    def payment(self) -> algopy.itxn.PaymentInnerTransaction:
        """
        Retrieve the last PaymentInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.PaymentInnerTransaction)

    @property
    def asset_config(self) -> algopy.itxn.AssetConfigInnerTransaction:
        """
        Retrieve the last AssetConfigInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetConfigInnerTransaction)

    @property
    def asset_transfer(self) -> algopy.itxn.AssetTransferInnerTransaction:
        """
        Retrieve the last AssetTransferInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetTransferInnerTransaction)

    @property
    def asset_freeze(self) -> algopy.itxn.AssetFreezeInnerTransaction:
        """
        Retrieve the last AssetFreezeInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetFreezeInnerTransaction)

    @property
    def application_call(self) -> algopy.itxn.ApplicationCallInnerTransaction:
        """
        Retrieve the last ApplicationCallInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.ApplicationCallInnerTransaction)

    @property
    def key_registration(self) -> algopy.itxn.KeyRegistrationInnerTransaction:
        """
        Retrieve the last KeyRegistrationInnerTransaction.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.KeyRegistrationInnerTransaction)

    @property
    def transaction(self) -> algopy.itxn.InnerTransactionResult:
        """
        Retrieve the last InnerTransactionResult.

        Raises:
            ValueError: If the transaction is not found or not of the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.InnerTransactionResult)


class ITxnGroupLoader:
    @overload
    def __getitem__(self, index: int) -> ITxnLoader: ...

    @overload
    def __getitem__(self, index: slice) -> list[ITxnLoader]: ...

    def __getitem__(self, index: int | slice) -> ITxnLoader | list[ITxnLoader]:
        if isinstance(index, int):
            return ITxnLoader(self._inner_txn_group[index])
        elif isinstance(index, slice):
            return [ITxnLoader(self._inner_txn_group[i]) for i in range(*index.indices(len(self)))]
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._inner_txn_group)

    def __init__(self, inner_txn_group: Sequence[InnerTransactionResultType]):
        self._inner_txn_group = inner_txn_group

    def _get_itxn(self, index: int, txn_type: type[T]) -> T:
        try:
            txn = self._inner_txn_group[index]
        except IndexError as err:
            raise ValueError(f"No inner transaction available at index {index}!") from err

        if not isinstance(txn, txn_type):
            raise TypeError(f"Last transaction is not of type {txn_type.__name__}!")

        return txn

    def payment(self, index: int) -> algopy.itxn.PaymentInnerTransaction:
        import algopy

        return ITxnLoader(self._get_itxn(index, algopy.itxn.PaymentInnerTransaction)).payment

    def asset_config(self, index: int) -> algopy.itxn.AssetConfigInnerTransaction:
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetConfigInnerTransaction)

    def asset_transfer(self, index: int) -> algopy.itxn.AssetTransferInnerTransaction:
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetTransferInnerTransaction)

    def asset_freeze(self, index: int) -> algopy.itxn.AssetFreezeInnerTransaction:
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetFreezeInnerTransaction)

    def application_call(self, index: int) -> algopy.itxn.ApplicationCallInnerTransaction:
        import algopy

        return self._get_itxn(index, algopy.itxn.ApplicationCallInnerTransaction)

    def key_registration(self, index: int) -> algopy.itxn.KeyRegistrationInnerTransaction:
        import algopy

        return self._get_itxn(index, algopy.itxn.KeyRegistrationInnerTransaction)

    def transaction(self, index: int) -> algopy.itxn.InnerTransactionResult:
        import algopy

        return self._get_itxn(index, algopy.itxn.InnerTransactionResult)


@dataclass
class ARC4Factory:
    def __init__(self, *, context: AlgopyTestContext) -> None:
        self._context = context

    def any_address(self) -> algopy.arc4.Address:
        """Generate a random Algorand address.

        Returns:
            algopy.arc4.Address: A new, random Algorand address.
        """
        import algopy

        return algopy.arc4.Address(algosdk.account.generate_account()[1])

    def any_uint8(self, min_value: int = 0, max_value: int = MAX_UINT8) -> algopy.arc4.UInt8:
        """Generate a random UInt8 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to MAX_UINT8.

        Returns:
            algopy.arc4.UInt8: A random UInt8 value.

        Raises:
            AssertionError: If values are out of UInt8 range.
        """
        import algopy

        return algopy.arc4.UInt8(generate_random_int(min_value, max_value))

    def any_uint16(self, min_value: int = 0, max_value: int = MAX_UINT16) -> algopy.arc4.UInt16:
        """Generate a random UInt16 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to MAX_UINT16.

        Returns:
            algopy.arc4.UInt16: A random UInt16 value.

        Raises:
            AssertionError: If values are out of UInt16 range.
        """
        import algopy

        return algopy.arc4.UInt16(generate_random_int(min_value, max_value))

    def any_uint32(self, min_value: int = 0, max_value: int = MAX_UINT32) -> algopy.arc4.UInt32:
        """Generate a random UInt32 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to MAX_UINT32.

        Returns:
            algopy.arc4.UInt32: A random UInt32 value.

        Raises:
            AssertionError: If values are out of UInt32 range.
        """
        import algopy

        return algopy.arc4.UInt32(generate_random_int(min_value, max_value))

    def any_uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.arc4.UInt64:
        """Generate a random UInt64 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to MAX_UINT64.

        Returns:
            algopy.arc4.UInt64: A random UInt64 value.

        Raises:
            AssertionError: If values are out of UInt64 range.
        """
        import algopy

        return algopy.arc4.UInt64(generate_random_int(min_value, max_value))

    def any_biguint128(
        self, min_value: int = 0, max_value: int = (1 << 128) - 1
    ) -> algopy.arc4.UInt128:
        """Generate a random UInt128 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to (2^128 - 1).

        Returns:
            algopy.arc4.UInt128: A random UInt128 value.

        Raises:
            AssertionError: If values are out of UInt128 range.
        """
        import algopy

        return algopy.arc4.UInt128(generate_random_int(min_value, max_value))

    def any_biguint256(
        self, min_value: int = 0, max_value: int = (1 << 256) - 1
    ) -> algopy.arc4.UInt256:
        """Generate a random UInt256 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to (2^256 - 1).

        Returns:
            algopy.arc4.UInt256: A random UInt256 value.

        Raises:
            AssertionError: If values are out of UInt256 range.
        """
        import algopy

        return algopy.arc4.UInt256(generate_random_int(min_value, max_value))

    def any_biguint512(
        self, min_value: int = 0, max_value: int = MAX_UINT512
    ) -> algopy.arc4.UInt512:
        """Generate a random UInt512 within the specified range.

        Args:
            min_value (int): Minimum value (inclusive). Defaults to 0.
            max_value (int): Maximum value (inclusive). Defaults to MAX_UINT512.

        Returns:
            algopy.arc4.UInt512: A random UInt512 value.

        Raises:
            AssertionError: If values are out of UInt512 range.
        """
        import algopy

        return algopy.arc4.UInt512(generate_random_int(min_value, max_value))

    def any_dynamic_bytes(self, n: int) -> algopy.arc4.DynamicBytes:
        """Generate a random dynamic bytes of size `n` bits.

        Args:
            n (int): The number of bits for the dynamic bytes. Must be a multiple of 8, otherwise
                the last byte will be truncated.

        Returns:
            algopy.arc4.DynamicBytes: A new, random dynamic bytes of size `n` bits.
        """
        import secrets

        import algopy

        # rounding up
        num_bytes = (n + 7) // 8
        random_bytes = secrets.token_bytes(num_bytes)

        # trim to exact bit length if necessary
        if n % 8 != 0:
            last_byte = random_bytes[-1]
            mask = (1 << (n % 8)) - 1
            random_bytes = random_bytes[:-1] + bytes([last_byte & mask])

        return algopy.arc4.DynamicBytes(random_bytes)

    def any_string(self, n: int) -> algopy.arc4.String:
        """Generate a random string of size `n` bits.

        Args:
            n (int): The number of bits for the string.

        Returns:
            algopy.arc4.String: A new, random string of size `n` bits.
        """
        import secrets
        import string

        import algopy

        # Calculate the number of characters needed (rounding up)
        num_chars = (n + 7) // 8

        # Generate random string
        random_string = "".join(secrets.choice(string.printable) for _ in range(num_chars))

        # Trim to exact bit length if necessary
        if n % 8 != 0:
            last_char = ord(random_string[-1])
            mask = (1 << (n % 8)) - 1
            random_string = random_string[:-1] + chr(last_char & mask)

        return algopy.arc4.String(random_string)


@dataclass
class AlgopyTestContext:
    _arc4: ARC4Factory

    def __init__(
        self,
        *,
        default_creator: algopy.Account | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        import algopy

        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

        self._active_contract: algopy_testing.Contract | algopy_testing.ARC4Contract | None = None
        self._contracts: list[algopy_testing.Contract | algopy_testing.ARC4Contract] = []
        self._app_id_to_contract: dict[
            int, algopy_testing.Contract | algopy_testing.ARC4Contract
        ] = {}
        self._txn_fields: TxnFields = {}
        self._gtxns: list[algopy.gtxn.TransactionBase] = []
        self._active_transaction_index: int | None = None
        self._application_data: dict[int, ApplicationFields] = {}
        self._application_logs: dict[int, list[bytes]] = {}
        self._asset_data: dict[int, AssetFields] = {}
        self._inner_transaction_groups: list[Sequence[InnerTransactionResultType]] = []
        self._constructing_inner_transaction_group: list[InnerTransactionResultType] = []
        self._constructing_inner_transaction: InnerTransactionResultType | None = None
        self._scratch_spaces: dict[str, list[algopy.Bytes | algopy.UInt64 | bytes | int]] = {}
        self._template_vars: dict[str, Any] = template_vars or {}
        self._blocks: dict[int, dict[str, int]] = {}
        self._boxes: dict[bytes, bytes] = {}
        self._lsigs: dict[algopy.LogicSig, Callable[[], algopy.UInt64 | bool]] = {}
        self._active_lsig_args: Sequence[algopy.Bytes] = []
        # using defaultdict here because there should be an AccountContextData for any
        # account, it defaults to an account with no balance
        self._account_data = defaultdict[str, AccountContextData](get_empty_account)

        self.default_creator: algopy.Account = default_creator or algopy.Account(
            algosdk.account.generate_account()[1]
        )
        self._account_data[self.default_creator.public_key] = get_empty_account()

        self._global_fields: GlobalFields = {
            "min_txn_fee": algopy.UInt64(algosdk.constants.MIN_TXN_FEE),
            "min_balance": algopy.UInt64(DEFAULT_ACCOUNT_MIN_BALANCE),
            "max_txn_life": algopy.UInt64(DEFAULT_MAX_TXN_LIFE),
            "zero_address": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "creator_address": self.default_creator,
            "asset_create_min_balance": algopy.UInt64(DEFAULT_ASSET_CREATE_MIN_BALANCE),
            "asset_opt_in_min_balance": algopy.UInt64(DEFAULT_ASSET_OPT_IN_MIN_BALANCE),
            "genesis_hash": algopy.Bytes(DEFAULT_GLOBAL_GENESIS_HASH),
        }

        self._arc4 = ARC4Factory(context=self)

    @property
    def arc4(self) -> ARC4Factory:
        return self._arc4

    def patch_global_fields(self, **global_fields: Unpack[GlobalFields]) -> None:
        """
        Patch 'Global' fields in the test context.

        Args:
            **global_fields: Key-value pairs for global fields.

        Raises:
            AttributeError: If a key is invalid.
        """
        invalid_keys = global_fields.keys() - GlobalFields.__annotations__.keys()

        if invalid_keys:
            raise AttributeError(
                f"Invalid field(s) found during patch for `Global`: {', '.join(invalid_keys)}"
            )

        self._global_fields.update(global_fields)

    def patch_txn_fields(self, **txn_fields: Unpack[TxnFields]) -> None:
        """
        Patch 'algopy.Txn' fields in the test context.

        Args:
            **txn_fields: Key-value pairs for transaction fields.

        Raises:
            AttributeError: If a key is invalid.
        """
        invalid_keys = txn_fields.keys() - TxnFields.__annotations__.keys()
        if invalid_keys:
            raise AttributeError(
                f"Invalid field(s) found during patch for `Txn`: {', '.join(invalid_keys)}"
            )

        self._txn_fields.update(txn_fields)

    def get_application_for_contract(
        self, contract: algopy.Contract | algopy.ARC4Contract
    ) -> algopy.Application:
        for app_id, app_contract in self._app_id_to_contract.items():
            if app_contract == contract:
                return self.get_application(app_id)
        raise ValueError("Contract not found in testing context!")

    def set_scratch_space(
        self, txn: str, scratch_space: dict[int, algopy.Bytes | algopy.UInt64 | bytes | int]
    ) -> None:
        new_scratch_space: list[algopy.Bytes | algopy.UInt64 | bytes | int] = [0] * 256
        # insert values to list at specific indexes, use key as index and value as value to set
        for index, value in scratch_space.items():
            new_scratch_space[index] = value

        self._scratch_spaces[str(txn)] = new_scratch_space

    def set_active_contract(self, contract: algopy.Contract | algopy.ARC4Contract) -> None:
        """
        Set the active contract for the current context. By default, invoked automatically
        as part of invocation of any app calls against instances
        of Contract or ARC4Contract classes.

        Args:
            contract (algopy.Contract | algopy.ARC4Contract): The contract to set as active.

        Returns:
            None
        """
        self._active_contract = contract
        app = self.get_application_for_contract(contract)
        self._global_fields["current_application_address"] = app.address
        self._global_fields["current_application_id"] = app

    def set_template_var(self, name: str, value: Any) -> None:
        """
        Set a template variable for the current context.

        Args:
            name (str): The name of the template variable.
            value (Any): The value to assign to the template variable.

        Returns:
            None
        """
        self._template_vars[name] = value

    def get_account(self, address: str) -> algopy.Account:
        """
        Retrieve an account by address.

        Args:
            address (str): Account address.

        Returns:
            algopy.Account: The account associated with the address.
        """
        return algopy_testing.Account(address)

    def get_account_data(self) -> dict[str, AccountContextData]:
        """
        Retrieve all account data.

        Returns:
            dict[str, AccountContextData]: The account data.
        """
        return self._account_data

    def get_asset_data(self) -> dict[int, AssetFields]:
        """
        Retrieve all asset data.

        Returns:
            dict[int, AssetFields]: The asset data.
        """
        return self._asset_data

    def get_application_data(self) -> dict[int, ApplicationFields]:
        """
        Retrieve all application data.

        Returns:
            dict[int, ApplicationFields]: The application data.
        """
        return self._application_data

    def update_account(self, address: str, **account_fields: Unpack[AccountFields]) -> None:
        """
        Update an existing account.

        Args:
            address (str): Account address.
            **account_fields: New account data.

        Raises:
            TypeError: If the provided object is not an instance of `Account`.
        """
        _assert_address_is_valid(address)
        self._account_data[address].fields.update(account_fields)

    def get_opted_asset_balance(
        self, account: algopy.Account, asset_id: algopy.UInt64
    ) -> algopy.UInt64 | None:
        """
        Retrieve the opted asset balance for an account and asset ID.

        Args:
            account (algopy.Account): Account to retrieve the balance for.
            asset_id (algopy.UInt64): Asset ID.

        Returns:
            algopy.UInt64 | None: The opted asset balance or None if not opted in.
        """

        response = self._account_data[account.public_key].opted_asset_balances.get(asset_id, None)

        return response

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        """
        Retrieve an asset by ID.

        Args:
            asset_id (int): Asset ID.

        Returns:
            algopy.Asset: The asset associated with the ID.
        """
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id

        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")

        return algopy.Asset(asset_id)

    def update_asset(self, asset_id: int, **asset_fields: Unpack[AssetFields]) -> None:
        """
        Update an existing asset.

        Args:
            asset_id (int): Asset ID.
            **asset_fields: New asset data.
        """
        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")

        self._asset_data[asset_id].update(asset_fields)

    def get_application(self, app_id: algopy.UInt64 | int) -> algopy.Application:
        """
        Retrieve an application by ID.

        Args:
            app_id (int): Application ID.

        Returns:
            algopy.Application: The application associated with the ID.
        """
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id

        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        return algopy.Application(app_id)

    def update_application(
        self, app_id: int, **application_fields: Unpack[ApplicationFields]
    ) -> None:
        """
        Update an existing application.

        Args:
            app_id (int): Application ID.
            **application_fields: New application data.
        """
        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        self._application_data[app_id].update(application_fields)

    def _append_inner_transaction_group(
        self,
        itxn: Sequence[InnerTransactionResultType],
    ) -> None:
        """
        Append a group of inner transactions to the context.

        Args:
            itxn (Sequence[InnerTransactionResultType]): The group of inner transactions to append.
        """
        import algopy.itxn

        self._inner_transaction_groups.append(cast(list[algopy.itxn.InnerTransactionResult], itxn))

    def get_submitted_itxn_groups(self) -> list[Sequence[InnerTransactionResultType]]:
        """
        Retrieve the number of inner transaction groups.

        Returns:
            int: The number of inner transaction groups.
        """
        return self._inner_transaction_groups

    def get_submitted_itxn_group(self, index: int) -> ITxnGroupLoader:
        """
        Retrieve the last group of inner transactions.

        Returns:
            Sequence[algopy.itxn.InnerTransactionResult]: The last group of inner transactions.

        Raises:
            ValueError: If no inner transaction groups have been submitted yet.
        """

        if not self._inner_transaction_groups:
            raise ValueError("No inner transaction groups submitted yet!")

        try:
            return ITxnGroupLoader(self._inner_transaction_groups[index])
        except IndexError as err:
            raise ValueError(f"No inner transaction group available at index {index}!") from err

    @property
    def last_submitted_itxn(self) -> ITxnLoader:
        """
        Retrieve the last submitted inner transaction from the
        last inner transaction group (if both exist).

        Returns:
            ITxnLoader: The last submitted inner transaction loader.

        Raises:
            ValueError: If no inner transactions exist in the last inner transaction group.
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
        """
        Generate and add a new account with a random address.

        Returns:
            algopy.Account: The newly generated account.
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
        """
        Generate and add a new asset with a unique ID.

        Returns:
            algopy.Asset: The newly generated asset.
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
            "creator": self.default_creator,
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
        """
        Generate and add a new application with a unique ID.

        Args:
            id (int | None): Optional application ID. If not provided, a new ID will be generated.
            address (algopy.Account | None): Optional application address. If not provided,
            it will be generated.
            **application_fields: Additional application fields.

        Returns:
            algopy.Application: The newly generated application.
        """
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
            "creator": self.default_creator,
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

        self._application_data[int(new_app.id)] = app_fields

        return new_app

    def add_application_logs(
        self,
        *,
        app_id: algopy.UInt64 | algopy.Application | int,
        logs: bytes | list[bytes],
        prepend_arc4_prefix: bool = False,
    ) -> None:
        """
        Add logs for an application.

        Args:
            app_id (int): The ID of the application.
            logs (bytes | list[bytes]): A single log entry or a list of log entries.
        """
        import algopy

        raw_app_id = (
            int(app_id)
            if isinstance(app_id, algopy.UInt64)
            else int(app_id.id)
            if isinstance(app_id, algopy.Application)
            else app_id
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
        """
        Retrieve the application logs for a given app ID.

        Args:
            app_id (int): The ID of the application.

        Returns:
            list[bytes]: The application logs for the given app ID.
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
        """
        Set the block seed and timestamp for block at index `index`.
        """
        self._blocks[index] = {"seed": int(seed), "timestamp": int(timestamp)}

    def set_transaction_group(
        self, gtxn: list[algopy.gtxn.TransactionBase], active_transaction_index: int | None = None
    ) -> None:
        """
        Set the transaction group using a list of transactions.

        Args:
            gtxn (list[algopy.gtxn.TransactionBase]): List of transactions.
            active_transaction_index (int, optional): Index of the active transaction.
            Defaults to None.
        """
        self._gtxns = gtxn

        if active_transaction_index is not None:
            self.set_active_transaction_index(active_transaction_index)

    def add_transactions(
        self,
        gtxns: list[algopy.gtxn.TransactionBase],
    ) -> None:
        """
        Add transactions to the current transaction group.

        Args:
            gtxns (list[algopy.gtxn.TransactionBase]): List of transactions to add.

        Raises:
            ValueError: If any transaction is not an instance of TransactionBase or if the total
            number of transactions exceeds the group limit.
        """
        # ensure that new len after append is at most 16 txns in a group
        import algopy.gtxn

        if not all(isinstance(txn, algopy.gtxn.TransactionBase) for txn in gtxns):  # type: ignore[arg-type, unused-ignore]
            raise ValueError("All transactions must be instances of TransactionBase")

        if len(self._gtxns) + len(gtxns) > algosdk.constants.TX_GROUP_LIMIT:
            raise ValueError(
                f"Transaction group can have at most {algosdk.constants.TX_GROUP_LIMIT} "
                "transactions, as per AVM limits."
            )

        self._gtxns.extend(gtxns)

        # iterate and refresh group_index to match the order of transactions
        for i, txn in enumerate(self._gtxns):
            txn._fields["group_index"] = i

    def get_transaction_group(self) -> list[algopy.gtxn.TransactionBase]:
        """
        Retrieve the current transaction group.

        Returns:
            list[algopy.gtxn.TransactionBase]: The current transaction group.
        """
        return self._gtxns

    def set_active_transaction_index(self, index: int) -> None:
        """
        Set the index of the active transaction.

        Args:
            index (int): The index of the active transaction.
        """
        self._active_transaction_index = index

    def get_active_application(self) -> algopy.Application:
        if self._active_contract is None:
            raise ValueError("no active contract")
        return self.get_application_for_contract(self._active_contract)

    def get_active_transaction(
        self,
    ) -> algopy.gtxn.Transaction:
        """
        Retrieve the active transaction.

        Returns:
            algopy.gtxn.Transaction | None: The active transaction if it exists, otherwise None.

        Raises:
            ValueError: If no active transaction is found.
        """
        import algopy

        if self._active_transaction_index is None:
            raise ValueError("No active transaction found")
        active_txn = self._gtxns[self._active_transaction_index]
        return typing.cast(algopy.gtxn.Transaction, active_txn)

    def any_uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.UInt64:
        """
        Generate a random UInt64 value within a specified range.

        Args:
            min_value (int, optional): Minimum value. Defaults to 0.
            max_value (int, optional): Maximum value. Defaults to MAX_UINT64.

        Returns:
            algopy.UInt64: The randomly generated UInt64 value.

        Raises:
            ValueError: If `max_value` exceeds MAX_UINT64 or `min_value` exceeds `max_value`.
        """
        import algopy

        if max_value > MAX_UINT64:
            raise ValueError("max_value must be less than or equal to MAX_UINT64")
        if min_value > max_value:
            raise ValueError("min_value must be less than or equal to max_value")

        return algopy.UInt64(generate_random_int(min_value, max_value))

    def any_bytes(self, length: int = MAX_BYTES_SIZE) -> algopy.Bytes:
        """
        Generate a random byte sequence of a specified length.

        Args:
            length (int, optional): Length of the byte sequence. Defaults to MAX_BYTES_SIZE.

        Returns:
            algopy.Bytes: The randomly generated byte sequence.
        """
        import algopy

        return algopy.Bytes(secrets.token_bytes(length))

    def any_string(self, length: int = MAX_BYTES_SIZE) -> algopy.String:
        """
        Generate a random string of a specified length.
        """
        import algopy

        return algopy.String(
            "".join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(length))
        )

    def any_application_call_transaction(  # type: ignore[misc] # noqa: PLR0913
        self,
        app_id: algopy.Application,
        app_args: Sequence[algopy.Bytes] = (),
        accounts: Sequence[algopy.Account] = (),
        assets: Sequence[algopy.Asset] = (),
        apps: Sequence[algopy.Application] = (),
        approval_program_pages: Sequence[algopy.Bytes] = (),
        clear_state_program_pages: Sequence[algopy.Bytes] = (),
        scratch_space: dict[int, algopy.Bytes | algopy.UInt64 | int | bytes] | None = None,
        **kwargs: Unpack[_ApplicationCallFields],
    ) -> algopy.gtxn.ApplicationCallTransaction:
        """
        Generate a new application call transaction with specified fields.

        Args:
            **kwargs (Unpack[ApplicationCallFields]): Fields to be set in the transaction.

        Returns:
            algopy.gtxn.ApplicationCallTransaction: The newly generated application
            call transaction.
        """
        import algopy.gtxn

        if not isinstance(app_id, algopy.Application):
            raise TypeError("`app_id` must be an instance of algopy.Application")
        if int(app_id.id) not in self._application_data:
            raise ValueError(
                f"algopy.Application with ID {app_id.id} not found in testing context!"
            )

        dynamic_params = {
            "app_id": lambda: app_id,
            "app_args": lambda index: app_args[index],
            "accounts": lambda index: accounts[index],
            "assets": lambda index: assets[index],
            "apps": lambda index: apps[index],
            "approval_program_pages": lambda index: approval_program_pages[index],
            "clear_state_program_pages": lambda index: clear_state_program_pages[index],
        }
        new_txn = algopy.gtxn.ApplicationCallTransaction(NULL_GTXN_GROUP_INDEX)

        merged_params = dict(ChainMap(kwargs, dynamic_params))
        for key, value in merged_params.items():
            setattr(new_txn, key, value)

        self.set_scratch_space(new_txn.txn_id, scratch_space or {})

        return new_txn

    def any_asset_transfer_transaction(
        self, **kwargs: Unpack[AssetTransferFields]
    ) -> algopy.gtxn.AssetTransferTransaction:
        """
        Generate a new asset transfer transaction with specified fields.

        Args:
            **kwargs (Unpack[AssetTransferFields]): Fields to be set in the transaction.

        Returns:
            algopy.gtxn.AssetTransferTransaction: The newly generated asset transfer transaction.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.AssetTransferTransaction(NULL_GTXN_GROUP_INDEX)

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def any_payment_transaction(
        self, **kwargs: Unpack[PaymentFields]
    ) -> algopy.gtxn.PaymentTransaction:
        """
        Generate a new payment transaction with specified fields.

        Args:
            **kwargs (Unpack[PaymentFields]): Fields to be set in the transaction.

        Returns:
            algopy.gtxn.PaymentTransaction: The newly generated payment transaction.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.PaymentTransaction(NULL_GTXN_GROUP_INDEX)

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def any_asset_config_transaction(
        self, **kwargs: Unpack[AssetConfigFields]
    ) -> algopy.gtxn.AssetConfigTransaction:
        """
        Generate a new ACFG transaction with specified fields.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.AssetConfigTransaction(NULL_GTXN_GROUP_INDEX)

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def any_key_registration_transaction(
        self, **kwargs: Unpack[KeyRegistrationFields]
    ) -> algopy.gtxn.KeyRegistrationTransaction:
        """
        Generate a new key registration transaction with specified fields.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.KeyRegistrationTransaction(NULL_GTXN_GROUP_INDEX)

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def any_asset_freeze_transaction(
        self, **kwargs: Unpack[AssetFreezeFields]
    ) -> algopy.gtxn.AssetFreezeTransaction:
        """
        Generate a new asset freeze transaction with specified fields.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.AssetFreezeTransaction(NULL_GTXN_GROUP_INDEX)

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def any_transaction(  # type: ignore[misc]
        self,
        type: algopy.TransactionType,  # noqa: A002
        **kwargs: Unpack[TransactionFields],
    ) -> algopy.gtxn.Transaction:
        """
        Generate a new transaction with specified fields.

        Args:
            type (algopy.TransactionType): Transaction type.
            **kwargs (Unpack[TransactionFields]): Fields to be set in the transaction.

        Returns:
            algopy.gtxn.Transaction: The newly generated transaction.
        """
        import algopy.gtxn

        new_txn = algopy.gtxn.Transaction(NULL_GTXN_GROUP_INDEX, type=type)  # type: ignore[arg-type, unused-ignore]

        for key, value in kwargs.items():
            setattr(new_txn, key, value)

        return new_txn

    def does_box_exist(self, name: algopy.Bytes | bytes) -> bool:
        """return true if the box with the given name exists."""
        name_bytes = name if isinstance(name, bytes) else name.value
        return name_bytes in self._boxes

    def get_box(self, name: algopy.Bytes | bytes) -> bytes:
        """Get the content of a box."""

        name_bytes = name if isinstance(name, bytes) else name.value
        return self._boxes.get(name_bytes, b"")

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        """Set the content of a box."""

        name_bytes = name if isinstance(name, bytes) else name.value
        content_bytes = content if isinstance(content, bytes) else content.value
        self._boxes[name_bytes] = content_bytes

    def execute_logicsig(
        self, lsig: algopy.LogicSig, lsig_args: Sequence[algopy.Bytes] | None = None
    ) -> bool | algopy.UInt64:
        self._active_lsig_args = lsig_args or []
        # TODO: refine LogicSig class to handle injects into context
        if lsig not in self._lsigs:
            self._lsigs[lsig] = lsig.func
        return lsig.func()

    def clear_box(self, name: algopy.Bytes | bytes) -> bool:
        """Clear the content of a box."""

        name_bytes = name if isinstance(name, bytes) else name.value
        if name_bytes in self._boxes:
            del self._boxes[name_bytes]
            return True
        return False

    def clear_all_boxes(self) -> None:
        """Clear all boxes."""
        self._boxes.clear()

    def clear_inner_transaction_groups(self) -> None:
        """
        Clear all inner transactions.
        """
        self._inner_transaction_groups.clear()

    def clear_transaction_group(self) -> None:
        """
        Clear the transaction group.
        """
        self._gtxns.clear()

    def clear_accounts(self) -> None:
        """
        Clear all accounts.
        """
        self._account_data.clear()

    def clear_applications(self) -> None:
        """
        Clear all applications.
        """
        self._application_data.clear()

    def clear_assets(self) -> None:
        """
        Clear all assets.
        """
        self._asset_data.clear()

    def clear_application_logs(self) -> None:
        """
        Clear all application logs.
        """
        self._application_logs.clear()

    def clear_scratch_spaces(self) -> None:
        """
        Clear all scratch spaces.
        """
        self._scratch_spaces.clear()

    def clear_active_transaction_index(self) -> None:
        """
        Clear the active transaction index.
        """
        self._active_transaction_index = None

    def clear_active_contract(self) -> None:
        """
        Clear the active contract.
        """
        self._active_contract = None

    def clear(self) -> None:
        """
        Clear all data, including accounts, applications, assets, inner transactions,
        transaction groups, and application_logs.
        """
        self.clear_accounts()
        self.clear_applications()
        self.clear_assets()
        self.clear_inner_transaction_groups()
        self.clear_transaction_group()
        self.clear_application_logs()
        self.clear_scratch_spaces()
        self.clear_active_transaction_index()
        self.clear_active_contract()

    def reset(self) -> None:
        """
        Reset the test context to its initial state, clearing all data and resetting ID counters.
        """
        self._account_data = defaultdict(AccountContextData)
        self._application_data = {}
        self._asset_data = {}
        self._active_transaction_index = None
        self._scratch_spaces = {}
        self._inner_transaction_groups = []
        self._gtxns = []
        self._global_fields = {}
        self._txn_fields = {}
        self._application_logs = {}
        self._asset_id = iter(range(1, 2**64))
        self._app_id = iter(range(1, 2**64))


_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


def get_test_context() -> AlgopyTestContext:
    result = _var.get()
    if result is None:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to "
            "access the context manager."
        )
    return result


@contextmanager
def algopy_testing_context(
    *,
    default_creator: algopy.Account | None = None,
) -> Generator[AlgopyTestContext, None, None]:
    token = _var.set(
        AlgopyTestContext(
            default_creator=default_creator,
        )
    )
    try:
        yield _var.get()
    finally:
        _var.reset(token)


def _assert_address_is_valid(address: str) -> None:
    assert algosdk.encoding.is_valid_address(address), "Invalid Algorand address supplied!"
