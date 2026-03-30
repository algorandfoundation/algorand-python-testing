from __future__ import annotations

import typing

import _algopy_testing
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.mutable import set_item_on_mutate
from _algopy_testing.state.local_state import LocalState
from _algopy_testing.state.utils import (
    cast_from_bytes,
    cast_to_bytes,
    deserialize,
    get_account,
    serialize,
)

_TKey = typing.TypeVar("_TKey")
_TValue = typing.TypeVar("_TValue")

if typing.TYPE_CHECKING:
    import algopy


class LocalMap(typing.Generic[_TKey, _TValue]):
    """LocalMap abstracts the reading and writing of a set of local state values using a
    common key and content type, associated with a specific account.

    Adequate space must be allocated for the application on creation (see
    algopy.StateTotals).
    """

    def __init__(
        self,
        key_type: type[_TKey],
        value_type: type[_TValue],
        /,
        *,
        key_prefix: bytes | str | algopy.Bytes | algopy.String | None = None,
    ) -> None:
        self.key_type = key_type
        self.value_type = value_type
        match key_prefix:
            case None:
                self._key_prefix = None
            case bytes(key) | _algopy_testing.Bytes(value=key):
                self._key_prefix = _algopy_testing.Bytes(key)
            case str(key_str) | _algopy_testing.String(value=key_str):
                self._key_prefix = _algopy_testing.Bytes(key_str.encode("utf8"))
            case _:
                typing.assert_never(key_prefix)
        self.app_id = lazy_context.active_group.active_app_id

    @property
    def key_prefix(self) -> algopy.Bytes:
        """Provides access to the raw storage key-prefix."""
        if self._key_prefix is None:
            raise RuntimeError("LocalMap key prefix is not defined")
        return self._key_prefix

    def _full_key(self, key: _TKey) -> algopy.Bytes:
        return self.key_prefix + cast_to_bytes(key)

    def __getitem__(
        self, account_and_key: tuple[algopy.Account | algopy.UInt64 | int, _TKey]
    ) -> _TValue:
        account_or_index, key = account_and_key
        content, exists = self.maybe(account_or_index, key)
        if not exists:
            raise RuntimeError("LocalMap key has not been defined")
        return set_item_on_mutate(self, account_and_key, content)

    def __setitem__(
        self, account_and_key: tuple[algopy.Account | algopy.UInt64 | int, _TKey], value: _TValue
    ) -> None:
        account_or_index, key = account_and_key
        account = get_account(account_or_index)
        key_bytes = self._full_key(key)
        lazy_context.ledger.set_local_state(self.app_id, account, key_bytes, serialize(value))

    def __delitem__(
        self, account_and_key: tuple[algopy.Account | algopy.UInt64 | int, _TKey]
    ) -> None:
        account_or_index, key = account_and_key
        account = get_account(account_or_index)
        key_bytes = self._full_key(key)
        lazy_context.ledger.set_local_state(self.app_id, account, key_bytes, None)

    def __contains__(
        self, account_and_key: tuple[algopy.Account | algopy.UInt64 | int, _TKey]
    ) -> bool:
        account_or_index, key = account_and_key
        account = get_account(account_or_index)
        key_bytes = self._full_key(key)
        try:
            lazy_context.ledger.get_local_state(self.app_id, account, key_bytes)
        except KeyError:
            return False
        return True

    def get(
        self, account: algopy.Account | algopy.UInt64 | int, key: _TKey, *, default: _TValue
    ) -> _TValue:
        content, exists = self.maybe(account, key)
        return default if not exists else content

    def maybe(
        self, account: algopy.Account | algopy.UInt64 | int, key: _TKey
    ) -> tuple[_TValue, bool]:
        account = get_account(account)
        key_bytes = self._full_key(key)
        try:
            native = lazy_context.ledger.get_local_state(self.app_id, account, key_bytes)
        except KeyError:
            return cast_from_bytes(self.value_type, b""), False
        return deserialize(self.value_type, native), True

    def state(self, key: _TKey) -> LocalState[_TValue]:
        key_bytes = self._full_key(key)
        ls = LocalState(self.value_type, key=key_bytes)
        ls.app_id = self.app_id
        return ls
