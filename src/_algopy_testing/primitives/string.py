from __future__ import annotations

from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import as_bytes, as_string, check_type


class String(BytesBacked):
    """Represents a UTF-8 encoded string backed by Bytes, accessible via .bytes.

    Works with str literals instead of bytes literals. Due to lack of AVM support for
    unicode, indexing and length operations are not supported. Use .bytes.length for
    byte length.
    """

    _value: bytes  # underlying 'bytes' value representing the String

    def __init__(self, value: str = "") -> None:
        check_type(value, str)
        self._value = value.encode("utf-8")

    def __repr__(self) -> str:
        return repr(self.value)

    def __str__(self) -> str:
        return str(self.value)

    def __bool__(self) -> bool:
        return bool(self.value)

    def __eq__(self, other: object) -> bool:
        try:
            other_string = as_string(other)
        except TypeError:
            return NotImplemented
        return self.value == other_string

    def __contains__(self, item: object) -> bool:
        return as_string(item) in self.value

    def __add__(self, other: String | str) -> String:
        return String(self.value + as_string(other))

    def __radd__(self, other: String | str) -> String:
        return String(as_string(other) + self.value)

    def startswith(self, prefix: String | str) -> bool:
        return self.value.startswith(as_string(prefix))

    def endswith(self, suffix: String | str) -> bool:
        return self.value.endswith(as_string(suffix))

    def join(self, others: tuple[String, ...], /) -> String:
        return String(self.value.join(map(as_string, others)))

    @classmethod
    def from_bytes(cls, value: Bytes | bytes) -> String:
        """Construct an instance from the underlying bytes (no validation)"""
        value = as_bytes(value)
        result = cls()
        result._value = bytes(value)
        return result

    @property
    def bytes(self) -> Bytes:
        """Get the underlying Bytes."""
        return Bytes(self._value)

    @property
    def value(self) -> str:
        return self._value.decode("utf-8")
