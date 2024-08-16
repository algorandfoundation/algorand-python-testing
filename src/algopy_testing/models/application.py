from __future__ import annotations

import inspect
import typing

from algopy_testing.primitives import UInt64
from algopy_testing.protocols import UInt64Backed
from algopy_testing.utils import as_bytes, as_int64

if typing.TYPE_CHECKING:
    from collections.abc import Sequence

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
        # TODO: 1.0 add getter to ledger context, get_global_state, get_local_state, get_box
        self.app_logs: Sequence[bytes] = (logs,) if isinstance(logs, bytes) else logs

    def get_global_state(self, key: algopy.Bytes | bytes) -> StateValueType:
        return self.global_state[as_bytes(key)]

    def set_global_state(self, key: algopy.Bytes | bytes, value: StateValueType | None) -> None:
        key_bytes = as_bytes(key)
        if value is None:
            if key_bytes in self.global_state:
                del self.global_state[key_bytes]
        else:
            self.global_state[key_bytes] = value

    def get_local_state(
        self, account: algopy.Account | str, key: algopy.Bytes | bytes
    ) -> StateValueType:
        account_public_key = account if isinstance(account, str) else account.public_key
        return self.local_state[(account_public_key, as_bytes(key))]

    def set_local_state(
        self,
        account: algopy.Account | str,
        key: algopy.Bytes | bytes,
        value: StateValueType | None,
    ) -> None:
        account_public_key = account if isinstance(account, str) else account.public_key
        key_bytes = as_bytes(key)
        if value is None:
            del self.local_state[(account_public_key, key_bytes)]
        else:
            self.local_state[(account_public_key, key_bytes)] = value


class Application(UInt64Backed):
    def __init__(self, application_id: algopy.UInt64 | int = 0, /):
        self._id = as_int64(application_id)

    @property
    def id(self) -> algopy.UInt64:
        return UInt64(self._id)

    @property
    def int_(self) -> int:
        return self._id

    @classmethod
    def from_int(cls, value: int, /) -> typing.Self:
        return cls(value)

    @property
    def fields(self) -> ApplicationFields:
        from algopy_testing._context_helpers import lazy_context

        if self._id == 0:
            raise ValueError("cannot access properties of an app with an id of 0") from None
        return lazy_context.get_app_data(self._id).fields

    def __getattr__(self, name: str) -> typing.Any:
        if name in inspect.get_annotations(ApplicationFields):
            value = self.fields.get(name)
            # TODO: 1.0 ensure reasonable default values are present (like account does)
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
