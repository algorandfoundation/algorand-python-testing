import math
import random
import secrets
import typing
from pathlib import Path

import algosdk
from algokit_utils import (
    Account,
    ApplicationClient,
    EnsureBalanceParameters,
    ensure_funded,
    get_localnet_default_account,
)
from algosdk.v2client.algod import AlgodClient

INITIAL_BALANCE_MICRO_ALGOS = int(20e6)


class AVMInvoker:
    """Protocol used in global test fixtures to simplify invocation of AVM methods via an Algokit
    typed client."""

    def __init__(self, client: ApplicationClient):
        self.client = client

    def __call__(
        self,
        method: str,
        on_complete: algosdk.transaction.OnComplete = algosdk.transaction.OnComplete.NoOpOC,
        **kwargs: typing.Any,
    ) -> object:
        response = self.client.call(
            method,
            transaction_parameters={
                # random note avoids duplicate txn if tests are running concurrently
                "note": _random_note(),
                "accounts": kwargs.pop("accounts", None),
                "foreign_apps": kwargs.pop("foreign_apps", None),
                "foreign_assets": kwargs.pop("foreign_assets", None),
                "suggested_params": kwargs.pop("suggested_params", None),
                "on_complete": on_complete,
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


def generate_test_asset(  # noqa: PLR0913
    *,
    algod_client: AlgodClient,
    sender: Account,
    total: int | None = None,
    decimals: int = 0,
    default_frozen: bool = False,
    unit_name: str = "",
    asset_name: str | None = None,
    manager: str | None = None,
    reserve: str | None = None,
    freeze: str | None = None,
    clawback: str | None = None,
    url: str = "https://algorand.co",
    metadata_hash: bytes | None = None,
    note: bytes | None = None,
    lease: bytes | None = None,
    rekey_to: str | None = None,
) -> int:
    if total is None:
        total = math.floor(random.random() * 100) + 20

    if asset_name is None:
        asset_name = (
            f"ASA ${math.floor(random.random() * 100) + 1}_"
            f"${math.floor(random.random() * 100) + 1}_${total}"
        )

    params = algod_client.suggested_params()

    txn = algosdk.transaction.AssetConfigTxn(
        sender=sender.address,
        sp=params,
        total=total * 10**decimals,
        decimals=decimals,
        default_frozen=default_frozen,
        unit_name=unit_name,
        asset_name=asset_name,
        manager=manager,
        reserve=reserve,
        freeze=freeze,
        clawback=clawback,
        url=url,
        metadata_hash=metadata_hash,
        note=note or _random_note(),
        lease=lease,
        strict_empty_address_check=False,
        rekey_to=rekey_to,
    )  # type: ignore[no-untyped-call, unused-ignore]

    signed_transaction = txn.sign(sender.private_key)  # type: ignore[no-untyped-call, unused-ignore]
    algod_client.send_transaction(signed_transaction)
    ptx = algod_client.pending_transaction_info(txn.get_txid())  # type: ignore[no-untyped-call, unused-ignore]

    if isinstance(ptx, dict) and "asset-index" in ptx and isinstance(ptx["asset-index"], int):
        return ptx["asset-index"]
    else:
        raise ValueError("Unexpected response from pending_transaction_info")


def generate_test_account(algod_client: AlgodClient) -> Account:
    raw_account = algosdk.account.generate_account()
    account = Account(private_key=raw_account[0], address=raw_account[1])

    ensure_funded(
        algod_client,
        EnsureBalanceParameters(
            account_to_fund=account,
            min_spending_balance_micro_algos=INITIAL_BALANCE_MICRO_ALGOS,
        ),
    )

    return account
