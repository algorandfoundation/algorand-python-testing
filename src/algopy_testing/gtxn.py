from __future__ import annotations

import typing

from algopy_testing._context_storage import get_app_data, get_test_context
from algopy_testing.enums import TransactionType
from algopy_testing.models import Application
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
    def __init__(self, group_index_or_fields: algopy.UInt64 | int | dict[str, typing.Any]):
        if isinstance(group_index_or_fields, dict):
            self._fields: dict[str, typing.Any] | None = group_index_or_fields
            self._group_index = 0
        else:
            self._fields = None
            self._group_index = int(group_index_or_fields)

    @property
    def key_txn(self) -> TransactionBase:
        if self._fields is not None:
            return self

        return get_test_context().last_group.transactions[self._group_index]

    @property
    def fields(self) -> dict[str, object]:
        fields = self.key_txn._fields
        if fields is None:
            raise ValueError(
                "invalid transaction group,"
                " ensure transaction was created with the current AlgopyTestingContext"
            )
        return fields

    @property
    def app_id(self) -> algopy.Application:
        app_id: algopy.Application = self.fields["app_id"]  # type: ignore[assignment]
        app_data = get_app_data(int(app_id.id))
        if app_data.is_creating:
            # return zero app while creating
            return Application(0)
        return app_id


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
