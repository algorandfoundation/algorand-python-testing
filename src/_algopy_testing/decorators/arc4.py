from __future__ import annotations

import dataclasses
import functools
import inspect
import types
import typing

import algosdk

import _algopy_testing
from _algopy_testing.constants import ALWAYS_APPROVE_TEAL_PROGRAM, ARC4_RETURN_PREFIX
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.enums import OnCompleteAction
from _algopy_testing.primitives import BigUInt, Bytes, String, UInt64

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


def _parse_allow_actions(allow_actions: Sequence[_AllowActions]) -> list[OnCompleteAction]:
    allow_ac = []
    for action in allow_actions:
        if isinstance(action, str):
            action = OnCompleteAction._from_str(action)
        allow_ac.append(action)
    return allow_ac


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
    _fn: Callable[..., typing.Any], app_args: Sequence[typing.Any], kwargs: dict[str, typing.Any]
) -> list[typing.Any]:
    sig = inspect.signature(_fn)
    params = list(sig.parameters.values())[1:]  # Skip 'self'
    app_args_iter = iter(app_args)

    ordered_args = []
    for p in params:
        try:
            arg = kwargs[p.name]
        except KeyError:
            try:
                arg = next(app_args_iter)
            except StopIteration:
                if p.default is p.empty:
                    raise TypeError(f"missing required argument {p.name}") from None
                arg = p.default
        ordered_args.append(arg)

    if list(app_args_iter):
        raise TypeError("Too many positional arguments")

    if len(ordered_args) != len(params):
        missing = [p.name for p in params if p.name not in kwargs and p.default is p.empty]
        raise TypeError(f"Missing required argument(s): {', '.join(missing)}")

    return ordered_args


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
    from _algopy_testing.utilities.log import log

    allow_actions = _parse_allow_actions(allow_actions)

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
        from _algopy_testing.serialize import native_to_arc4

        contract, *app_args = args
        assert isinstance(contract, _algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"
        app_id = contract.__app_id__

        context = lazy_context.value
        ordered_args = get_ordered_args(fn, app_args, kwargs)
        assert metadata.arc4_signature is not None, "expected abimethod"
        txns = create_abimethod_txns(
            app_id=app_id,
            arc4_signature=metadata.arc4_signature,
            args=ordered_args,
            allow_actions=allow_actions,
        )
        with context.txn._maybe_implicit_txn_group(txns):
            check_routing_conditions(app_id, metadata)
            result = fn(*args, **kwargs)
            if result is not None:

                abi_result = native_to_arc4(result)
                log(ARC4_RETURN_PREFIX, abi_result)
            return result

    return wrapper


def create_abimethod_txns(
    app_id: int,
    arc4_signature: str,
    args: Sequence[object],
    allow_actions: Sequence[_AllowActions],
) -> list[algopy.gtxn.TransactionBase]:
    contract_app = lazy_context.ledger.get_app(app_id)
    txn_fields = get_active_txn_fields(contract_app, allow_actions)

    method = algosdk.abi.Method.from_signature(arc4_signature)
    method_selector = Bytes(method.get_selector())
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

    app_txn = lazy_context.any.txn.application_call(**txn_fields)
    return [*txn_arrays.txns, app_txn]


def get_active_txn_fields(
    app: algopy.Application, allow_actions: Sequence[_AllowActions] = ()
) -> dict[str, typing.Any]:
    txn_fields = lazy_context.get_active_txn_overrides()
    txn_app = txn_fields.setdefault("app_id", app)
    txn_fields.setdefault("sender", lazy_context.value.default_sender)
    if app != txn_app:
        raise ValueError("txn app_id does not match contract")

    # if there is a single allowed action then use that
    try:
        (allow_action,) = allow_actions
    except ValueError:
        pass
    else:
        txn_fields.setdefault("on_completion", allow_action)
    # at some point could get the actual values by using puya to compile the contract
    # this should be opt-in behaviour, as that it would be too slow to always do
    txn_fields.setdefault(
        "approval_program_pages", [_algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )
    txn_fields.setdefault(
        "clear_state_program_pages", [_algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM)]
    )
    return txn_fields


def create_baremethod_txns(
    app_id: int, allow_actions: Sequence[_AllowActions]
) -> list[algopy.gtxn.TransactionBase]:
    app = lazy_context.ledger.get_app(app_id)
    txn_fields = get_active_txn_fields(app, allow_actions)
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
    from _algopy_testing.serialize import native_to_arc4

    txns = list[_algopy_testing.gtxn.TransactionBase]()
    apps = [app]
    assets = list[_algopy_testing.Asset]()
    accounts = [sender]
    app_args = list[_algopy_testing.arc4._ABIEncoded]()
    for arg in args:
        match arg:
            case _algopy_testing.gtxn.TransactionBase() as txn:
                txns.append(txn)
            case _algopy_testing.Account() as acc:
                app_args.append(_algopy_testing.arc4.UInt8(len(accounts)))
                accounts.append(acc)
            case _algopy_testing.Asset() as asset:
                app_args.append(_algopy_testing.arc4.UInt8(len(assets)))
                assets.append(asset)
            case _algopy_testing.Application() as arg_app:
                app_args.append(_algopy_testing.arc4.UInt8(len(apps)))
                apps.append(arg_app)
            case _ as maybe_native:
                app_args.append(native_to_arc4(maybe_native))
    if len(app_args) > 15:
        packed = _algopy_testing.arc4.Tuple(tuple(app_args[14:]))
        app_args[14:] = [packed]
    return _TxnArrays(
        txns=txns,
        apps=apps,
        assets=assets,
        accounts=accounts,
        app_args=[method_selector, *(a.bytes for a in app_args)],
    )


def _generate_arc4_signature_from_fn(fn: typing.Callable[_P, _R], arc4_name: str) -> str:
    annotations = inspect.get_annotations(fn, eval_str=True).copy()
    returns = algosdk.abi.Returns(_type_to_arc4(annotations.pop("return")))
    method = algosdk.abi.Method(
        name=arc4_name,
        args=[algosdk.abi.Argument(_type_to_arc4(a)) for a in annotations.values()],
        returns=returns,
    )
    return method.get_signature()


def _type_to_arc4(annotation: types.GenericAlias | type | None) -> str:  # noqa: PLR0911, PLR0912
    from _algopy_testing.arc4 import _ABIEncoded
    from _algopy_testing.gtxn import Transaction, TransactionBase
    from _algopy_testing.models import Account, Application, Asset
    from _algopy_testing.primitives import ImmutableArray

    if annotation is None:
        return "void"

    if isinstance(annotation, types.GenericAlias) and typing.get_origin(annotation) is tuple:
        tuple_args = [_type_to_arc4(a) for a in typing.get_args(annotation)]
        return f"({','.join(tuple_args)})"

    if not isinstance(annotation, type):
        raise TypeError(f"expected type: {annotation!r}")

    if typing.NamedTuple in getattr(annotation, "__orig_bases__", []):
        tuple_fields = list(inspect.get_annotations(annotation).values())
        tuple_args = [_type_to_arc4(a) for a in tuple_fields]
        return f"({','.join(tuple_args)})"

    if issubclass(annotation, ImmutableArray):
        return f"{_type_to_arc4(annotation._element_type)}[]"
    # arc4 types
    if issubclass(annotation, _ABIEncoded):
        return annotation._type_info.arc4_name
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
        assert isinstance(contract, _algopy_testing.ARC4Contract), "expected ARC4 contract"
        assert fn is not None, "expected function"

        txns = create_baremethod_txns(contract.__app_id__, allow_actions)

        with lazy_context.txn._maybe_implicit_txn_group(txns):
            check_routing_conditions(contract.__app_id__, metadata)
            return fn(*args, **kwargs)

    return wrapper
