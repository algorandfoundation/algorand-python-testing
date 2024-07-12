import math
import random
import secrets
import typing
from pathlib import Path

import algosdk
from algokit_utils import Account, ApplicationClient, get_localnet_default_account
from algosdk.v2client.algod import AlgodClient


class AVMInvoker:
    """Protocol used in global test fixtures to simplify invocation of AVM methods via an Algokit
    typed client."""

    def __init__(self, client: ApplicationClient):
        self.client = client

    def __call__(self, method: str, **kwargs: typing.Any) -> object:
        response = self.client.call(
            method,
            transaction_parameters={
                # random note avoids duplicate txn if tests are running concurrently
                "note": _random_note(),
                "suggested_params": kwargs.pop("suggested_params", None),
            },
            **kwargs,
        )
        if response.decode_error:
            raise ValueError(response.decode_error)
        result = response.return_value
        if result is None:
            return response.tx_info.get("logs", None)
        if isinstance(result, list) and all(
            isinstance(i, int) and i >= 0 and i <= 255 for i in result
        ):
            return bytes(result)
        return result


def _random_note() -> bytes:
    return secrets.token_bytes(8)


def create_avm_invoker(app_spec: Path, algod_client: AlgodClient) -> AVMInvoker:
    client = ApplicationClient(
        algod_client,
        app_spec,
        signer=get_localnet_default_account(algod_client),
    )

    client.create(
        transaction_parameters={
            # random note avoids duplicate txn if tests are running concurrently
            "note": _random_note(),
        }
    )

    return AVMInvoker(client)


def generate_test_asset(algod_client: AlgodClient, sender: Account, total: int | None) -> int:
    if total is None:
        total = math.floor(random.random() * 100) + 20  # noqa: S311

    decimals = 0
    asset_name = (
        f"ASA ${math.floor(random.random() * 100) + 1}_"  # noqa: S311
        f"${math.floor(random.random() * 100) + 1}_${total}"  # noqa: S311
    )

    params = algod_client.suggested_params()

    txn = algosdk.transaction.AssetConfigTxn(
        sender=sender.address,
        sp=params,
        total=total * 10**decimals,
        decimals=decimals,
        default_frozen=False,
        unit_name="",
        asset_name=asset_name,
        manager=sender.address,
        reserve=sender.address,
        freeze=sender.address,
        clawback=sender.address,
        url="https://algorand.co",
        metadata_hash=None,
        note=None,
        lease=None,
        rekey_to=None,
    )  # type: ignore[no-untyped-call, unused-ignore]

    signed_transaction = txn.sign(sender.private_key)  # type: ignore[no-untyped-call, unused-ignore]
    algod_client.send_transaction(signed_transaction)
    ptx = algod_client.pending_transaction_info(txn.get_txid())  # type: ignore[no-untyped-call, unused-ignore]

    if isinstance(ptx, dict) and "asset-index" in ptx and isinstance(ptx["asset-index"], int):
        return ptx["asset-index"]
    else:
        raise ValueError("Unexpected response from pending_transaction_info")
