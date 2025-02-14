from __future__ import annotations

import functools
import typing
from dataclasses import dataclass

import _algopy_testing
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.decorators.arc4 import get_active_txn_fields, maybe_arc4_metadata
from _algopy_testing.mutable import set_attr_on_mutate
from _algopy_testing.primitives import Bytes, UInt64
from _algopy_testing.protocols import BytesBacked, Serializable, UInt64Backed
from _algopy_testing.state.utils import deserialize, serialize

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
    _name: str
    _scratch_slots: typing.Any
    _state_totals: StateTotals | None
    _avm_version: int

    def __init__(cls, *args: typing.Any, **kwargs: typing.Any) -> None:
        super().__init__(*args, **kwargs)
        cls.global_state_types = dict[str, type]()

    def __call__(cls, *args: typing.Any, **kwargs: dict[str, typing.Any]) -> object:
        context = lazy_context.value
        app_ref = context.any.application()  # new reference to get a unique app_id
        app_id = app_ref.id.value
        instance: Contract = cls.__new__(cls, *args, **kwargs)  # type: ignore[arg-type]
        instance.__app_id__ = app_id
        app_data = lazy_context.get_app_data(app_id)
        app_data.contract = instance
        app_data.is_creating = True

        fields = get_active_txn_fields(app_ref)
        txn = context.any.txn.application_call(**fields)
        with context.txn._maybe_implicit_txn_group([txn]) as active_group:
            if active_group.active_app_id != app_id:
                raise ValueError(
                    "contract being instantiated has different app_id than active txn"
                )
            creator = active_group.active_txn.sender
            context.ledger.update_app(
                app_id,
                creator=creator,
            )
            instance.__init__(*args, **kwargs)  # type: ignore[misc]
        app_data.is_creating = _has_create_methods(cls)

        assert isinstance(instance, Contract)
        cls_state_totals = cls._state_totals or StateTotals()
        state_totals = _get_state_totals(instance, cls_state_totals)
        context.ledger.update_app(
            app_id,
            global_num_bytes=_algopy_testing.UInt64(state_totals.global_bytes),
            global_num_uint=_algopy_testing.UInt64(state_totals.global_uints),
            local_num_bytes=_algopy_testing.UInt64(state_totals.local_bytes),
            local_num_uint=_algopy_testing.UInt64(state_totals.local_uints),
        )
        return instance


class Contract(metaclass=_ContractMeta):
    # note: it is import to minimize any additional attributes (including methods)
    #       on this class, that aren't part of the official stubs
    #       to reduce the potential for clashes with classes that inherit from this
    __app_id__: int

    def __init_subclass__(
        cls,
        *,
        name: str | None = None,
        scratch_slots: (
            algopy.urange | tuple[int | algopy.urange, ...] | list[int | algopy.urange] | None
        ) = None,
        state_totals: StateTotals | None = None,
        avm_version: int = 10,
    ):
        cls._name = name or cls.__name__
        cls._scratch_slots = scratch_slots
        cls._state_totals = state_totals
        cls._avm_version = avm_version

    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`approval_program` is not implemented.")

    def clear_state_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`clear_state_program` is not implemented.")

    def __getattribute__(self, name: str) -> typing.Any:
        attr = super().__getattribute__(name)
        # wrap direct calls to approval and clear programs
        # TODO: find a less convoluted pattern
        if name in ("approval_program", "clear_state_program"):

            def create_txn_group(*args: typing.Any, **kwargs: dict[str, typing.Any]) -> typing.Any:
                context = lazy_context.value
                app = context.ledger.get_app(_get_self_or_active_app_id(self))
                txn_fields = get_active_txn_fields(app)
                txns = [context.any.txn.application_call(**txn_fields)]
                with context.txn._maybe_implicit_txn_group(txns):
                    try:
                        return attr(*args, **kwargs)
                    finally:
                        lazy_context.get_app_data(self).is_creating = False

            return create_txn_group

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
        value = lazy_context.ledger.get_global_state(
            _get_self_or_active_app_id(self), name.encode("utf8")
        )

        value = deserialize(unproxied_global_state_type, value)
        return set_attr_on_mutate(self, name, value)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        name_bytes = _algopy_testing.String(name).bytes
        match value:
            case (_algopy_testing.Box() | _algopy_testing.BoxRef()) as box if not box._key:
                box._key = name_bytes
            case _algopy_testing.GlobalState() as state:
                state.app_id = _get_self_or_active_app_id(self)
                if not state._key:
                    state.set_key(name_bytes)
            case _algopy_testing.LocalState() as state:
                state.app_id = _get_self_or_active_app_id(self)
                if not state._key:
                    state._key = name_bytes
            case _algopy_testing.BoxMap() as box_map if box_map._key_prefix is None:
                box_map._key_prefix = name_bytes
            case Bytes() | UInt64() | BytesBacked() | Serializable() | UInt64Backed() | bool():
                app_id = _get_self_or_active_app_id(self)
                lazy_context.ledger.set_global_state(app_id, name_bytes, serialize(value))
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
    from _algopy_testing.primitives import UInt64
    from _algopy_testing.protocols import UInt64Backed

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
        if isinstance(attribute, _algopy_testing.LocalState)
    }

    return local_states


def get_global_states(contract: Contract) -> dict[bytes, type]:
    global_states = {}
    for key, attribute in vars(contract).items():
        if isinstance(
            attribute,
            _algopy_testing.LocalState
            | _algopy_testing.Box
            | _algopy_testing.BoxMap
            | _algopy_testing.BoxRef,
        ) or callable(attribute):
            continue
        if isinstance(attribute, _algopy_testing.GlobalState):
            global_states[attribute.key.value] = attribute.type_
        elif isinstance(attribute, UInt64Backed | BytesBacked | UInt64 | Bytes | bool):
            global_states[key.encode()] = type(attribute)

    return global_states
