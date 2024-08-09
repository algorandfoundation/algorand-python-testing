from __future__ import annotations

import dataclasses
import functools
import types
import typing

import algosdk

import algopy_testing
from algopy_testing._context_helpers import lazy_context
from algopy_testing.constants import ALWAYS_APPROVE_TEAL_PROGRAM
from algopy_testing.primitives import BigUInt, Bytes, String, UInt64

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
    app_data = lazy_context.get_app_data(contract)

    is_creating = app_data.is_creating
    if is_creating and create == "disallow":
        raise RuntimeError("method can not be called while creating")
    if not is_creating and create == "require":
        raise RuntimeError("method can only be called while creating")


def check_oca(actions: Sequence[_AllowActions]) -> None:
    txn = lazy_context.active_group.active_txn
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

    arc4_name = name or fn.__name__
    fn.is_create = create != "disallow"  # type: ignore[attr-defined]
    arc4_signature = _generate_arc4_signature_from_fn(fn, arc4_name)

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"

        context = lazy_context.value
        # TODO: does contract need to be active here?
        # TODO: handle custom txn groups
        # TODO: order kwargs correctly based on fn signature
        ordered_args = [*app_args, *kwargs.values()]
        txns = _extract_group_txns(
            context,
            contract=contract,
            arc4_signature=arc4_signature,
            args=ordered_args,
        )
        with context.txn._maybe_implicit_txn_group(txns):
            check_create(contract, create)
            check_oca(allow_actions)
            result = fn(*args, **kwargs)
            # TODO: add result along with ARC4 log prefix to application logs?
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
    txn_fields = lazy_context.get_active_txn_fields()

    contract_app = context.ledger.get_application(contract.__app_id__)
    txn_app = txn_fields.get("app_id", contract_app)
    if contract_app != txn_app:
        raise ValueError("txn app_id does not match contract")
    txn_arrays = _extract_arrays_from_args(
        args,
        method_selector=method_selector,
        sender=context.default_sender,
        app=contract_app,
    )

    txn_fields.setdefault("sender", context.default_sender)
    txn_fields.setdefault("app_id", contract_app)
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

    app_txn = context.any.txn.application_call(**txn_fields)
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
            case _ as maybe_native:
                app_args.append(algopy_testing.arc4.native_value_to_arc4(maybe_native).bytes)
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
    returns = algosdk.abi.Returns(_type_to_arc4(annotations.pop("return")))
    method = algosdk.abi.Method(
        name=arc4_name,
        args=[algosdk.abi.Argument(_type_to_arc4(a)) for a in annotations.values()],
        returns=returns,
    )
    return method.get_signature()


def _type_to_arc4(annotation: types.GenericAlias | type | None) -> str:  # noqa: PLR0911, PLR0912
    from algopy_testing.arc4 import Struct, _ABIEncoded
    from algopy_testing.gtxn import Transaction, TransactionBase
    from algopy_testing.models import Account, Application, Asset

    if annotation is None:
        return "void"

    if isinstance(annotation, types.GenericAlias) and typing.get_origin(annotation) is tuple:
        tuple_args = [_type_to_arc4(a) for a in typing.get_args(annotation)]
        return f"({','.join(tuple_args)})"

    if not isinstance(annotation, type):
        raise TypeError(f"expected type: {annotation!r}")

    # arc4 types
    if issubclass(annotation, _ABIEncoded | Struct):
        return annotation.type_info.arc4_name
    # txn types
    if issubclass(annotation, Transaction):
        return "txn"
    if issubclass(annotation, TransactionBase):
        return annotation.type_enum.txn_name
    # reference types
    if issubclass(annotation, Account):
        return "account"
    if issubclass(annotation, Asset):
        return "asset"
    if issubclass(annotation, Application):
        return "application"
    # native types
    if issubclass(annotation, UInt64):
        return "uint64"
    if issubclass(annotation, String):
        return "string"
    if issubclass(annotation, BigUInt):
        return "uint512"
    if issubclass(annotation, Bytes):
        return "byte[]"
    if issubclass(annotation, bool):
        return "bool"
    raise TypeError(f"type not a valid ARC4 type: {annotation}")


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
        assert isinstance(contract, algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"

        # TODO: handle custom txn groups
        contract_app = lazy_context.ledger.get_application(contract.__app_id__)
        txns = [
            lazy_context.value.any.txn.application_call(
                # TODO: fill out other fields where possible (see abimethod)
                app_id=contract_app,
            ),
        ]

        with lazy_context.txn._maybe_implicit_txn_group(txns):
            check_create(contract, create)
            check_oca(allow_actions)
            return fn(*args, **kwargs)

    return wrapper
