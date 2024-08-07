from __future__ import annotations

import dataclasses
import functools
import typing

import algosdk

import algopy_testing
from algopy_testing._context_storage import get_app_data, get_test_context
from algopy_testing.constants import ALWAYS_APPROVE_TEAL_PROGRAM
from algopy_testing.primitives import Bytes
from algopy_testing.utils import (
    abi_return_type_annotation_for_arg,
    abi_type_name_for_arg,
)

_P = typing.ParamSpec("_P")
_R = typing.TypeVar("_R")

if typing.TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    import algopy

    _AllowActions = (
        algopy.OnCompleteAction
        | typing.Literal[
            "NoOp",
            "OptIn",
            "CloseOut",
            # ClearState has its own program, so is not considered as part of ARC4 routing
            "UpdateApplication",
            "DeleteApplication",
        ]
    )
_CreateValues = typing.Literal["allow", "require", "disallow"]


def check_create(contract: algopy.Contract, create: _CreateValues) -> None:
    app_data = get_app_data(contract)

    is_creating = app_data.is_creating
    if is_creating and create == "disallow":
        raise RuntimeError("method can not be called while creating")
    if not is_creating and create == "require":
        raise RuntimeError("method can only be called while creating")


def check_oca(actions: Sequence[_AllowActions]) -> None:
    context = get_test_context()
    txn = context.get_active_transaction()
    allowed_actions = [action if isinstance(action, str) else action.name for action in actions]
    if txn.on_completion.name not in allowed_actions:
        raise RuntimeError(
            "method can only be called with one of the following"
            f" on_completion values: {', '.join(allowed_actions)}"
        )


@typing.overload
def abimethod(fn: typing.Callable[_P, _R], /) -> typing.Callable[_P, _R]: ...


@typing.overload
def abimethod(
    *,
    name: str | None = None,
    create: _CreateValues = "disallow",
    allow_actions: Sequence[_AllowActions] = ("NoOp",),
    readonly: bool = False,
    default_args: Mapping[str, str | object] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def abimethod(  # noqa: PLR0913
    fn: Callable[_P, _R] | None = None,
    *,
    name: str | None = None,
    create: _CreateValues = "disallow",
    allow_actions: Sequence[_AllowActions] = ("NoOp",),
    readonly: bool = False,
    default_args: Mapping[str, str | object] | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]] | Callable[_P, _R]:
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

    fn.is_create = create != "disallow"  # type: ignore[attr-defined]

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract)

        context = get_test_context()
        context.set_active_contract(contract)
        # TODO: handle custom txn groups
        # TODO: order kwargs correctly based on fn signature
        ordered_args = [*app_args, *kwargs.values()]
        arc4_name = name or fn.__name__
        arc4_signature = _generate_arc4_signature_from_args(fn, arc4_name, ordered_args)
        txns = _extract_group_txns(
            context,
            contract=contract,
            arc4_signature=arc4_signature,
            args=ordered_args,
        )
        context.set_transaction_group(txns)

        check_create(contract, create)
        check_oca(allow_actions)
        try:
            result = fn(*args, **kwargs)
        finally:
            context.clear_active_contract()
        return result

    return wrapper


def _extract_group_txns(
    context: algopy_testing.AlgopyTestContext,
    contract: algopy_testing.Contract,
    arc4_signature: str,
    args: Sequence[object],
) -> list[algopy.gtxn.TransactionBase]:
    method = algosdk.abi.Method.from_signature(arc4_signature)
    method_selector = Bytes(method.get_selector())
    txn_fields = context._active_txn_fields.copy()

    app = txn_fields.get("app_id", context.get_application_for_contract(contract))
    txn_arrays = _extract_arrays_from_args(
        args,
        method_selector=method_selector,
        sender=context.default_sender,
        app=app,
    )

    txn_fields.setdefault("sender", context.default_sender)
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

    app_txn = context.any_application_call_transaction(**txn_fields)
    return [*txn_arrays.txns, app_txn]


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


def _generate_arc4_signature_from_fn(fn: typing.Callable[_P, _R], arc4_name: str) -> str:
    annotations = fn.__annotations__.copy()
    returns = algosdk.abi.Returns(_annotation_to_arc4(annotations.pop("return")))
    method = algosdk.abi.Method(
        name=arc4_name,
        args=[algosdk.abi.Argument(_annotation_to_arc4(a)) for a in annotations.values()],
        returns=returns,
    )
    return method.get_signature()


def _annotation_to_arc4(_annotation: object) -> str:
    # TODO: use ARC4 type to get arc4_name
    raise NotImplementedError


def _generate_arc4_signature_from_args(
    fn: typing.Callable[_P, _R], arc4_name: str, args: Sequence[object]
) -> str:

    arg_types = [algosdk.abi.Argument(abi_type_name_for_arg(arg=arg)) for arg in args]
    return_type = algosdk.abi.Returns(
        abi_return_type_annotation_for_arg(fn.__annotations__.get("return"))
    )
    method = algosdk.abi.Method(name=arc4_name, args=arg_types, returns=return_type)
    return method.get_signature()


@typing.overload
def baremethod(fn: typing.Callable[_P, _R], /) -> typing.Callable[_P, _R]: ...


@typing.overload
def baremethod(
    *,
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
) -> typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]]: ...


def baremethod(
    fn: typing.Callable[_P, _R] | None = None,
    *,
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
) -> typing.Callable[[typing.Callable[_P, _R]], typing.Callable[_P, _R]] | typing.Callable[_P, _R]:
    if fn is None:
        return functools.partial(
            baremethod,
            create=create,
            allow_actions=allow_actions,
        )

    fn.is_create = create != "disallow"  # type: ignore[attr-defined]

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract)

        context = get_test_context()
        context.set_active_contract(contract)
        # TODO: handle custom txn groups
        txns = [
            context.any_application_call_transaction(
                # TODO: fill out other fields where possible (see abimethod)
                sender=context.default_sender,
                app_id=context.get_active_application(),
            ),
        ]

        context.set_transaction_group(txns)

        check_create(contract, create)
        check_oca(allow_actions)
        try:
            result = fn(*args, **kwargs)
        finally:
            context.clear_active_contract()
        return result

    return wrapper
