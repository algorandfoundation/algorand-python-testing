from __future__ import annotations

import typing

import algopy_testing
from algopy_testing._context_helpers.context_storage import get_test_context
from algopy_testing.constants import MAX_BOX_SIZE
from algopy_testing.state.utils import cast_from_bytes, cast_to_bytes
from algopy_testing.utils import as_bytes, as_string

_TKey = typing.TypeVar("_TKey")
_TValue = typing.TypeVar("_TValue")

if typing.TYPE_CHECKING:
    import algopy


class Box(typing.Generic[_TValue]):
    """Box abstracts the reading and writing of a single value to a single box.

    The box size will be reconfigured dynamically to fit the size of the
    value being assigned to it.
    """

    def __init__(
        self, type_: type[_TValue], /, *, key: bytes | str | algopy.Bytes | algopy.String = ""
    ) -> None:
        self._type = type_

        self._key = (
            algopy_testing.String(as_string(key)).bytes
            if isinstance(key, str | algopy_testing.String)
            else algopy_testing.Bytes(as_bytes(key))
        )

    def __bool__(self) -> bool:
        """Returns True if the box exists, regardless of the truthiness of the
        contents of the box."""
        context = get_test_context()
        return context.ledger.box_exists(self.key)

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key."""
        if not self._key:
            raise RuntimeError("Box key is empty")
        return self._key

    @property
    def value(self) -> _TValue:
        """Retrieve the contents of the box.

        Fails if the box has not been created.
        """
        context = get_test_context()
        if not context.ledger.box_exists(self.key):
            raise RuntimeError("Box has not been created")
        # TODO: 1.0 will need to use a proxy here too for mutable types
        return cast_from_bytes(self._type, context.ledger.get_box(self.key))

    @value.setter
    def value(self, value: _TValue) -> None:
        """Write _value_ to the box.

        Creates the box if it does not exist.
        """
        context = get_test_context()
        bytes_value = cast_to_bytes(value)
        context.ledger.set_box(self.key, bytes_value)

    @value.deleter
    def value(self) -> None:
        """Delete the box."""
        context = get_test_context()
        context.ledger.delete_box(self.key)

    def get(self, *, default: _TValue) -> _TValue:
        """Retrieve the contents of the box, or return the default value if the
        box has not been created.

        :arg default: The default value to return if the box has not
        been created
        """
        box_content, box_exists = self.maybe()
        return default if not box_exists else box_content

    def maybe(self) -> tuple[_TValue, bool]:
        """Retrieve the contents of the box if it exists, and return a boolean
        indicating if the box exists."""
        context = get_test_context()
        box_exists = context.ledger.box_exists(self.key)
        box_content_bytes = context.ledger.get_box(self.key)
        box_content = cast_from_bytes(self._type, box_content_bytes)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        """Get the length of this Box.

        Fails if the box does not exist
        """
        context = get_test_context()
        if not context.ledger.box_exists(self.key):
            raise RuntimeError("Box has not been created")
        return algopy_testing.UInt64(len(context.ledger.get_box(self.key)))


class BoxRef:
    """BoxRef abstracts the reading and writing of boxes containing raw binary
    data.

    The size is configured manually, and can be set to values larger
    than what the AVM can handle in a single value.
    """

    def __init__(self, /, *, key: bytes | str | algopy.Bytes | algopy.String = "") -> None:
        self._key = (
            algopy_testing.String(as_string(key)).bytes
            if isinstance(key, str | algopy_testing.String)
            else algopy_testing.Bytes(as_bytes(key))
        )

    def __bool__(self) -> bool:
        """Returns True if the box has a value set, regardless of the
        truthiness of that value."""
        context = get_test_context()
        return context.ledger.box_exists(self.key)

    @property
    def key(self) -> algopy.Bytes:
        """Provides access to the raw storage key."""
        if not self._key:
            raise RuntimeError("Box key is empty")

        return self._key

    def create(self, *, size: algopy.UInt64 | int) -> bool:
        """Creates a box with the specified size, setting all bits to zero.
        Fails if the box already exists with a different size. Fails if the
        specified size is greater than the max box size (32,768)

        Returns True if the box was created, False if the box already
        existed
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
        context.ledger.set_box(self.key, b"\x00" * size_int)
        return True

    def delete(self) -> bool:
        """Deletes the box if it exists and returns a value indicating if the
        box existed."""
        context = get_test_context()
        return context.ledger.delete_box(self.key)

    def extract(
        self, start_index: algopy.UInt64 | int, length: algopy.UInt64 | int
    ) -> algopy.Bytes:
        """Extract a slice of bytes from the box.

        Fails if the box does not exist, or if `start_index + length >
        len(box)`

        :arg start_index: The offset to start extracting bytes from :arg
        length: The number of bytes to extract
        """
        box_content, box_exists = self._maybe()
        start_int = int(start_index)
        length_int = int(length)
        if not box_exists:
            raise RuntimeError("Box has not been created")
        if (start_int + length_int) > len(box_content):
            raise ValueError("Index out of bounds")
        result = box_content[start_int : start_int + length_int]
        return algopy_testing.Bytes(result)

    def resize(self, new_size: algopy.UInt64 | int) -> None:
        """Resizes the box the specified `new_size`. Truncating existing data
        if the new value is shorter or padding with zero bytes if it is longer.

        :arg new_size: The new size of the box
        """
        context = get_test_context()
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
        context.ledger.set_box(self.key, updated_content)

    def replace(self, start_index: algopy.UInt64 | int, value: algopy.Bytes | bytes) -> None:
        """Write `value` to the box starting at `start_index`. Fails if the box
        does not exist, or if `start_index + len(value) > len(box)`

        :arg start_index: The offset to start writing bytes from :arg
        value: The bytes to be written
        """
        context = get_test_context()
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise RuntimeError("Box has not been created")
        start = int(start_index)
        length = len(value)
        if (start + length) > len(box_content):
            raise ValueError("Replacement content exceeds box size")
        updated_content = box_content[:start] + value + box_content[start + length :]
        context.ledger.set_box(self.key, updated_content)

    def splice(
        self,
        start_index: algopy.UInt64 | int,
        length: algopy.UInt64 | int,
        value: algopy.Bytes | bytes,
    ) -> None:
        """Set box to contain its previous bytes up to index `start_index`,
        followed by `bytes`, followed by the original bytes of the box that
        began at index `start_index + length`

        **Important: This op does not resize the box**
        If the new value is longer than the box size, it will be truncated.
        If the new value is shorter than the box size, it will be padded with zero bytes

        :arg start_index: The index to start inserting `value`
        :arg length: The number of bytes after `start_index` to omit from the new value
        :arg value: The `value` to be inserted.
        """
        context = get_test_context()
        box_content, box_exists = self._maybe()

        start = int(start_index)
        delete_count = int(length)
        insert_content = value.value if isinstance(value, algopy_testing.Bytes) else value

        if not box_exists:
            raise RuntimeError("Box has not been created")

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
        context.ledger.set_box(self.key, new_content)

    def get(self, *, default: algopy.Bytes | bytes) -> algopy.Bytes:
        """Retrieve the contents of the box, or return the default value if the
        box has not been created.

        :arg default: The default value to return if the box has not
        been created
        """

        box_content, box_exists = self._maybe()
        default_bytes = (
            default if isinstance(default, algopy_testing.Bytes) else algopy_testing.Bytes(default)
        )
        return default_bytes if not box_exists else algopy_testing.Bytes(box_content)

    def put(self, value: algopy.Bytes | bytes) -> None:
        """Replaces the contents of box with value. Fails if box exists and
        len(box) != len(value). Creates box if it does not exist.

        :arg value: The value to write to the box
        """
        box_content, box_exists = self._maybe()
        if box_exists and len(box_content) != len(value):
            raise ValueError("Box already exists with a different size")

        context = get_test_context()
        content = value if isinstance(value, algopy_testing.Bytes) else algopy_testing.Bytes(value)
        context.ledger.set_box(self.key, content)

    def maybe(self) -> tuple[algopy.Bytes, bool]:
        """Retrieve the contents of the box if it exists, and return a boolean
        indicating if the box exists."""
        box_content, box_exists = self._maybe()
        return algopy_testing.Bytes(box_content), box_exists

    def _maybe(self) -> tuple[bytes, bool]:
        context = get_test_context()
        box_exists = context.ledger.box_exists(self.key)
        box_content = context.ledger.get_box(self.key)
        return box_content, box_exists

    @property
    def length(self) -> algopy.UInt64:
        """Get the length of this Box.

        Fails if the box does not exist
        """
        box_content, box_exists = self._maybe()
        if not box_exists:
            raise RuntimeError("Box has not been created")
        return algopy_testing.UInt64(len(box_content))


class BoxMap(typing.Generic[_TKey, _TValue]):
    """BoxMap abstracts the reading and writing of a set of boxes using a
    common key and content type.

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
        """Declare a box map.

        :arg key_type: The type of the keys :arg value_type: The type of
        the values :arg key_prefix: The value used as a prefix to key
        data, can be empty.                  When the BoxMap is being
        assigned to a member variable,                  this argument is
        optional and defaults to the member variable name, and if a
        custom value is supplied it must be static.
        """
        self._key_type = key_type
        self._value_type = value_type
        match key_prefix:
            case None:
                self._key_prefix = None
            case bytes(key) | algopy_testing.Bytes(value=key):
                self._key_prefix = algopy_testing.Bytes(key)
            case str(key_str) | algopy_testing.String(value=key_str):
                self._key_prefix = algopy_testing.Bytes(key_str.encode("utf8"))
            case _:
                typing.assert_never(key_prefix)

    @property
    def key_prefix(self) -> algopy.Bytes:
        """Provides access to the raw storage key-prefix."""
        # empty bytes is a valid key prefix, so check for None explicitly
        if self._key_prefix is None:
            raise RuntimeError("Box key prefix is not defined")
        return self._key_prefix

    def __getitem__(self, key: _TKey) -> _ProxyValue:
        """Retrieve the contents of a keyed box.

        Fails if the box for the key has not been created.
        """
        box_content, box_exists = self.maybe(key)
        if not box_exists:
            raise RuntimeError("Box has not been created")
        return _ProxyValue(self, key, box_content)

    def __setitem__(self, key: _TKey, value: _TValue) -> None:
        """Write _value_ to a keyed box.

        Creates the box if it does not exist
        """
        context = get_test_context()
        key_bytes = self._full_key(key)
        bytes_value = cast_to_bytes(value)
        context.ledger.set_box(key_bytes, bytes_value)

    def __delitem__(self, key: _TKey) -> None:
        """Deletes a keyed box."""
        context = get_test_context()
        key_bytes = self._full_key(key)
        context.ledger.delete_box(key_bytes)

    def __contains__(self, key: _TKey) -> bool:
        """Returns True if a box with the specified key exists in the map,
        regardless of the truthiness of the contents of the box."""
        context = get_test_context()
        key_bytes = self._full_key(key)
        return context.ledger.box_exists(key_bytes)

    def get(self, key: _TKey, *, default: _TValue) -> _TValue:
        """Retrieve the contents of a keyed box, or return the default value if
        the box has not been created.

        :arg key: The key of the box to get :arg default: The default
        value to return if the box has not been created.
        """
        box_content, box_exists = self.maybe(key)
        return default if not box_exists else box_content

    def maybe(self, key: _TKey) -> tuple[_TValue, bool]:
        """Retrieve the contents of a keyed box if it exists, and return a
        boolean indicating if the box exists.

        :arg key: The key of the box to get
        """
        context = get_test_context()
        key_bytes = self._full_key(key)
        box_exists = context.ledger.box_exists(key_bytes)
        if not box_exists:
            return self._value_type(), False
        box_content_bytes = context.ledger.get_box(key_bytes)
        box_content = cast_from_bytes(self._value_type, box_content_bytes)
        return box_content, box_exists

    def length(self, key: _TKey) -> algopy.UInt64:
        """Get the length of an item in this BoxMap. Fails if the box does not
        exist.

        :arg key: The key of the box to get
        """
        context = get_test_context()
        key_bytes = self._full_key(key)
        box_exists = context.ledger.box_exists(key_bytes)
        if not box_exists:
            raise RuntimeError("Box has not been created")
        box_content_bytes = context.ledger.get_box(key_bytes)
        return algopy_testing.UInt64(len(box_content_bytes))

    def _full_key(self, key: _TKey) -> algopy.Bytes:
        return self.key_prefix + cast_to_bytes(key)


# TODO: 1.0 using this proxy will mean other parts of the library that do isinstance will not be
#       correct. To solve this need to do the following
#       1.) only use the proxy if the value is mutable, currently this means only
#           ARC Arrays, Tuples and structs should need this proxy
#       2.) modify the metaclass of the above types to ensure they still pass the appropriate
#           isinstance checks, when a ProxyValue is being used
#           see https://docs.python.org/3.12/reference/datamodel.html#customizing-instance-and-subclass-checks
class _ProxyValue:
    """Allows mutating attributes of objects retrieved from a BoxMap."""

    def __init__(self, box_map: BoxMap[_TKey, _TValue], key: _TKey, value: _TValue) -> None:
        self._box_map = box_map
        self._key = key
        self._value = value

    def __getattr__(self, name: str) -> typing.Any:
        return getattr(self._value, name)

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if name.startswith("_"):
            super().__setattr__(name, value)
        else:
            new_value = self._value.__class__(**{**self._value.__dict__, name: value})
            self._box_map[self._key] = new_value
            self._value = new_value

    def __repr__(self) -> str:
        return repr(self._value)
