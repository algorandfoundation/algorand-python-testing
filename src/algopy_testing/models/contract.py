from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

import algopy_testing
from algopy_testing._context_storage import get_app_data, get_test_context, link_application

if TYPE_CHECKING:
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
    def __call__(cls, *args: Any, **kwargs: dict[str, Any]) -> object:
        instance = super().__call__(*args, **kwargs)

        assert isinstance(instance, Contract)
        cls_state_totals = cls._state_totals or StateTotals()  # type: ignore[attr-defined]
        state_totals = _get_state_totals(instance, cls_state_totals)
        context = get_test_context()
        app_ref = context.any_application(
            global_num_bytes=algopy_testing.UInt64(state_totals.global_bytes),
            global_num_uint=algopy_testing.UInt64(state_totals.global_uints),
            local_num_bytes=algopy_testing.UInt64(state_totals.local_bytes),
            local_num_uint=algopy_testing.UInt64(state_totals.local_uints),
            # TODO: this should come from the active txn if available
            creator=context.default_sender,
        )
        app_id = int(app_ref.id)
        link_application(instance, app_id)
        app_data = get_app_data(app_id)
        app_data.is_creating = _has_create_methods(cls)

        return instance


class Contract(metaclass=_ContractMeta):
    _name: str
    _scratch_slots: Any | None
    _state_totals: StateTotals | None

    def __init_subclass__(
        cls,
        *,
        name: str | None = None,
        scratch_slots: (
            algopy.urange | tuple[int | algopy.urange, ...] | list[int | algopy.urange] | None
        ) = None,
        state_totals: StateTotals | None = None,
    ):
        # TODO: check storing these on cls does not interfere with instances
        #       by having a contract with _name, _scratch_slots and _state_totals attributes
        cls._name = name or cls.__name__
        cls._scratch_slots = scratch_slots
        cls._state_totals = state_totals

    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`approval_program` is not implemented.")

    def clear_state_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`clear_state_program` is not implemented.")

    def __getattribute__(self, name: str) -> Any:
        attr = super().__getattribute__(name)
        # wrap direct calls to approval and clear programs
        # TODO: find a less convoluted pattern
        if name in ("approval_program", "clear_state_program"):

            def set_active_contract(*args: Any, **kwargs: dict[str, Any]) -> Any:
                # TODO: this should also set up the current txn like abimethod does
                context = get_test_context()
                context.set_active_contract(self)
                try:
                    return attr(*args, **kwargs)
                finally:
                    get_app_data(self).is_creating = False
                    context.clear_active_contract()

            return set_active_contract

        if callable(attr) and not name.startswith("__"):

            def set_is_creating(*args: Any, **kwargs: dict[str, Any]) -> Any:
                try:
                    return attr(*args, **kwargs)
                finally:
                    get_app_data(self).is_creating = False

            return set_is_creating

        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        name_bytes = algopy_testing.String(name).bytes
        match value:
            case (
                algopy_testing.Box()
                | algopy_testing.BoxRef()
                | algopy_testing.GlobalState()
                | algopy_testing.LocalState()
            ) as state if not state._key:
                value._key = name_bytes
            case algopy_testing.BoxMap() as state if state._key_prefix is None:
                value._key_prefix = name_bytes

        super().__setattr__(name, value)


class ARC4Contract(Contract):
    @final
    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError(
            "`approval_program` is not implemented. To test ARC4 specific logic, "
            "refer to direct calls to ARC4 methods."
        )

    def clear_state_program(self) -> algopy.UInt64 | bool:
        return True


def _is_uint64_backed_type(typ: type) -> bool:
    return issubclass(
        typ, algopy_testing.UInt64 | algopy_testing.Application | algopy_testing.Asset | bool
    )


def _get_state_totals(contract: Contract, cls_state_totals: StateTotals) -> _StateTotals:
    global_bytes = global_uints = local_bytes = local_uints = 0
    for value in get_global_states(contract).values():
        if isinstance(value, algopy_testing.GlobalState):
            type_ = value.type_
        else:
            type_ = type(value)
        if _is_uint64_backed_type(type_):
            global_uints += 1
        else:
            global_bytes += 1
    for local_state in get_local_states(contract).values():
        if _is_uint64_backed_type(local_state.type_):
            local_uints += 1
        else:
            local_bytes += 1

    # TODO: add tests for state overrides
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
        if callable(method) and getattr(method, "is_create", False):
            return True

    return False


def get_local_states(contract: Contract) -> dict[bytes, algopy_testing.LocalState[Any]]:
    local_states = {
        attribute._key.value: attribute
        for _, attribute in vars(contract).items()
        if isinstance(attribute, algopy_testing.LocalState)
    }

    return local_states


def get_global_states(contract: Contract) -> dict[bytes, algopy_testing.GlobalState[Any]]:
    global_states = {}
    for key, attribute in vars(contract).items():
        if isinstance(
            attribute,
            algopy_testing.LocalState
            | algopy_testing.Box
            | algopy_testing.BoxMap
            | algopy_testing.BoxRef,
        ) or callable(attribute):
            pass
        if isinstance(attribute, algopy_testing.GlobalState):
            global_states[attribute._key.value] = attribute
        else:
            global_states[key.encode()] = algopy_testing.GlobalState(attribute, key=key)

    return global_states
