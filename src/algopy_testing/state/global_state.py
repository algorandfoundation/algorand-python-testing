from __future__ import annotations

import typing
from typing import overload

from algopy_testing._context_helpers import lazy_context
from algopy_testing.primitives import Bytes, String
from algopy_testing.state.utils import deserialize, serialize

if typing.TYPE_CHECKING:
    import algopy


_T = typing.TypeVar("_T")


class GlobalState(typing.Generic[_T]):
    @overload
    def __init__(
        self,
        type_: type[_T],
        /,
        *,
        key: Bytes | String | bytes | str = "",
        description: str = "",
    ) -> None: ...

    @overload
    def __init__(
        self,
        initial_value: _T,
        /,
        *,
        key: Bytes | String | bytes | str = "",
        description: str = "",
    ) -> None: ...

    def __init__(
        self,
        type_or_value: type[_T] | _T,
        /,
        *,
        key: Bytes | String | bytes | str = "",
        description: str = "",
    ) -> None:
        self.description = description
        self.app_id = lazy_context.active_group.active_app_id
        self._key: Bytes | None = None
        self._pending_value: _T | None = None

        if isinstance(type_or_value, type):
            self.type_: type[_T] = type_or_value
        else:
            self.type_ = type(type_or_value)
            self._pending_value = type_or_value

        self.set_key(key)

    def set_key(self, key: Bytes | String | bytes | str) -> None:
        """Set the key and apply any pending value.

        Pending values are used for implicit keys in Contract
        subclasses. They're stored until the 'Contract''s initialization
        sets the key.
        """
        match key:
            case bytes(bytes_key):
                self._key = Bytes(bytes_key)
            case Bytes() as key_bytes:
                self._key = key_bytes
            case str(str_key):
                self._key = String(str_key).bytes
            case String() as key_str:
                self._key = key_str.bytes
            case _:
                raise ValueError("Key must be bytes or str")

        if self._key and self._pending_value is not None:
            self.value = self._pending_value
            self._pending_value = None

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key."""
        if self._key is None:
            raise ValueError("Key is not set")
        return self._key

    @property
    def value(self) -> _T:
        if self._key is None:
            if self._pending_value is not None:
                return self._pending_value
            raise ValueError("Key is not set")
        app_data = lazy_context.get_app_data(self.app_id)
        try:
            native = app_data.get_global_state(self._key.value)
        except KeyError as e:
            raise ValueError("Value is not set") from e
        return deserialize(self.type_, native)

    @value.setter
    def value(self, value: _T) -> None:
        if self._key is None:
            self._pending_value = value
        else:
            app_data = lazy_context.get_app_data(self.app_id)
            app_data.set_global_state(self._key.value, serialize(value))

    @value.deleter
    def value(self) -> None:
        if self._key is None:
            self._pending_value = None
        else:
            app_data = lazy_context.get_app_data(self.app_id)
            app_data.set_global_state(self._key.value, None)

    def __bool__(self) -> bool:
        return self._key is not None or self._pending_value is not None

    def get(self, default: _T | None = None) -> _T:
        try:
            return self.value
        except ValueError:
            if default is not None:
                return default
            return self.type_()

    def maybe(self) -> tuple[_T | None, bool]:
        try:
            return self.value, True
        except ValueError:
            return None, False
