from __future__ import annotations

import typing
import warnings

from typing_extensions import deprecated

import _algopy_testing
from _algopy_testing.constants import MAX_BOX_SIZE
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.mutable import set_attr_on_mutate, set_item_on_mutate
from _algopy_testing.state.utils import cast_from_bytes, cast_to_bytes
from _algopy_testing.utils import as_bytes, as_int64, as_string, get_static_size_of

_TKey = typing.TypeVar("_TKey")
_TValue = typing.TypeVar("_TValue")

if typing.TYPE_CHECKING:
    import algopy


class Box(typing.Generic[_TValue]):
    """Box abstracts the reading and writing of a single value to a single box.

    The box size will be reconfigured dynamically to fit the size of the value being
    assigned to it.
    """

    def __init__(
        self, type_: type[_TValue], /, *, key: bytes | str | algopy.Bytes | algopy.String = ""
    ) -> None:
        self._type = type_

        self._key = (
            _algopy_testing.String(as_string(key)).bytes
            if isinstance(key, str | _algopy_testing.String)
            else _algopy_testing.Bytes(as_bytes(key))
        )
        self.app_id = lazy_context.active_app_id

    def __bool__(self) -> bool:
        return lazy_context.ledger.box_exists(self.app_id, self.key)

    def create(self, *, size: algopy.UInt64 | int | None = None) -> bool:
        missing_size_err_msg = (
            f"{self._type} does not have a fixed byte size. Please specify a size argument"
        )

        size_arg = None if size is None else as_int64(size)
        content_type_size = get_static_size_of(self._type)

        if content_type_size is None and size_arg is None:
            raise ValueError(missing_size_err_msg)
        if content_type_size is not None and size_arg is not None:
            if size_arg < content_type_size:
                warnings.warn(
                    f"Box size should not be less than {content_type_size}",
                    stacklevel=2,
                )

            if size_arg > content_type_size:
                warnings.warn(
                    f"Size is set to {size_arg} but {self._type} has a fixed size of {content_type_size}",  # noqa: E501
                    stacklevel=2,
                )

        size_int = size_arg if size_arg is not None else content_type_size
        assert size_int is not None, missing_size_err_msg

        if size_int > MAX_BOX_SIZE:
            raise ValueError(f"Box size cannot exceed {MAX_BOX_SIZE}")

        box_exists = lazy_context.ledger.box_exists(self.app_id, self.key)
        if box_exists:
            if self.length == size_int:
                return False
            else:
                raise ValueError(f"Box already exists with a different size: {self.length}")

        lazy_context.ledger.set_box(self.app_id, self.key, b"\x00" * size_int)
        return True

    @property
    def key(self) -> algopy.Bytes:
        if not self._key:
            raise RuntimeError("Box key is empty")
        return self._key

    @property
    def value(self) -> _TValue:
        if not lazy_context.ledger.box_exists(self.app_id, self.key):
            raise RuntimeError("Box has not been created")
        value = cast_from_bytes(self._type, lazy_context.ledger.get_box(self.app_id, self.key))
        return set_attr_on_mutate(self, "value", value)

    @value.setter
    def value(self, value: _TValue) -> None:
        bytes_value = cast_to_bytes(value)
        lazy_context.ledger.set_box(self.app_id, self.key, bytes_value)

    @value.deleter
    def value(self) -> None:
        lazy_context.ledger.delete_box(self.app_id, self.key)

    @property
    @deprecated("Box methods previously accessed via `.ref` are now directly available")
    def ref(self) -> BoxRef:
        return BoxRef(key=self.key)

    def extract(
        self, start_index: algopy.UInt64 | int, length: algopy.UInt64 | int
    ) -> algopy.Bytes:
        """Extract a slice of bytes from the box.

        Fails if the box does not exist, or if `start_index + length > len(box)`

        :arg start_index: The offset to start extracting bytes from
        :arg length: The number of bytes to extract
        :return: The extracted bytes
        """
        return _BoxRef(key=self.key).extract(start_index, length)

    def resize(self, new_size: algopy.UInt64 | int) -> None:
        """Resizes the box the specified `new_size`. Truncating existing data if the new
        value is shorter or padding with zero bytes if it is longer.

        :arg new_size: The new size of the box
        """
        return _BoxRef(key=self.key).resize(new_size)

    def replace(self, start_index: algopy.UInt64 | int, value: algopy.Bytes | bytes) -> None:
        """Write `value` to the box starting at `start_index`. Fails if the box does not
        exist, or if `start_index + len(value) > len(box)`

        :arg start_index: The offset to start writing bytes from
        :arg value: The bytes to be written
        """
        return _BoxRef(key=self.key).replace(start_index, value)

    def splice(
        self,
        start_index: algopy.UInt64 | int,
        length: algopy.UInt64 | int,
        value: algopy.Bytes | bytes,
    ) -> None:
        """Set box to contain its previous bytes up to index `start_index`, followed by
        `bytes`, followed by the original bytes of the box that began at index
        `start_index + length`

        **Important: This op does not resize the box**
        If the new value is longer than the box size, it will be truncated.
        If the new value is shorter than the box size, it will be padded with zero bytes

        :arg start_index: The index to start inserting `value`
        :arg length: The number of bytes after `start_index` to omit from the new value
        :arg value: The `value` to be inserted.
        """
        return _BoxRef(key=self.key).splice(start_index, length, value)

    def get(self, *, default: _TValue) -> _TValue:
        box_content, box_exists = self.maybe()
        return default if not box_exists else box_content

    def maybe(self) -> tuple[_TValue, bool]:
        box_exists = lazy_context.ledger.box_exists(self.app_id, self.key)
        box_content_bytes = lazy_context.ledger.get_box(self.app_id, self.key)
        box_content = cast_from_bytes(self._type, box_content_bytes)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        if not lazy_context.ledger.box_exists(self.app_id, self.key):
            raise RuntimeError("Box has not been created")
        return _algopy_testing.UInt64(len(lazy_context.ledger.get_box(self.app_id, self.key)))


class _BoxRef:
    """BoxRef abstracts the reading and writing of boxes containing raw binary data.

    The size is configured manually, and can be set to values larger than what the AVM
    can handle in a single value.
    """

    def __init__(self, /, *, key: bytes | str | algopy.Bytes | algopy.String = "") -> None:
        self._key = (
            _algopy_testing.String(as_string(key)).bytes
            if isinstance(key, str | _algopy_testing.String)
            else _algopy_testing.Bytes(as_bytes(key))
        )
        self.app_id = lazy_context.active_app_id

    def __bool__(self) -> bool:
        return lazy_context.ledger.box_exists(self.app_id, self.key)

    @property
    def key(self) -> algopy.Bytes:
        if not self._key:
            raise RuntimeError("Box key is empty")

        return self._key

    def create(self, *, size: algopy.UInt64 | int) -> bool:
        size_int = int(size)
        if size_int > MAX_BOX_SIZE:
            raise ValueError(f"Box size cannot exceed {MAX_BOX_SIZE}")

        box_content, box_exists = self._maybe()
        if box_exists and len(box_content) != size_int:
            raise ValueError("Box already exists with a different size")
        if box_exists:
            return False
        lazy_context.ledger.set_box(self.app_id, self.key, b"\x00" * size_int)
        return True

    def delete(self) -> bool:
        return lazy_context.ledger.delete_box(self.app_id, self.key)

    def extract(
        self, start_index: algopy.UInt64 | int, length: algopy.UInt64 | int
    ) -> algopy.Bytes:
        box_content, box_exists = self._maybe()
        start_int = int(start_index)
        length_int = int(length)
        if not box_exists:
            raise RuntimeError("Box has not been created")
        if (start_int + length_int) > len(box_content):
            raise ValueError("Index out of bounds")
        result = box_content[start_int : start_int + length_int]
        return _algopy_testing.Bytes(result)

    def resize(self, new_size: algopy.UInt64 | int) -> None:
        new_size_int = int(new_size)

        if new_size_int > MAX_BOX_SIZE:
            raise ValueError(f"Box size cannot exceed {MAX_BOX_SIZE}")
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise RuntimeError("Box has not been created")
        if new_size_int > len(box_content):
            updated_content = box_content + b"\x00" * (new_size_int - len(box_content))
        else:
            updated_content = box_content[:new_size_int]
        lazy_context.ledger.set_box(self.app_id, self.key, updated_content)

    def replace(self, start_index: algopy.UInt64 | int, value: algopy.Bytes | bytes) -> None:
        replace_content = value.value if isinstance(value, _algopy_testing.Bytes) else value
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise RuntimeError("Box has not been created")
        start = int(start_index)
        length = len(replace_content)
        if (start + length) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = box_content[:start] + replace_content + box_content[start + length :]
        lazy_context.ledger.set_box(self.app_id, self.key, updated_content)

    def splice(
        self,
        start_index: algopy.UInt64 | int,
        length: algopy.UInt64 | int,
        value: algopy.Bytes | bytes,
    ) -> None:
        box_content, box_exists = self._maybe()

        start = int(start_index)
        delete_count = int(length)
        insert_content = value.value if isinstance(value, _algopy_testing.Bytes) else value

        if not box_exists:
            raise RuntimeError("Box has not been created")

        if start > len(box_content):
            raise ValueError("Start index exceeds box size")

        end = min(start + delete_count, len(box_content))
        new_content = box_content[:start] + insert_content + box_content[end:]

        if len(new_content) > len(box_content):
            new_content = new_content[: len(box_content)]
        elif len(new_content) < len(box_content):
            new_content += b"\x00" * (len(box_content) - len(new_content))

        lazy_context.ledger.set_box(self.app_id, self.key, new_content)

    def get(self, *, default: algopy.Bytes | bytes) -> algopy.Bytes:
        box_content, box_exists = self._maybe()
        default_bytes = (
            default
            if isinstance(default, _algopy_testing.Bytes)
            else _algopy_testing.Bytes(default)
        )
        return default_bytes if not box_exists else _algopy_testing.Bytes(box_content)

    def put(self, value: algopy.Bytes | bytes) -> None:
        box_content, box_exists = self._maybe()
        if box_exists and len(box_content) != len(value):
            raise ValueError("Box already exists with a different size")

        content = (
            value if isinstance(value, _algopy_testing.Bytes) else _algopy_testing.Bytes(value)
        )
        lazy_context.ledger.set_box(self.app_id, self.key, content)

    def maybe(self) -> tuple[algopy.Bytes, bool]:
        box_content, box_exists = self._maybe()
        return _algopy_testing.Bytes(box_content), box_exists

    def _maybe(self) -> tuple[bytes, bool]:
        box_exists = lazy_context.ledger.box_exists(self.app_id, self.key)
        box_content = lazy_context.ledger.get_box(self.app_id, self.key)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise RuntimeError("Box has not been created")
        return _algopy_testing.UInt64(len(box_content))


@deprecated("Methods in BoxRef are now directly available on Box")
class BoxRef(_BoxRef):
    pass


class BoxMap(typing.Generic[_TKey, _TValue]):
    """BoxMap abstracts the reading and writing of a set of boxes using a common key and
    content type.

    Each composite key (prefix + key) still needs to be made available to the application via the
    `boxes` property of the Transaction.
    """

    def __init__(
        self,
        key_type: type[_TKey],
        value_type: type[_TValue],
        /,
        *,
        key_prefix: bytes | str | algopy.Bytes | algopy.String | None = None,
    ) -> None:
        self._key_type = key_type
        self._value_type = value_type
        match key_prefix:
            case None:
                self._key_prefix = None
            case bytes(key) | _algopy_testing.Bytes(value=key):
                self._key_prefix = _algopy_testing.Bytes(key)
            case str(key_str) | _algopy_testing.String(value=key_str):
                self._key_prefix = _algopy_testing.Bytes(key_str.encode("utf8"))
            case _:
                typing.assert_never(key_prefix)
        self.app_id = lazy_context.active_app_id

    @property
    def key_prefix(self) -> algopy.Bytes:
        if self._key_prefix is None:
            raise RuntimeError("Box key prefix is not defined")
        return self._key_prefix

    def __getitem__(self, key: _TKey) -> _TValue:
        box_content, box_exists = self.maybe(key)
        if not box_exists:
            raise RuntimeError("Box has not been created")

        return set_item_on_mutate(self, key, box_content)

    def __setitem__(self, key: _TKey, value: _TValue) -> None:
        key_bytes = self._full_key(key)
        bytes_value = cast_to_bytes(value)
        lazy_context.ledger.set_box(self.app_id, key_bytes, bytes_value)

    def __delitem__(self, key: _TKey) -> None:
        key_bytes = self._full_key(key)
        lazy_context.ledger.delete_box(self.app_id, key_bytes)

    def __contains__(self, key: _TKey) -> bool:
        key_bytes = self._full_key(key)
        return lazy_context.ledger.box_exists(self.app_id, key_bytes)

    def get(self, key: _TKey, *, default: _TValue) -> _TValue:
        box_content, box_exists = self.maybe(key)
        return default if not box_exists else box_content

    def maybe(self, key: _TKey) -> tuple[_TValue, bool]:
        key_bytes = self._full_key(key)
        box_exists = lazy_context.ledger.box_exists(self.app_id, key_bytes)
        box_content_bytes = (
            b"" if not box_exists else lazy_context.ledger.get_box(self.app_id, key_bytes)
        )
        box_content = cast_from_bytes(self._value_type, box_content_bytes)
        return box_content, box_exists

    def length(self, key: _TKey) -> algopy.UInt64:
        key_bytes = self._full_key(key)
        box_exists = lazy_context.ledger.box_exists(self.app_id, key_bytes)
        if not box_exists:
            raise RuntimeError("Box has not been created")
        box_content_bytes = lazy_context.ledger.get_box(self.app_id, key_bytes)
        return _algopy_testing.UInt64(len(box_content_bytes))

    def _full_key(self, key: _TKey) -> algopy.Bytes:
        return self.key_prefix + cast_to_bytes(key)

    def box(self, key: _TKey) -> Box[_TValue]:
        """Returns a Box holding the box value at key."""
        key_bytes = self._full_key(key)
        return Box(self._value_type, key=key_bytes)
