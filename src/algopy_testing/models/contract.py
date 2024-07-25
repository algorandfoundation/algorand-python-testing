from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

from algopy_testing.utils import is_instance

if TYPE_CHECKING:
    import algopy


@dataclass
class StateTotals:
    global_uints: int | None = None
    global_bytes: int | None = None
    local_uints: int | None = None
    local_bytes: int | None = None


class _ContractMeta(type):
    def __call__(cls, *args: Any, **kwargs: dict[str, Any]) -> object:
        from algopy import Contract

        from algopy_testing.context import get_test_context

        context = get_test_context()
        instance = super().__call__(*args, **kwargs)

        if context and isinstance(instance, Contract):
            global_num_uint, global_num_bytes = instance._get_global_state_totals()
            local_num_uint, local_num_bytes = instance._get_local_state_totals()
            context._app_id_to_contract[
                int(
                    context.any_application(
                        global_num_bytes=global_num_bytes,
                        global_num_uints=global_num_uint,
                        local_num_bytes=local_num_bytes,
                        local_num_uints=local_num_uint,
                    ).id
                )
            ] = instance

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
        cls._name = name or cls.__name__
        cls._scratch_slots = scratch_slots
        cls._state_totals = state_totals

    def _get_local_states(self) -> dict[str, algopy.LocalState[Any]]:
        import algopy

        local_states = {
            name: value
            for name, value in vars(self).items()
            if isinstance(value, algopy.LocalState)
        }

        return local_states

    def _get_global_states(self) -> dict[str, algopy.GlobalState[Any]]:
        import algopy

        global_states = {
            name: value
            for name, value in vars(self).items()
            if isinstance(value, algopy.GlobalState)
        }

        return global_states

    def _count_state_types(
        self, states: dict[str, algopy.GlobalState[Any]] | dict[str, algopy.LocalState[Any]]
    ) -> tuple[int, int]:
        import algopy

        uint_count = sum(1 for state in states.values() if is_instance(state.type_, algopy.UInt64))
        bytes_count = len(states) - uint_count
        return uint_count, bytes_count

    def _get_global_state_totals(
        self, global_states: dict[str, algopy.GlobalState[Any]] | None = None
    ) -> tuple[int, int]:
        return self._count_state_types(global_states or self._get_global_states())

    def _get_local_state_totals(
        self, local_states: dict[str, algopy.LocalState[Any]] | None = None
    ) -> tuple[int, int]:
        return self._count_state_types(local_states or self._get_local_states())

    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`approval_program` is not implemented.")

    def clear_state_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`clear_state_program` is not implemented.")

    def __hash__(self) -> int:
        # TODO: verify whether its needed
        # TODO: If needed, ensure dunder equals is implemented as well
        return hash(self._name + str(self._scratch_slots) + str(self._state_totals))

    def __getattribute__(self, name: str) -> Any:
        from algopy_testing.context import get_test_context

        context = get_test_context()
        context.set_active_contract(self)

        attr = super().__getattribute__(name)
        if callable(attr):

            def wrapper(*args: Any, **kwargs: dict[str, Any]) -> Any:
                return attr(*args, **kwargs)

            return wrapper
        return attr

    def __setattr__(self, name: str, value: Any) -> None:
        import algopy

        name_bytes = algopy.String(name).bytes
        match value:
            case algopy.Box() | algopy.BoxRef() | algopy.GlobalState() | algopy.LocalState():
                value._key = name_bytes
            case algopy.BoxMap():
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
