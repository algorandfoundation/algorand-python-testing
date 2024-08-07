from __future__ import annotations

import logging
import typing
from copy import deepcopy

import algosdk

from algopy_testing._context_storage import get_test_context
from algopy_testing.enums import TransactionType
from algopy_testing.models import Account, Asset
from algopy_testing.models.txn_fields import (
    TransactionFieldsBase,
    get_txn_defaults,
    narrow_field_type,
)
from algopy_testing.primitives import Bytes, UInt64

logger = logging.getLogger(__name__)

if typing.TYPE_CHECKING:
    from collections.abc import Callable

    import algopy


__all__ = [
    "ApplicationCall",
    "ApplicationCallInnerTransaction",
    "AssetConfig",
    "AssetConfigInnerTransaction",
    "AssetFreeze",
    "AssetFreezeInnerTransaction",
    "AssetTransfer",
    "AssetTransferInnerTransaction",
    "InnerTransaction",
    "InnerTransactionResult",
    "KeyRegistration",
    "KeyRegistrationInnerTransaction",
    "Payment",
    "PaymentInnerTransaction",
    "submit_txns",
]


# ==== Inner Transaction Results  ====
# These are used to represent finalized transactions submitted to the network
# and are created by the `submit` method of each inner transaction class


class _BaseInnerTransactionResult(TransactionFieldsBase):
    txn_type: TransactionType = TransactionType.Payment

    def __init__(self, **fields: typing.Any):
        self._fields = fields

    def __getattr__(self, name: str) -> typing.Any:
        if name in self._fields:
            return self._fields[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if name == "_fields":
            super().__setattr__(name, value)
        else:
            self._fields[name] = narrow_field_type(name, value)

    @property
    def fields(self) -> dict[str, object]:
        return self._fields

    @property
    def _logs(self) -> list[bytes]:

        context = get_test_context()
        try:
            return context._application_logs[int(self.app_id.id)]
        except KeyError:
            return []

    @property
    def last_log(self) -> algopy.Bytes:
        try:
            last = self._logs[-1]
        except IndexError:
            last = b""
        return Bytes(last)

    @property
    def num_logs(self) -> algopy.UInt64:
        return UInt64(len(self._logs))

    @property
    def logs(self) -> Callable[[algopy.UInt64 | int], algopy.Bytes]:
        return lambda i: Bytes(self._logs[int(i)])


class PaymentInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.Payment


class KeyRegistrationInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.KeyRegistration


class AssetConfigInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.AssetConfig


class AssetTransferInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.AssetTransfer


class AssetFreezeInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.AssetFreeze


class ApplicationCallInnerTransaction(_BaseInnerTransactionResult):
    txn_type = TransactionType.ApplicationCall


class InnerTransactionResult(_BaseInnerTransactionResult):
    pass


class _BaseInnerTransactionFields:
    txn_class: type[_BaseInnerTransactionResult]
    fields: dict[str, typing.Any]

    def __init__(self, **fields: typing.Any) -> None:
        # TODO: validate fields against TransactionFields composite type
        context = get_test_context()
        txn_type = self.txn_class.txn_type or TransactionType.Payment
        fields = {
            **get_txn_defaults(),
            "type": txn_type,
            "sender": context.get_active_application().address,
            **fields,
        }
        _narrow_covariant_types(fields)
        self.fields = fields

    def set(self, **fields: typing.Any) -> None:
        self.fields.update(fields)
        _narrow_covariant_types(fields)

    def submit(self) -> typing.Any:
        context = get_test_context()
        result = _get_itxn_result(self)
        context._append_inner_transaction_group([result])
        return result

    def copy(self) -> typing.Self:
        return deepcopy(self)


class InnerTransaction(_BaseInnerTransactionFields):
    txn_class = InnerTransactionResult


class Payment(_BaseInnerTransactionFields):
    txn_class = PaymentInnerTransaction


class KeyRegistration(_BaseInnerTransactionFields):
    txn_class = KeyRegistrationInnerTransaction


class AssetConfig(_BaseInnerTransactionFields):
    txn_class = AssetConfigInnerTransaction


class AssetTransfer(_BaseInnerTransactionFields):
    txn_class = AssetTransferInnerTransaction


class AssetFreeze(_BaseInnerTransactionFields):
    txn_class = AssetFreezeInnerTransaction


class ApplicationCall(_BaseInnerTransactionFields):
    txn_class = ApplicationCallInnerTransaction


def submit_txns(
    *transactions: _BaseInnerTransactionFields,
) -> tuple[_BaseInnerTransactionResult, ...]:
    """Submits a group of up to 16 inner transactions parameters.

    :returns: A tuple of the resulting inner transactions
    """
    context = get_test_context()

    if len(transactions) > algosdk.constants.TX_GROUP_LIMIT:
        raise ValueError("Cannot submit more than 16 inner transactions at once")

    results = tuple(_get_itxn_result(tx) for tx in transactions)
    context._append_inner_transaction_group(results)

    return results


def _get_itxn_result(itxn: _BaseInnerTransactionFields) -> _BaseInnerTransactionResult:
    fields = itxn.fields
    txn_type = fields["type"]
    result = _TXN_HANDLERS[txn_type](fields)
    return itxn.txn_class(**result)


# handlers for submitting each txn type, done here rather than on the typed specific classes
# as not everything goes through those types
def _on_pay(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:
    return fields


def _on_keyreg(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:
    return fields


def _on_asset_config(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:
    # if it is a txn to create an asset then ensure this is reflected in the context
    if fields.get("config_asset") == Asset():
        context = get_test_context()
        created_asset = context.any_asset(
            total=fields["total"],
            decimals=fields["decimals"],
            default_frozen=fields["default_frozen"],
            unit_name=fields["unit_name"],
            name=fields["asset_name"],
            url=fields["url"],
            metadata_hash=fields["metadata_hash"],
            manager=fields["manager"],  # TODO: set to sender?
            reserve=fields["reserve"],
            freeze=fields["freeze"],
            clawback=fields["clawback"],
            creator=fields["manager"],
        )
        fields["created_asset"] = created_asset
    return fields


def _on_asset_freeze(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:
    return fields


def _on_asset_xfer(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:
    if fields["asset_sender"] == Account():
        fields["asset_sender"] = fields["sender"]
    return fields


def _on_app_call(fields: dict[str, typing.Any]) -> dict[str, typing.Any]:

    return fields


_TXN_HANDLERS = {
    TransactionType.Payment: _on_pay,
    TransactionType.KeyRegistration: _on_keyreg,
    TransactionType.AssetConfig: _on_asset_config,
    TransactionType.AssetTransfer: _on_asset_xfer,
    TransactionType.AssetFreeze: _on_asset_freeze,
    TransactionType.ApplicationCall: _on_app_call,
}


def _narrow_covariant_types(fields: dict[str, typing.Any]) -> None:
    for field, value in fields.items():
        fields[field] = narrow_field_type(field, value)
