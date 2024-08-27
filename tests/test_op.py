import contextlib
import typing
from pathlib import Path

import _algopy_testing
import algopy
import algosdk
import coincurve
import ecdsa  # type: ignore  # noqa: PGH003
import ecdsa.util  # type: ignore  # noqa: PGH003
import nacl.signing
import pytest
from algokit_utils import LogicError, get_localnet_default_account
from algopy import op
from algopy_testing import AlgopyTestContext, algopy_testing_context, arc4_prefix
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
        "data": algopy.Bytes(message_hash),
        "r": algopy.Bytes(r.to_bytes(32, byteorder="big")),
        "s": algopy.Bytes(s.to_bytes(32, byteorder="big")),
        "recovery_id": algopy.UInt64(recovery_id),
        "pubkey_x": algopy.Bytes(vk.to_string()[:32]),
        "pubkey_y": algopy.Bytes(vk.to_string()[32:]),
    }


@pytest.fixture()
def context() -> typing.Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


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
def get_state_app_local_avm_opted_in(algod_client: AlgodClient) -> AVMInvoker:
    invoker = create_avm_invoker(STATE_OPS_APP_LOCAL_SPEC, algod_client)
    invoker.client.opt_in()
    return invoker


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

    def run_real_vrf_verify() -> tuple[algopy.Bytes, bool]:
        sp = algod_client.suggested_params()
        sp.fee = 6000
        result: tuple[list[int], bool] = get_crypto_ops_avm_result(  # type: ignore[assignment]
            "verify_vrf_verify", a=a, b=b, c=c, suggested_params=sp
        )

        return (algopy.Bytes(bytes(result[0])), result[1])

    def run_mocked_vrf_verify() -> tuple[algopy.Bytes, bool]:
        return op.vrf_verify(op.VrfVerify.VrfAlgorand, a, b, c)

    avm_result = run_real_vrf_verify()
    mocker.patch("algopy.op.vrf_verify", return_value=(avm_result[0], True))
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
        ("verify_asset_params_get_creator", "creator"),
    ],
)
def test_asset_params_get(
    algod_client: AlgodClient,
    get_state_asset_params_avm_result: AVMInvoker,
    context: AlgopyTestContext,
    method_name: str,
    expected_value: object,
) -> None:
    dummy_account = get_localnet_default_account(algod_client)
    creator = dummy_account.address
    metadata_hash = b"test" + b" " * 28

    mock_asset = context.any.asset(
        total=algopy.UInt64(100),
        decimals=algopy.UInt64(0),
        name=algopy.Bytes(b"TEST"),
        unit_name=algopy.Bytes(b"UNIT"),
        url=algopy.Bytes(b"https://algorand.co"),
        metadata_hash=algopy.Bytes(metadata_hash),
        creator=algopy.Account(creator),
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

    if isinstance(expected_value, str):
        expected_value = algopy.Account(creator if expected_value == "creator" else expected_value)
    assert mock_result == avm_result == expected_value


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
        ("verify_app_params_get_creator", "app.creator"),
        ("verify_app_params_get_address", "app.address"),
    ],
)
def test_app_params_get(
    algod_client: AlgodClient,
    get_state_app_params_avm_result: AVMInvoker,
    method_name: str,
    expected_value: object,
) -> None:
    client = get_state_app_params_avm_result.client
    with algopy_testing_context() as ctx:
        app_id = client.app_id
        assert client.approval
        assert client.clear
        assert client.app_address
        app = ctx.any.application(
            id=app_id,
            approval_program=algopy.Bytes(client.approval.raw_binary),
            clear_state_program=algopy.Bytes(client.clear.raw_binary),
            global_num_uint=algopy.UInt64(0),
            global_num_bytes=algopy.UInt64(0),
            local_num_uint=algopy.UInt64(0),
            local_num_bytes=algopy.UInt64(0),
            extra_program_pages=algopy.UInt64(0),
            creator=algopy.Account(get_localnet_default_account(algod_client).address),
        )

        contract = StateAppParamsContract()

        sp = algod_client.suggested_params()
        sp.fee = 1000
        sp.flat_fee = True

        avm_result = get_state_app_params_avm_result(method_name, a=app_id, suggested_params=sp)
        contract_method = getattr(contract, method_name)
        result = contract_method(app)

        assert avm_result == result
        if expected_value == "app.creator":
            expected_value = app.creator
        elif expected_value == "app.address":
            expected_value = app.address
        if expected_value is not None:
            assert avm_result == expected_value


@pytest.mark.parametrize(
    ("method_name", "expected_value"),
    [
        ("verify_acct_balance", INITIAL_BALANCE_MICRO_ALGOS + 100_000),
        ("verify_acct_min_balance", 100_000),
        ("verify_acct_auth_addr", algosdk.constants.ZERO_ADDRESS),
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
    expected_value: object,
) -> None:
    dummy_account = generate_test_account(algod_client)

    mock_account = context.any.account(
        address=dummy_account.address,
        balance=algopy.UInt64(INITIAL_BALANCE_MICRO_ALGOS + 100_000),
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
    with context.txn.create_group(
        active_txn_overrides={"fee": algopy.UInt64(1000), "sender": mock_account}
    ):
        mock_result = getattr(mock_contract, method_name)(mock_account)

    if isinstance(expected_value, str):
        expected_value = algopy.Account(expected_value)
    assert mock_result == avm_result == expected_value


@pytest.mark.parametrize(
    ("key", "value"),
    [
        (b"local_bytes", b"test_bytes"),
        (b"local_uint64", 42),
    ],
)
def test_app_local_put_get_and_delete(
    context: AlgopyTestContext,
    localnet_creator: _algopy_testing.Account,
    get_state_app_local_avm_opted_in: AVMInvoker,
    key: bytes,
    value: bytes | int,
) -> None:
    assert context
    type_suffix = "bytes" if isinstance(value, bytes) else "uint64"
    put_method_name = f"verify_put_{type_suffix}"
    get_method_name = f"verify_get_{type_suffix}"

    # Put operation
    get_state_app_local_avm_opted_in(
        put_method_name,
        a=localnet_creator.public_key,
        b=key,
        c=value,
    )
    contract = StateAppLocalContract()
    getattr(contract, put_method_name)(
        a=localnet_creator,
        b=algopy.Bytes(key),
        c=algopy.Bytes(value) if isinstance(value, bytes) else algopy.UInt64(value),
    )

    # Get operation
    avm_result = get_state_app_local_avm_opted_in(
        get_method_name,
        a=localnet_creator.public_key,
        b=key,
    )
    mock_result = getattr(contract, get_method_name)(a=localnet_creator, b=algopy.Bytes(key))
    assert avm_result == mock_result == value

    # Delete operation
    get_state_app_local_avm_opted_in(
        "verify_delete",
        a=localnet_creator.public_key,
        b=key,
    )
    contract.verify_delete(a=localnet_creator, b=algopy.Bytes(key))

    # Verify deletion
    avm_result = get_state_app_local_avm_opted_in(
        "verify_exists", a=localnet_creator.public_key, b=key
    )
    mock_result = contract.verify_exists(a=localnet_creator, b=algopy.Bytes(key))
    assert avm_result == mock_result, "verify_exists does not match"


def test_app_local_ex_get(
    context: AlgopyTestContext,
    localnet_creator: _algopy_testing.Account,
    get_state_app_local_avm_result: AVMInvoker,
    get_state_app_local_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppLocalExContract()
    mock_secondary_app = context.ledger.get_app(mock_secondary_contract)
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
    localnet_creator: _algopy_testing.Account,
    get_state_app_local_avm_result: AVMInvoker,
    get_state_app_local_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppLocalExContract()
    mock_secondary_app = context.ledger.get_app(mock_secondary_contract)
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
        a=algopy.Bytes(key),
        b=algopy.Bytes(value) if isinstance(value, bytes) else algopy.UInt64(value),
    )

    # Get operation
    get_method = "verify_get_bytes" if isinstance(value, bytes) else "verify_get_uint64"
    avm_result = get_state_app_global_avm_result(
        get_method,
        a=key,
    )
    mock_result = getattr(contract, get_method)(a=algopy.Bytes(key))
    assert avm_result == mock_result == expected

    # Delete operation
    get_state_app_global_avm_result(
        "verify_delete",
        a=key,
    )
    contract.verify_delete(a=algopy.Bytes(key))

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
    assert getattr(contract, get_method)(a=algopy.Bytes(key)) == 0


def test_app_global_ex_get(
    context: AlgopyTestContext,
    get_state_app_global_avm_result: AVMInvoker,
    get_state_app_global_ex_avm_result: AVMInvoker,
) -> None:
    mock_secondary_contract = StateAppGlobalExContract()
    mock_secondary_app = context.ledger.get_app(mock_secondary_contract)
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
    mock_secondary_app = context.ledger.get_app(mock_secondary_contract)
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
    assert context.txn.last_group.get_scratch_slot(index) == value

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

    # Test application call transaction fields
    assert appl_itxn.approval_program == algopy.Bytes.from_hex("068101068101")
    assert appl_itxn.clear_state_program == algopy.Bytes.from_hex("068101")
    approval_pages = [
        appl_itxn.approval_program_pages(i)
        for i in range(int(appl_itxn.num_approval_program_pages))
    ]
    assert approval_pages == [appl_itxn.approval_program]
    assert appl_itxn.on_completion == algopy.OnCompleteAction.DeleteApplication
    assert appl_itxn.fee == algopy.UInt64(algosdk.constants.MIN_TXN_FEE)
    assert appl_itxn.sender == context.ledger.get_app(contract).address
    # NOTE: would implementing emulation for this behavior be useful
    # in unit testing context (vs integration tests)?
    # considering we don't emulate balance (transfer, accounting for fees and etc)
    assert appl_itxn.app_id == 0
    assert appl_itxn.type == algopy.TransactionType.ApplicationCall
    assert appl_itxn.type_bytes == algopy.Bytes(b"appl")

    # Test payment transaction fields
    assert pay_itxn.receiver == context.default_sender
    assert pay_itxn.amount == algopy.UInt64(1000)
    assert pay_itxn.sender == context.ledger.get_app(contract).address
    assert pay_itxn.type == algopy.TransactionType.Payment
    assert pay_itxn.type_bytes == algopy.Bytes(b"pay")

    # Test common fields for both transactions
    for itxn in [appl_itxn, pay_itxn]:
        assert isinstance(itxn.sender, algopy.Account)
        assert isinstance(itxn.fee, algopy.UInt64)
        assert isinstance(itxn.first_valid, algopy.UInt64)
        assert isinstance(itxn.last_valid, algopy.UInt64)
        assert isinstance(itxn.note, algopy.Bytes)
        assert isinstance(itxn.lease, algopy.Bytes)
        assert isinstance(itxn.txn_id, algopy.Bytes)

    # Test logs (should be empty for newly created transactions as its a void method)
    assert context.txn.last_active.num_logs == algopy.UInt64(0)
    assert context.txn.last_active.last_log == algopy.Bytes(b"")

    # Test created_app and created_asset (should be created for these transactions)
    assert hasattr(appl_itxn, "created_app")
    assert hasattr(pay_itxn, "created_asset")


def test_blk_seed_existing_block(context: AlgopyTestContext) -> None:
    block_index = 42
    block_seed = 123
    context.ledger.set_block(block_index, block_seed, 1234567890)
    result = op.Block.blk_seed(algopy.UInt64(block_index))
    assert op.btoi(result) == block_seed


@pytest.mark.usefixtures("context")
def test_blk_seed_missing_block() -> None:
    block_index = 42
    with pytest.raises(KeyError, match=f"Block {block_index}*"):
        op.Block.blk_seed(algopy.UInt64(block_index))


def test_blk_timestamp_existing_block(context: AlgopyTestContext) -> None:
    block_index = 42
    block_timestamp = 1234567890
    context.ledger.set_block(block_index, 123, block_timestamp)
    result = op.Block.blk_timestamp(algopy.UInt64(block_index))
    assert result == algopy.UInt64(block_timestamp)


@pytest.mark.usefixtures("context")
def test_blk_timestamp_missing_block() -> None:
    block_index = 42
    with pytest.raises(KeyError, match=f"Block {block_index}*"):
        op.Block.blk_timestamp(algopy.UInt64(block_index))


def test_gaid(context: AlgopyTestContext) -> None:
    from tests.artifacts.CreatedAppAsset.contract import AppExpectingEffects

    # arrange
    created_asset = context.any.asset()
    created_app = context.any.application()
    asset_create_txn = context.any.txn.asset_config(created_asset=created_asset)
    app_create_txn = context.any.txn.application_call(created_app=created_app)

    contract = AppExpectingEffects()

    # act
    asset_id, app_id = contract.create_group(asset_create_txn, app_create_txn)

    # assert
    assert asset_id == created_asset.id
    assert app_id == created_app.id

    # arrange
    app_call_txn = context.any.txn.application_call(
        app_args=[algopy.arc4.arc4_signature("some_value()uint64")],
        logs=[arc4_prefix(algopy.arc4.UInt64(2).bytes)],
    )

    # act
    contract.log_group(app_call_txn)


@pytest.mark.usefixtures("context")
def test_contains() -> None:
    from tests.artifacts.Contains.contract import MyContract

    contract = MyContract()

    contract.approval_program()


def test_globals(context: AlgopyTestContext) -> None:
    creator = context.any.account()
    app = context.any.application(creator=creator)
    txn1 = context.any.txn.application_call(app_id=app)
    with context.txn.create_group(gtxns=[txn1]):
        first_group_id = algopy.Global.group_id
        first_timestamp = algopy.Global.latest_timestamp
        assert first_group_id.length == 32
        assert first_timestamp != 0
        assert algopy.Global.group_size == 1
        assert algopy.Global.round == 1
        assert algopy.Global.caller_application_id == 0
        assert algopy.Global.creator_address == creator
        assert algopy.Global.current_application_id == app
        assert algopy.Global.current_application_address == app.address

    txn2 = context.any.txn.payment()
    txn3 = context.any.txn.application_call()
    caller = context.any.application()
    context.ledger.patch_global_fields(caller_application_id=caller.id)
    with context.txn.create_group(gtxns=[txn2, txn3]):
        second_group_id = algopy.Global.group_id
        second_timestamp = algopy.Global.latest_timestamp
        assert second_group_id.length == 32
        assert algopy.Global.group_size == 2
        assert algopy.Global.round == 2
        assert algopy.Global.caller_application_id == caller.id
        assert algopy.Global.caller_application_address == caller.address

    assert first_group_id != second_group_id, "expected unique group ids"
    assert first_timestamp <= second_timestamp, "expected unique group ids"
