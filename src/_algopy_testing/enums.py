from __future__ import annotations

import typing

from algosdk import constants

from _algopy_testing.primitives import UInt64


class _EnumLike(UInt64):
    names: dict[_EnumLike, str]

    @property
    def name(self) -> str:
        return self.names[self]


_T = typing.TypeVar("_T", bound=_EnumLike)


def _add_enum_values(cls: type[_T], **values: _T) -> None:
    cls.names = {v: k for k, v in values.items()}
    for name, value in values.items():
        setattr(cls, name, value)


# can't use an actual enum here as this type need to subclass UInt64
class OnCompleteAction(_EnumLike):
    NoOp: OnCompleteAction
    OptIn: OnCompleteAction
    CloseOut: OnCompleteAction
    ClearState: OnCompleteAction
    UpdateApplication: OnCompleteAction
    DeleteApplication: OnCompleteAction

    @classmethod
    def _from_str(
        cls,
        action: str | OnCompleteAction,
    ) -> OnCompleteAction:
        if isinstance(action, cls):
            return action

        if isinstance(action, str):
            try:
                return getattr(cls, action)  # type: ignore[no-any-return]
            except AttributeError as e:
                raise ValueError(f"Invalid OnCompleteAction: {action}") from e

        raise TypeError(f"Expected str or OnCompleteAction, got {type(action)}")


_add_enum_values(
    OnCompleteAction,
    NoOp=OnCompleteAction(0),
    OptIn=OnCompleteAction(1),
    CloseOut=OnCompleteAction(2),
    ClearState=OnCompleteAction(3),
    UpdateApplication=OnCompleteAction(4),
    DeleteApplication=OnCompleteAction(5),
)


class TransactionType(_EnumLike):
    Payment: TransactionType
    KeyRegistration: TransactionType
    AssetConfig: TransactionType
    AssetTransfer: TransactionType
    AssetFreeze: TransactionType
    ApplicationCall: TransactionType

    @property
    def txn_name(self) -> str:
        match self:
            case self.Payment:
                return constants.PAYMENT_TXN
            case self.KeyRegistration:
                return constants.KEYREG_TXN
            case self.AssetConfig:
                return constants.ASSETCONFIG_TXN
            case self.AssetTransfer:
                return constants.ASSETTRANSFER_TXN
            case self.AssetFreeze:
                return constants.ASSETFREEZE_TXN
            case self.ApplicationCall:
                return constants.APPCALL_TXN
            case _:
                raise ValueError("unexpected transaction type")


_add_enum_values(
    TransactionType,
    Payment=TransactionType(0),
    KeyRegistration=TransactionType(1),
    AssetConfig=TransactionType(2),
    AssetTransfer=TransactionType(3),
    AssetFreeze=TransactionType(4),
    ApplicationCall=TransactionType(5),
)
