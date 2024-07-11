from __future__ import annotations

import secrets
import typing

from algopy_testing.context import get_test_context
from algopy_testing.utils import as_bytes, as_string

_TValue = typing.TypeVar("_TValue")

if typing.TYPE_CHECKING:
    import algopy


class Box(typing.Generic[_TValue]):
    """
    Box abstracts the reading and writing of a single value to a single box.
    The box size will be reconfigured dynamically to fit the size of the value being assigned to
    it.
    """

    def __init__(
        self, type_: type[_TValue], /, *, key: bytes | str | algopy.Bytes | algopy.String = ""
    ) -> None:
        import algopy

        self._type = type_

        # if key parameter is empty string, generate a random 32 bytes for key
        if isinstance(key, str) and key == "":
            self._key = algopy.Bytes(secrets.token_bytes(32))
        else:
            self._key = (
                algopy.String(as_string(key)).bytes
                if isinstance(key, str | algopy.String)
                else algopy.Bytes(as_bytes(key))
            )

    def __bool__(self) -> bool:
        """
        Returns True if the box exists, regardless of the truthiness of the contents
        of the box
        """
        context = get_test_context()
        return context.does_box_exist(self._key)

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key"""
        return self._key

    @property
    def value(self) -> _TValue:
        """Retrieve the contents of the box. Fails if the box has not been created."""
        context = get_test_context()
        if not context.does_box_exist(self._key):
            raise ValueError("Box has not been created")
        return self._cast_to_type(context.get_box(self._key))

    @value.setter
    def value(self, value: _TValue) -> None:
        """Write _value_ to the box. Creates the box if it does not exist."""
        context = get_test_context()
        bytes_value = self._cast_to_bytes(value)
        context.set_box(self._key, bytes_value)

    @value.deleter
    def value(self) -> None:
        """Delete the box"""
        context = get_test_context()
        context.clear_box(self._key)

    def get(self, *, default: _TValue) -> _TValue:
        """
        Retrieve the contents of the box, or return the default value if the box has not been
        created.

        :arg default: The default value to return if the box has not been created
        """
        context = get_test_context()
        return (
            default
            if not context.does_box_exist(self._key)
            else self._cast_to_type(context.get_box(self._key))
        )

    def maybe(self) -> tuple[_TValue, bool]:
        """
        Retrieve the contents of the box if it exists, and return a boolean indicating if the box
        exists.

        """
        context = get_test_context()
        return self._cast_to_type(context.get_box(self._key)), context.does_box_exist(self._key)

    @property
    def length(self) -> algopy.UInt64:
        """
        Get the length of this Box. Fails if the box does not exist
        """
        import algopy

        context = get_test_context()
        if not context.does_box_exist(self._key):
            raise ValueError("Box has not been created")
        return algopy.UInt64(len(context.get_box(self._key)))

    def _cast_to_type(self, value: algopy.Bytes) -> _TValue:
        """
        assuming _TValue to be one of the followings:
            - algopy.UInt64
            - algopy.Bytes
            - algopy_testing.BytesBacked
                - any type with `from_bytes` class method and `bytes` property
                - .e.g algopy.String, algopy.Address, algopy.arc4.DynamicArray etc.
        """
        import algopy

        if hasattr(self._type, "from_bytes"):
            return typing.cast(_TValue, self._type.from_bytes(value))  # type: ignore[attr-defined]
        elif self._type is algopy.UInt64:
            return typing.cast(_TValue, algopy.op.btoi(value))
        return typing.cast(_TValue, value)

    def _cast_to_bytes(self, value: _TValue) -> algopy.Bytes:
        """
        assuming _TValue to be one of the followings:
            - algopy.UInt64
            - algopy.Bytes
            - algopy_testing.BytesBacked
                - any type with `from_bytes` class method and `bytes` property
                - .e.g algopy.String, algopy.Address, algopy.arc4.DynamicArray etc.
        """

        import algopy

        if hasattr(value, "bytes"):
            return typing.cast(algopy.Bytes, value.bytes)
        elif isinstance(value, algopy.UInt64):
            return algopy.op.itob(value)
        return typing.cast(algopy.Bytes, value)
