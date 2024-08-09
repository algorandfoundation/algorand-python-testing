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
        self.app_id = lazy_context.maybe_active_app_id
        match key:
            case bytes(bytes_key):
                self._key: algopy.Bytes = Bytes(bytes_key)
            case Bytes() as key_bytes:
                self._key = key_bytes
            case str(str_key):
                self._key = String(str_key).bytes
            case String() as key_str:
                self._key = key_str.bytes
            case _:
                raise ValueError("Key must be bytes or str")
        if isinstance(type_or_value, type):
            self.type_: type[_T] = type_or_value
        else:
            self.type_ = type(type_or_value)
            self._value = type_or_value

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key."""
        return self._key

    @property
    def value(self) -> _T:
        if self._value is None:
            raise ValueError("Value is not set")
        return self._value

    @value.setter
    def value(self, value: _T) -> None:
        self._value = value

    @value.deleter
    def value(self) -> None:
        self._value = None

    @property
    def _value(self) -> _T | None:
        app_data = lazy_context.get_app_data(self.app_id)
        try:
            native = app_data.get_global_state(self._key.value)
        except KeyError:
            return None
        else:
            return deserialize(self.type_, native)

    @_value.setter
    def _value(self, value: _T | None) -> None:
        native = None if value is None else serialize(value)
        app_data = lazy_context.get_app_data(self.app_id)
        app_data.set_global_state(self._key.value, native)

    def __bool__(self) -> bool:
        return self._value is not None

    def get(self, default: _T | None = None) -> _T:
        if self._value is not None:
            return self._value
        if default is not None:
            return default
        return self.type_()

    def maybe(self) -> tuple[_T | None, bool]:
        return self._value, self._value is not None
