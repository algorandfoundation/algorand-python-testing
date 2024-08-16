from __future__ import annotations

import typing

from algopy_testing._context_helpers import lazy_context
from algopy_testing.constants import MAX_ITEMS_IN_LOG
from algopy_testing.enums import TransactionType
from algopy_testing.models import Application
from algopy_testing.models.txn_fields import TransactionFieldsGetter
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import convert_native_to_stack, get_new_scratch_space

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.primitives.bytes import Bytes

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
    _app_logs: list[bytes]
    _scratch_space: list[Bytes | UInt64]

    # since the only thing that matters is that the implementation matches the stubs
    # we can define all the fields in TransactionBase
    def __init__(self, group_index_or_fields: algopy.UInt64 | int | dict[str, typing.Any]):
        if isinstance(group_index_or_fields, dict):
            self._fields: dict[str, typing.Any] | None = group_index_or_fields
            self._group_index = 0
        else:
            self._fields = None
            self._group_index = int(group_index_or_fields)

        self._app_logs: list[bytes] = []
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

    def _get_app_logs(self) -> list[bytes]:
        if self.type_enum != TransactionType.ApplicationCall:
            raise ValueError("Can only get logs from ApplicationCallTransaction!")

        return self._app_logs

    def _add_app_logs(self, logs: bytes | list[bytes]) -> None:
        logs = [logs] if isinstance(logs, bytes) else logs

        if self.type_enum != TransactionType.ApplicationCall:
            raise ValueError("Can only add logs to ApplicationCallTransaction!")

        if len(logs) > MAX_ITEMS_IN_LOG:
            # Note this isn't 100% accurate to AVM behaviour as it counts elements not accesses
            # to the logs. But generally 32 calls to log() opcode will result in 32 items being
            # added to the logs which is comparable to 32 accesses to the logs
            raise ValueError("Too many log calls in program. up to 32 is allowed")

        self._app_logs.extend(logs)

    def _set_scratch_slot(
        self, index: UInt64 | int, value: algopy.Bytes | algopy.UInt64 | bytes | int
    ) -> None:
        index = int(index) if isinstance(index, UInt64) else index
        self._scratch_space[index] = convert_native_to_stack(value)

    def _set_scratch_space(
        self,
        scratch_space: typing.Sequence[algopy.Bytes | algopy.UInt64 | bytes | int],
    ) -> None:
        new_scratch_space = get_new_scratch_space()
        for index, value in enumerate(scratch_space):
            new_scratch_space[index] = convert_native_to_stack(value)
        self._scratch_space = new_scratch_space

    def _get_scratch_space(self) -> list[Bytes | UInt64]:
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
