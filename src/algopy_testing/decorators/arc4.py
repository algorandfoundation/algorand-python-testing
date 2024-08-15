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
ARC4_METADATA_ATTR = "arc4_metadata"


@dataclasses.dataclass
class MethodMetadata:
    create: _CreateValues
    allow_actions: Sequence[_AllowActions]
    arc4_signature: str | None = None

    @property
    def is_create(self) -> bool:
        return self.create != "disallow"


def set_arc4_metadata(fn: object, data: MethodMetadata) -> None:
    setattr(fn, ARC4_METADATA_ATTR, data)


def maybe_arc4_metadata(fn: object) -> MethodMetadata | None:
    return getattr(fn, ARC4_METADATA_ATTR, None)


def get_arc4_metadata(fn: object) -> MethodMetadata:
    metadata = maybe_arc4_metadata(fn)
    if metadata is None:
        raise ValueError("Expected ARC4 abimethod or baremethod")
    return metadata


def get_ordered_args(
    _fn: Callable[..., typing.Any], app_args: list[typing.Any], kwargs: dict[str, typing.Any]
) -> list[typing.Any]:
    # TODO: 1.0 order kwargs correctly based on fn signature
    return [*app_args, *kwargs.values()]


def check_routing_conditions(app_id: int, metadata: MethodMetadata) -> None:
    app_data = lazy_context.get_app_data(app_id)

    # check if app is creating and if method allows this
    is_creating = app_data.is_creating
    if is_creating and metadata.create == "disallow":
        raise RuntimeError("method can not be called while creating")
    if not is_creating and metadata.create == "require":
        raise RuntimeError("method can only be called while creating")

    # check on completion action
    txn = lazy_context.active_group.active_txn
    allowed_actions = [
        action if isinstance(action, str) else action.name for action in metadata.allow_actions
    ]
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
    metadata = MethodMetadata(
        create=create,
        allow_actions=allow_actions,
        arc4_signature=_generate_arc4_signature_from_fn(fn, arc4_name),
    )
    set_arc4_metadata(fn, metadata)

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"
        app_id = contract.__app_id__

        context = lazy_context.value
        ordered_args = get_ordered_args(fn, app_args, kwargs)
        assert metadata.arc4_signature is not None, "expected abimethod"
        txns = create_abimethod_txns(
            app_id=app_id,
            arc4_signature=metadata.arc4_signature,
            args=ordered_args,
        )
        with context.txn._maybe_implicit_txn_group(txns):
            check_routing_conditions(app_id, metadata)
            result = fn(*args, **kwargs)
            # TODO: 1.0 add result along with ARC4 log prefix to application logs?
            return result

    return wrapper


def create_abimethod_txns(
    app_id: int,
    arc4_signature: str,
    args: Sequence[object],
) -> list[algopy.gtxn.TransactionBase]:
    method = algosdk.abi.Method.from_signature(arc4_signature)
    method_selector = Bytes(method.get_selector())
    txn_fields = lazy_context.get_txn_op_fields()

    contract_app = lazy_context.ledger.get_application(app_id)
    txn_app = txn_fields.setdefault("app_id", contract_app)
    txn_fields.setdefault("sender", lazy_context.value.default_sender)
    if contract_app != txn_app:
        raise ValueError("txn app_id does not match contract")
    txn_arrays = _extract_arrays_from_args(
        args,
        method_selector=method_selector,
        sender=txn_fields["sender"],
        app=contract_app,
    )

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

    app_txn = lazy_context.any.txn.application_call(**txn_fields)
    return [*txn_arrays.txns, app_txn]


def create_baremethod_txns(app_id: int) -> list[algopy.gtxn.TransactionBase]:
    txn_fields = lazy_context.get_txn_op_fields()

    contract_app = lazy_context.ledger.get_application(app_id)
    txn_fields.setdefault("app_id", contract_app)

    txn_fields.setdefault(
        "approval_program_pages", [algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )
    txn_fields.setdefault(
        "clear_state_program_pages", [algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )
    txn_fields.setdefault("sender", lazy_context.value.default_sender)
    return [
        lazy_context.value.any.txn.application_call(
            **txn_fields,
        ),
    ]


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
        # TODO:1.0 pack extra args into an ARC4 tuple
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

    metadata = MethodMetadata(
        create=create,
        allow_actions=allow_actions,
    )
    set_arc4_metadata(fn, metadata)

    @functools.wraps(fn)
    def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
        contract, *app_args = args
        assert isinstance(contract, algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"

        txns = create_baremethod_txns(contract.__app_id__)

        with lazy_context.txn._maybe_implicit_txn_group(txns):
            check_routing_conditions(contract.__app_id__, metadata)
            return fn(*args, **kwargs)

    return wrapper
