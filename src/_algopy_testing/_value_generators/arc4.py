from __future__ import annotations

import secrets
import string
import typing

import algosdk

from _algopy_testing import arc4
from _algopy_testing.constants import MAX_UINT8, MAX_UINT16, MAX_UINT32, MAX_UINT64, MAX_UINT512
from _algopy_testing.utils import generate_random_int

if typing.TYPE_CHECKING:
    import algopy


class ARC4ValueGenerator:
    """Factory for generating ARC4-compliant test data."""

    def address(self) -> algopy.arc4.Address:
        """Generate a random Algorand address.

        :returns: A new, random Algorand address.
        """

        return arc4.Address(algosdk.account.generate_account()[1])

    def uint8(self, min_value: int = 0, max_value: int = MAX_UINT8) -> algopy.arc4.UInt8:
        """Generate a random UInt8 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to MAX_UINT8.
        :returns: A random UInt8 value.
        """
        return arc4.UInt8(generate_random_int(min_value, max_value))

    def uint16(self, min_value: int = 0, max_value: int = MAX_UINT16) -> algopy.arc4.UInt16:
        """Generate a random UInt16 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to MAX_UINT16.
        :returns: A random UInt16 value.
        """
        return arc4.UInt16(generate_random_int(min_value, max_value))

    def uint32(self, min_value: int = 0, max_value: int = MAX_UINT32) -> algopy.arc4.UInt32:
        """Generate a random UInt32 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to MAX_UINT32.
        :returns: A random UInt32 value.
        """
        return arc4.UInt32(generate_random_int(min_value, max_value))

    def uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.arc4.UInt64:
        """Generate a random UInt64 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to MAX_UINT64.
        :returns: A random UInt64 value.
        """
        return arc4.UInt64(generate_random_int(min_value, max_value))

    def biguint128(
        self, min_value: int = 0, max_value: int = (1 << 128) - 1
    ) -> algopy.arc4.UInt128:
        """Generate a random UInt128 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to (2^128 - 1).
        :returns: A random UInt128 value.
        """
        return arc4.UInt128(generate_random_int(min_value, max_value))

    def biguint256(
        self, min_value: int = 0, max_value: int = (1 << 256) - 1
    ) -> algopy.arc4.UInt256:
        """Generate a random UInt256 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to (2^256 - 1).
        :returns: A random UInt256 value.
        """
        return arc4.UInt256(generate_random_int(min_value, max_value))

    def biguint512(self, min_value: int = 0, max_value: int = MAX_UINT512) -> algopy.arc4.UInt512:
        """Generate a random UInt512 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :param max_value: Maximum value (inclusive). Defaults to MAX_UINT512.
        :returns: A random UInt512 value.
        """
        return arc4.UInt512(generate_random_int(min_value, max_value))

    def dynamic_bytes(self, n: int) -> algopy.arc4.DynamicBytes:
        """Generate a random dynamic bytes of size `n` bits.

        :param n: The number of bits for the dynamic bytes. Must be a multiple of 8, otherwise
                the last byte will be truncated.
        :returns: A new, random dynamic bytes of size `n` bits.
        """
        # rounding up
        num_bytes = (n + 7) // 8
        random_bytes = secrets.token_bytes(num_bytes)

        # trim to exact bit length if necessary
        if n % 8 != 0:
            last_byte = random_bytes[-1]
            mask = (1 << (n % 8)) - 1
            random_bytes = random_bytes[:-1] + bytes([last_byte & mask])

        return arc4.DynamicBytes(random_bytes)

    def string(self, n: int) -> algopy.arc4.String:
        """Generate a random string of size `n` bits.

        :param n: The number of bits for the string.
        :returns: A new, random string of size `n` bits.
        """
        # Calculate the number of characters needed (rounding up)
        num_chars = (n + 7) // 8

        # Generate random string
        random_string = "".join(secrets.choice(string.printable) for _ in range(num_chars))

        # Trim to exact bit length if necessary
        if n % 8 != 0:
            last_char = ord(random_string[-1])
            mask = (1 << (n % 8)) - 1
            random_string = random_string[:-1] + chr(last_char & mask)

        return arc4.String(random_string)
