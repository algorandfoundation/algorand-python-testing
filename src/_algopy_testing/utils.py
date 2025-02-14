from __future__ import annotations

import secrets
import typing
from typing import TYPE_CHECKING

import algosdk

import _algopy_testing
from _algopy_testing.constants import (
    ARC4_RETURN_PREFIX,
    DEFAULT_ACCOUNT_MIN_BALANCE,
    DEFAULT_ASSET_CREATE_MIN_BALANCE,
    DEFAULT_ASSET_OPT_IN_MIN_BALANCE,
    DEFAULT_GLOBAL_GENESIS_HASH,
    DEFAULT_MAX_TXN_LIFE,
    MAX_BYTES_SIZE,
    MAX_UINT8,
    MAX_UINT16,
    MAX_UINT64,
    MAX_UINT512,
)

if TYPE_CHECKING:
    import types

    import algopy

    from _algopy_testing.op.global_values import GlobalFields

    _TBytes = typing.TypeVar("_TBytes", bytes, algopy.Bytes)


def resolve_app_index(app_id_or_index: algopy.UInt64 | int) -> int:
    from _algopy_testing.context_helpers import lazy_context

    if app_id_or_index >= 1001:
        app_id = app_id_or_index
    else:
        txn = lazy_context.active_group.active_txn
        app_id = txn.apps(app_id_or_index).id
    return int(app_id)


def resolve_asset_index(asset_id_or_index: algopy.UInt64 | int) -> int:
    from _algopy_testing.context_helpers import lazy_context

    if asset_id_or_index >= 1001:
        asset_id = asset_id_or_index
    else:
        txn = lazy_context.active_group.active_txn
        asset_id = txn.assets(asset_id_or_index).id
    return int(asset_id)


def generate_random_int(min_value: int, max_value: int) -> int:
    return secrets.randbelow(max_value - min_value + 1) + min_value


def generate_random_bytes32() -> bytes:
    return secrets.token_bytes(32)


def as_int(value: object, *, max: int | None) -> int:  # noqa: A002
    match value:
        case int(int_value):
            pass
        case _algopy_testing.UInt64(value=int_value):
            pass
        case _algopy_testing.BigUInt(value=int_value):
            pass
        case _algopy_testing.arc4.UIntN(native=native):
            int_value = native.value
        case _algopy_testing.arc4.BigUIntN(native=native):
            int_value = native.value
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
    match value:
        case bytes(bytes_value):
            pass
        case _algopy_testing.Bytes(value=bytes_value):
            pass
        case _:
            raise TypeError(f"value must be a bytes or Bytes type, not {type(value).__name__!r}")
    if len(bytes_value) > max_size:
        raise ValueError(f"expected value length <= {max_size}, got: {len(bytes_value)}")
    return bytes_value


def as_string(value: object) -> str:
    match value:
        case str(string_value) | _algopy_testing.String(value=string_value):
            return string_value
        case _algopy_testing.arc4.String(native=native):
            return native.value
        case _:
            raise TypeError(f"value must be a string or String type, not {type(value).__name__!r}")


def int_to_bytes(x: int, pad_to: int | None = None) -> bytes:
    result = x.to_bytes((x.bit_length() + 7) // 8, "big")
    result = (
        b"\x00" * (pad_to - len(result)) if pad_to is not None and len(result) < pad_to else b""
    ) + result

    return result


def convert_native_to_stack(
    value: algopy.Bytes | algopy.UInt64 | bytes | int,
) -> algopy.Bytes | algopy.UInt64:
    if isinstance(value, int):
        return _algopy_testing.UInt64(value)
    if isinstance(value, bytes):
        return _algopy_testing.Bytes(value)
    return value


def convert_stack_to_native(
    value: algopy.Bytes | algopy.UInt64 | bytes | int,
) -> bytes | int:
    if isinstance(value, int | bytes):
        return value
    else:
        return value.value


def check_type(value: object, typ: type | types.UnionType) -> None:
    if not isinstance(value, typ):
        expected_name = typ.__name__ if isinstance(typ, type) else str(typ)
        raise TypeError(f"expected {expected_name}, got {type(value).__name__!r}")


def assert_address_is_valid(address: str) -> None:
    assert algosdk.encoding.is_valid_address(address), "Invalid Algorand address supplied!"


def get_default_global_fields() -> GlobalFields:
    import algopy

    return {
        "min_txn_fee": algopy.UInt64(algosdk.constants.MIN_TXN_FEE),
        "min_balance": algopy.UInt64(DEFAULT_ACCOUNT_MIN_BALANCE),
        "max_txn_life": algopy.UInt64(DEFAULT_MAX_TXN_LIFE),
        "zero_address": algopy.Account(algosdk.constants.ZERO_ADDRESS),
        "caller_application_id": algopy.UInt64(),
        "asset_create_min_balance": algopy.UInt64(DEFAULT_ASSET_CREATE_MIN_BALANCE),
        "asset_opt_in_min_balance": algopy.UInt64(DEFAULT_ASSET_OPT_IN_MIN_BALANCE),
        "genesis_hash": algopy.Bytes(DEFAULT_GLOBAL_GENESIS_HASH),
        "payouts_enabled": False,
        "payouts_go_online_fee": algopy.UInt64(),
        "payouts_max_balance": algopy.UInt64(),
        "payouts_min_balance": algopy.UInt64(),
        "payouts_percent": algopy.UInt64(),
    }


def get_new_scratch_space() -> list[algopy.Bytes | algopy.UInt64]:
    import algopy

    return [algopy.UInt64(0)] * 256


def arc4_prefix(value: _TBytes) -> _TBytes:
    """Return the value with the ARC4 prefix prepended."""
    return ARC4_RETURN_PREFIX + value


def raise_mocked_function_error(func_name: str) -> typing.Never:
    raise NotImplementedError(
        f"{func_name!r} is not available in test context. "
        "Mock using your preferred testing framework."
    )
