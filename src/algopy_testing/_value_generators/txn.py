from __future__ import annotations

import typing

import algopy_testing
from algopy_testing.gtxn import TransactionBase
from algopy_testing.models.txn_fields import get_txn_defaults

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing import AlgopyTestContext
    from algopy_testing.models.txn_fields import (
        ApplicationCallFields,
        AssetConfigFields,
        AssetFreezeFields,
        AssetTransferFields,
        KeyRegistrationFields,
        PaymentFields,
        TransactionFields,
    )


_TGlobalTxn = typing.TypeVar("_TGlobalTxn", bound=TransactionBase)


class TxnValueGenerator:
    """Factory for generating test data for transactions."""

    def __init__(self, context: AlgopyTestContext) -> None:
        """Initializes the ARC4ValueGenerator with the given testing context.

        Args:
            context (AlgopyTestContext): The testing context for generating test data.
        """
        self.context = context

    def application_call(
        self,
        scratch_space: typing.Sequence[algopy.Bytes | algopy.UInt64 | int | bytes] | None = None,
        **fields: typing.Unpack[ApplicationCallFields],
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
            app = fields["app_id"]
        except KeyError:
            app = fields["app_id"] = self.context.any.application()

        if not isinstance(app, algopy_testing.Application):
            raise TypeError("`app_id` must be an instance of algopy.Application")

        new_txn = self._new_gtxn(algopy_testing.gtxn.ApplicationCallTransaction, **fields)
        self.context.set_scratch_space(new_txn, scratch_space or [])

        return new_txn

    def asset_transfer(
        self, **fields: typing.Unpack[AssetTransferFields]
    ) -> algopy.gtxn.AssetTransferTransaction:
        """Generate a new asset transfer transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[AssetTransferFields] :param **fields:
        Unpack[AssetTransferFields]:
        :returns: The newly generated asset transfer transaction.
        :rtype: algopy.gtxn.AssetTransferTransaction
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetTransferTransaction, **fields)

    def payment(self, **fields: typing.Unpack[PaymentFields]) -> algopy.gtxn.PaymentTransaction:
        """Generate a new payment transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[PaymentFields] :param **fields:
        Unpack[PaymentFields]:
        :returns: The newly generated payment transaction.
        :rtype: algopy.gtxn.PaymentTransaction
        """
        return self._new_gtxn(algopy_testing.gtxn.PaymentTransaction, **fields)

    def asset_config(
        self, **fields: typing.Unpack[AssetConfigFields]
    ) -> algopy.gtxn.AssetConfigTransaction:
        """Generate a new ACFG transaction with specified fields.

        :param **fields: Unpack[AssetConfigFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetConfigTransaction, **fields)

    def key_registration(
        self, **fields: typing.Unpack[KeyRegistrationFields]
    ) -> algopy.gtxn.KeyRegistrationTransaction:
        """Generate a new key registration transaction with specified fields.

        :param **fields: Unpack[KeyRegistrationFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.KeyRegistrationTransaction, **fields)

    def asset_freeze(
        self, **fields: typing.Unpack[AssetFreezeFields]
    ) -> algopy.gtxn.AssetFreezeTransaction:
        """Generate a new asset freeze transaction with specified fields.

        :param **fields: Unpack[AssetFreezeFields]:
        """
        return self._new_gtxn(algopy_testing.gtxn.AssetFreezeTransaction, **fields)

    def transaction(
        self,
        **fields: typing.Unpack[TransactionFields],
    ) -> algopy.gtxn.Transaction:
        """Generate a new transaction with specified fields.

        :param **fields: Fields to be set in the transaction. :type
        **fields: Unpack[TransactionFields] :param **fields:
        Unpack[TransactionFields]:
        :returns: The newly generated transaction.
        :rtype: algopy.gtxn.Transaction
        """
        return self._new_gtxn(algopy_testing.gtxn.Transaction, **fields)

    def _new_gtxn(self, txn_type: type[_TGlobalTxn], **fields: object) -> _TGlobalTxn:
        # TODO: check reference types are known?
        fields.setdefault("type", txn_type.type_enum)
        fields.setdefault("sender", self.context.default_sender)

        fields = {**get_txn_defaults(), **fields}
        return txn_type(fields)