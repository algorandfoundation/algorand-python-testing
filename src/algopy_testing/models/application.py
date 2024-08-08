from __future__ import annotations

import dataclasses
import inspect
import typing

from algopy_testing._context_helpers._context_storage import get_app_data
from algopy_testing.primitives import UInt64
from algopy_testing.utils import as_int64

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.models.contract import Contract


class ApplicationFields(typing.TypedDict, total=False):
    approval_program: algopy.Bytes
    clear_state_program: algopy.Bytes
    global_num_uint: algopy.UInt64
    global_num_bytes: algopy.UInt64
    local_num_uint: algopy.UInt64
    local_num_bytes: algopy.UInt64
    extra_program_pages: algopy.UInt64
    creator: algopy.Account
    address: algopy.Account


@dataclasses.dataclass
class ApplicationContextData:
    app_id: int
    fields: ApplicationFields
    is_creating: bool = False
    contract: Contract | None = None


class Application:
    def __init__(self, application_id: algopy.UInt64 | int = 0, /):
        self._id = as_int64(application_id)

    @property
    def id(self) -> algopy.UInt64:
        return UInt64(self._id)

    @property
    def fields(self) -> ApplicationFields:
        try:
            return get_app_data(self._id).fields
        except KeyError:
            if self._id == 0:
                return {}
            raise ValueError(
                "`algopy.Application` is not present in the test context! "
                "Use `context.add_application()` or `context.any.application()` to add the "
                "application to your test setup."
            ) from None

    def __getattr__(self, name: str) -> typing.Any:
        if name in inspect.get_annotations(ApplicationFields):
            value = self.fields.get(name)
            if value is None:
                raise ValueError(
                    f"The Application value '{name}' has not been defined on the test context. "
                    f"Make sure to patch the field '{name}' using your `AlgopyTestContext` "
                    "instance."
                )
            return value
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Application):
            return self._id == other._id
        return self._id == as_int64(other)

    def __bool__(self) -> bool:
        return self._id != 0

    def __hash__(self) -> int:
        return hash(self._id)
