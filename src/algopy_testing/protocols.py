from __future__ import annotations

import typing

if typing.TYPE_CHECKING:
    import algopy


class BytesBacked:
    """Represents a type that is a single bytes value."""

    @classmethod
    def from_bytes(cls, value: algopy.Bytes | bytes, /) -> typing.Self:
        """Construct an instance from the underlying bytes (no validation)"""
        raise NotImplementedError

    @property
    def bytes(self) -> algopy.Bytes:
        """Get the underlying Bytes."""
        raise NotImplementedError
