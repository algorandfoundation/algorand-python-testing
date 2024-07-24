from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, final

if TYPE_CHECKING:
    import algopy


@dataclass
class StateTotals:
    global_uints: int | None = None
    global_bytes: int | None = None
    local_uints: int | None = None
    local_bytes: int | None = None


class Contract:
    """Base class for an Algorand Smart Contract"""

    _name: str
    _scratch_slots: Any | None
    _state_totals: StateTotals | None

    def __init_subclass__(
        cls,
        *,
        name: str | None = None,
        scratch_slots: (
            algopy.UInt64 | tuple[int | algopy.UInt64, ...] | list[int | algopy.UInt64] | None
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

    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`approval_program` is not implemented.")

    def clear_state_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError("`clear_state_program` is not implemented.")

    def __hash__(self) -> int:
        return hash(self._name)

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


class ARC4Contract(Contract):
    @final
    def approval_program(self) -> algopy.UInt64 | bool:
        raise NotImplementedError(
            "`approval_program` is not implemented. To test ARC4 specific logic, "
            "refer to direct calls to ARC4 methods."
        )

    def clear_state_program(self) -> algopy.UInt64 | bool:
        return True
