from __future__ import annotations

import typing

from _algopy_testing.constants import MAX_ITEMS_IN_LOG
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.enums import TransactionType
from _algopy_testing.models import Application
from _algopy_testing.models.txn_fields import TransactionFieldsGetter, combine_into_max_byte_pages
from _algopy_testing.primitives import Bytes, UInt64
from _algopy_testing.utils import convert_native_to_stack, get_new_scratch_space

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

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


class TransactionBase(TransactionFieldsGetter):
    type_enum: TransactionType

    # since the only thing that matters is that the implementation matches the stubs
    # we can define all the fields in TransactionBase
    def __init__(self, group_index_or_fields: algopy.UInt64 | int | dict[str, typing.Any]):
        if isinstance(group_index_or_fields, dict):
            fields = group_index_or_fields
            for field in ("approval_program", "clear_state_program"):
                pages = fields[field]
                fields[field] = combine_into_max_byte_pages(pages)
            self._fields: dict[str, typing.Any] | None = fields
            self._group_index = 0
        else:
            self._fields = None
            self._group_index = int(group_index_or_fields)

        self._scratch_space = get_new_scratch_space()
        self._is_active = False

    @property
    def is_active(self) -> bool:
        return self._is_active

    @is_active.setter
    def is_active(self, value: bool) -> None:
        self._is_active = value
        if value:
            if "logs" in self.fields:
                raise RuntimeError("Cannot have existing logs for active transaction")
            self.fields["logs"] = []

    @property
    def key_txn(self) -> TransactionBase:
        if self._fields is not None:
            return self

        return lazy_context.active_group.txns[self._group_index]

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
        app_data = lazy_context.get_app_data(app_id)
        if app_data.is_creating:
            # return zero app while creating
            return Application(0)
        return app_id

    def append_log(self, log: bytes) -> None:
        if not self.is_active:
            raise RuntimeError("Can only add logs to active transaction")
        if self.type_enum != TransactionType.ApplicationCall:
            raise RuntimeError("Can only add logs to ApplicationCallTransaction!")
        logs = self.fields["logs"]
        assert isinstance(logs, list), "expected list"
        if len(logs) + 1 > MAX_ITEMS_IN_LOG:
            raise RuntimeError(
                f"Too many log calls in program, up to {MAX_ITEMS_IN_LOG} is allowed"
            )
        logs.append(log)

    def set_scratch_slot(
        self, index: UInt64 | int, value: algopy.Bytes | algopy.UInt64 | bytes | int
    ) -> None:
        index = int(index) if isinstance(index, UInt64) else index
        try:
            self._scratch_space[index] = convert_native_to_stack(value)
        except IndexError:
            raise ValueError("invalid scratch slot") from None

    def get_scratch_slot(self, index: UInt64 | int) -> algopy.UInt64 | algopy.Bytes:
        index = int(index) if isinstance(index, UInt64) else index
        try:
            return self._scratch_space[index]
        except IndexError:
            raise ValueError("invalid scratch slot") from None

    def get_scratch_space(self) -> Sequence[Bytes | UInt64]:
        return self._scratch_space


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
