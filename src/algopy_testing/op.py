from __future__ import annotations

import base64
import hashlib
import json
import math
import typing
from typing import TYPE_CHECKING, Any, Literal, cast

import algosdk
import coincurve
import nacl.exceptions
import nacl.signing
from Cryptodome.Hash import SHA512, keccak
from ecdsa import (  # type: ignore  # noqa: PGH003
    BadSignatureError,
    NIST256p,
    SECP256k1,
    VerifyingKey,
)

from algopy_testing.constants import (
    BITS_IN_BYTE,
    DEFAULT_ACCOUNT_MIN_BALANCE,
    MAX_BOX_SIZE,
    MAX_BYTES_SIZE,
    MAX_UINT64,
)
from algopy_testing.context import get_test_context
from algopy_testing.enums import EC, ECDSA, Base64, VrfVerify
from algopy_testing.models.block import Block
from algopy_testing.models.gitxn import GITxn
from algopy_testing.models.global_values import Global
from algopy_testing.models.gtxn import GTxn
from algopy_testing.models.itxn import ITxn, ITxnCreate
from algopy_testing.models.txn import Txn
from algopy_testing.primitives.biguint import BigUInt
from algopy_testing.primitives.bytes import Bytes
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import (
    as_bytes,
    as_int,
    as_int8,
    as_int64,
    as_int512,
    int_to_bytes,
)

if TYPE_CHECKING:
    import algopy


def sha256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    return Bytes(hashlib.sha256(input_value).digest())


def sha3_256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    return Bytes(hashlib.sha3_256(input_value).digest())


def keccak256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    hashed_value = keccak.new(data=input_value, digest_bits=256)
    return Bytes(hashed_value.digest())


def sha512_256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    hash_object = SHA512.new(input_value, truncate="256")
    return Bytes(hash_object.digest())


def ed25519verify_bare(a: Bytes | bytes, b: Bytes | bytes, c: Bytes | bytes, /) -> bool:
    a, b, c = (as_bytes(x) for x in [a, b, c])

    try:
        verify_key = nacl.signing.VerifyKey(c)
        verify_key.verify(a, b)
    except nacl.exceptions.BadSignatureError:
        return False
    else:
        return True


def ed25519verify(a: Bytes | bytes, b: Bytes | bytes, c: Bytes | bytes, /) -> bool:
    from algopy_testing.context import get_test_context
    from algopy_testing.utils import as_bytes

    try:
        ctx = get_test_context()
    except LookupError as e:
        raise RuntimeError(
            "function must be run within an active context"
            " using `with algopy_testing.context.new_context():`"
        ) from e

    # TODO: Decide on whether to pick clear or approval depending on OnComplete state
    if not ctx._txn_fields:
        raise RuntimeError("`txn_fields` must be set in the context")

    program_bytes = as_bytes(ctx._txn_fields.get("approval_program", None))
    if not program_bytes:
        raise RuntimeError("`program_bytes` must be set in the context")

    decoded_address = algosdk.encoding.decode_address(algosdk.logic.address(program_bytes))
    address_bytes = as_bytes(decoded_address)
    a = algosdk.constants.logic_data_prefix + address_bytes + a
    return ed25519verify_bare(a, b, c)


def ecdsa_verify(  # noqa: PLR0913
    v: ECDSA,
    a: Bytes | bytes,
    b: Bytes | bytes,
    c: Bytes | bytes,
    d: Bytes | bytes,
    e: Bytes | bytes,
    /,
) -> bool:
    data_bytes, sig_r_bytes, sig_s_bytes, pubkey_x_bytes, pubkey_y_bytes = map(
        as_bytes, [a, b, c, d, e]
    )

    curve_map = {
        ECDSA.Secp256k1: SECP256k1,
        ECDSA.Secp256r1: NIST256p,
    }

    curve = curve_map.get(v)
    if curve is None:
        raise ValueError(f"Unsupported ECDSA curve: {v}")

    public_key = b"\x04" + pubkey_x_bytes + pubkey_y_bytes
    vk = VerifyingKey.from_string(public_key, curve=curve)

    # Concatenate R and S components to form the signature
    signature = sig_r_bytes + sig_s_bytes
    try:
        vk.verify_digest(signature, data_bytes)
    except BadSignatureError:
        return False
    return True


def ecdsa_pk_recover(
    v: ECDSA, a: Bytes | bytes, b: UInt64 | int, c: Bytes | bytes, d: Bytes | bytes, /
) -> tuple[Bytes, Bytes]:
    if v is not ECDSA.Secp256k1:
        raise ValueError(f"Unsupported ECDSA curve: {v}")

    data_bytes = as_bytes(a)
    r_bytes = as_bytes(c)
    s_bytes = as_bytes(d)
    recovery_id = int(b)

    if len(r_bytes) != 32 or len(s_bytes) != 32:
        raise ValueError("Invalid length for r or s bytes.")

    signature_rs = r_bytes + s_bytes + bytes([recovery_id])

    try:
        public_key = coincurve.PublicKey.from_signature_and_message(
            signature_rs, data_bytes, hasher=None
        )
        pubkey_x, pubkey_y = public_key.point()
    except Exception as e:
        raise ValueError(f"Failed to recover public key: {e}") from e
    else:
        return Bytes(pubkey_x.to_bytes(32, byteorder="big")), Bytes(
            pubkey_y.to_bytes(32, byteorder="big")
        )


def ecdsa_pk_decompress(v: ECDSA, a: Bytes | bytes, /) -> tuple[Bytes, Bytes]:
    if v not in [ECDSA.Secp256k1, ECDSA.Secp256r1]:
        raise ValueError(f"Unsupported ECDSA curve: {v}")

    compressed_pubkey = as_bytes(a)

    try:
        public_key = coincurve.PublicKey(compressed_pubkey)
        pubkey_x, pubkey_y = public_key.point()
    except Exception as e:
        raise ValueError(f"Failed to decompress public key: {e}") from e
    else:
        return Bytes(pubkey_x.to_bytes(32, byteorder="big")), Bytes(
            pubkey_y.to_bytes(32, byteorder="big")
        )


def vrf_verify(
    _s: VrfVerify,
    _a: Bytes | bytes,
    _b: Bytes | bytes,
    _c: Bytes | bytes,
    /,
) -> tuple[Bytes, bool]:
    raise NotImplementedError(
        "'op.vrf_verify' is not implemented. Mock using preferred testing tools."
    )


def addw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    result = a + b
    return _int_to_uint128(result)


def base64_decode(e: Base64, a: Bytes | bytes, /) -> Bytes:
    a_str = _bytes_to_string(a, "illegal base64 data")
    a_str = a_str + "="  # append padding to ensure there is at least one

    result = (
        base64.urlsafe_b64decode(a_str) if e == Base64.URLEncoding else base64.b64decode(a_str)
    )
    return Bytes(result)


def bitlen(a: Bytes | UInt64 | bytes | int, /) -> UInt64:
    int_value = int.from_bytes(as_bytes(a)) if (isinstance(a, Bytes | bytes)) else as_int64(a)
    return UInt64(int_value.bit_length())


def bsqrt(a: BigUInt | int, /) -> BigUInt:
    a = as_int512(a)
    return BigUInt(math.isqrt(a))


def btoi(a: Bytes | bytes, /) -> UInt64:
    a_bytes = as_bytes(a)
    if len(a_bytes) > 8:
        raise ValueError(f"btoi arg too long, got [{len(a_bytes)}]bytes")
    return UInt64(int.from_bytes(a_bytes))


def bzero(a: UInt64 | int, /) -> Bytes:
    a = as_int64(a)
    if a > MAX_BYTES_SIZE:
        raise ValueError("bzero attempted to create a too large string")
    return Bytes(b"\x00" * a)


def divmodw(
    a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, d: UInt64 | int, /
) -> tuple[UInt64, UInt64, UInt64, UInt64]:
    i = _uint128_to_int(a, b)
    j = _uint128_to_int(c, d)
    d = i // j
    m = i % j
    return _int_to_uint128(d) + _int_to_uint128(m)


def divw(a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, /) -> UInt64:
    i = _uint128_to_int(a, b)
    c = as_int64(c)
    return UInt64(i // c)


def err() -> None:
    raise RuntimeError("err opcode executed")


def exp(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int64(b)
    if a == b and a == 0:
        raise ArithmeticError("0^0 is undefined")
    return UInt64(a**b)


def expw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    if a == b and a == 0:
        raise ArithmeticError("0^0 is undefined")
    result = a**b
    return _int_to_uint128(result)


def extract(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    start = as_int64(b)
    stop = start + as_int64(c)

    if isinstance(b, int) and isinstance(c, int) and c == 0:
        stop = len(a)

    if start > len(a):
        raise ValueError(f"extraction start {start} is beyond length")
    if stop > len(a):
        raise ValueError(f"extraction end {stop} is beyond length")

    return Bytes(a)[slice(start, stop)]


def extract_uint16(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 2)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def extract_uint32(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 4)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def extract_uint64(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    result = extract(a, b, 8)
    result_int = int.from_bytes(result.value)
    return UInt64(result_int)


def getbit(a: Bytes | UInt64 | bytes | int, b: UInt64 | int, /) -> UInt64:
    if isinstance(a, Bytes | bytes):
        return _getbit_bytes(a, b)
    if isinstance(a, UInt64 | int):
        a_bytes = _uint64_to_bytes(a)
        return _getbit_bytes(a_bytes, b, "little")
    raise TypeError("Unknown type for argument a")


def getbyte(a: Bytes | bytes, b: UInt64 | int, /) -> UInt64:
    a = as_bytes(a)
    int_list = list(a)

    max_index = len(int_list) - 1
    b = as_int(b, max=max_index)

    return UInt64(int_list[b])


def itob(a: UInt64 | int, /) -> Bytes:
    return Bytes(_uint64_to_bytes(a))


def mulw(a: UInt64 | int, b: UInt64 | int, /) -> tuple[UInt64, UInt64]:
    a = as_int64(a)
    b = as_int64(b)
    result = a * b
    return _int_to_uint128(result)


def replace(a: Bytes | bytes, b: UInt64 | int, c: Bytes | bytes, /) -> Bytes:
    a = a if (isinstance(a, Bytes)) else Bytes(a)
    b = as_int64(b)
    c = as_bytes(c)
    if b + len(c) > len(a):
        raise ValueError(f"expected value <= {len(a)}, got: {b + len(c)}")
    return a[slice(0, b)] + c + a[slice(b + len(c), len(a))]


def select_bytes(a: Bytes | bytes, b: Bytes | bytes, c: bool | UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    b = as_bytes(b)
    c = int(c) if (isinstance(c, bool)) else as_int64(c)
    return Bytes(b if c != 0 else a)


def select_uint64(a: UInt64 | int, b: UInt64 | int, c: bool | UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int64(b)
    c = int(c) if (isinstance(c, bool)) else as_int64(c)
    return UInt64(b if c != 0 else a)


def setbit_bytes(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    return _setbit_bytes(a, b, c)


def setbit_uint64(a: UInt64 | int, b: UInt64 | int, c: UInt64 | int, /) -> UInt64:
    a_bytes = _uint64_to_bytes(a)
    result = _setbit_bytes(a_bytes, b, c, "little")
    return UInt64(int.from_bytes(result.value))


def setbyte(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    int_list = list(a)

    max_index = len(int_list) - 1
    b = as_int(b, max=max_index)
    c = as_int8(c)

    int_list[b] = c
    return Bytes(_int_list_to_bytes(int_list))


def shl(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int(b, max=63)
    result = (a * (2**b)) % (2**64)
    return UInt64(result)


def shr(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    b = as_int(b, max=63)
    result = a // (2**b)
    return UInt64(result)


def sqrt(a: UInt64 | int, /) -> UInt64:
    a = as_int64(a)
    return UInt64(math.isqrt(a))


def substring(a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, /) -> Bytes:
    a = as_bytes(a)
    c = as_int(c, max=len(a))
    b = as_int(b, max=c)
    return Bytes(a)[slice(b, c)]


def concat(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
    a = a if (isinstance(a, Bytes)) else Bytes(a)
    b = b if (isinstance(b, Bytes)) else Bytes(b)
    return a + b


def _int_to_uint128(a: int) -> tuple[UInt64, UInt64]:
    cf, rest = a >> 64, a & MAX_UINT64
    return (
        UInt64(cf),
        UInt64(rest),
    )


def _uint128_to_int(a: UInt64 | int, b: UInt64 | int) -> int:
    a = as_int64(a)
    b = as_int64(b)
    return (a << 64) + b


def _uint64_to_bytes(a: UInt64 | int) -> bytes:
    a = as_int64(a)
    return a.to_bytes(8)


def _int_list_to_bytes(a: list[int]) -> bytes:
    return b"".join([b"\x00" if i == 0 else int_to_bytes(i) for i in a])


def _getbit_bytes(
    a: Bytes | bytes, b: UInt64 | int, byteorder: Literal["little", "big"] = "big"
) -> UInt64:
    a = as_bytes(a)
    if byteorder != "big":  # reverse bytes if NOT big endian
        a = bytes(reversed(a))

    int_list = list(a)
    max_index = len(int_list) * BITS_IN_BYTE - 1
    b = as_int(b, max=max_index)

    byte_index = b // BITS_IN_BYTE
    bit_index = b % BITS_IN_BYTE
    if byteorder == "big":
        bit_index = 7 - bit_index
    bit = _get_bit(int_list[byte_index], bit_index)

    return UInt64(bit)


def _setbit_bytes(
    a: Bytes | bytes, b: UInt64 | int, c: UInt64 | int, byteorder: Literal["little", "big"] = "big"
) -> Bytes:
    a = as_bytes(a)
    if byteorder != "big":  # reverse bytes if NOT big endian
        a = bytes(reversed(a))

    int_list = list(a)
    max_index = len(int_list) * BITS_IN_BYTE - 1
    b = as_int(b, max=max_index)
    c = as_int(c, max=1)

    byte_index = b // BITS_IN_BYTE
    bit_index = b % BITS_IN_BYTE
    if byteorder == "big":
        bit_index = 7 - bit_index
    int_list[byte_index] = _set_bit(int_list[byte_index], bit_index, c)

    # reverse int array if NOT big endian before casting it to Bytes
    if byteorder != "big":
        int_list = list(reversed(int_list))

    return Bytes(_int_list_to_bytes(int_list))


def _get_bit(v: int, index: int) -> int:
    return (v >> index) & 1


def _set_bit(v: int, index: int, x: int) -> int:
    """Set the index:th bit of v to 1 if x is truthy, else to 0, and return the new value."""
    mask = 1 << index  # Compute mask, an integer with just bit 'index' set.
    v &= ~mask  # Clear the bit indicated by the mask (if x is False)
    if x:
        v |= mask  # If x was True, set the bit indicated by the mask.
    return v


def _bytes_to_string(a: Bytes | bytes, err_msg: str) -> str:
    a = as_bytes(a)
    try:
        return a.decode()
    except UnicodeDecodeError:
        raise ValueError(err_msg) from None


class JsonRef:
    @staticmethod
    def _load_json(a: Bytes | bytes) -> dict[Any, Any]:
        a = as_bytes(a)
        try:
            # load the whole json payload as an array of key value pairs
            pairs = json.loads(a, object_pairs_hook=lambda x: x)
        except json.JSONDecodeError:
            raise ValueError("error while parsing JSON text, invalid json text") from None

        # turn the pairs into the dictionay for the top level,
        # all other levels remain as key value pairs
        # e.g.
        # input bytes: b'{"key0": 1,"key1": {"key2":2,"key2":"10"}, "key2": "test"}'
        # output dict: {'key0': 1, 'key1': [('key2', 2), ('key2', '10')], 'key2': 'test'}
        result = dict(pairs)
        if len(pairs) != len(result):
            raise ValueError(
                "error while parsing JSON text, invalid json text, duplicate keys found"
            )

        return result

    @staticmethod
    def _raise_key_error(key: str) -> None:
        raise ValueError(f"key {key} not found in JSON text")

    @staticmethod
    def json_string(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, str):
            raise TypeError(f"value must be a string type, not {type(result).__name__!r}")

        # encode with `surrogatepass` to allow sequences such as `\uD800`
        # decode with `replace` to replace with official replacement character `U+FFFD`
        # encode with default settings to get the final bytes result
        result = result.encode("utf-16", "surrogatepass").decode("utf-16", "replace").encode()
        return Bytes(result)

    @staticmethod
    def json_uint64(a: Bytes | bytes, b: Bytes | bytes, /) -> UInt64:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None

        try:
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        result = as_int(result, max=MAX_UINT64)
        return UInt64(result)

    @staticmethod
    def json_object(a: Bytes | bytes, b: Bytes | bytes, /) -> Bytes:
        b_str = _bytes_to_string(b, "can't decode bytes as string")
        obj = JsonRef._load_json(a)
        result = None
        try:
            # using a custom dict object to allow duplicate keys which is essentially a list
            result = obj[b_str]
        except KeyError:
            JsonRef._raise_key_error(b_str)

        if not isinstance(result, list) or not all(isinstance(i, tuple) for i in result):
            raise TypeError(f"value must be an object type, not {type(result).__name__!r}")

        result = _MultiKeyDict(result)
        result_string = json.dumps(result, separators=(",", ":"))
        return Bytes(result_string.encode())


class Scratch:
    @staticmethod
    def load_bytes(a: UInt64 | int, /) -> Bytes:
        from algopy_testing import get_test_context

        context = get_test_context()
        active_txn = context.get_active_transaction()

        slot_content = context._scratch_spaces[str(active_txn.txn_id)][a]
        match slot_content:
            case Bytes():
                return slot_content
            case bytes():
                return Bytes(slot_content)
            case UInt64() | int():
                return itob(slot_content)
            case _:
                raise ValueError(f"Invalid scratch space type: {type(slot_content)}")

    @staticmethod
    def load_uint64(a: UInt64 | int, /) -> UInt64:
        from algopy_testing import get_test_context

        context = get_test_context()
        active_txn = context.get_active_transaction()

        slot_content = context._scratch_spaces[str(active_txn.txn_id)][a]
        match slot_content:
            case Bytes() | bytes():
                return btoi(slot_content)
            case UInt64():
                return slot_content
            case int():
                return UInt64(slot_content)
            case _:
                raise ValueError(f"Invalid scratch space type: {type(slot_content)}")

    @staticmethod
    def store(a: UInt64 | int, b: Bytes | UInt64 | bytes | int, /) -> None:
        from algopy_testing import get_test_context

        context = get_test_context()
        active_txn = context.get_active_transaction()

        context._scratch_spaces[str(active_txn.txn_id)][a] = b


class _MultiKeyDict(dict[Any, Any]):
    def __init__(self, items: list[Any]):
        self[""] = ""
        items = [
            (
                (i[0], _MultiKeyDict(i[1]))
                if isinstance(i[1], list) and all(isinstance(j, tuple) for j in i[1])
                else i
            )
            for i in items
        ]
        self._items = items

    def items(self) -> Any:
        return self._items


def gload_uint64(a: UInt64 | int, b: UInt64 | int, /) -> UInt64:
    from algopy_testing import get_test_context

    context = get_test_context()
    txn_group = context.get_transaction_group()
    if not txn_group:
        raise ValueError("No transaction group found to reference scratch space")
    if a >= len(txn_group):
        raise ValueError(f"Index {a} out of range for transaction group")
    txn = txn_group[a]
    slot_content = context._scratch_spaces[str(txn.txn_id)][int(b)]
    match slot_content:
        case Bytes() | bytes():
            return btoi(slot_content)
        case int():
            return UInt64(slot_content)
        case UInt64():
            return slot_content
        case _:
            raise ValueError(f"Invalid scratch space type: {type(slot_content)}")


def gload_bytes(a: algopy.UInt64 | int, b: algopy.UInt64 | int, /) -> algopy.Bytes:
    import algopy

    from algopy_testing import get_test_context

    context = get_test_context()
    txn_group = context.get_transaction_group()
    if not txn_group:
        raise ValueError("No transaction group found to reference scratch space")
    if a >= len(txn_group):
        raise ValueError(f"Index {a} out of range for transaction group")
    txn = txn_group[a]
    slot_content = context._scratch_spaces[str(txn.txn_id)][int(b)]
    match slot_content:
        case algopy.Bytes():
            return slot_content
        case bytes():
            return algopy.Bytes(slot_content)
        case int() | algopy.UInt64():
            return itob(slot_content)
        case _:
            raise ValueError(f"Invalid scratch space type: {type(slot_content)}")


def gaid(a: UInt64 | int, /) -> algopy.Application:
    import algopy

    from algopy_testing import get_test_context

    context = get_test_context()
    txn_group = context.get_transaction_group()

    if not txn_group:
        raise ValueError("No transaction group found to reference gaid")

    a = int(a)
    if a >= len(txn_group):
        raise ValueError(f"Index {a} out of range for transaction group")

    txn = txn_group[a]

    if not txn.type == algopy.TransactionType.ApplicationCall:
        raise TypeError(f"Transaction at index {a} is not an ApplicationCallTransaction")

    app_id = txn.created_application_id
    if app_id is None:
        raise ValueError(f"Transaction at index {a} did not create an application")

    return context.get_application(cast(int, app_id))


def balance(a: algopy.Account | algopy.UInt64 | int, /) -> algopy.UInt64:
    import algopy

    from algopy_testing.context import get_test_context

    context = get_test_context()
    if not context:
        raise ValueError(
            "Test context is not initialized! Use `with algopy_testing_context()` to access "
            "the context manager."
        )

    active_txn = context.get_active_transaction()

    if isinstance(a, algopy.Account):
        account = a
    elif isinstance(a, (algopy.UInt64 | int)):
        index = int(a)
        if index == 0:
            account = active_txn.sender
        else:
            accounts = getattr(active_txn, "accounts", None)
            if not accounts or index >= len(accounts):
                raise ValueError(f"Invalid account index: {index}")
            account = accounts[index]
    else:
        raise TypeError("Invalid type for account parameter")

    account_data = context._account_data.get(account.public_key)
    if not account_data:
        raise ValueError(f"Account {account} not found in testing context!")

    balance = account_data.fields.get("balance")
    if balance is None:
        raise ValueError(f"Balance not set for account {account}")

    # Deduct the fee for the current transaction
    if account == active_txn.sender:
        fee = getattr(active_txn, "fee", algopy.UInt64(0))
        balance = algopy.UInt64(int(balance) - int(fee))

    return balance


def min_balance(a: algopy.Account | algopy.UInt64 | int, /) -> algopy.UInt64:
    import algopy

    from algopy_testing.context import get_test_context

    context = get_test_context()
    if not context:
        raise ValueError("Test context is not initialized!")

    active_txn = context.get_active_transaction()

    if isinstance(a, algopy.Account):
        account = a
    elif isinstance(a, (algopy.UInt64 | int)):
        index = int(a)
        if index == 0:
            account = active_txn.sender
        else:
            accounts = getattr(active_txn, "accounts", None)
            if not accounts or index >= len(accounts):
                raise ValueError(f"Invalid account index: {index}")
            account = accounts[index]
    else:
        raise TypeError("Invalid type for account parameter")

    account_data = context._account_data.get(account.public_key)
    if not account_data:
        raise ValueError(f"Account {account} not found in testing context!")

    # Return the pre-set min_balance if available, otherwise use a default value
    return account_data.fields.get("min_balance", UInt64(DEFAULT_ACCOUNT_MIN_BALANCE))


def exit(a: UInt64 | int, /) -> typing.Never:  # noqa: A001
    value = UInt64(a) if isinstance(a, int) else a
    raise SystemExit(int(value))


def app_opted_in(
    a: algopy.Account | algopy.UInt64 | int, b: algopy.Application | algopy.UInt64 | int, /
) -> bool:
    import algopy

    from algopy_testing.context import get_test_context

    context = get_test_context()
    active_txn = context.get_active_transaction()

    # Resolve account
    if isinstance(a, (algopy.UInt64 | int)):
        index = int(a)
        account = active_txn.sender if index == 0 else active_txn.accounts[index]
    else:
        account = a

    # Resolve application
    if isinstance(b, (algopy.UInt64 | int)):
        index = int(b)
        app_id = active_txn.application_id if index == 0 else active_txn.foreign_apps[index]
    else:
        app_id = b.id

    # Check if account is opted in to the application
    account_data = context._account_data.get(account.public_key)
    if not account_data:
        return False

    return app_id in account_data.opted_apps


class _AcctParamsGet:
    def __getattr__(
        self, name: str
    ) -> typing.Callable[
        [algopy.Account | algopy.UInt64 | int], tuple[algopy.UInt64 | algopy.Account, bool]
    ]:
        def get_account_param(
            a: algopy.Account | algopy.UInt64 | int,
        ) -> tuple[algopy.UInt64 | algopy.Account, bool]:
            import algopy

            from algopy_testing.context import get_test_context

            context = get_test_context()
            if not context:
                raise ValueError(
                    "Test context is not initialized! Use `with algopy_testing_context()` to "
                    "access the context manager."
                )

            active_txn = context.get_active_transaction()

            account_data = None

            if isinstance(a, (algopy.Account)):
                account_data = context.get_account(a.public_key)
            elif isinstance(a, (algopy.UInt64 | int)):
                active_txn = context.get_active_transaction()
                try:
                    account_data = active_txn.accounts(a)
                except IndexError as e:
                    raise ValueError(
                        f"Invalid account index for accounts in active transaction: {a}"
                    ) from e
            else:
                raise TypeError(f"Invalid type for account parameter: {type(a)}")

            if account_data is None:
                return UInt64(0), False

            param = name.removeprefix("acct_")
            value = getattr(account_data, param, None)
            return value, True  # type: ignore[return-value]

        if name.startswith("acct_"):
            return get_account_param
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


AcctParamsGet = _AcctParamsGet()


class _AssetParamsGet:
    def __getattr__(
        self, name: str
    ) -> typing.Callable[[algopy.Asset | algopy.UInt64 | int], tuple[typing.Any, bool]]:
        def get_asset_param(a: algopy.Asset | algopy.UInt64 | int) -> tuple[typing.Any, bool]:
            import algopy

            from algopy_testing.context import get_test_context

            context = get_test_context()
            if not context:
                raise ValueError(
                    "Test context is not initialized! Use `with algopy_testing_context()` to "
                    "access the context manager."
                )

            active_txn = context.get_active_transaction()
            if not active_txn:
                raise ValueError("No active transaction found to reference asset")

            is_index = isinstance(a, (algopy.UInt64 | int)) and int(a) < 1001
            try:
                asset_id = active_txn.assets(a).id if is_index else getattr(a, "id", a)
            except IndexError as e:
                raise ValueError(
                    f"Invalid asset index for assets in active transaction: {a}"
                ) from e
            asset_data = context.get_asset(asset_id)

            if asset_data is None:
                return algopy.UInt64(0), False

            param = name.removeprefix("asset_")
            value = getattr(asset_data, param, None)
            return value, True

        if name.startswith("asset_"):
            return get_asset_param
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


AssetParamsGet = _AssetParamsGet()


class _AssetHoldingGet:
    def _get_asset_holding(
        self,
        account: algopy.Account | algopy.UInt64 | int,
        asset: algopy.Asset | algopy.UInt64 | int,
        field: str,
    ) -> tuple[typing.Any, bool]:
        import algopy

        from algopy_testing.context import get_test_context

        context = get_test_context()
        if not context:
            raise ValueError(
                "Test context is not initialized! Use `with algopy_testing_context()` to access "
                "the context manager."
            )

        active_txn = context.get_active_transaction()

        # Resolve account
        if isinstance(account, (algopy.UInt64 | int)):
            index = int(account)
            account = active_txn.sender if index == 0 else active_txn.accounts[index]

        # Resolve asset
        if isinstance(asset, (algopy.UInt64 | int)):
            index = int(asset)
            asset_id = active_txn.assets[index]
        else:
            asset_id = asset.id

        assert isinstance(account, algopy.Account)
        account_data = context._account_data.get(account.public_key)
        if not account_data:
            return algopy.UInt64(0), False

        asset_balance = account_data.opted_asset_balances.get(asset_id)
        if asset_balance is None:
            return algopy.UInt64(0), False

        if field == "balance":
            return asset_balance, True
        elif field == "frozen":
            asset_data = context._asset_data.get(int(asset_id))
            if not asset_data:
                return algopy.UInt64(0), False
            return asset_data["default_frozen"], True
        else:
            raise ValueError(f"Invalid asset holding field: {field}")

    def asset_balance(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Asset | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        import algopy

        balance, exists = self._get_asset_holding(a, b, "balance")
        return algopy.UInt64(balance if exists else 0), exists

    def asset_frozen(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Asset | algopy.UInt64 | int, /
    ) -> tuple[bool, bool]:
        frozen, exists = self._get_asset_holding(a, b, "frozen")
        return bool(frozen), exists


AssetHoldingGet = _AssetHoldingGet()


class _AppParamsGet:
    def _get_app_param_from_ctx(
        self, a: algopy.Application | algopy.UInt64 | int, param: str
    ) -> tuple[Any, bool]:
        import algopy

        from algopy_testing import get_test_context

        context = get_test_context()

        if not context:
            raise ValueError(
                "Test context is not initialized! Use `with algopy_testing_context()` "
                "to access the context manager."
            )

        active_txn = context.get_active_transaction()

        is_index = isinstance(a, (algopy.UInt64 | int)) and int(a) < 1001
        try:
            app_id = active_txn.apps(a).id if is_index else getattr(a, "id", a)
        except IndexError as e:
            raise ValueError(f"Invalid app index for apps in active transaction: {a}") from e
        app_data = context.get_application(int(app_id))

        if app_data is None:
            return algopy.UInt64(0), False

        value = getattr(app_data, param, None)
        return value, True

    def app_approval_program(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Bytes, bool]:
        return self._get_app_param_from_ctx(a, "approval_program")

    def app_clear_state_program(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Bytes, bool]:
        return self._get_app_param_from_ctx(a, "clear_state_program")

    def app_global_num_uint(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "global_num_uint")

    def app_global_num_byte_slice(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "global_num_byte_slice")

    def app_local_num_uint(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "local_num_uint")

    def app_local_num_byte_slice(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "local_num_byte_slice")

    def app_extra_program_pages(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.UInt64, bool]:
        return self._get_app_param_from_ctx(a, "extra_program_pages")

    def app_creator(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Account, bool]:
        return self._get_app_param_from_ctx(a, "creator")

    def app_address(
        self, a: algopy.Application | algopy.UInt64 | int, /
    ) -> tuple[algopy.Account, bool]:
        return self._get_app_param_from_ctx(a, "address")


AppParamsGet = _AppParamsGet()


class _AppLocal:
    def _get_local_state(self, key: bytes) -> algopy.LocalState[Any]:
        from algopy_testing import get_test_context

        test_context = get_test_context()
        if not test_context or not test_context._active_contract:
            raise ValueError("No active contract or test context found.")

        local_states = test_context._active_contract._get_local_states()
        local_state = local_states.get(key)
        if local_state is None:
            key_repr = key.decode("utf-8", errors="backslashreplace")
            raise ValueError(f"Local state with key {key_repr!r} not found")
        return local_state

    def _get_key(self, b: algopy.Bytes | bytes) -> bytes:
        import algopy

        return b.value if isinstance(b, algopy.Bytes) else b

    def _parse_local_state_value(self, value: Any) -> Any:
        if hasattr(value, "bytes"):
            return value.bytes
        return value

    def _get_contract(
        self,
        b: algopy.Application | algopy.UInt64 | int,
    ) -> algopy.Contract | algopy.ARC4Contract:
        import algopy

        from algopy_testing import get_test_context

        test_context = get_test_context()
        if not test_context:
            raise ValueError("Test context is not initialized!")

        app_id = int(b.id) if isinstance(b, algopy.Application) else int(b)
        contract = test_context._app_id_to_contract.get(app_id)
        if contract is None:
            raise ValueError(f"Contract with app id {b} not found")
        return contract

    def get_bytes(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> algopy.Bytes:
        import algopy

        try:
            key = self._get_key(b)
            local_state = self._get_local_state(key)[a]
            return algopy.Bytes(self._parse_local_state_value(local_state))
        except (ValueError, KeyError):
            return algopy.UInt64(0)  # type: ignore[return-value]

    def get_uint64(
        self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> algopy.UInt64:
        import algopy

        try:
            local_state = self._get_local_state(self._get_key(b))
            return algopy.UInt64(local_state.get(a))
        except (ValueError, KeyError):
            return algopy.UInt64(0)

    def get_ex_bytes(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Application | algopy.UInt64 | int,
        c: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.Bytes, bool]:
        import algopy

        contract = self._get_contract(b)
        local_states = contract._get_local_states()
        local_state = local_states.get(self._get_key(c))

        if local_state and a in local_state and local_state[a] is not None:
            return algopy.Bytes(self._parse_local_state_value(local_state[a])), True
        else:
            return algopy.Bytes(b""), False

    def get_ex_uint64(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Application | algopy.UInt64 | int,
        c: algopy.Bytes | bytes,
        /,
    ) -> tuple[algopy.UInt64, bool]:
        import algopy

        contract = self._get_contract(b)
        local_states = contract._get_local_states()
        local_state = local_states.get(self._get_key(c))

        if local_state and a in local_state:
            return algopy.UInt64(local_state[a]), True
        else:
            return algopy.UInt64(0), False

    def delete(self, a: algopy.Account | algopy.UInt64 | int, b: algopy.Bytes | bytes, /) -> None:
        local_state = self._get_local_state(self._get_key(b))
        del local_state[a]

    def put(
        self,
        a: algopy.Account | algopy.UInt64 | int,
        b: algopy.Bytes | bytes,
        c: algopy.Bytes | algopy.UInt64 | bytes | int,
        /,
    ) -> None:
        local_state = self._get_local_state(self._get_key(b))
        local_state[a] = c


AppLocal = _AppLocal()


class _AppGlobal:
    def _get_global_state(self, key: bytes) -> algopy.GlobalState[Any]:
        from algopy_testing import get_test_context

        test_context = get_test_context()
        if not test_context or not test_context._active_contract:
            raise ValueError("No active contract or test context found.")

        global_states = test_context._active_contract._get_global_states()
        if global_states is None:
            raise ValueError("No global state found on active contract instance")
        return global_states[key]

    def _get_key(self, b: algopy.Bytes | bytes) -> bytes:
        import algopy

        return b.value if isinstance(b, algopy.Bytes) else b

    def _get_contract(
        self,
        b: algopy.Application | algopy.UInt64 | int,
    ) -> algopy.Contract | algopy.ARC4Contract:
        import algopy

        from algopy_testing import get_test_context

        test_context = get_test_context()
        if not test_context:
            raise ValueError("Test context is not initialized!")

        app_id = int(b.id) if isinstance(b, algopy.Application) else int(b)
        contract = test_context._app_id_to_contract.get(app_id)
        if contract is None:
            raise ValueError(f"Contract with app id {b} not found")
        return contract

    def _parse_global_state_value(self, value: Any) -> Any:
        if hasattr(value, "bytes"):
            return value.bytes
        return value

    def get_bytes(self, b: algopy.Bytes | bytes, /) -> algopy.Bytes:
        import algopy

        try:
            global_state = self._get_global_state(self._get_key(b))
            return algopy.Bytes(self._parse_global_state_value(global_state.get(b)))
        except (ValueError, KeyError):
            return algopy.UInt64(0)  # type: ignore[return-value]

    def get_uint64(self, b: algopy.Bytes | bytes, /) -> algopy.UInt64:
        import algopy

        try:
            global_state = self._get_global_state(self._get_key(b))
            return algopy.UInt64(global_state.get(b))
        except (ValueError, KeyError):
            return algopy.UInt64(0)

    def get_ex_bytes(
        self, a: algopy.Application | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> tuple[algopy.Bytes, bool]:
        import algopy

        contract = self._get_contract(a)
        global_states = contract._get_global_states()
        global_state = global_states.get(self._get_key(b))
        value = self._parse_global_state_value(
            global_state
            if not isinstance(global_state, algopy.GlobalState)
            else global_state.value
        )
        return (algopy.Bytes(value), True) if value is not None else (algopy.Bytes(b""), False)

    def get_ex_uint64(
        self, a: algopy.Application | algopy.UInt64 | int, b: algopy.Bytes | bytes, /
    ) -> tuple[algopy.UInt64, bool]:
        import algopy

        contract = self._get_contract(a)
        global_state = contract._get_global_state()
        value = global_state.get(self._get_key(b))
        return (algopy.UInt64(value), True) if value is not None else (algopy.UInt64(0), False)

    def delete(self, b: algopy.Bytes | bytes, /) -> None:
        from algopy_testing import get_test_context

        test_context = get_test_context()
        if not test_context or not test_context._active_contract:
            raise ValueError("No active contract or test context found.")

        delattr(test_context._active_contract, self._get_key(b).decode("utf-8"))

    def put(
        self, a: algopy.Bytes | bytes, b: algopy.Bytes | algopy.UInt64 | bytes | int, /
    ) -> None:
        global_state = self._get_global_state(self._get_key(a))
        global_state.value = b


AppGlobal = _AppGlobal()


def arg(a: UInt64 | int, /) -> Bytes:
    from algopy_testing.context import get_test_context

    context = get_test_context()
    if not context:
        raise ValueError("Test context is not initialized!")

    return context._active_lsig_args[int(a)]


class _EllipticCurve:
    def __getattr__(self, __name: str) -> Any:
        raise NotImplementedError(
            f"EllipticCurve.{__name} is currently not available as a native "
            "`algorand-python-testing` type. Use your own preferred testing "
            "framework of choice to mock the behaviour."
        )


EllipticCurve = _EllipticCurve()


class Box:
    @staticmethod
    def create(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> bool:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        size = int(b)
        if not name_bytes or size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        if context.get_box(name_bytes):
            return False
        context.set_box(name_bytes, b"\x00" * size)
        return True

    @staticmethod
    def delete(a: algopy.Bytes | bytes, /) -> bool:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        if context.get_box(name_bytes):
            context.clear_box(name_bytes)
            return True
        return False

    @staticmethod
    def extract(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.UInt64 | int, /
    ) -> algopy.Bytes:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        start = int(b)
        length = int(c)
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        result = box_content[start : start + length]
        return algopy.Bytes(result)

    @staticmethod
    def get(a: algopy.Bytes | bytes, /) -> tuple[algopy.Bytes, bool]:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        box_content = algopy.Bytes(context.get_box(name_bytes))
        box_exists = context.does_box_exist(name_bytes)
        return box_content, box_exists

    @staticmethod
    def length(a: algopy.Bytes | bytes, /) -> tuple[algopy.UInt64, bool]:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        box_content = context.get_box(name_bytes)
        box_exists = context.does_box_exist(name_bytes)
        return algopy.UInt64(len(box_content)), box_exists

    @staticmethod
    def put(a: algopy.Bytes | bytes, b: algopy.Bytes | bytes, /) -> None:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        content = b.value if isinstance(b, algopy.Bytes) else b
        existing_content = context.get_box(name_bytes)
        if existing_content and len(existing_content) != len(content):
            raise ValueError("New content length does not match existing box length")
        context.set_box(name_bytes, algopy.Bytes(content))

    @staticmethod
    def replace(
        a: algopy.Bytes | bytes, b: algopy.UInt64 | int, c: algopy.Bytes | bytes, /
    ) -> None:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        start = int(b)
        new_content = c.value if isinstance(c, algopy.Bytes) else c
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if start + len(new_content) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = (
            box_content[:start] + new_content + box_content[start + len(new_content) :]
        )
        context.set_box(name_bytes, updated_content)

    @staticmethod
    def resize(a: algopy.Bytes | bytes, b: algopy.UInt64 | int, /) -> None:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        new_size = int(b)
        if not name_bytes or new_size > MAX_BOX_SIZE:
            raise ValueError("Invalid box name or size")
        box_content = context.get_box(name_bytes)
        if not box_content:
            raise RuntimeError("Box does not exist")
        if new_size > len(box_content):
            updated_content = box_content + b"\x00" * (new_size - len(box_content))
        else:
            updated_content = box_content[:new_size]
        context.set_box(name_bytes, updated_content)

    @staticmethod
    def splice(
        a: algopy.Bytes | bytes,
        b: algopy.UInt64 | int,
        c: algopy.UInt64 | int,
        d: algopy.Bytes | bytes,
        /,
    ) -> None:
        import algopy

        context = get_test_context()
        name_bytes = a.value if isinstance(a, algopy.Bytes) else a
        start = int(b)
        delete_count = int(c)
        insert_content = d.value if isinstance(d, algopy.Bytes) else d
        box_content = context.get_box(name_bytes)

        if not box_content:
            raise RuntimeError("Box does not exist")

        if start > len(box_content):
            raise ValueError("Start index exceeds box size")

        # Calculate the end index for deletion
        end = min(start + delete_count, len(box_content))

        # Construct the new content
        new_content = box_content[:start] + insert_content + box_content[end:]

        # Adjust the size if necessary
        if len(new_content) > len(box_content):
            # Truncate if the new content is too long
            new_content = new_content[: len(box_content)]
        elif len(new_content) < len(box_content):
            # Pad with zeros if the new content is too short
            new_content += b"\x00" * (len(box_content) - len(new_content))

        # Update the box with the new content
        context.set_box(name_bytes, new_content)


__all__ = [
    "AcctParamsGet",
    "AppGlobal",
    "AppLocal",
    "AppParamsGet",
    "AssetHoldingGet",
    "AssetParamsGet",
    "Base64",
    "BigUInt",
    "Block",
    "Box",
    "EC",
    "ECDSA",
    "EllipticCurve",
    "GITxn",
    "GTxn",
    "Global",
    "ITxn",
    "ITxnCreate",
    "JsonRef",
    "Scratch",
    "Txn",
    "UInt64",
    "VrfVerify",
    "addw",
    "arg",
    "app_opted_in",
    "balance",
    "base64_decode",
    "bitlen",
    "bsqrt",
    "btoi",
    "bzero",
    "concat",
    "divmodw",
    "divw",
    "ecdsa_pk_decompress",
    "ecdsa_pk_recover",
    "ecdsa_verify",
    "ed25519verify",
    "ed25519verify_bare",
    "err",
    "exit",
    "exp",
    "expw",
    "extract",
    "extract_uint16",
    "extract_uint32",
    "extract_uint64",
    "gaid",
    "getbit",
    "getbyte",
    "gload_bytes",
    "gload_uint64",
    "itob",
    "keccak256",
    "min_balance",
    "mulw",
    "replace",
    "select_bytes",
    "select_uint64",
    "setbit_bytes",
    "setbit_uint64",
    "setbyte",
    "sha256",
    "sha3_256",
    "sha512_256",
    "shl",
    "shr",
    "sqrt",
    "substring",
    "vrf_verify",
]
