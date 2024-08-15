from __future__ import annotations

import functools
import typing
from dataclasses import dataclass

import algopy_testing
from algopy_testing._context_helpers import lazy_context
from algopy_testing.decorators.arc4 import maybe_arc4_metadata
from algopy_testing.primitives import Bytes, UInt64
from algopy_testing.protocols import BytesBacked, UInt64Backed
from algopy_testing.state.utils import deserialize, serialize

if typing.TYPE_CHECKING:
    import algopy


@dataclass
class StateTotals:
    global_uints: int | None = None
    global_bytes: int | None = None
    local_uints: int | None = None
    local_bytes: int | None = None


@dataclass
class _StateTotals:
    global_uints: int
    global_bytes: int
    local_uints: int
    local_bytes: int


class _ContractMeta(type):
    def __init__(cls, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        cls.global_state_types = dict[str, type]()

    def __call__(cls, *args: typing.Any, **kwargs: dict[str, typing.Any]) -> object:
        context = lazy_context.value
        app_ref = context.any.application()  # new reference to get a unique app_id
        app_id = app_ref.id.value
        instance = cls.__new__(cls)  # type: ignore[call-overload]
        instance.__app_id__ = app_id
        app_data = lazy_context.get_app_data(app_id)
        app_data.is_creating = True

        fields = lazy_context.get_txn_op_fields()
        fields["app_id"] = app_ref

        # TODO: 1.0 provide app_id during instantiation without requiring a txn
        txn = context.any.txn.application_call(**fields)
        with context.txn.create_group([txn]):
            instance = super().__call__(*args, **kwargs)
            instance.__app_id__ = app_id

        assert isinstance(instance, Contract)
        cls_state_totals = cls._state_totals or StateTotals()  # type: ignore[attr-defined]
        state_totals = _get_state_totals(instance, cls_state_totals)
        context.ledger.update_application(
            app_id,
            global_num_bytes=algopy_testing.UInt64(state_totals.global_bytes),
            global_num_uint=algopy_testing.UInt64(state_totals.global_uints),
            local_num_bytes=algopy_testing.UInt64(state_totals.local_bytes),
            local_num_uint=algopy_testing.UInt64(state_totals.local_uints),
            creator=txn.sender,
        )

        app_data = lazy_context.get_app_data(app_id)
        app_data.contract = instance
        app_data.is_creating = _has_create_methods(cls)

        return instance


class Contract(metaclass=_ContractMeta):
    # note: it is import to minimize any additional attributes (including methods)
    #       on this class, that aren't part of the official stubs
    #       to reduce the potential for clashes with classes that inherit from this
    __app_id__: int
    _name: typing.ClassVar[str]
    _scratch_slots: typing.ClassVar[typing.Any | None]
    _state_totals: typing.ClassVar[StateTotals | None]

    def __init_subclass__(
        cls,
        *,
        name: str | None = None,
        scratch_slots: (
            algopy.urange | tuple[int | algopy.urange, ...] | list[int | algopy.urange] | None
        ) = None,
        state_totals: StateTotals | None = None,
    ):
        # TODO: 1.0 add test : check storing these on cls does not interfere with instances
        #       by having a contract with _name, _scratch_slots and _state_totals attributes
        cls._name = name or cls.__name__
        cls._scratch_slots = scratch_slots
        cls._state_totals = state_totals

    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`approval_program` is not implemented.")

    def clear_state_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`clear_state_program` is not implemented.")

    def __getattribute__(self, name: str) -> typing.Any:
        attr = super().__getattribute__(name)
        # wrap direct calls to approval and clear programs
        # TODO: find a less convoluted pattern
        if name in ("approval_program", "clear_state_program"):

            def set_active_contract(
                *args: typing.Any, **kwargs: dict[str, typing.Any]
            ) -> typing.Any:
                context = lazy_context.value
                # TODO: 1.0 should populate the app txn as much as possible like abimethod does
                app = context.ledger.get_application(_get_self_or_active_app_id(self))
                txns = [context.any.txn.application_call(app_id=app)]
                with context.txn._maybe_implicit_txn_group(txns):
                    try:
                        return attr(*args, **kwargs)
                    finally:
                        lazy_context.get_app_data(self).is_creating = False

            return set_active_contract

        if callable(attr) and not name.startswith("__"):

            @functools.wraps(attr)
            def set_is_creating(*args: typing.Any, **kwargs: dict[str, typing.Any]) -> typing.Any:
                try:
                    return attr(*args, **kwargs)
                finally:
                    lazy_context.get_app_data(self).is_creating = False

            return set_is_creating

        cls = type(self)
        assert isinstance(cls, _ContractMeta)
        try:
            unproxied_global_state_type = cls.global_state_types[name]
        except KeyError:
            return attr
        app_data = lazy_context.get_app_data(_get_self_or_active_app_id(self))
        value = app_data.get_global_state(name.encode("utf8"))
        return deserialize(unproxied_global_state_type, value)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        name_bytes = algopy_testing.String(name).bytes
        match value:
            case (algopy_testing.Box() | algopy_testing.BoxRef()) as box if not box._key:
                box._key = name_bytes
            case algopy_testing.GlobalState() as state:
                state.app_id = _get_self_or_active_app_id(self)
                if not state._key:
                    state.set_key(name_bytes)
            case algopy_testing.LocalState() as state:
                state.app_id = _get_self_or_active_app_id(self)
                if not state._key:
                    state._key = name_bytes
            case algopy_testing.BoxMap() as box_map if box_map._key_prefix is None:
                box_map._key_prefix = name_bytes
            case Bytes() | UInt64() | BytesBacked() | UInt64Backed() | bool():
                app_id = _get_self_or_active_app_id(self)
                app = lazy_context.get_app_data(app_id)
                app.set_global_state(name_bytes.value, serialize(value))
                cls = type(self)
                assert isinstance(cls, _ContractMeta)
                cls.global_state_types[name] = type(value)

        super().__setattr__(name, value)


def _get_self_or_active_app_id(contract: Contract) -> int:
    try:
        return contract.__app_id__
    # during construction app_id is not available, get from context instead
    except AttributeError:
        return lazy_context.active_group.active_app_id


class ARC4Contract(Contract):
    @typing.final
    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError(
            "`approval_program` is not implemented. To test ARC4 specific logic, "
            "refer to direct calls to ARC4 methods."
        )

    def clear_state_program(self) -> algopy.UInt64 | bool:
        return True


def _get_state_totals(contract: Contract, cls_state_totals: StateTotals) -> _StateTotals:
    from algopy_testing.primitives import UInt64
    from algopy_testing.protocols import UInt64Backed

    global_bytes = global_uints = local_bytes = local_uints = 0
    for type_ in get_global_states(contract).values():
        if issubclass(type_, UInt64 | UInt64Backed | bool):
            global_uints += 1
        else:
            global_bytes += 1
    for type_ in get_local_states(contract).values():
        if issubclass(type_, UInt64 | UInt64Backed | bool):
            local_uints += 1
        else:
            local_bytes += 1

    # TODO: 1.0 add tests for state overrides
    # apply any cls specific overrides
    if cls_state_totals.global_uints is not None:
        global_uints = cls_state_totals.global_uints
    if cls_state_totals.global_bytes is not None:
        global_bytes = cls_state_totals.global_bytes
    if cls_state_totals.local_uints is not None:
        local_uints = cls_state_totals.local_uints
    if cls_state_totals.local_bytes is not None:
        local_bytes = cls_state_totals.local_bytes
    return _StateTotals(
        global_uints=global_uints,
        global_bytes=global_bytes,
        local_uints=local_uints,
        local_bytes=local_bytes,
    )


def _has_create_methods(contract_cls: _ContractMeta) -> bool:
    for method in vars(contract_cls).values():
        if callable(method) and (arc4_meta := maybe_arc4_metadata(method)) and arc4_meta.is_create:
            return True

    return False


def get_local_states(contract: Contract) -> dict[bytes, type]:
    local_states = {
        attribute._key.value: attribute.type_
        for _, attribute in vars(contract).items()
        if isinstance(attribute, algopy_testing.LocalState)
    }

    return local_states


def get_global_states(contract: Contract) -> dict[bytes, type]:
    global_states = {}
    for key, attribute in vars(contract).items():
        if isinstance(
            attribute,
            algopy_testing.LocalState
            | algopy_testing.Box
            | algopy_testing.BoxMap
            | algopy_testing.BoxRef,
        ) or callable(attribute):
            continue
        if isinstance(attribute, algopy_testing.GlobalState):
            global_states[attribute.key.value] = attribute.type_
        elif isinstance(attribute, UInt64Backed | BytesBacked | UInt64 | Bytes | bool):
            global_states[key.encode()] = type(attribute)

    return global_states
