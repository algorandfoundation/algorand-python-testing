import math
import random
import secrets
import typing
from pathlib import Path

import algosdk
from algokit_utils import (
    AlgorandClient,
    AppClient,
    AppClientMethodCallParams,
    AppFactory,
    AppFactoryCreateMethodCallParams,
    AppFactoryCreateParams,
    AppFactoryParams,
    SigningAccount,
)
from algosdk.v2client.algod import AlgodClient

INITIAL_BALANCE_MICRO_ALGOS = int(20e6)


class AVMInvoker:
    """Protocol used in global test fixtures to simplify invocation of AVM methods via an Algokit
    typed client."""

    def __init__(self, client: AppClient, factory: AppFactory):
        self.client = client
        self.factory = factory

    def __call__(
        self,
        method: str,
        on_complete: algosdk.transaction.OnComplete = algosdk.transaction.OnComplete.NoOpOC,
        *,
        return_raw: bool = False,
        **kwargs: typing.Any,
    ) -> object:
        response = self.client.send.call(
            AppClientMethodCallParams(
                method=method,
                note=_random_note(),
                account_references=kwargs.pop("accounts", None),
                app_references=kwargs.pop("foreign_apps", None),
                asset_references=kwargs.pop("foreign_assets", None),
                on_complete=on_complete,
                static_fee=kwargs.pop("static_fee", None),
                args=[item[1] for item in kwargs.items()],
            ),
        )
        if response.returns and len(response.returns) > 0 and response.returns[0].decode_error:
            raise ValueError(response.returns[0].decode_error)
        if return_raw and response.returns and len(response.returns) > 0:
            return response.returns[0].raw_value
        result = response.abi_return
        if result is None and response.returns and len(response.returns) > 0:
            assert response.returns[0].tx_info
            return response.returns[0].tx_info.get("logs", None)
        if isinstance(result, list) and all(
            isinstance(i, int) and i >= 0 and i <= 255 for i in result
        ):
            return bytes(result)  # type: ignore[arg-type]
        return result


def _random_note() -> bytes:
    return secrets.token_bytes(8)


def create_avm_invoker(app_spec: Path, algorand: AlgorandClient) -> AVMInvoker:
    dispenser = algorand.account.localnet_dispenser()
    factory = AppFactory(
        AppFactoryParams(
            algorand=algorand,
            app_spec=app_spec.read_text(),
            default_sender=dispenser.address,
        ),
    )
    try:
        client, _ = factory.send.bare.create(
            AppFactoryCreateParams(note=_random_note()),
        )
    except Exception as __:
        client, _ = factory.send.create(
            AppFactoryCreateMethodCallParams(method="create", note=_random_note()),
        )

    return AVMInvoker(client, factory)


def generate_test_asset(  # noqa: PLR0913
    *,
    algod_client: AlgodClient,
    sender: SigningAccount,
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
