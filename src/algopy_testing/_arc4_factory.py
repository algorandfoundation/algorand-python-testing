from __future__ import annotations

import secrets
import string
import typing
from dataclasses import dataclass

import algosdk

from algopy_testing import arc4
from algopy_testing.constants import MAX_UINT8, MAX_UINT16, MAX_UINT32, MAX_UINT64, MAX_UINT512
from algopy_testing.utils import generate_random_int

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing import AlgopyTestContext


@dataclass
class ARC4Factory:
    """Factory for generating ARC4-compliant test data."""

    def __init__(self, *, context: AlgopyTestContext) -> None:
        """Initializes the ARC4Factory with the given testing context.

        Args:
            context (AlgopyTestContext): The testing context for generating test data.
        """
        self._context = context

    def any_address(self) -> algopy.arc4.Address:
        """Generate a random Algorand address.

        :returns: A new, random Algorand address.
        :rtype: algopy.arc4.Address
        """

        return arc4.Address(algosdk.account.generate_account()[1])

    def any_uint8(self, min_value: int = 0, max_value: int = MAX_UINT8) -> algopy.arc4.UInt8:
        """Generate a random UInt8 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT8.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT8)
        :returns: A random UInt8 value.
        :rtype: algopy.arc4.UInt8
        :raises AssertionError: If values are out of UInt8 range.
        """
        return arc4.UInt8(generate_random_int(min_value, max_value))

    def any_uint16(self, min_value: int = 0, max_value: int = MAX_UINT16) -> algopy.arc4.UInt16:
        """Generate a random UInt16 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT16.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT16)
        :returns: A random UInt16 value.
        :rtype: algopy.arc4.UInt16
        :raises AssertionError: If values are out of UInt16 range.
        """
        return arc4.UInt16(generate_random_int(min_value, max_value))

    def any_uint32(self, min_value: int = 0, max_value: int = MAX_UINT32) -> algopy.arc4.UInt32:
        """Generate a random UInt32 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT32.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT32)
        :returns: A random UInt32 value.
        :rtype: algopy.arc4.UInt32
        :raises AssertionError: If values are out of UInt32 range.
        """
        return arc4.UInt32(generate_random_int(min_value, max_value))

    def any_uint64(self, min_value: int = 0, max_value: int = MAX_UINT64) -> algopy.arc4.UInt64:
        """Generate a random UInt64 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT64.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT64)
        :returns: A random UInt64 value.
        :rtype: algopy.arc4.UInt64
        :raises AssertionError: If values are out of UInt64 range.
        """
        return arc4.UInt64(generate_random_int(min_value, max_value))

    def any_biguint128(
        self, min_value: int = 0, max_value: int = (1 << 128) - 1
    ) -> algopy.arc4.UInt128:
        """Generate a random UInt128 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to (2^128 - 1).
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = (1 << 128) - 1)
        :returns: A random UInt128 value.
        :rtype: algopy.arc4.UInt128
        :raises AssertionError: If values are out of UInt128 range.
        """
        return arc4.UInt128(generate_random_int(min_value, max_value))

    def any_biguint256(
        self, min_value: int = 0, max_value: int = (1 << 256) - 1
    ) -> algopy.arc4.UInt256:
        """Generate a random UInt256 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to (2^256 - 1).
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = (1 << 256) - 1)
        :returns: A random UInt256 value.
        :rtype: algopy.arc4.UInt256
        :raises AssertionError: If values are out of UInt256 range.
        """
        return arc4.UInt256(generate_random_int(min_value, max_value))

    def any_biguint512(
        self, min_value: int = 0, max_value: int = MAX_UINT512
    ) -> algopy.arc4.UInt512:
        """Generate a random UInt512 within the specified range.

        :param min_value: Minimum value (inclusive). Defaults to 0.
        :type min_value: int
        :param max_value: Maximum value (inclusive). Defaults to
            MAX_UINT512.
        :type max_value: int
        :param min_value: int:  (Default value = 0)
        :param max_value: int:  (Default value = MAX_UINT512)
        :returns: A random UInt512 value.
        :rtype: algopy.arc4.UInt512
        :raises AssertionError: If values are out of UInt512 range.
        """
        return arc4.UInt512(generate_random_int(min_value, max_value))

    def any_dynamic_bytes(self, n: int) -> algopy.arc4.DynamicBytes:
        """Generate a random dynamic bytes of size `n` bits.

        :param n: The number of bits for the dynamic bytes. Must be a multiple of 8, otherwise
                the last byte will be truncated.
        :type n: int
        :param n: int:
        :returns: A new, random dynamic bytes of size `n` bits.
        :rtype: algopy.arc4.DynamicBytes
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

    def any_string(self, n: int) -> algopy.arc4.String:
        """Generate a random string of size `n` bits.

        :param n: The number of bits for the string.
        :type n: int
        :param n: int:
        :returns: A new, random string of size `n` bits.
        :rtype: algopy.arc4.String
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