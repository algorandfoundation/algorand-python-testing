from __future__ import annotations

import typing

from algopy_testing.constants import MAX_BOX_SIZE
from algopy_testing.context import get_test_context
from algopy_testing.utils import as_bytes, as_string

_TKey = typing.TypeVar("_TKey")
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
        return context.does_box_exist(self.key)

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key"""
        if not self._key:
            raise ValueError("Box key is empty")
        return self._key

    @property
    def value(self) -> _TValue:
        """Retrieve the contents of the box. Fails if the box has not been created."""
        context = get_test_context()
        if not context.does_box_exist(self.key):
            raise ValueError("Box has not been created")
        return _cast_to_value_type(self._type, context.get_box(self.key))

    @value.setter
    def value(self, value: _TValue) -> None:
        """Write _value_ to the box. Creates the box if it does not exist."""
        context = get_test_context()
        bytes_value = _cast_to_bytes(value)
        context.set_box(self.key, bytes_value)

    @value.deleter
    def value(self) -> None:
        """Delete the box"""
        context = get_test_context()
        context.clear_box(self.key)

    def get(self, *, default: _TValue) -> _TValue:
        """
        Retrieve the contents of the box, or return the default value if the box has not been
        created.

        :arg default: The default value to return if the box has not been created
        """
        box_content, box_exists = self.maybe()
        return default if not box_exists else box_content

    def maybe(self) -> tuple[_TValue, bool]:
        """
        Retrieve the contents of the box if it exists, and return a boolean indicating if the box
        exists.

        """
        context = get_test_context()
        box_exists = context.does_box_exist(self.key)
        box_content_bytes = context.get_box(self.key)
        box_content = _cast_to_value_type(self._type, box_content_bytes)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        """
        Get the length of this Box. Fails if the box does not exist
        """
        import algopy

        context = get_test_context()
        if not context.does_box_exist(self.key):
            raise ValueError("Box has not been created")
        return algopy.UInt64(len(context.get_box(self.key)))


class BoxRef:
    """
    BoxRef abstracts the reading and writing of boxes containing raw binary data. The size is
    configured manually, and can be set to values larger than what the AVM can handle in a single
    value.
    """

    def __init__(self, /, *, key: bytes | str | algopy.Bytes | algopy.String = "") -> None:
        import algopy

        self._key = (
            algopy.String(as_string(key)).bytes
            if isinstance(key, str | algopy.String)
            else algopy.Bytes(as_bytes(key))
        )

    def __bool__(self) -> bool:
        """Returns True if the box has a value set, regardless of the truthiness of that value"""
        context = get_test_context()
        return context.does_box_exist(self.key)

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key"""
        if not self._key:
            raise ValueError("Box key is empty")

        return self._key

    def create(self, *, size: algopy.UInt64 | int) -> bool:
        """
        Creates a box with the specified size, setting all bits to zero. Fails if the box already
        exists with a different size. Fails if the specified size is greater than the max box size
        (32,768)

        Returns True if the box was created, False if the box already existed
        """
        size_int = int(size)
        if size_int > MAX_BOX_SIZE:
            raise ValueError(f"Box size cannot exceed {MAX_BOX_SIZE}")

        box_content, box_exists = self._maybe()
        if box_exists and len(box_content) != size_int:
            raise ValueError("Box already exists with a different size")
        if box_exists:
            return False
        context = get_test_context()
        context.set_box(self.key, b"\x00" * size_int)
        return True

    def delete(self) -> bool:
        """
        Deletes the box if it exists and returns a value indicating if the box existed
        """
        context = get_test_context()
        return context.clear_box(self.key)

    def extract(
        self, start_index: algopy.UInt64 | int, length: algopy.UInt64 | int
    ) -> algopy.Bytes:
        """
        Extract a slice of bytes from the box.

        Fails if the box does not exist, or if `start_index + length > len(box)`

        :arg start_index: The offset to start extracting bytes from
        :arg length: The number of bytes to extract
        """
        import algopy

        box_content, box_exists = self._maybe()
        start_int = int(start_index)
        length_int = int(length)
        if not box_exists:
            raise ValueError("Box does not exist")
        if (start_int + length_int) > len(box_content):
            raise ValueError("Index out of bounds")
        result = box_content[start_int : start_int + length_int]
        return algopy.Bytes(result)

    def resize(self, new_size: algopy.UInt64 | int) -> None:
        """
        Resizes the box the specified `new_size`. Truncating existing data if the new value is
        shorter or padding with zero bytes if it is longer.

        :arg new_size: The new size of the box
        """
        context = get_test_context()
        new_size_int = int(new_size)

        if new_size_int > MAX_BOX_SIZE:
            raise ValueError(f"Box size cannot exceed {MAX_BOX_SIZE}")
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise ValueError("Box has not been created")
        if new_size_int > len(box_content):
            updated_content = box_content + b"\x00" * (new_size_int - len(box_content))
        else:
            updated_content = box_content[:new_size_int]
        context.set_box(self.key, updated_content)

    def replace(self, start_index: algopy.UInt64 | int, value: algopy.Bytes | bytes) -> None:
        """
        Write `value` to the box starting at `start_index`. Fails if the box does not exist,
        or if `start_index + len(value) > len(box)`

        :arg start_index: The offset to start writing bytes from
        :arg value: The bytes to be written
        """
        context = get_test_context()
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise ValueError("Box has not been created")
        start = int(start_index)
        length = len(value)
        if (start + length) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = box_content[:start] + value + box_content[start + length :]
        context.set_box(self.key, updated_content)

    def splice(
        self,
        start_index: algopy.UInt64 | int,
        length: algopy.UInt64 | int,
        value: algopy.Bytes | bytes,
    ) -> None:
        """
        set box to contain its previous bytes up to index `start_index`, followed by `bytes`,
        followed by the original bytes of the box that began at index `start_index + length`

        **Important: This op does not resize the box**
        If the new value is longer than the box size, it will be truncated.
        If the new value is shorter than the box size, it will be padded with zero bytes

        :arg start_index: The index to start inserting `value`
        :arg length: The number of bytes after `start_index` to omit from the new value
        :arg value: The `value` to be inserted.
        """
        import algopy

        context = get_test_context()
        box_content, box_exists = self._maybe()

        start = int(start_index)
        delete_count = int(length)
        insert_content = value.value if isinstance(value, algopy.Bytes) else value

        if not box_exists:
            raise ValueError("Box has not been created")

        if start > len(box_content):
            raise ValueError("Start index exceeds box size")

        # Calculate the end index for deletion
        end = min(start + delete_count, len(box_content))

        # Construct the new content
        new_content = box_content[:start] + insert_content + box_content[end:]

        # Adjust the size if necessary
        if len(new_content) > len(box_content):
            # Truncate if the new content is too long
            new_content = new_content[: len(box_content)]
        elif len(new_content) < len(box_content):
            # Pad with zeros if the new content is too short
            new_content += b"\x00" * (len(box_content) - len(new_content))

        # Update the box with the new content
        context.set_box(self.key, new_content)

    def get(self, *, default: algopy.Bytes | bytes) -> algopy.Bytes:
        """
        Retrieve the contents of the box, or return the default value if the box has not been
        created.

        :arg default: The default value to return if the box has not been created
        """
        import algopy

        box_content, box_exists = self._maybe()
        default_bytes = default if isinstance(default, algopy.Bytes) else algopy.Bytes(default)
        return default_bytes if not box_exists else algopy.Bytes(box_content)

    def put(self, value: algopy.Bytes | bytes) -> None:
        """
        Replaces the contents of box with value. Fails if box exists and len(box) != len(value).
        Creates box if it does not exist

        :arg value: The value to write to the box
        """
        import algopy

        box_content, box_exists = self._maybe()
        if box_exists and len(box_content) != len(value):
            raise ValueError("Box already exists with a different size")

        context = get_test_context()
        content = value if isinstance(value, algopy.Bytes) else algopy.Bytes(value)
        context.set_box(self.key, content)

    def maybe(self) -> tuple[algopy.Bytes, bool]:
        """
        Retrieve the contents of the box if it exists, and return a boolean indicating if the box
        exists.
        """
        import algopy

        box_content, box_exists = self._maybe()
        return algopy.Bytes(box_content), box_exists

    def _maybe(self) -> tuple[bytes, bool]:
        context = get_test_context()
        box_exists = context.does_box_exist(self.key)
        box_content = context.get_box(self.key)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        """
        Get the length of this Box. Fails if the box does not exist
        """
        import algopy

        box_content, box_exists = self._maybe()
        if not box_exists:
            raise ValueError("Box has not been created")
        return algopy.UInt64(len(box_content))


class BoxMap(typing.Generic[_TKey, _TValue]):
    """
    BoxMap abstracts the reading and writing of a set of boxes using a common key and content type.
    Each composite key (prefix + key) still needs to be made available to the application via the
    `boxes` property of the Transaction.
    """

    def __init__(
        self,
        key_type: type[_TKey],
        value_type: type[_TValue],
        /,
        *,
        key_prefix: bytes | str | algopy.Bytes | algopy.String = "",
    ) -> None:
        """Declare a box map.

        :arg key_type: The type of the keys
        :arg value_type: The type of the values
        :arg key_prefix: The value used as a prefix to key data, can be empty.
                         When the BoxMap is being assigned to a member variable,
                         this argument is optional and defaults to the member variable name,
                         and if a custom value is supplied it must be static.
        """
        import algopy

        self._key_type = key_type
        self._value_type = value_type
        self._key_prefix = (
            algopy.String(as_string(key_prefix)).bytes
            if isinstance(key_prefix, str | algopy.String)
            else algopy.Bytes(as_bytes(key_prefix))
        )

    @property
    def key_prefix(self) -> algopy.Bytes:
        """Provides access to the raw storage key-prefix"""
        if not self._key_prefix:
            raise ValueError("Box key prefix is empty")
        return self._key_prefix

    def __getitem__(self, key: _TKey) -> _TValue:
        """
        Retrieve the contents of a keyed box. Fails if the box for the key has not been created.
        """
        box_content, box_exists = self.maybe(key)
        if not box_exists:
            raise ValueError("Box has not been created")
        return box_content

    def __setitem__(self, key: _TKey, value: _TValue) -> None:
        """Write _value_ to a keyed box. Creates the box if it does not exist"""
        context = get_test_context()
        key_bytes = self._full_key(key)
        bytes_value = _cast_to_bytes(value)
        context.set_box(key_bytes, bytes_value)

    def __delitem__(self, key: _TKey) -> None:
        """Deletes a keyed box"""
        context = get_test_context()
        key_bytes = self._full_key(key)
        context.clear_box(key_bytes)

    def __contains__(self, key: _TKey) -> bool:
        """
        Returns True if a box with the specified key exists in the map, regardless of the
        truthiness of the contents of the box
        """
        context = get_test_context()
        key_bytes = self._full_key(key)
        return context.does_box_exist(key_bytes)

    def get(self, key: _TKey, *, default: _TValue) -> _TValue:
        """
        Retrieve the contents of a keyed box, or return the default value if the box has not been
        created.

        :arg key: The key of the box to get
        :arg default: The default value to return if the box has not been created.
        """
        box_content, box_exists = self.maybe(key)
        return default if not box_exists else box_content

    def maybe(self, key: _TKey) -> tuple[_TValue, bool]:
        """
        Retrieve the contents of a keyed box if it exists, and return a boolean indicating if the
        box exists.

        :arg key: The key of the box to get
        """
        context = get_test_context()
        key_bytes = self._full_key(key)
        box_exists = context.does_box_exist(key_bytes)
        box_content_bytes = context.get_box(key_bytes)
        box_content = _cast_to_value_type(self._value_type, box_content_bytes)
        return box_content, box_exists

    def length(self, key: _TKey) -> algopy.UInt64:
        """
        Get the length of an item in this BoxMap. Fails if the box does not exist

        :arg key: The key of the box to get
        """
        import algopy

        context = get_test_context()
        key_bytes = self._full_key(key)
        box_exists = context.does_box_exist(key_bytes)
        if not box_exists:
            raise ValueError("Box has not been created")
        box_content_bytes = context.get_box(key_bytes)
        return algopy.UInt64(len(box_content_bytes))

    def _full_key(self, key: _TKey) -> algopy.Bytes:
        return self.key_prefix + _cast_to_bytes(key)


def _cast_to_value_type(t: type[_TValue], value: bytes) -> _TValue:
    """
    assuming _TValue to be one of the followings:
        - bool,
        - algopy.Bytes,
        - algopy.UInt64
        - algopy.Asset,
        - algopy.Application,
        - algopy.UInt64 enums
        - algopy.arc4.Struct
        - algopy_testing.BytesBacked
            - any type with `from_bytes` class method and `bytes` property
            - .e.g algopy.String, algopy.Address, algopy.arc4.DynamicArray etc.
    """
    import algopy

    context = get_test_context()

    if t is bool:
        return algopy.op.btoi(value) == 1  # type: ignore[return-value]
    elif t is algopy.Bytes:
        return algopy.Bytes(value)  # type: ignore[return-value]
    elif t is algopy.UInt64:
        return algopy.op.btoi(value)  # type: ignore[return-value]
    elif t is algopy.Asset:
        asset_id = algopy.op.btoi(value)
        return context.get_asset(asset_id)  # type: ignore[return-value]
    elif t is algopy.Application:
        application_id = algopy.op.btoi(value)
        return context.get_application(application_id)  # type: ignore[return-value]
    elif hasattr(t, "from_bytes"):
        return t.from_bytes(value)  # type: ignore[attr-defined, no-any-return]

    raise ValueError(f"Unsupported type: {t}")


def _cast_to_bytes(value: _TValue) -> algopy.Bytes:
    """
    assuming _TValue to be one of the followings:
        - bool,
        - algopy.Bytes,
        - algopy.UInt64
        - algopy.Asset,
        - algopy.Application,
        - algopy.UInt64 enums
        - algopy.arc4.Struct
        - algopy_testing.BytesBacked
            - any type with `from_bytes` class method and `bytes` property
            - .e.g algopy.String, algopy.Address, algopy.arc4.DynamicArray etc.
    """
    import algopy

    if isinstance(value, bool):
        return algopy.op.itob(1 if value else 0)
    elif isinstance(value, algopy.Bytes):
        return value
    elif isinstance(value, algopy.UInt64):
        return algopy.op.itob(value)
    elif isinstance(value, algopy.Asset | algopy.Application):
        return algopy.op.itob(value.id)
    elif hasattr(value, "bytes"):
        return typing.cast(algopy.Bytes, value.bytes)

    raise ValueError(f"Unsupported type: {type(value)}")
