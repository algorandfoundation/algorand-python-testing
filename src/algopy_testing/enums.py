from __future__ import annotations

from enum import Enum, StrEnum

from algopy_testing.primitives import UInt64


class OnCompleteAction(UInt64):
    NoOp: OnCompleteAction
    OptIn: OnCompleteAction
    CloseOut: OnCompleteAction
    ClearState: OnCompleteAction
    UpdateApplication: OnCompleteAction
    DeleteApplication: OnCompleteAction


OnCompleteAction.NoOp = OnCompleteAction(0)
OnCompleteAction.OptIn = OnCompleteAction(1)
OnCompleteAction.CloseOut = OnCompleteAction(2)
OnCompleteAction.ClearState = OnCompleteAction(3)
OnCompleteAction.UpdateApplication = OnCompleteAction(4)
OnCompleteAction.DeleteApplication = OnCompleteAction(5)


class TransactionType(UInt64):
    Payment: TransactionType
    KeyRegistration: TransactionType
    AssetConfig: TransactionType
    AssetTransfer: TransactionType
    AssetFreeze: TransactionType
    ApplicationCall: TransactionType


TransactionType.Payment = TransactionType(0)
TransactionType.KeyRegistration = TransactionType(1)
TransactionType.AssetConfig = TransactionType(2)
TransactionType.AssetTransfer = TransactionType(3)
TransactionType.AssetFreeze = TransactionType(4)
TransactionType.ApplicationCall = TransactionType(5)


class ECDSA(Enum):
    Secp256k1 = 0
    Secp256r1 = 1


class VrfVerify(Enum):
    VrfAlgorand = 0


class Base64(Enum):
    URLEncoding = 0
    StdEncoding = 1


class EC(StrEnum):
    """Available values for the `EC` enum"""

    BN254g1 = "BN254g1"
    BN254g2 = "BN254g2"
    BLS12_381g1 = "BLS12_381g1"
    BLS12_381g2 = "BLS12_381g2"
