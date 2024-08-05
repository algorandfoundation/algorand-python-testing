from __future__ import annotations

import typing

from algopy_testing.enums import TransactionType
from algopy_testing.models.txn_fields import TransactionFieldsBase

if typing.TYPE_CHECKING:

    import algopy


__all__ = [
    "ApplicationCallTransaction",
    "AssetConfigTransaction",
    "AssetFreezeTransaction",
    "AssetTransferTransaction",
    "KeyRegistrationTransaction",
    "PaymentTransaction",
    "Transaction",
    "TransactionBase",
]


class TransactionBase(TransactionFieldsBase):
    type_enum: TransactionType

    # since the only thing that matters is that the implementation matches the stubs
    # we can define all the fields in TransactionBase
    def __init__(self, group_index: algopy.UInt64 | int):
        self._group_index = int(group_index)
        self._is_context_mapped = False
        # indicates this instance has field mappings on the context

    @classmethod
    def new(cls) -> typing.Self:
        instance = cls(0)
        instance._is_context_mapped = True
        return instance

    @property
    def key_txn(self) -> TransactionBase:
        from algopy_testing.context import get_test_context

        if self._is_context_mapped:
            return self

        # positive values are indexes into the current group
        # find the canonical instance
        context = get_test_context()
        try:
            txn = context._current_transaction_group[self._group_index]
        except IndexError:
            raise ValueError("invalid group index") from None
        return txn

    @property
    def fields(self) -> dict[str, object]:
        from algopy_testing.context import get_test_context

        context = get_test_context()
        try:
            return context._gtxns[self.key_txn]
        except KeyError:
            raise ValueError(
                "invalid transaction group id,"
                " ensure transaction was created with the current AlgopyTestingContext"
            ) from None


class AssetTransferTransaction(TransactionBase):
    type_enum = TransactionType.AssetTransfer


class PaymentTransaction(TransactionBase):
    type_enum = TransactionType.Payment


class ApplicationCallTransaction(TransactionBase):
    type_enum = TransactionType.ApplicationCall


class KeyRegistrationTransaction(TransactionBase):
    type_enum = TransactionType.KeyRegistration


class AssetConfigTransaction(TransactionBase):
    type_enum = TransactionType.AssetConfig


class AssetFreezeTransaction(TransactionBase):
    type_enum = TransactionType.AssetFreeze


class Transaction(TransactionBase):
    type_enum = TransactionType.Payment
