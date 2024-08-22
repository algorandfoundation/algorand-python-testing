from __future__ import annotations

import typing

from _algopy_testing.context_helpers import lazy_context

_T = typing.TypeVar("_T")


class TemplateVarGeneric:
    def __getitem__(self, type_: type[_T]) -> typing.Callable[[str], typing.Any]:
        def create_template_var(variable_name: str) -> typing.Any:
            try:
                return lazy_context.value._template_vars[variable_name]
            except KeyError:
                raise ValueError(
                    f"Template variable {variable_name} not found in test context!"
                ) from None

        return create_template_var


TemplateVar: TemplateVarGeneric = TemplateVarGeneric()
"""Template variables can be used to represent a placeholder for a deploy-time provided
value."""
