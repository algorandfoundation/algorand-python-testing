from __future__ import annotations

import typing

from algopy_testing._context_helpers import lazy_context
from algopy_testing.models import Account
from algopy_testing.primitives import Bytes, String
from algopy_testing.state.utils import deserialize, serialize

if typing.TYPE_CHECKING:
    import algopy


_T = typing.TypeVar("_T")


class LocalState(typing.Generic[_T]):
    def __init__(
        self,
        type_: type[_T],
        /,
        *,
        key: Bytes | String | bytes | str = "",
        description: str = "",
    ) -> None:
        self.app_id = lazy_context.active_group.active_app_id
        self.type_ = type_
        if key == "":
            self._key: algopy.Bytes = Bytes()
        else:
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
        self.description = description

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key."""
        return self._key

    def __setitem__(self, key: algopy.Account | algopy.UInt64 | int, value: _T) -> None:
        account = _get_account(key)
        app_data = lazy_context.get_app_data(self.app_id)
        app_data.set_local_state(account, self._key.value, serialize(value))

    def __getitem__(self, key: algopy.Account | algopy.UInt64 | int) -> _T:
        account = _get_account(key)
        app_data = lazy_context.get_app_data(self.app_id)
        native = app_data.get_local_state(account, self._key.value)
        return deserialize(self.type_, native)

    def __delitem__(self, key: algopy.Account | algopy.UInt64 | int) -> None:
        account = _get_account(key)
        app_data = lazy_context.get_app_data(self.app_id)
        app_data.set_local_state(account, self._key.value, None)

    def __contains__(self, key: algopy.Account | algopy.UInt64 | int) -> bool:
        account = _get_account(key)
        app_data = lazy_context.get_app_data(self.app_id)
        try:
            app_data.get_local_state(account, self._key.value)
        except KeyError:
            return False
        return True

    def get(self, key: algopy.Account | algopy.UInt64 | int, default: _T | None = None) -> _T:
        account = _get_account(key)
        try:
            return self[account]
        except KeyError:
            return default if default is not None else self.type_()

    def maybe(self, key: algopy.Account | algopy.UInt64 | int) -> tuple[_T, bool]:
        account = _get_account(key)
        try:
            return self[account], True
        except KeyError:
            return self.type_(), False


# TODO: make a util function along with one used by ops
def _get_account(account_or_index: algopy.Account | algopy.UInt64 | int) -> algopy.Account:
    if isinstance(account_or_index, Account):
        return account_or_index
    txn = lazy_context.active_group.active_txn
    return txn.accounts(account_or_index)
