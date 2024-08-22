from __future__ import annotations

import typing

from _algopy_testing import gtxn
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.models.application import Application
from _algopy_testing.models.txn_fields import get_txn_defaults

if typing.TYPE_CHECKING:
    import algopy

    from _algopy_testing.models.txn_fields import (
        ApplicationCallFields,
        AssetConfigFields,
        AssetFreezeFields,
        AssetTransferFields,
        KeyRegistrationFields,
        PaymentFields,
        TransactionFields,
    )


_TGlobalTxn = typing.TypeVar("_TGlobalTxn", bound=gtxn.TransactionBase)


class TxnValueGenerator:
    """Factory for generating test data for transactions."""

    def application_call(
        self,
        scratch_space: typing.Sequence[algopy.Bytes | algopy.UInt64 | int | bytes] | None = None,
        **fields: typing.Unpack[ApplicationCallFields],
    ) -> algopy.gtxn.ApplicationCallTransaction:
        """Generate a new application call transaction.

        :param scratch_space: Scratch space data.
        :param **fields: Fields to be set in the transaction.
        :return: New application call transaction.
        :raises TypeError: If `app_id` is not an instance of algopy.Application
        """
        try:
            app = fields["app_id"]
        except KeyError:
            app = fields["app_id"] = lazy_context.any.application()

        if not isinstance(app, Application):
            raise TypeError("`app_id` must be an instance of algopy.Application")

        new_txn = self._new_gtxn(gtxn.ApplicationCallTransaction, **fields)

        for idx, value in enumerate(scratch_space or []):
            new_txn.set_scratch_slot(idx, value)

        return new_txn

    def asset_transfer(
        self, **fields: typing.Unpack[AssetTransferFields]
    ) -> algopy.gtxn.AssetTransferTransaction:
        """Generate a new asset transfer transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated asset transfer transaction.
        """
        return self._new_gtxn(gtxn.AssetTransferTransaction, **fields)

    def payment(self, **fields: typing.Unpack[PaymentFields]) -> algopy.gtxn.PaymentTransaction:
        """Generate a new payment transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated payment transaction.
        """
        return self._new_gtxn(gtxn.PaymentTransaction, **fields)

    def asset_config(
        self, **fields: typing.Unpack[AssetConfigFields]
    ) -> algopy.gtxn.AssetConfigTransaction:
        """Generate a new ACFG transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated asset config transaction.
        """
        return self._new_gtxn(gtxn.AssetConfigTransaction, **fields)

    def key_registration(
        self, **fields: typing.Unpack[KeyRegistrationFields]
    ) -> algopy.gtxn.KeyRegistrationTransaction:
        """Generate a new key registration transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated key registration transaction.
        """
        return self._new_gtxn(gtxn.KeyRegistrationTransaction, **fields)

    def asset_freeze(
        self, **fields: typing.Unpack[AssetFreezeFields]
    ) -> algopy.gtxn.AssetFreezeTransaction:
        """Generate a new asset freeze transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated asset freeze transaction.
        """
        return self._new_gtxn(gtxn.AssetFreezeTransaction, **fields)

    def transaction(
        self,
        **fields: typing.Unpack[TransactionFields],
    ) -> algopy.gtxn.Transaction:
        """Generate a new transaction with specified fields.

        :param **fields: Fields to be set in the transaction.
        :return: The newly generated transaction.
        """
        return self._new_gtxn(gtxn.Transaction, **fields)

    def _new_gtxn(self, txn_type: type[_TGlobalTxn], **fields: object) -> _TGlobalTxn:
        fields.setdefault("type", txn_type.type_enum)
        fields.setdefault("sender", lazy_context.value.default_sender)

        fields = {
            **get_txn_defaults(),
            **fields,
        }
        return txn_type(fields)
