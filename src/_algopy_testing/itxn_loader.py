from __future__ import annotations

import typing

from _algopy_testing import itxn
from _algopy_testing.enums import TransactionType

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    import algopy

    InnerTransactionResultType = (
        algopy.itxn.InnerTransactionResult
        | algopy.itxn.PaymentInnerTransaction
        | algopy.itxn.KeyRegistrationInnerTransaction
        | algopy.itxn.AssetConfigInnerTransaction
        | algopy.itxn.AssetTransferInnerTransaction
        | algopy.itxn.AssetFreezeInnerTransaction
        | algopy.itxn.ApplicationCallInnerTransaction
    )

_T = typing.TypeVar("_T")


class ITxnLoader:
    """A helper class for handling access to individual inner transactions in test
    context.

    This class provides methods to access and retrieve specific types of inner
    transactions. It performs type checking and conversion for various transaction
    types.
    """

    _TXN_TYPE_MAP: typing.ClassVar = {
        itxn.PaymentInnerTransaction: TransactionType.Payment,
        itxn.AssetConfigInnerTransaction: TransactionType.AssetConfig,
        itxn.AssetTransferInnerTransaction: TransactionType.AssetTransfer,
        itxn.AssetFreezeInnerTransaction: TransactionType.AssetFreeze,
        itxn.ApplicationCallInnerTransaction: TransactionType.ApplicationCall,
        itxn.KeyRegistrationInnerTransaction: TransactionType.KeyRegistration,
        itxn.InnerTransactionResult: -1,
    }

    def __init__(self, inner_txn: InnerTransactionResultType):
        self._inner_txn = inner_txn

    def _get_itxn(self, txn_type: type[_T]) -> _T:
        if (
            not isinstance(self._inner_txn, txn_type)
            and getattr(self._inner_txn, "type", None) != self._TXN_TYPE_MAP[txn_type]
        ):
            raise TypeError(f"transaction is not of type {txn_type.__name__}!")
        return self._inner_txn  # type: ignore[return-value]

    @property
    def payment(self) -> algopy.itxn.PaymentInnerTransaction:
        """Retrieve the last PaymentInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.PaymentInnerTransaction)

    @property
    def asset_config(self) -> algopy.itxn.AssetConfigInnerTransaction:
        """Retrieve the last AssetConfigInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.AssetConfigInnerTransaction)

    @property
    def asset_transfer(self) -> algopy.itxn.AssetTransferInnerTransaction:
        """Retrieve the last AssetTransferInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.AssetTransferInnerTransaction)

    @property
    def asset_freeze(self) -> algopy.itxn.AssetFreezeInnerTransaction:
        """Retrieve the last AssetFreezeInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.AssetFreezeInnerTransaction)

    @property
    def application_call(self) -> algopy.itxn.ApplicationCallInnerTransaction:
        """Retrieve the last ApplicationCallInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.ApplicationCallInnerTransaction)

    @property
    def key_registration(self) -> algopy.itxn.KeyRegistrationInnerTransaction:
        """Retrieve the last KeyRegistrationInnerTransaction.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.KeyRegistrationInnerTransaction)

    @property
    def transaction(self) -> algopy.itxn.InnerTransactionResult:
        """Retrieve the last InnerTransactionResult.

        :raises ValueError: If the transaction is not found or not of the expected type.
        """
        return self._get_itxn(itxn.InnerTransactionResult)


class ITxnGroupLoader:
    """A helper class for handling access to groups of inner transactions in test
    context.

    This class provides methods to access and retrieve inner transactions from a group,
    either individually or as slices. It supports type-specific retrieval of inner
    transactions and implements indexing operations.
    """

    @typing.overload
    def __getitem__(self, index: int) -> ITxnLoader: ...

    @typing.overload
    def __getitem__(self, index: slice) -> list[ITxnLoader]: ...

    def __getitem__(self, index: int | slice) -> ITxnLoader | list[ITxnLoader]:
        if isinstance(index, int):
            return ITxnLoader(self._get_itxn(index))
        elif isinstance(index, slice):
            return [ITxnLoader(self._inner_txn_group[i]) for i in range(*index.indices(len(self)))]
        else:
            raise TypeError("Index must be int or slice")

    def __len__(self) -> int:
        return len(self._inner_txn_group)

    def __init__(self, inner_txn_group: Sequence[InnerTransactionResultType]):
        self._inner_txn_group = inner_txn_group

    def _get_itxn(self, index: int) -> InnerTransactionResultType:
        try:
            txn = self._inner_txn_group[index]
        except IndexError as err:
            raise ValueError(f"No inner transaction available at index {index}!") from err
        return txn

    def payment(self, index: int) -> algopy.itxn.PaymentInnerTransaction:
        """Return a PaymentInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The PaymentInnerTransaction at the given index.
        :raises TypeError: If the transaction is not found or not of
        """
        return ITxnLoader(self._get_itxn(index)).payment

    def asset_config(self, index: int) -> algopy.itxn.AssetConfigInnerTransaction:
        """Return an AssetConfigInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The AssetConfigInnerTransaction at the given index.
        :raises TypeError: If the transaction is not found or not of the expected type.
        """
        return ITxnLoader(self._get_itxn(index)).asset_config

    def asset_transfer(self, index: int) -> algopy.itxn.AssetTransferInnerTransaction:
        """Return an AssetTransferInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The AssetTransferInnerTransaction at the given index.
        """
        return ITxnLoader(self._get_itxn(index)).asset_transfer

    def asset_freeze(self, index: int) -> algopy.itxn.AssetFreezeInnerTransaction:
        """Return an AssetFreezeInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The AssetFreezeInnerTransaction at the given index.
        """
        return ITxnLoader(self._get_itxn(index)).asset_freeze

    def application_call(self, index: int) -> algopy.itxn.ApplicationCallInnerTransaction:
        """Return an ApplicationCallInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The ApplicationCallInnerTransaction at the given index.
        """
        return ITxnLoader(self._get_itxn(index)).application_call

    def key_registration(self, index: int) -> algopy.itxn.KeyRegistrationInnerTransaction:
        """Return a KeyRegistrationInnerTransaction from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The KeyRegistrationInnerTransaction at the given index.
        """
        return ITxnLoader(self._get_itxn(index)).key_registration

    def transaction(self, index: int) -> algopy.itxn.InnerTransactionResult:
        """Return an InnerTransactionResult from the group at the given index.

        :param index: The index of the transaction in the group.
        :returns: The InnerTransactionResult at the given index.
        """
        return ITxnLoader(self._get_itxn(index)).transaction
