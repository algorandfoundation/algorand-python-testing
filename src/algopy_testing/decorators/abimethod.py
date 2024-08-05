from __future__ import annotations

import dataclasses
import functools
import typing

import algosdk

import algopy_testing
from algopy_testing.constants import ALWAYS_APPROVE_TEAL_PROGRAM
from algopy_testing.models.txn_fields import ApplicationCallFields
from algopy_testing.utils import (
    abi_return_type_annotation_for_arg,
    abi_type_name_for_arg,
)

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    import algopy


_P = typing.ParamSpec("_P")
_R = typing.TypeVar("_R")


@typing.overload
def abimethod(fn: typing.Callable[_P, _R], /) -> typing.Callable[_P, _R]: ...


@typing.overload
def abimethod(
    *,
    name: str | None = None,
    create: typing.Literal["allow", "require", "disallow"] = "disallow",
    allow_actions: typing.Sequence[
        algopy.OnCompleteAction
        | typing.Literal[
            "NoOp",
            "OptIn",
            "CloseOut",
            # ClearState has its own program, so is not considered as part of ARC4 routing
            "UpdateApplication",
            "DeleteApplication",
        ]
    ] = ("NoOp",),
    readonly: bool = False,
    default_args: typing.Mapping[str, str | object] = {},
) -> typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]]: ...


def abimethod(  # noqa: PLR0913
    fn: typing.Callable[_P, _R] | None = None,
    *,
    name: str | None = None,
    create: typing.Literal["allow", "require", "disallow"] = "disallow",
    allow_actions: typing.Sequence[
        algopy.OnCompleteAction
        | typing.Literal[
            "NoOp",
            "OptIn",
            "CloseOut",
            "UpdateApplication",
            "DeleteApplication",
        ]
    ] = ("NoOp",),
    readonly: bool = False,
    default_args: typing.Mapping[str, str | object] | None = None,
) -> typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]] | typing.Callable[_P, _R]:
    # TODO: ARC4 signature should be derived here
    #       then possibly store on the context, or fn itself?
    if fn is None:
        return functools.partial(
            abimethod,
            name=name,
            create=create,
            allow_actions=allow_actions,
            readonly=readonly,
            default_args=default_args,
        )

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        context = algopy_testing.get_test_context()
        if context._active_transaction_index is not None:
            return fn(*args, **kwargs)

        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract)
        # TODO: order kwargs correctly based on fn signature
        ordered_args = [*app_args, *kwargs.values()]
        _extract_and_append_txn_to_context(
            context,
            contract=contract,
            name=name or fn.__name__,
            fn=fn,
            args=ordered_args,
        )
        context.set_active_contract(contract)
        return fn(*args, **kwargs)

    return wrapper


def _extract_and_append_txn_to_context(
    context: algopy_testing.AlgopyTestContext,
    contract: algopy_testing.Contract,
    name: str,
    fn: typing.Callable[_P, _R],
    args: Sequence[object],
) -> None:
    method_selector = _generate_arc4_signature(fn, name, args)
    txn_fields = context._active_txn_fields.copy()

    app = txn_fields.get("app_id", context.get_application_for_contract(contract))
    txn_arrays = _extract_arrays_from_args(
        args,
        method_selector=method_selector,
        sender=context.default_creator,
        app=app,
    )

    txn_fields.setdefault("sender", context.default_creator)
    txn_fields.setdefault("app_id", app)
    txn_fields.setdefault("accounts", txn_arrays.accounts)
    txn_fields.setdefault("assets", txn_arrays.assets)
    txn_fields.setdefault("apps", txn_arrays.apps)
    txn_fields.setdefault("app_args", txn_arrays.app_args)
    # at some point could get the actual values by using puya to compile the contract
    # this should be opt-in behaviour, as that it would be too slow to always do
    txn_fields.setdefault(
        "approval_program_pages", [algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )
    txn_fields.setdefault(
        "clear_state_program_pages", [algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )

    app_txn = context.any_application_call_transaction(
        **typing.cast(ApplicationCallFields, txn_fields)
    )

    context.add_transactions([*txn_arrays.txns, app_txn])
    new_active_txn_index = len(context.get_transaction_group()) - 1
    context.set_active_transaction_index(new_active_txn_index)


@dataclasses.dataclass
class _TxnArrays:
    txns: list[algopy.gtxn.TransactionBase]
    apps: list[algopy.Application]
    assets: list[algopy.Asset]
    accounts: list[algopy.Account]
    app_args: list[algopy.Bytes]


def _extract_arrays_from_args(
    args: Sequence[object],
    method_selector: algopy.Bytes,
    app: algopy.Application,
    sender: algopy.Account,
) -> _TxnArrays:
    txns = list[algopy_testing.gtxn.TransactionBase]()
    apps = [app]
    assets = list[algopy_testing.Asset]()
    accounts = [sender]
    app_args = [method_selector]
    for arg in args:
        match arg:
            case algopy_testing.gtxn.TransactionBase() as txn:
                txns.append(txn)
            case algopy_testing.Account() as acc:
                app_args.append(algopy_testing.arc4.UInt8(len(accounts)).bytes)
                accounts.append(acc)
            case algopy_testing.Asset() as asset:
                app_args.append(algopy_testing.arc4.UInt8(len(assets)).bytes)
                assets.append(asset)
            case algopy_testing.Application() as arg_app:
                app_args.append(algopy_testing.arc4.UInt8(len(apps)).bytes)
                apps.append(arg_app)
            case (algopy_testing.UInt64() | bool()) as uint64:
                app_args.append(algopy_testing.op.itob(uint64))
            case tuple():
                # TODO: convert to ARC4 tuple
                raise NotImplementedError
            case _ as bytes_arg:
                if hasattr(bytes_arg, "bytes"):
                    bytes_arg = bytes_arg.bytes
                if isinstance(bytes_arg, algopy_testing.Bytes):
                    app_args.append(bytes_arg)
                else:
                    raise TypeError(f"unsupported type: {type(bytes_arg).__name__}")
    if len(app_args) > 16:
        # TODO: pack extra args into an ARC4 tuple
        raise NotImplementedError
    return _TxnArrays(
        txns=txns,
        apps=apps,
        assets=assets,
        accounts=accounts,
        app_args=app_args,
    )


def _generate_arc4_signature(
    fn: typing.Callable[_P, _R], name: str, args: Sequence[object]
) -> algopy.Bytes:
    import algopy

    arg_types = [algosdk.abi.Argument(abi_type_name_for_arg(arg=arg)) for arg in args]
    return_type = algosdk.abi.Returns(
        abi_return_type_annotation_for_arg(fn.__annotations__.get("return"))
    )
    method = algosdk.abi.Method(name=name, args=arg_types, returns=return_type)
    return algopy.Bytes(method.get_selector())
