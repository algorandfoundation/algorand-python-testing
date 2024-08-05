from __future__ import annotations

import secrets
import string
import typing
from collections import ChainMap, defaultdict
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

# Define the union type
from typing import TYPE_CHECKING, Any, Unpack, overload

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

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Sequence

    import algopy

    from algopy_testing.models.application import ApplicationFields
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

    InnerTransactionResultType = (
        algopy.itxn.InnerTransactionResult
        | algopy.itxn.PaymentInnerTransaction
        | algopy.itxn.KeyRegistrationInnerTransaction
        | algopy.itxn.AssetConfigInnerTransaction
        | algopy.itxn.AssetTransferInnerTransaction
        | algopy.itxn.AssetFreezeInnerTransaction
        | algopy.itxn.ApplicationCallInnerTransaction
    )

_TGlobalTxn = typing.TypeVar("_TGlobalTxn", bound=TransactionBase)
T = typing.TypeVar("T")

# temporary group_index value used for group transactions while arranging a test
# will be replaced with actual group index once a call is made or user sets transaction group
NULL_GTXN_GROUP_INDEX = -1


class ITxnLoader:
    """A helper class for handling access to individual inner transactions in
    test context.

    This class provides methods to access and retrieve specific types of
    inner transactions. It performs type checking and conversion for
    various transaction types.
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
        """Retrieve the last PaymentInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.PaymentInnerTransaction)

    @property
    def asset_config(self) -> algopy.itxn.AssetConfigInnerTransaction:
        """Retrieve the last AssetConfigInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetConfigInnerTransaction)

    @property
    def asset_transfer(self) -> algopy.itxn.AssetTransferInnerTransaction:
        """Retrieve the last AssetTransferInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetTransferInnerTransaction)

    @property
    def asset_freeze(self) -> algopy.itxn.AssetFreezeInnerTransaction:
        """Retrieve the last AssetFreezeInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.AssetFreezeInnerTransaction)

    @property
    def application_call(self) -> algopy.itxn.ApplicationCallInnerTransaction:
        """Retrieve the last ApplicationCallInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.ApplicationCallInnerTransaction)

    @property
    def key_registration(self) -> algopy.itxn.KeyRegistrationInnerTransaction:
        """Retrieve the last KeyRegistrationInnerTransaction.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.KeyRegistrationInnerTransaction)

    @property
    def transaction(self) -> algopy.itxn.InnerTransactionResult:
        """Retrieve the last InnerTransactionResult.

        :raises ValueError: If the transaction is not found or not of
            the expected type.
        """
        import algopy

        return self._get_itxn(algopy.itxn.InnerTransactionResult)


class ITxnGroupLoader:
    """A helper class for handling access to groups of inner transactions in
    test context.

    This class provides methods to access and retrieve inner
    transactions from a group, either individually or as slices. It
    supports type-specific retrieval of inner transactions and
    implements indexing operations.
    """

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
            raise TypeError(
                f"Inner transaction at index {index} is of "
                f"type '{type(txn).__name__}' not '{txn_type.__name__}'!"
            )

        return txn

    def payment(self, index: int) -> algopy.itxn.PaymentInnerTransaction:
        """Return a PaymentInnerTransaction from the group at the given index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.PaymentInnerTransaction: The
            PaymentInnerTransaction at the given index.
        """
        import algopy

        return ITxnLoader(self._get_itxn(index, algopy.itxn.PaymentInnerTransaction)).payment

    def asset_config(self, index: int) -> algopy.itxn.AssetConfigInnerTransaction:
        """Return an AssetConfigInnerTransaction from the group at the given
        index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.AssetConfigInnerTransaction: The
            AssetConfigInnerTransaction at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetConfigInnerTransaction)

    def asset_transfer(self, index: int) -> algopy.itxn.AssetTransferInnerTransaction:
        """Return an AssetTransferInnerTransaction from the group at the given
        index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.AssetTransferInnerTransaction: The
            AssetTransferInnerTransaction at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetTransferInnerTransaction)

    def asset_freeze(self, index: int) -> algopy.itxn.AssetFreezeInnerTransaction:
        """Return an AssetFreezeInnerTransaction from the group at the given
        index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.AssetFreezeInnerTransaction: The
            AssetFreezeInnerTransaction at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.AssetFreezeInnerTransaction)

    def application_call(self, index: int) -> algopy.itxn.ApplicationCallInnerTransaction:
        """Return an ApplicationCallInnerTransaction from the group at the
        given index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.ApplicationCallInnerTransaction: The
            ApplicationCallInnerTransaction at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.ApplicationCallInnerTransaction)

    def key_registration(self, index: int) -> algopy.itxn.KeyRegistrationInnerTransaction:
        """Return a KeyRegistrationInnerTransaction from the group at the given
        index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.KeyRegistrationInnerTransaction: The
            KeyRegistrationInnerTransaction at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.KeyRegistrationInnerTransaction)

    def transaction(self, index: int) -> algopy.itxn.InnerTransactionResult:
        """Return an InnerTransactionResult from the group at the given index.

        :param index: int
        :param index: int:
        :returns: algopy.itxn.InnerTransactionResult: The
            InnerTransactionResult at the given index.
        """
        import algopy

        return self._get_itxn(index, algopy.itxn.InnerTransactionResult)


@dataclass
class ARC4Factory:
    """Factory for generating ARC4-compliant test data."""

    def __init__(self, *, context: AlgopyTestContext) -> None:
        """Initializes the ARC4Factory with the given testing context.

        Args:
            context (AlgopyTestContext): The testing context for generating test data.
        """
        self._context = context

    def any_address(self) -> algopy.arc4.Address:
        """Generate a random Algorand address.

        :returns: A new, random Algorand address.
        :rtype: algopy.arc4.Address
        """

        return algopy_testing.arc4.Address(algosdk.account.generate_account()[1])

    def any_uint8(self, min_value: int = 0, max_value: int = MAX_UINT8) -> algopy.arc4.UInt8:
        """Generate a random UInt8 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT8.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT8)
        :returns: A random UInt8 value.
        :rtype: algopy.arc4.UInt8
        :raises AssertionError: If values are out of UInt8 range.
        """
        import algopy

        return algopy.arc4.UInt8(generate_random_int(min_value, max_value))

    def any_uint16(self, min_value: int = 0, max_value: int = MAX_UINT16) -> algopy.arc4.UInt16:
        """Generate a random UInt16 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT16.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT16)
        :returns: A random UInt16 value.
        :rtype: algopy.arc4.UInt16
        :raises AssertionError: If values are out of UInt16 range.
        """
        import algopy

        return algopy.arc4.UInt16(generate_random_int(min_value, max_value))

    def any_uint32(self, min_value: int = 0, max_value: int = MAX_UINT32) -> algopy.arc4.UInt32:
        """Generate a random UInt32 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT32.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT32)
        :returns: A random UInt32 value.
        :rtype: algopy.arc4.UInt32
        :raises AssertionError: If values are out of UInt32 range.
        """
        import algopy

        return algopy.arc4.UInt32(generate_random_int(min_value, max_value))

    def any_uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.arc4.UInt64:
        """Generate a random UInt64 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT64.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT64)
        :returns: A random UInt64 value.
        :rtype: algopy.arc4.UInt64
        :raises AssertionError: If values are out of UInt64 range.
        """
        import algopy

        return algopy.arc4.UInt64(generate_random_int(min_value, max_value))

    def any_biguint128(
        self, min_value: int = 0, max_value: int = (1 << 128) - 1
    ) -> algopy.arc4.UInt128:
        """Generate a random UInt128 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to (2^128 - 1).
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = (1 << 128) - 1)
        :returns: A random UInt128 value.
        :rtype: algopy.arc4.UInt128
        :raises AssertionError: If values are out of UInt128 range.
        """
        import algopy

        return algopy.arc4.UInt128(generate_random_int(min_value, max_value))

    def any_biguint256(
        self, min_value: int = 0, max_value: int = (1 << 256) - 1
    ) -> algopy.arc4.UInt256:
        """Generate a random UInt256 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to (2^256 - 1).
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = (1 << 256) - 1)
        :returns: A random UInt256 value.
        :rtype: algopy.arc4.UInt256
        :raises AssertionError: If values are out of UInt256 range.
        """
        import algopy

        return algopy.arc4.UInt256(generate_random_int(min_value, max_value))

    def any_biguint512(
        self, min_value: int = 0, max_value: int = MAX_UINT512
    ) -> algopy.arc4.UInt512:
        """Generate a random UInt512 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT512.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT512)
        :returns: A random UInt512 value.
        :rtype: algopy.arc4.UInt512
        :raises AssertionError: If values are out of UInt512 range.
        """
        import algopy

        return algopy.arc4.UInt512(generate_random_int(min_value, max_value))

    def any_dynamic_bytes(self, n: int) -> algopy.arc4.DynamicBytes:
        """Generate a random dynamic bytes of size `n` bits.

        :param n: The number of bits for the dynamic bytes. Must be a multiple of 8, otherwise
                the last byte will be truncated.
        :type n: int
        :param n: int:
        :returns: A new, random dynamic bytes of size `n` bits.
        :rtype: algopy.arc4.DynamicBytes
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

        :param n: The number of bits for the string.
        :type n: int
        :param n: int:
        :returns: A new, random string of size `n` bits.
        :rtype: algopy.arc4.String
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
        default_creator: algopy.Account | None = None,
        template_vars: dict[str, Any] | None = None,
    ) -> None:
        import algopy

        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

        self._active_contract: algopy_testing.Contract | None = None
        self._app_id_to_contract = dict[int, algopy_testing.Contract]()
        # TODO: combine these?
        self._gtxns: dict[algopy_testing.gtxn.TransactionBase, dict[str, object]] = {}
        self._active_txn_fields = dict[str, typing.Any]()
        self._scratch_spaces = defaultdict[
            algopy_testing.gtxn.TransactionBase, list[algopy.Bytes | algopy.UInt64]
        ](_get_scratch_slots)
        self._current_transaction_group = list[algopy_testing.gtxn.TransactionBase]()
        self._active_transaction_index: int | None = None
        self._application_data: dict[int, ApplicationFields] = {}
        # TODO: this map is from app_id to logs, should probably instead be stored against
        #       the appropriate txn
        self._application_logs: dict[int, list[bytes]] = {}
        self._asset_data: dict[int, AssetFields] = {}
        self._inner_transaction_groups: list[Sequence[InnerTransactionResultType]] = []
        self._constructing_inner_transaction_group: list[InnerTransactionResultType] = []
        self._constructing_inner_transaction: InnerTransactionResultType | None = None
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
        for app_id, app_contract in self._app_id_to_contract.items():
            if app_contract == contract:
                return self.get_application(app_id)
        raise ValueError("Contract not found in testing context!")

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
        app = self.get_application_for_contract(contract)
        self._global_fields["current_application_address"] = app.address
        self._global_fields["current_application_id"] = app

    def set_template_var(self, name: str, value: Any) -> None:
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
        return self._application_data

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

        self._application_data[app_id].update(application_fields)

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
        self, gtxn: list[algopy.gtxn.TransactionBase], active_transaction_index: int | None = None
    ) -> None:
        """Set the transaction group using a list of transactions.

        :param gtxn: List of transactions.
        :type gtxn: list[algopy.gtxn.TransactionBase]
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
        self._update_current_transaction_group(gtxn)

        if active_transaction_index is not None:
            self.set_active_transaction_index(active_transaction_index)

    def add_transactions(
        self,
        gtxns: list[algopy.gtxn.TransactionBase],
    ) -> None:
        """Add transactions to the current transaction group.

        :param gtxns: List of transactions to add.
        :type gtxns: list[algopy.gtxn.TransactionBase]
        :param gtxns: list[algopy.gtxn.TransactionBase]:
        :raises ValueError: If any transaction is not an instance of
            TransactionBase or if the total
        :raises ValueError: If any transaction is not an instance of
            TransactionBase or if the total number of transactions
            exceeds the group limit.
        """
        self._update_current_transaction_group([*self._current_transaction_group, *gtxns])

    def _update_current_transaction_group(
        self, group: list[algopy_testing.gtxn.TransactionBase | algopy.gtxn.TransactionBase]
    ) -> None:
        if not all(isinstance(txn, algopy_testing.gtxn.TransactionBase) for txn in group):
            raise ValueError("All transactions must be instances of TransactionBase")

        if len(group) > algosdk.constants.TX_GROUP_LIMIT:
            raise ValueError(
                f"Transaction group can have at most {algosdk.constants.TX_GROUP_LIMIT} "
                "transactions, as per AVM limits."
            )
        for i, txn in enumerate(group):
            txn.fields["group_index"] = algopy_testing.UInt64(i)
        self._current_transaction_group = group

    def get_transaction_group(self) -> Sequence[algopy.gtxn.TransactionBase]:
        """Retrieve the current transaction group.

        :returns: The current transaction group.
        :rtype: list[algopy.gtxn.TransactionBase]
        """
        return self._current_transaction_group

    def set_active_transaction_index(self, index: int) -> None:
        """Set the index of the active transaction.

        :param index: The index of the active transaction.
        :type index: int
        :param index: int:
        """
        # TODO: check active transaction is an app_call
        # NOTE: In case of can't the Txn refer to non app call txns? Otherwise not sure how htls lsig code compiles (see examples)
        self._active_transaction_index = index

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
            active_txn = self._current_transaction_group[index]
        except IndexError:
            raise ValueError("invalid group index") from None

        return typing.cast(algopy_testing.gtxn.Transaction, active_txn)

    def get_active_transaction(self) -> algopy.gtxn.Transaction:
        """Retrieve the active transaction.

        :returns: The active transaction.
        :rtype: algopy.gtxn.Transaction
        :raises ValueError: If no active transaction is found.
        """
        if self._active_transaction_index is None:
            raise ValueError("No active transaction found")

        return self.get_transaction(self._active_transaction_index)

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
    def set_txn_fields(self, **fields: Unpack[TransactionFields]) -> Generator[None, None, None]:
        last_txn = self._active_txn_fields
        self._active_txn_fields = fields  # type: ignore[assignment]
        try:
            yield
        finally:
            self._active_txn_fields = last_txn

    def _new_gtxn(self, txn_type: type[_TGlobalTxn], **fields: object) -> _TGlobalTxn:
        txn = txn_type.new()
        # TODO: check reference types are known?
        fields.setdefault("type", txn_type.type_enum)
        fields.setdefault("sender", self.default_creator)  # TODO: have a default sender too?

        self._gtxns[txn] = {**get_txn_defaults(), **fields}
        return txn

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
        :param name: algopy.Bytes | bytes:
        :returns: The content of the box.
        :rtype: bytes
        """

        name_bytes = name if isinstance(name, bytes) else name.value
        return self._boxes.get(name_bytes, b"")

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        """Set the content of a box.

        :param name: algopy.Bytes | bytes:
        :param content: algopy.Bytes | bytes:
        """

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
        self._current_transaction_group.clear()

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

    def clear_active_transaction_index(self) -> None:
        """Clear the active transaction index."""
        self._active_transaction_index = None

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
        self.clear_active_transaction_index()
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
        self._current_transaction_group = []
        self._global_fields = {}
        self._application_logs = {}
        self._asset_id = iter(range(1, 2**64))
        self._app_id = iter(range(1, 2**64))


_var: ContextVar[AlgopyTestContext] = ContextVar("_var")


def get_test_context() -> AlgopyTestContext:
    try:
        result = _var.get()
    except LookupError:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to "
            "access the context manager."
        ) from None
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


def _get_scratch_slots() -> list[algopy.Bytes | algopy.UInt64]:
    return [UInt64(0)] * 256
