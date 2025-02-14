from __future__ import annotations

# ruff: noqa: ARG001, PLR0913
import typing

from _algopy_testing.utils import raise_mocked_function_error

if typing.TYPE_CHECKING:
    from collections.abc import Mapping

    import algopy


class CompiledContract(typing.NamedTuple):
    approval_program: tuple[algopy.Bytes, algopy.Bytes]
    clear_state_program: tuple[algopy.Bytes, algopy.Bytes]
    extra_program_pages: algopy.UInt64
    global_uints: algopy.UInt64
    global_bytes: algopy.UInt64
    local_uints: algopy.UInt64
    local_bytes: algopy.UInt64


class CompiledLogicSig(typing.NamedTuple):
    account: algopy.Account


def compile_contract(
    contract: type[algopy.Contract],
    /,
    *,
    extra_program_pages: algopy.UInt64 | int = 0,
    global_uints: algopy.UInt64 | int = 0,
    global_bytes: algopy.UInt64 | int = 0,
    local_uints: algopy.UInt64 | int = 0,
    local_bytes: algopy.UInt64 | int = 0,
    template_vars: Mapping[str, object] | None = None,
    template_vars_prefix: str = "",
) -> CompiledContract:
    raise_mocked_function_error("compile_contract")


def compile_logicsig(
    logicsig: algopy.LogicSig,
    /,
    *,
    template_vars: Mapping[str, object] | None = None,
    template_vars_prefix: str = "",
) -> CompiledLogicSig:
    raise_mocked_function_error("compile_logicsig")
