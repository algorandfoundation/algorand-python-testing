from __future__ import annotations

import enum
import hashlib
import typing
from collections.abc import Sequence

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

from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.enums import OnCompleteAction
from _algopy_testing.primitives import Bytes, UInt64
from _algopy_testing.utils import as_bytes, raise_mocked_function_error


class ECDSA(enum.Enum):
    Secp256k1 = 0
    Secp256r1 = 1


class VrfVerify(enum.Enum):
    VrfAlgorand = 0


def sha256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    return Bytes(hashlib.sha256(input_value).digest())


def sha3_256(a: Bytes | bytes, /) -> Bytes:
    input_value = as_bytes(a)
    return Bytes(hashlib.sha3_256(input_value).digest())


def sumhash512(_a: Bytes | bytes, /) -> Bytes:
    raise_mocked_function_error("sumhash512")


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
    from _algopy_testing.utils import as_bytes

    txn = lazy_context.active_group.active_txn

    program_pages = typing.cast(
        Sequence[Bytes],
        (
            txn.fields["clear_state_program"]
            if txn.on_completion == OnCompleteAction.ClearState
            else txn.fields["approval_program"]
        ),
    )
    program_bytes = b"".join(map(as_bytes, program_pages))

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


def falcon_verify(_a: Bytes | bytes, _b: Bytes | bytes, _c: Bytes | bytes, /) -> bool:
    raise_mocked_function_error("falcon_verify")


def vrf_verify(
    _s: VrfVerify,
    _a: Bytes | bytes,
    _b: Bytes | bytes,
    _c: Bytes | bytes,
    /,
) -> tuple[Bytes, bool]:
    raise_mocked_function_error("vrf_verify")


class EC(enum.StrEnum):
    """Available values for the `EC` enum."""

    BN254g1 = "BN254g1"
    BN254g2 = "BN254g2"
    BLS12_381g1 = "BLS12_381g1"
    BLS12_381g2 = "BLS12_381g2"


class _MockedMember:

    def __set_name__(self, owner: type, name: str) -> None:
        self.name = f"{owner.__name__}.{name}"

    def __call__(self, *_args: typing.Any, **_kwargs: typing.Any) -> None:
        raise_mocked_function_error(self.name)


class EllipticCurve:
    add = _MockedMember()
    map_to = _MockedMember()
    pairing_check = _MockedMember()
    scalar_mul = _MockedMember()
    scalar_mul_multi = _MockedMember()
    subgroup_check = _MockedMember()


class MiMCConfigurations(enum.StrEnum):
    BN254Mp110 = enum.auto()
    BLS12_381Mp111 = enum.auto()


def mimc(_c: MiMCConfigurations, _a: Bytes | bytes, /) -> Bytes:
    raise_mocked_function_error("mimc")
