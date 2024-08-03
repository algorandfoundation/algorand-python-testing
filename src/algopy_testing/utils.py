from __future__ import annotations

import enum
import functools
import secrets
import typing
from types import UnionType
from typing import TYPE_CHECKING, get_args

import algosdk
import algosdk.transaction

import algopy_testing
from algopy_testing.constants import MAX_BYTES_SIZE, MAX_UINT8, MAX_UINT16, MAX_UINT64, MAX_UINT512

if TYPE_CHECKING:
    import algopy

ALWAYS_APPROVE_TEAL_PROGRAM = (
    b"\x09"  # pragma version 9
    b"\x81\x01"  # pushint 1
)


def generate_random_int(min_value: int, max_value: int) -> int:
    return secrets.randbelow(max_value - min_value + 1) + min_value


def as_int(value: object, *, max: int | None) -> int:  # noqa: A002
    """
    Returns the underlying int value for any numeric type up to UInt512

    Raises:
        TypeError: If `value` is not a numeric type
        ValueError: If not 0 <= `value` <= max
    """

    match value:
        case int(int_value):
            pass
        case algopy_testing.UInt64(value=int_value):
            pass
        case algopy_testing.BigUInt(value=int_value):
            pass
        case algopy_testing.arc4.UIntN(native=native):
            int_value = native.value
        case algopy_testing.arc4.BigUIntN(native=native):
            int_value = native.value
        # TODO: add arc4 numerics
        case _:
            raise TypeError(f"value must be a numeric type, not {type(value).__name__!r}")
    if int_value < 0:
        raise ValueError(f"expected positive value, got {int_value}")
    if max is not None and int_value > max:
        raise ValueError(f"expected value <= {max}, got: {int_value}")
    return int_value


def as_int8(value: object) -> int:
    return as_int(value, max=MAX_UINT8)


def as_int16(value: object) -> int:
    return as_int(value, max=MAX_UINT16)


def as_int64(value: object) -> int:
    return as_int(value, max=MAX_UINT64)


def as_int512(value: object) -> int:
    return as_int(value, max=MAX_UINT512)


def as_bytes(value: object, *, max_size: int = MAX_BYTES_SIZE) -> bytes:
    """
    Returns the underlying bytes value for bytes or Bytes type up to 4096

    Raises:
        TypeError: If `value` is not a bytes type
        ValueError: If not 0 <= `len(value)` <= max_size
    """

    match value:
        case bytes(bytes_value):
            pass
        case algopy_testing.Bytes(value=bytes_value):
            pass
        case _:
            raise TypeError(f"value must be a bytes or Bytes type, not {type(value).__name__!r}")
    if len(bytes_value) > max_size:
        raise ValueError(f"expected value length <= {max_size}, got: {len(bytes_value)}")
    return bytes_value


def as_string(value: object) -> str:
    match value:
        case str(string_value) | algopy_testing.String(value=string_value):
            return string_value
        case algopy_testing.arc4.String(native=native):
            return native.value
        case _:
            raise TypeError(f"value must be a string or String type, not {type(value).__name__!r}")


def int_to_bytes(x: int, pad_to: int | None = None) -> bytes:
    result = x.to_bytes((x.bit_length() + 7) // 8, "big")
    result = (
        b"\x00" * (pad_to - len(result)) if pad_to is not None and len(result) < pad_to else b""
    ) + result

    return result


def dummy_transaction_id() -> bytes:
    private_key, address = algosdk.account.generate_account()

    suggested_params = algosdk.transaction.SuggestedParams(fee=1000, first=0, last=1, gh="")
    txn = algosdk.transaction.PaymentTxn(
        sender=address,
        receiver=address,
        amt=1000,
        sp=suggested_params,
        note=secrets.token_bytes(8),
    )

    signed_txn = txn.sign(private_key)
    txn_id = str(signed_txn.transaction.get_txid()).encode("utf-8")
    return txn_id


class _TransactionStrType(enum.StrEnum):
    PAYMENT = algosdk.constants.PAYMENT_TXN
    KEYREG = algosdk.constants.KEYREG_TXN
    ASSETCONFIG = algosdk.constants.ASSETCONFIG_TXN
    ASSETTRANSFER = algosdk.constants.ASSETTRANSFER_TXN
    ASSETFREEZE = algosdk.constants.ASSETFREEZE_TXN
    APPCALL = algosdk.constants.APPCALL_TXN


@functools.cache
def txn_type_to_bytes(txn_type: int) -> algopy.Bytes:
    match txn_type:
        case algopy_testing.TransactionType.Payment:
            result = _TransactionStrType.PAYMENT
        case algopy_testing.TransactionType.KeyRegistration:
            result = _TransactionStrType.KEYREG
        case algopy_testing.TransactionType.AssetConfig:
            result = _TransactionStrType.ASSETCONFIG
        case algopy_testing.TransactionType.AssetTransfer:
            result = _TransactionStrType.ASSETTRANSFER
        case algopy_testing.TransactionType.AssetFreeze:
            result = _TransactionStrType.ASSETFREEZE
        case algopy_testing.TransactionType.ApplicationCall:
            result = _TransactionStrType.APPCALL
        case _:
            raise ValueError(f"invalid transaction type: {txn_type}")

    return algopy_testing.Bytes(bytes(result, encoding="utf-8"))


def is_instance(obj: object, class_or_tuple: type | UnionType) -> bool:
    if isinstance(class_or_tuple, UnionType):
        return any(is_instance(obj, arg) for arg in get_args(class_or_tuple))

    if isinstance(obj, typing._ProtocolMeta):
        return (
            f"{obj.__module__}.{obj.__name__}"
            == f"{class_or_tuple.__module__}.{class_or_tuple.__name__}"
        )

    # Manual comparison by module and name
    if (
        hasattr(obj, "__module__")
        and hasattr(obj, "__name__")
        and (
            obj.__module__,
            obj.__name__,
        )
        == (
            class_or_tuple.__module__,
            class_or_tuple.__name__,
        )
    ):
        return True

    return isinstance(obj, class_or_tuple)


def abi_type_name_for_arg(  # noqa: PLR0912, C901, PLR0911
    *, arg: object, is_return_type: bool = False
) -> str:
    """
    Returns the ABI type name for the given argument. Especially convenient for use with
    algosdk to generate method signatures
    """
    # TODO: abi_return_type_annotation_for_arg use this with a type rather than an instance
    #       add tests to ensure this still returns the correct value for complex ARC4 types
    #       e.g. arc4.Tuple[arc4.DynamicArray[arc4.DynamicArray[arc4.UInt64]],
    #                       arc4.StaticArray[arc4.UInt64, typing.Literal[3]]]

    if is_instance(arg, algopy_testing.arc4.String | algopy_testing.String | str):
        return "string"
    if is_instance(arg, algopy_testing.arc4.Bool | bool):
        return "bool"
    if is_instance(arg, algopy_testing.BigUInt):
        return "uint512"
    if is_instance(arg, algopy_testing.UInt64):
        return "uint64"
    if isinstance(arg, int):
        return "uint64" if arg <= MAX_UINT64 else "uint512"
    if is_instance(arg, algopy_testing.Bytes | bytes):
        return "byte[]"
    if is_instance(arg, algopy_testing.arc4.Address):
        return "address"
    if is_instance(arg, algopy_testing.Asset):
        if is_return_type:
            raise TypeError("Asset cannot be used as an arc4 return type")
        return "asset"
    if is_instance(arg, algopy_testing.Account):
        if is_return_type:
            raise TypeError("Account cannot be used as an arc4 return type")
        return "account"
    if is_instance(arg, algopy_testing.Application):
        if is_return_type:
            raise TypeError("Application cannot be used as an arc4 return type")
        return "application"
    if is_instance(arg, algopy_testing.arc4.UIntN):
        return "uint" + str(arg._bit_size)  # type: ignore[attr-defined]
    if is_instance(arg, algopy_testing.arc4.BigUIntN):
        return "uint" + str(arg._bit_size)  # type: ignore[attr-defined]
    if is_instance(arg, algopy_testing.arc4.UFixedNxM):
        return f"ufixed{arg._n}x{arg._m}"  # type: ignore[attr-defined]
    if is_instance(arg, algopy_testing.arc4.BigUFixedNxM):
        return f"ufixed{arg._n}x{arg._m}"  # type: ignore[attr-defined]
    if is_instance(arg, algopy_testing.arc4.StaticArray):
        arr_type = abi_type_name_for_arg(arg=arg[0], is_return_type=is_return_type)  # type: ignore[index]
        return f"{arr_type}[{arg.length.value}]"  # type: ignore[attr-defined]
    if is_instance(arg, algopy_testing.arc4.DynamicArray):
        arr_type = abi_type_name_for_arg(arg=arg[0], is_return_type=is_return_type)  # type: ignore[index]
        return f"{arr_type}[]"
    if is_instance(arg, algopy_testing.gtxn.AssetConfigTransaction):
        return algosdk.constants.ASSETCONFIG_TXN
    if is_instance(arg, algopy_testing.gtxn.AssetFreezeTransaction):
        return algosdk.constants.ASSETFREEZE_TXN
    if is_instance(arg, algopy_testing.gtxn.AssetTransferTransaction):
        return algosdk.constants.ASSETTRANSFER_TXN
    if is_instance(arg, algopy_testing.gtxn.PaymentTransaction):
        return algosdk.constants.PAYMENT_TXN
    if is_instance(arg, algopy_testing.gtxn.KeyRegistrationTransaction):
        return algosdk.constants.KEYREG_TXN
    if is_instance(arg, algopy_testing.gtxn.ApplicationCallTransaction):
        return algosdk.constants.APPCALL_TXN
    if is_instance(arg, algopy_testing.gtxn.Transaction):
        return "txn"
    if isinstance(arg, tuple):
        tuple_types = [abi_type_name_for_arg(arg=a, is_return_type=is_return_type) for a in arg]
        return f"({','.join(tuple_types)})"
    if typing.get_origin(arg) is tuple:
        tuple_types = [
            abi_type_name_for_arg(arg=a, is_return_type=is_return_type) for a in get_args(arg)
        ]
        return f"({','.join(tuple_types)})"

    raise ValueError(f"Unsupported type {type(arg)}")


def abi_return_type_annotation_for_arg(arg: object) -> str:
    """
    Returns the ABI type name for the given argument. Especially convenient for use with
    algosdk to generate method signatures
    """

    try:
        return abi_type_name_for_arg(arg=arg, is_return_type=True)
    except ValueError:
        if arg is None:
            return "void"
        raise
