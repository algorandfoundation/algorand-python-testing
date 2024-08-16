import contextlib
import typing
from pathlib import Path

import algopy
import algopy_testing
import algosdk
import coincurve
import ecdsa  # type: ignore  # noqa: PGH003
import ecdsa.util  # type: ignore  # noqa: PGH003
import nacl.signing
import pytest
from algokit_utils import LogicError, get_localnet_default_account
from algopy_testing import algopy_testing_context, op
from algopy_testing.context import AlgopyTestContext
from algopy_testing.primitives.bytes import Bytes
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import convert_native_to_stack
from algosdk.v2client.algod import AlgodClient
from Cryptodome.Hash import keccak
from ecdsa import SECP256k1, SigningKey, curves
from pytest_mock import MockerFixture

from tests.artifacts.StateOps.contract import (
    ITxnOpsContract,
    StateAcctParamsGetContract,
    StateAppGlobalContract,
    StateAppGlobalExContract,
    StateAppLocalContract,
    StateAppLocalExContract,
    StateAppParamsContract,
    StateAssetHoldingContract,
    StateAssetParamsContract,
)
from tests.common import (
    INITIAL_BALANCE_MICRO_ALGOS,
    AVMInvoker,
    create_avm_invoker,
    generate_test_account,
    generate_test_asset,
)

ARTIFACTS_DIR = Path(__file__).parent / "artifacts"
CRYPTO_OPS_APP_SPEC = ARTIFACTS_DIR / "CryptoOps" / "data" / "CryptoOpsContract.arc32.json"
STATE_OPS_APP_SPEC_ROOT = ARTIFACTS_DIR / "StateOps" / "data"
STATE_OPS_ACCT_PARAMS_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAcctParamsGetContract.arc32.json"
STATE_OPS_ASSET_HOLDING_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAssetHoldingContract.arc32.json"
STATE_OPS_ASSET_PARAMS_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAssetParamsContract.arc32.json"
STATE_OPS_APP_PARAMS_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAppParamsContract.arc32.json"
STATE_OPS_APP_LOCAL_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAppLocalContract.arc32.json"
STATE_OPS_APP_LOCAL_EX_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAppLocalExContract.arc32.json"
STATE_OPS_APP_GLOBAL_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAppGlobalContract.arc32.json"
STATE_OPS_APP_GLOBAL_EX_SPEC = STATE_OPS_APP_SPEC_ROOT / "StateAppGlobalExContract.arc32.json"

MAX_ARG_LEN = 2048
MAX_BYTES_SIZE = 4096


def _generate_ecdsa_test_data(curve: curves.Curve) -> dict[str, typing.Any]:
    sk = SigningKey.generate(curve=curve)
    vk = sk.verifying_key
    data = b"test data for ecdsa"
    message_hash = keccak.new(data=data, digest_bits=256).digest()

    signature = sk.sign_digest(message_hash, sigencode=ecdsa.util.sigencode_string)
    r, s = ecdsa.util.sigdecode_string(signature, sk.curve.order)
    recovery_id = 0  # Recovery ID is typically 0 or 1

    return {
        "data": Bytes(message_hash),
        "r": Bytes(r.to_bytes(32, byteorder="big")),
        "s": Bytes(s.to_bytes(32, byteorder="big")),
        "recovery_id": UInt64(recovery_id),
        "pubkey_x": Bytes(vk.to_string()[:32]),
        "pubkey_y": Bytes(vk.to_string()[32:]),
    }


@pytest.fixture()
def context() -> typing.Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()


@pytest.fixture(scope="module")
def get_crypto_ops_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(CRYPTO_OPS_APP_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_app_params_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_APP_PARAMS_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_app_local_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_APP_LOCAL_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_app_global_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_APP_GLOBAL_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_app_global_ex_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_APP_GLOBAL_EX_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_app_local_ex_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_APP_LOCAL_EX_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_asset_holding_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_ASSET_HOLDING_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_asset_params_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_ASSET_PARAMS_SPEC, algod_client)


@pytest.fixture(scope="module")
def get_state_acct_params_avm_result(algod_client: AlgodClient) -> AVMInvoker:
    return create_avm_invoker(STATE_OPS_ACCT_PARAMS_SPEC, algod_client)


@pytest.mark.parametrize(
    ("input_value", "pad_size"),
    [
        (b"", 0),
        (b"0" * (MAX_ARG_LEN - 14), 0),
        (b"abc", 0),
        (Bytes(b"abc").value, MAX_BYTES_SIZE - 3),
        (b"abc", MAX_BYTES_SIZE - 3),
    ],
)
def test_sha256(get_crypto_ops_avm_result: AVMInvoker, input_value: bytes, pad_size: int) -> None:
    avm_result = get_crypto_ops_avm_result("verify_sha256", a=input_value, pad_size=pad_size)
    result = op.sha256((b"\x00" * pad_size) + input_value)
    assert avm_result == result.value
    assert len(result.value) == 32


@pytest.mark.parametrize(
    ("input_value", "pad_size"),
    [
        (b"", 0),
        (b"0" * (MAX_ARG_LEN - 14), 0),
        (b"abc", 0),
        (Bytes(b"abc").value, MAX_BYTES_SIZE - 3),
        (b"abc", MAX_BYTES_SIZE - 3),
    ],
)
def test_sha3_256(
    get_crypto_ops_avm_result: AVMInvoker, input_value: bytes, pad_size: int
) -> None:
    avm_result = get_crypto_ops_avm_result("verify_sha3_256", a=input_value, pad_size=pad_size)
    result = op.sha3_256((b"\x00" * pad_size) + input_value)
    assert avm_result == result.value
    assert len(result.value) == 32


@pytest.mark.parametrize(
    ("input_value", "pad_size"),
    [
        (b"", 0),
        (b"0" * (MAX_ARG_LEN - 14), 0),
        (b"abc", 0),
        (Bytes(b"abc").value, MAX_BYTES_SIZE - 3),
        (b"abc", MAX_BYTES_SIZE - 3),
    ],
)
def test_keccak_256(
    get_crypto_ops_avm_result: AVMInvoker, input_value: bytes, pad_size: int
) -> None:
    avm_result = get_crypto_ops_avm_result("verify_keccak_256", a=input_value, pad_size=pad_size)
    result = op.keccak256((b"\x00" * pad_size) + input_value)
    assert avm_result == result.value
    assert len(result.value) == 32


@pytest.mark.parametrize(
    ("input_value", "pad_size"),
    [
        (b"", 0),
        (b"0" * (MAX_ARG_LEN - 14), 0),
        (b"abc", 0),
        (Bytes(b"abc").value, MAX_BYTES_SIZE - 3),
        (b"abc", MAX_BYTES_SIZE - 3),
    ],
)
def test_sha512_256(
    get_crypto_ops_avm_result: AVMInvoker, input_value: bytes, pad_size: int
) -> None:
    avm_result = get_crypto_ops_avm_result("verify_sha512_256", a=input_value, pad_size=pad_size)
    result = op.sha512_256((b"\x00" * pad_size) + input_value)
    assert avm_result == result.value
    assert len(result.value) == 32


def test_ed25519verify_bare(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    signing_key = nacl.signing.SigningKey.generate()
    public_key = signing_key.verify_key.encode()
    message = b"Test message for ed25519 verification"
    signature = signing_key.sign(message).signature

    sp = algod_client.suggested_params()
    sp.fee = 2000
    avm_result = get_crypto_ops_avm_result(
        "verify_ed25519verify_bare", a=message, b=signature, c=public_key, suggested_params=sp
    )
    result = op.ed25519verify_bare(message, signature, public_key)

    assert avm_result == result, "The AVM result should match the expected result"


def test_ed25519verify(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    approval = get_crypto_ops_avm_result.client.approval
    assert approval
    with algopy_testing_context() as ctx:
        app_call = ctx.any.txn.application_call(
            approval_program=(algopy.Bytes(approval.raw_binary),)
        )

        # Prepare message and signing parameters
        message = b"Test message for ed25519 verification"
        sp = algod_client.suggested_params()
        sp.fee = 2000

        # Generate key pair and sign the message
        private_key, public_key = algosdk.account.generate_account()
        public_key = algosdk.encoding.decode_address(public_key)
        signature = algosdk.logic.teal_sign_from_program(private_key, message, approval.raw_binary)

        # Verify the signature using AVM and local op
        avm_result = get_crypto_ops_avm_result(
            "verify_ed25519verify", a=message, b=signature, c=public_key, suggested_params=sp
        )
        with ctx.txn.create_group([app_call], active_txn_index=0):
            result = op.ed25519verify(message, signature, public_key)

        assert avm_result == result, "The AVM result should match the expected result"


def test_ed25519verify_no_context() -> None:
    # Ensure the function raises an error outside the state context
    with pytest.raises(ValueError, match="Test context is not initialized!"):
        op.ed25519verify(b"", b"", b"")


def test_ecdsa_verify_k1(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    message_hash = bytes.fromhex(
        "f809fd0aa0bb0f20b354c6b2f86ea751957a4e262a546bd716f34f69b9516ae1"
    )
    sig_r = bytes.fromhex("f7f913754e5c933f3825d3aef22e8bf75cfe35a18bede13e15a6e4adcfe816d2")
    sig_s = bytes.fromhex("0b5599159aa859d79677f33280848ae4c09c2061e8b5881af8507f8112966754")
    pubkey_x = bytes.fromhex("a710244d62747aa8db022ddd70617240adaf881b439e5f69993800e614214076")
    pubkey_y = bytes.fromhex("48d0d337704fe2c675909d2c93f7995e199156f302f63c74a8b96827b28d777b")

    sp = algod_client.suggested_params()
    sp.fee = 5000

    avm_result = get_crypto_ops_avm_result(
        "verify_ecdsa_verify_k1",
        a=message_hash,
        b=sig_r,
        c=sig_s,
        d=pubkey_x,
        e=pubkey_y,
        suggested_params=sp,
    )
    result = op.ecdsa_verify(op.ECDSA.Secp256k1, message_hash, sig_r, sig_s, pubkey_x, pubkey_y)
    assert avm_result == result, "The AVM result should match the expected result"


def test_ecdsa_verify_r1(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    message_hash = bytes.fromhex(
        "f809fd0aa0bb0f20b354c6b2f86ea751957a4e262a546bd716f34f69b9516ae1"
    )
    sig_r = bytes.fromhex("18d96c7cda4bc14d06277534681ded8a94828eb731d8b842e0da8105408c83cf")
    sig_s = bytes.fromhex("7d33c61acf39cbb7a1d51c7126f1718116179adebd31618c4604a1f03b5c274a")
    pubkey_x = bytes.fromhex("f8140e3b2b92f7cbdc8196bc6baa9ce86cf15c18e8ad0145d50824e6fa890264")
    pubkey_y = bytes.fromhex("bd437b75d6f1db67155a95a0da4b41f2b6b3dc5d42f7db56238449e404a6c0a3")

    sp = algod_client.suggested_params()
    sp.fee = 5000

    avm_result = get_crypto_ops_avm_result(
        "verify_ecdsa_verify_r1",
        a=message_hash,
        b=sig_r,
        c=sig_s,
        d=pubkey_x,
        e=pubkey_y,
        suggested_params=sp,
    )
    result = op.ecdsa_verify(op.ECDSA.Secp256r1, message_hash, sig_r, sig_s, pubkey_x, pubkey_y)
    assert avm_result == result, "The AVM result should match the expected result"


def test_verify_ecdsa_recover_k1(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    test_data = _generate_ecdsa_test_data(SECP256k1)

    a = test_data["data"].value
    b = test_data["recovery_id"].value
    c = test_data["r"].value
    d = test_data["s"].value

    expected_x, expected_y = op.ecdsa_pk_recover(op.ECDSA.Secp256k1, a, b, c, d)
    sp = algod_client.suggested_params()
    sp.fee = 3000
    result = get_crypto_ops_avm_result(
        "verify_ecdsa_recover_k1",
        a=a,
        b=b,
        c=c,
        d=d,
        suggested_params=sp,
    )
    assert isinstance(result, list)
    result_x, result_y = bytes(result[0]), bytes(result[1])

    assert result_x == expected_x, "X coordinate mismatch"
    assert result_y == expected_y, "Y coordinate mismatch"


def test_verify_ecdsa_decompress_k1(
    algod_client: AlgodClient,
    get_crypto_ops_avm_result: AVMInvoker,
) -> None:
    test_data = _generate_ecdsa_test_data(SECP256k1)

    a = test_data["data"].value
    b = test_data["recovery_id"].value
    c = test_data["r"].value
    d = test_data["s"].value
    signature_rs = c + d + bytes([b])
    pk = coincurve.PublicKey.from_signature_and_message(signature_rs, a, hasher=None)

    sp = algod_client.suggested_params()
    sp.fee = 3000
    result = get_crypto_ops_avm_result(
        "verify_ecdsa_decompress_k1",
        a=pk.format(compressed=True),
        suggested_params=sp,
    )
    assert isinstance(result, list)
    result_x, result_y = bytes(result[0]), bytes(result[1])

    assert result_x == pk.point()[0].to_bytes(32, byteorder="big"), "X coordinate mismatch"
    assert result_y == pk.point()[1].to_bytes(32, byteorder="big"), "Y coordinate mismatch"


def test_verify_vrf_verify(
    algod_client: AlgodClient, get_crypto_ops_avm_result: AVMInvoker, mocker: MockerFixture
) -> None:
    """
    'verify_vrf' is not implemented, the test aims to confirm that its possible to mock while
    comparing against the real vrf_verify execution.
    """

    a: bytes = bytes.fromhex("528b9e23d93d0e020a119d7ba213f6beb1c1f3495a217166ecd20f5a70e7c2d7")
    b: bytes = bytes.fromhex(
        "372a3afb42f55449c94aaa5f274f26543e77e8d8af4babee1a6fbc1c0391aa9e6e0b8d8d7f4ed045d5b517fea8ad3566025ae90d2f29f632e38384b4c4f5b9eb741c6e446b0f540c1b3761d814438b04"
    )
    c = bytes.fromhex("3a2740da7a0788ebb12a52154acbcca1813c128ca0b249e93f8eb6563fee418d")

    def run_real_vrf_verify() -> tuple[Bytes, bool]:
        sp = algod_client.suggested_params()
        sp.fee = 6000
        result = get_crypto_ops_avm_result("verify_vrf_verify", a=a, b=b, c=c, suggested_params=sp)
        return (Bytes(bytes(result[0])), bool(result[1]))  # type: ignore  # noqa: PGH003

    def run_mocked_vrf_verify() -> tuple[Bytes, bool]:
        return op.vrf_verify(op.VrfVerify.VrfAlgorand, a, b, c)

    avm_result = run_real_vrf_verify()
    mocker.patch("algopy_testing.op.vrf_verify", return_value=(avm_result[0], True))
    mocked_result = run_mocked_vrf_verify()

    assert avm_result == mocked_result


def test_asset_holding_get(
    algod_client: AlgodClient,
    get_state_asset_holding_avm_result: AVMInvoker,
    context: AlgopyTestContext,
) -> None:
    dummy_account_a = get_localnet_default_account(algod_client)
    expected_balance = 100
    dummy_asset = generate_test_asset(
        algod_client=algod_client,
        total=expected_balance,
        sender=dummy_account_a,
        decimals=0,
        default_frozen=False,
    )
    sp = algod_client.suggested_params()
    sp.fee = 1000

    avm_asset_balance = get_state_asset_holding_avm_result(
        "verify_asset_holding_get",
        a=dummy_account_a.address,
        b=dummy_asset,
        suggested_params=sp,
    )
    avm_frozen_balance = get_state_asset_holding_avm_result(
        "verify_asset_frozen_get",
        a=dummy_account_a.address,
        b=dummy_asset,
        suggested_params=sp,
    )

    mock_asset = context.any.asset()
    mock_account = context.any.account(
        opted_asset_balances={mock_asset.id: algopy.UInt64(expected_balance)}
    )
    mock_contract = StateAssetHoldingContract()
    mock_asset_balance = mock_contract.verify_asset_holding_get(mock_account, mock_asset)
    assert mock_asset_balance == avm_asset_balance == expected_balance
    mock_frozen_balance = mock_contract.verify_asset_frozen_get(mock_account, mock_asset)
    assert mock_frozen_balance == avm_frozen_balance is False


@pytest.mark.parametrize(
    ("method_name", "expected_value"),
    [
        ("verify_asset_params_get_total", 100),
        ("verify_asset_params_get_decimals", 0),
        ("verify_asset_params_get_default_frozen", False),
        ("verify_asset_params_get_unit_name", b"UNIT"),
        ("verify_asset_params_get_name", b"TEST"),
        ("verify_asset_params_get_url", b"https://algorand.co"),
        ("verify_asset_params_get_metadata_hash", b"test" + b" " * 28),
        ("verify_asset_params_get_manager", algosdk.constants.ZERO_ADDRESS),
        ("verify_asset_params_get_reserve", algosdk.constants.ZERO_ADDRESS),
        ("verify_asset_params_get_freeze", algosdk.constants.ZERO_ADDRESS),
        ("verify_asset_params_get_clawback", algosdk.constants.ZERO_ADDRESS),
        ("verify_asset_params_get_creator", lambda a: algopy.Account(a.address).bytes),
    ],
)
def test_asset_params_get(
    algod_client: AlgodClient,
    get_state_asset_params_avm_result: AVMInvoker,
    context: AlgopyTestContext,
    method_name: str,
    expected_value: int | bytes | bool | typing.Callable[..., algopy.Bytes],
) -> None:
    dummy_account = get_localnet_default_account(algod_client)
    metadata_hash = b"test" + b" " * 28

    mock_asset = context.any.asset(
        total=algopy.UInt64(100),
        decimals=algopy.UInt64(0),
        name=algopy.Bytes(b"TEST"),
        unit_name=algopy.Bytes(b"UNIT"),
        url=algopy.Bytes(b"https://algorand.co"),
        metadata_hash=algopy.Bytes(metadata_hash),
        creator=algopy.Account(dummy_account.address),
    )

    dummy_asset = generate_test_asset(
        algod_client=algod_client,
        total=100,
        sender=dummy_account,
        decimals=0,
        default_frozen=False,
        unit_name="UNIT",
        asset_name="TEST",
        url="https://algorand.co",
        metadata_hash=metadata_hash,
    )

    sp = algod_client.suggested_params()
    sp.fee = 1000

    mock_contract = StateAssetParamsContract()

    avm_result = get_state_asset_params_avm_result(method_name, a=dummy_asset, suggested_params=sp)
    mock_result = getattr(mock_contract, method_name)(mock_asset)
    # TODO: 1.0 add separate tests by foreign array index

    expected = expected_value(dummy_account) if callable(expected_value) else expected_value
    expected = (
        algopy.Account().bytes if str(expected) == algosdk.constants.ZERO_ADDRESS else expected
    )
    assert mock_result == avm_result == expected


@pytest.mark.parametrize(
    ("method_name", "expected_value"),
    [
        ("verify_app_params_get_approval_program", None),
        ("verify_app_params_get_clear_state_program", None),
        ("verify_app_params_get_global_num_uint", 0),
        ("verify_app_params_get_global_num_byte_slice", 0),
        ("verify_app_params_get_local_num_uint", 0),
        ("verify_app_params_get_local_num_byte_slice", 0),
        ("verify_app_params_get_extra_program_pages", 0),
        ("verify_app_params_get_creator", None),
        ("verify_app_params_get_address", None),
    ],
)
def test_app_params_get(
    algod_client: AlgodClient,
    get_state_app_params_avm_result: AVMInvoker,
    method_name: str,
    expected_value: int | bytes | bool | str | None,
) -> None:
    client = get_state_app_params_avm_result.client
    with algopy_testing_context() as ctx:
        app_id = client.app_id
        assert client.approval
        assert client.clear
        assert client.app_address
        app = ctx.any.application(
            id=app_id,
            approval_program=Bytes(client.approval.raw_binary),
            clear_state_program=Bytes(client.clear.raw_binary),
            global_num_uint=UInt64(0),
            global_num_bytes=UInt64(0),
            local_num_uint=UInt64(0),
            local_num_bytes=UInt64(0),
            extra_program_pages=UInt64(0),
            creator=algopy.Account(get_localnet_default_account(algod_client).address),
            address=algopy.Account(client.app_address),
        )

        contract = StateAppParamsContract()

        sp = algod_client.suggested_params()
        sp.fee = 1000
        sp.flat_fee = True

        avm_result = get_state_app_params_avm_result(method_name, a=app_id, suggested_params=sp)
        contract_method = getattr(contract, method_name)
        result = contract_method(app)

        # TODO: 1.0 add alternate tests for testing by index
        assert avm_result == result
        if expected_value is not None:
            assert avm_result == expected_value


@pytest.mark.parametrize(
    ("method_name", "expected_value"),
    [
        ("verify_acct_balance", INITIAL_BALANCE_MICRO_ALGOS + 100_000),
        ("verify_acct_min_balance", 100_000),
        ("verify_acct_auth_addr", algosdk.encoding.decode_address(algosdk.constants.ZERO_ADDRESS)),
        ("verify_acct_total_num_uint", 0),
        ("verify_acct_total_num_byte_slice", 0),
        ("verify_acct_total_extra_app_pages", 0),
        ("verify_acct_total_apps_created", 0),
        ("verify_acct_total_apps_opted_in", 0),
        ("verify_acct_total_assets_created", 0),
        ("verify_acct_total_assets", 0),
        ("verify_acct_total_boxes", 0),
        ("verify_acct_total_box_bytes", 0),
    ],
)
def test_acct_params_get(
    algod_client: AlgodClient,
    get_state_acct_params_avm_result: AVMInvoker,
    context: AlgopyTestContext,
    method_name: str,
    expected_value: int | bytes | bool | str | None,
) -> None:
    dummy_account = generate_test_account(algod_client)

    mock_account = context.any.account(
        balance=algopy.UInt64(100_100_000),
        min_balance=algopy.UInt64(100_000),
        auth_address=algopy.Account(algosdk.constants.ZERO_ADDRESS),
        total_num_uint=algopy.UInt64(0),
        total_num_byte_slice=algopy.UInt64(0),
        total_extra_app_pages=algopy.UInt64(0),
        total_apps_created=algopy.UInt64(0),
        total_apps_opted_in=algopy.UInt64(0),
        total_assets_created=algopy.UInt64(0),
        total_assets=algopy.UInt64(0),
        total_boxes=algopy.UInt64(0),
        total_box_bytes=algopy.UInt64(0),
    )

    sp = algod_client.suggested_params()
    sp.fee = 1000
    sp.flat_fee = True

    mock_contract = StateAcctParamsGetContract()

    avm_result = get_state_acct_params_avm_result(
        method_name, a=dummy_account.address, suggested_params=sp
    )

    mock_result = getattr(mock_contract, method_name)(mock_account)

    if method_name == "verify_acct_balance":
        assert mock_result == 100_100_000  # assert it returns the value set in test context
        mock_result = avm_result

    # TODO: 1.0 add alternate tests for testing by index
    assert mock_result == avm_result

    if expected_value is not None:
        assert mock_result == expected_value


@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    ("method_name", "key", "value", "expected"),
    [
        ("verify_put_bytes", b"local_bytes", b"test_bytes", b"test_bytes"),
        ("verify_put_uint64", b"local_uint64", 42, 42),
    ],
)
def test_app_local_put_get_and_delete(  # noqa: PLR0913
    localnet_creator: algopy_testing.Account,
    get_state_app_local_avm_result: AVMInvoker,
    method_name: str,
    key: bytes,
    value: bytes | int,
    expected: bytes | int,
) -> None:
    with contextlib.suppress(algosdk.error.AlgodHTTPError):
        get_state_app_local_avm_result.client.opt_in(
            "opt_in",
        )

    # Put operation
    get_state_app_local_avm_result(
        method_name,
        a=localnet_creator.public_key,
        b=key,
        c=value,
    )
    contract = StateAppLocalContract()
    getattr(contract, method_name)(
        a=localnet_creator,
        b=Bytes(key),
        c=Bytes(value) if isinstance(value, bytes) else UInt64(value),
    )

    # Get operation
    get_method = "verify_get_bytes" if isinstance(value, bytes) else "verify_get_uint64"
    avm_result = get_state_app_local_avm_result(
        get_method,
        a=localnet_creator.public_key,
        b=key,
    )
    mock_result = getattr(contract, get_method)(a=localnet_creator, b=Bytes(key))
    assert avm_result == mock_result == expected

    # Delete operation
    get_state_app_local_avm_result(
        "verify_delete",
        a=localnet_creator.public_key,
        b=key,
    )
    contract.verify_delete(a=localnet_creator, b=Bytes(key))

    # Verify deletion
    if method_name == "verify_put_bytes":
        with pytest.raises(LogicError):
            get_state_app_local_avm_result(
                get_method,
                a=localnet_creator.public_key,
                b=key,
            )
    else:
        assert (
            get_state_app_local_avm_result(
                get_method,
                a=localnet_creator.public_key,
                b=key,
            )
            == 0
        )
    assert getattr(contract, get_method)(a=localnet_creator, b=Bytes(key)) == 0


def test_app_local_ex_get(
    context: AlgopyTestContext,
    localnet_creator: algopy_testing.Account,
    get_state_app_local_avm_result: AVMInvoker,
    get_state_app_local_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppLocalExContract()
    mock_secondary_app = context.get_app_for_contract(mock_secondary_contract)
    assert mock_secondary_app.local_num_uint == 1
    assert mock_secondary_app.local_num_bytes == 2

    with contextlib.suppress(algosdk.error.AlgodHTTPError):
        get_state_app_local_ex_avm_result.client.opt_in("opt_in")
        get_state_app_local_avm_result.client.opt_in("opt_in")
    avm_result = get_state_app_local_avm_result(
        "verify_get_ex_bytes",
        a=localnet_creator.public_key,
        b=get_state_app_local_ex_avm_result.client.app_id,
        c=b"local_bytes",
    )
    contract = StateAppLocalContract()
    mock_secondary_contract.local_bytes[localnet_creator] = algopy.Bytes(
        b"dummy_bytes_from_external_contract"
    )
    mock_result = contract.verify_get_ex_bytes(
        a=localnet_creator, b=mock_secondary_app, c=algopy.Bytes(b"local_bytes")
    )
    assert avm_result == mock_result == b"dummy_bytes_from_external_contract"


def test_app_local_ex_get_arc4(
    context: AlgopyTestContext,
    localnet_creator: algopy_testing.Account,
    get_state_app_local_avm_result: AVMInvoker,
    get_state_app_local_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppLocalExContract()
    mock_secondary_app = context.get_app_for_contract(mock_secondary_contract)
    assert mock_secondary_app.local_num_uint == 1
    assert mock_secondary_app.local_num_bytes == 2

    with contextlib.suppress(algosdk.error.AlgodHTTPError):
        get_state_app_local_ex_avm_result.client.opt_in("opt_in")
        get_state_app_local_avm_result.client.opt_in("opt_in")
    avm_result = get_state_app_local_avm_result(
        "verify_get_ex_bytes",
        a=localnet_creator.public_key,
        b=get_state_app_local_ex_avm_result.client.app_id,
        c=b"local_arc4_bytes",
    )
    contract = StateAppLocalContract()
    mock_secondary_contract.local_arc4_bytes[localnet_creator] = algopy.arc4.DynamicBytes(
        b"dummy_arc4_bytes"
    )
    mock_result = contract.verify_get_ex_bytes(
        a=localnet_creator, b=mock_secondary_app, c=algopy.Bytes(b"local_arc4_bytes")
    )
    assert avm_result == mock_result == algopy.arc4.DynamicBytes(b"dummy_arc4_bytes").bytes


@pytest.mark.usefixtures("context")
@pytest.mark.parametrize(
    ("method_name", "key", "value", "expected"),
    [
        ("verify_put_bytes", b"global_bytes", b"test_bytes", b"test_bytes"),
        ("verify_put_uint64", b"global_uint64", 42, 42),
    ],
)
def test_app_global_put_get_and_delete(
    get_state_app_global_avm_result: AVMInvoker,
    method_name: str,
    key: bytes,
    value: bytes | int,
    expected: bytes | int,
) -> None:
    # Put operation
    get_state_app_global_avm_result(
        method_name,
        a=key,
        b=value,
    )
    contract = StateAppGlobalContract()
    getattr(contract, method_name)(
        a=Bytes(key),
        b=Bytes(value) if isinstance(value, bytes) else UInt64(value),
    )

    # Get operation
    get_method = "verify_get_bytes" if isinstance(value, bytes) else "verify_get_uint64"
    avm_result = get_state_app_global_avm_result(
        get_method,
        a=key,
    )
    mock_result = getattr(contract, get_method)(a=Bytes(key))
    assert avm_result == mock_result == expected

    # Delete operation
    get_state_app_global_avm_result(
        "verify_delete",
        a=key,
    )
    contract.verify_delete(a=Bytes(key))

    # Verify deletion
    if method_name == "verify_put_bytes":
        with pytest.raises(LogicError):
            get_state_app_global_avm_result(
                get_method,
                a=key,
            )
    else:
        assert (
            get_state_app_global_avm_result(
                get_method,
                a=key,
            )
            == 0
        )
    assert getattr(contract, get_method)(a=Bytes(key)) == 0


def test_app_global_ex_get(
    context: AlgopyTestContext,
    get_state_app_global_avm_result: AVMInvoker,
    get_state_app_global_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppGlobalExContract()
    mock_secondary_app = context.get_app_for_contract(mock_secondary_contract)
    assert mock_secondary_app.global_num_uint == 2
    assert mock_secondary_app.global_num_bytes == 4

    avm_result = get_state_app_global_avm_result(
        "verify_get_ex_bytes",
        a=get_state_app_global_ex_avm_result.client.app_id,
        b=b"global_bytes_explicit",
    )
    contract = StateAppGlobalContract()
    mock_result = contract.verify_get_ex_bytes(
        a=mock_secondary_app, b=algopy.Bytes(b"global_bytes_explicit")
    )
    assert avm_result[0] == list(mock_result[0].value)  # type: ignore[index]
    assert avm_result[1] == mock_result[1]  # type: ignore[index]


@pytest.mark.parametrize(
    ("key_name"),
    [
        b"global_arc4_bytes_explicit",
        b"global_arc4_bytes",
    ],
)
def test_app_global_ex_get_arc4(
    context: AlgopyTestContext,
    get_state_app_global_avm_result: AVMInvoker,
    get_state_app_global_ex_avm_result: AVMInvoker,
    key_name: str,
) -> None:
    mock_secondary_contract = StateAppGlobalExContract()
    mock_secondary_app = context.get_app_for_contract(mock_secondary_contract)
    assert mock_secondary_app.global_num_uint == 2
    assert mock_secondary_app.global_num_bytes == 4

    avm_result = get_state_app_global_avm_result(
        "verify_get_ex_bytes",
        a=get_state_app_global_ex_avm_result.client.app_id,
        b=key_name,
    )
    contract = StateAppGlobalContract()
    mock_result = contract.verify_get_ex_bytes(
        a=mock_secondary_app, b=algopy.Bytes(b"global_arc4_bytes_explicit")
    )
    assert avm_result[0] == list(mock_result[0].value)  # type: ignore[index]
    assert avm_result[1] == mock_result[1]  # type: ignore[index]


@pytest.mark.parametrize(
    ("index", "value"),
    [
        (0, algopy.Bytes(b"test_bytes")),
        (1, algopy.UInt64(42)),
        (2, b"test_bytes"),
        (3, 42),
        (255, algopy.Bytes(b"max_index")),  # Test maximum valid index
    ],
)
def test_scratch_slots(
    context: AlgopyTestContext, index: int, value: algopy.Bytes | algopy.UInt64 | bytes | int
) -> None:
    new_scratch_space: list[algopy.UInt64 | algopy.Bytes | int | bytes] = [0] * 256
    new_scratch_space[index] = value

    # Test set
    with context.txn.create_group(
        gtxns=[context.any.txn.application_call(scratch_space=new_scratch_space)]
    ):
        pass

    # Test get
    assert context.txn.last_group.get_scratch_slot(index) == convert_native_to_stack(value)

    # Test invalid index
    with pytest.raises(ValueError, match="invalid scratch slot"):
        context.txn.last_group.get_scratch_slot(256)


def test_itxn_ops(context: AlgopyTestContext) -> None:
    # arrange
    contract = ITxnOpsContract()

    # act (implicitly tests ITxn and GITxn as well)
    contract.verify_itxn_ops()

    # assert
    itxn_group = context.txn.last_group.get_itxn_group(0)
    appl_itxn = itxn_group.application_call(0)
    pay_itxn = itxn_group.payment(1)

    # TODO: 1.0 also test other array fields, apps, accounts, applications, assets
    assert appl_itxn.approval_program == algopy.Bytes.from_hex("068101068101")
    assert appl_itxn.clear_state_program == algopy.Bytes.from_hex("068101")
    approval_pages = [
        appl_itxn.approval_program_pages(i)
        for i in range(int(appl_itxn.num_approval_program_pages))
    ]
    assert approval_pages == [appl_itxn.approval_program]
    assert appl_itxn.on_completion == algopy.OnCompleteAction.DeleteApplication
    assert appl_itxn.fee == algopy.UInt64(algosdk.constants.MIN_TXN_FEE)

    assert pay_itxn.receiver == context.default_sender
    assert pay_itxn.amount == algopy.UInt64(1000)


# def test_
