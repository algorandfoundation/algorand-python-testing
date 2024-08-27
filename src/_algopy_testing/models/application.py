from __future__ import annotations

import typing

import algosdk.logic

from _algopy_testing.primitives import UInt64
from _algopy_testing.protocols import UInt64Backed
from _algopy_testing.utils import as_int64

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

    import algopy

    from _algopy_testing.models.contract import Contract


class ApplicationFields(typing.TypedDict, total=False):
    approval_program: algopy.Bytes
    clear_state_program: algopy.Bytes
    global_num_uint: algopy.UInt64
    global_num_bytes: algopy.UInt64
    local_num_uint: algopy.UInt64
    local_num_bytes: algopy.UInt64
    extra_program_pages: algopy.UInt64
    creator: algopy.Account


AccountKey = str
Key = bytes
StateValueType = int | bytes


class ApplicationContextData:
    def __init__(
        self,
        app_id: int,
        fields: ApplicationFields,
        logs: bytes | Sequence[bytes] = (),
    ):
        self.app_id = app_id
        self.fields = fields
        self.global_state = dict[Key, StateValueType]()
        self.local_state = dict[tuple[AccountKey, Key], StateValueType]()
        self.boxes = dict[bytes, bytes]()
        self.is_creating = False
        self.contract: Contract | None = None
        # TODO: add callables support (similar to side effects in pytest)
        self.app_logs: Sequence[bytes] = (logs,) if isinstance(logs, bytes) else logs


class Application(UInt64Backed):
    def __init__(self, application_id: algopy.UInt64 | int = 0, /):
        self._id = as_int64(application_id)

    @property
    def id(self) -> algopy.UInt64:
        return UInt64(self._id)

    @property
    def address(self) -> algopy.Account:
        from _algopy_testing.models import Account

        address = algosdk.logic.get_application_address(self._id)
        return Account(address)

    @property
    def int_(self) -> int:
        return self._id

    @classmethod
    def from_int(cls, value: int, /) -> typing.Self:
        return cls(value)

    @property
    def fields(self) -> ApplicationFields:
        from _algopy_testing.context_helpers import lazy_context

        return lazy_context.get_app_data(self._id).fields

    def __getattr__(self, name: str) -> typing.Any:
        try:
            return self.fields[name]  # type: ignore[literal-required]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{name}'"
            ) from None

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Application):
            return self._id == other._id
        # can compare Applications to int types only (not uint64)
        elif isinstance(other, int):
            return self._id == other
        else:
            return NotImplemented

    def __bool__(self) -> bool:
        return self._id != 0

    def __hash__(self) -> int:
        return hash(self._id)
