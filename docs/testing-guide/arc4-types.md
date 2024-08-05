# ARC4 Types

These types are available under the `algopy.arc4` namespace. Refer to the [ARC4 specification](https://arc.algorand.foundation/ARCs/arc-0004) for more details on the spec.

```{hint}
Test context manager provides _value generators_ for ARC4 types. To access those, use `{context_instance}.arc4` property. See more examples below.
```

```{note}
For all `algopy.arc4` types with and without respective _value generator_, instantiation can be performed directly. If you have a suggestion for a new _value generator_ implementation, please open an issue in the [`algorand-python-testing`](https://github.com/algorand-sdk/algorand-python-testing) repository or contribute by following the [contribution guide](https://github.com/algorand-sdk/algorand-python-testing/blob/main/CONTRIBUTING.md).
```

## Unsigned Integers

```python
from algopy import arc4

# Integer types
uint8_value = arc4.UInt8(255)
uint16_value = arc4.UInt16(65535)
uint32_value = arc4.UInt32(4294967295)
uint64_value = arc4.UInt64(18446744073709551615)

... # instantiate test context
# Generate a random unsigned arc4 integer with default range
uint8 = ctx.arc4.any_uint8()
uint16 = ctx.arc4.any_uint16()
uint32 = ctx.arc4.any_uint32()
uint64 = ctx.arc4.any_uint64()
uint128 = ctx.arc4.any_biguint128()
uint256 = ctx.arc4.any_biguint256()
uint512 = ctx.arc4.any_biguint512()

# Generate a random unsigned arc4 integer with specified range
uint8_custom = ctx.arc4.any_uint8(min_value=10, max_value=100)
uint16_custom = ctx.arc4.any_uint16(min_value=1000, max_value=5000)
uint32_custom = ctx.arc4.any_uint32(min_value=100000, max_value=1000000)
uint64_custom = ctx.arc4.any_uint64(min_value=1000000000, max_value=10000000000)
uint128_custom = ctx.arc4.any_biguint128(min_value=1000000000000000, max_value=10000000000000000)
uint256_custom = ctx.arc4.any_biguint256(min_value=1000000000000000000000000, max_value=10000000000000000000000000)
uint512_custom = ctx.arc4.any_biguint512(min_value=1000000000000000000000000000000000, max_value=10000000000000000000000000000000000)
```

## Address

```python
from algopy import arc4

# Address type
address_value = arc4.Address("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ")

# Generate a random address
random_address = ctx.arc4.any_address()
```

## Dynamic Bytes

```python
from algopy import arc4

# Dynamic byte string
bytes_value = arc4.DynamicBytes(b"Hello, Algorand!")

# Generate random dynamic bytes
random_dynamic_bytes = ctx.arc4.any_dynamic_bytes()
```

## String

```python
from algopy import arc4

# UTF-8 encoded string
string_value = arc4.String("Hello, Algorand!")
```
