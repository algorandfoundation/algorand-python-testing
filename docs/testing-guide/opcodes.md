# AVM Opcodes

The [coverage](coverage.md) file contains a complete list of all opcodes and respective types as well as whether they are _Mockable_, _Emulated_, or _Native_ within the `algorand-python-testing` package. The following section will highlight **only** common opcodes and types that usually require interaction with test context manager. `Native` opcodes are assumed to function as they are in the Algorand Virtual Machine given that their functionality is stateless, if you experience any issues with any of the `Native` opcodes, please raise an issue in the [`algorand-python-testing` repo](https://github.com/algorandfoundation/algorand-python-testing/issues/new/choose) repository or contribute a PR by following [Contributing](https://github.com/algorandfoundation/algorand-python-testing/blob/main/CONTRIBUTING.md) guide.

## Implemented Types

These types are fully implemented in Python and behave identically to their AVM counterparts. Some examples include:

### 1. Cryptographic Operations

```{testcode}
import algopy.op as op

# SHA256 hash
data = algopy.Bytes(b"Hello, World!")
hashed = op.sha256(data)

# Keccak256 hash
keccak_hashed = op.keccak256(data)

# ECDSA verification
message_hash = bytes.fromhex(
    "f809fd0aa0bb0f20b354c6b2f86ea751957a4e262a546bd716f34f69b9516ae1"
)
sig_r = bytes.fromhex("18d96c7cda4bc14d06277534681ded8a94828eb731d8b842e0da8105408c83cf")
sig_s = bytes.fromhex("7d33c61acf39cbb7a1d51c7126f1718116179adebd31618c4604a1f03b5c274a")
pubkey_x = bytes.fromhex("f8140e3b2b92f7cbdc8196bc6baa9ce86cf15c18e8ad0145d50824e6fa890264")
pubkey_y = bytes.fromhex("bd437b75d6f1db67155a95a0da4b41f2b6b3dc5d42f7db56238449e404a6c0a3")

result = op.ecdsa_verify(op.ECDSA.Secp256r1, message_hash, sig_r, sig_s, pubkey_x, pubkey_y)
assert result
```

### 2. Arithmetic and Bitwise Operations

```{testcode}
import algopy.op as op

# Addition with carry
result, carry = op.addw(algopy.UInt64(2**63), algopy.UInt64(2**63))

# Bitwise operations
value = algopy.UInt64(42)
bit_length = op.bitlen(value)
is_bit_set = op.getbit(value, 3)
new_value = op.setbit_uint64(value, 2, 1)
```

> Native types are implemented in Python and execute as per their stubs. For a **full** list of all opcodes and types, see the [coverage](../coverage.md) page.

## Emulated Types Requiring Transaction Context

These types require interaction with the transaction context to set or update them:

### 1. Global Values

```{testcode}
from algopy_testing import algopy_testing_context
import algopy.op as op

with algopy_testing_context() as ctx:
    # Patch global fields
    ctx.ledger.patch_global_fields(
        min_txn_fee=algopy.UInt64(1000),
        min_balance=algopy.UInt64(100000)
    )

    # Access global values in your contract
    class MyContract(algopy.ARC4Contract):
        @algopy.arc4.abimethod
        def check_globals(self) -> algopy.UInt64:
            return op.Global.min_txn_fee + op.Global.min_balance

    contract = MyContract()
    result = contract.check_globals()
    assert result == algopy.UInt64(101000)
```

### 2. Transaction Fields

```python
from algopy_testing import algopy_testing_context
import algopy.op as op

with algopy_testing_context() as ctx:
    class MyContract(algopy.ARC4Contract):
        @algopy.arc4.abimethod
        def check_txn_fields(self) -> algopy.Bytes:
            return op.Txn.sender

    contract = MyContract()

    # Set custom transaction fields
    custom_sender = ctx.any.account()
    with ctx.txn.create_group(txn_op_fields={"sender": custom_sender}):
        result = contract.check_txn_fields()

    assert result == custom_sender.bytes
```

### 3. Asset Holdings and Parameters

```python
from algopy_testing import algopy_testing_context
import algopy.op as op

with algopy_testing_context() as ctx:
    class AssetContract(algopy.ARC4Contract):
        @algopy.arc4.abimethod
        def check_asset_holding(self, account: algopy.Account, asset: algopy.Asset) -> algopy.UInt64:
            balance, _ = op.AssetHoldingGet.asset_balance(account, asset)
            return balance

    # Create an asset and set up holdings
    asset = ctx.any.asset(total=algopy.UInt64(1000000))
    account = ctx.any.account(opted_asset_balances={asset.id: algopy.UInt64(5000)})

    contract = AssetContract()
    result = contract.check_asset_holding(account, asset)
    assert result == algopy.UInt64(5000)
```

### 4. Application Local and Global State

```python
from algopy_testing import algopy_testing_context
import algopy.op as op

with algopy_testing_context() as ctx:
    class StateContract(algopy.ARC4Contract):
        @algopy.arc4.abimethod
        def set_and_get_state(self, key: algopy.Bytes, value: algopy.UInt64) -> algopy.UInt64:
            op.AppGlobal.put(key, value)
            return op.AppGlobal.get_uint64(key)

    contract = StateContract()
    key = algopy.Bytes(b"test_key")
    value = algopy.UInt64(42)

    result = contract.set_and_get_state(key, value)
    assert result == value

    # Verify state outside the contract
    stored_value = ctx.ledger.get_global_state(contract, key)
    assert stored_value == 42
```

# Mockable Opcodes

This section covers the mockable opcodes in `algorand-python-testing` and demonstrates how to mock them in unit tests. This category covers the cases where native or emulated implementation in a unit test context is impractical or overly complex.

## algopy.compile_contract

Used to compile a contract. In tests, you can mock its behavior to return predefined compilation results.

```{testcode}
import unittest
from unittest.mock import patch, MagicMock
import algopy
from algopy_testing.primitives import Bytes

mocked_response = MagicMock()
mocked_response.approval_program = (Bytes(b'mock_approval'), Bytes(b'mock_approval'))
mocked_response.clear_state_program = (Bytes(b'mock_clear'), Bytes(b'mock_clear'))

class MockContract(algopy.Contract):
    pass

with patch('algopy.compile_contract', return_value=mocked_response) as mock_compile_contract:
    compiled = algopy.compile_contract(MockContract)

compiled.approval_program == (Bytes(b'mock_approval'), Bytes(b'mock_approval'))
compiled.clear_state_program == (Bytes(b'mock_clear'), Bytes(b'mock_clear'))
mock_compile_contract.assert_called_once_with(MockContract)
```

## algopy.arc4.abi_call

Used for ABI method calls. Mocking allows testing contract interactions without actual execution.

```{testcode}
import unittest
from unittest.mock import patch
import algopy
from algopy_testing.primitives import UInt64

class MyContract(algopy.ARC4Contract):
    @algopy.arc4.abimethod
    def my_method(self, arg1: algopy.UInt64, arg2: algopy.UInt64) -> algopy.UInt64:
        return algopy.arc4.abi_call("my_other_method", arg1, arg2)

class MyOtherContract(algopy.ARC4Contract):
    @algopy.arc4.abimethod
    def my_other_method(self, arg1: algopy.UInt64, arg2: algopy.UInt64) -> algopy.UInt64:
        return arg1 + arg2

def test_mock_abi_call():
    with algopy_testing_context() as ctx:
        mock_abi_call = MagicMock()
        mock_abi_call.return_value = UInt64(11)
        contract = MyContract()

        with patch('algopy.arc4.abi_call', mock_abi_call):
            result = contract.my_method(UInt64(10), UInt64(1))

        assert result == UInt64(11)
        mock_abi_call.assert_called_once_with("my_other_method", UInt64(10), UInt64(1))

test_mock_abi_call()
```

## algopy.op.vrf_verify

Verifiable Random Function (VRF) verification. Mocking is useful for testing without actual cryptographic computations.

```{testcode}
import unittest
from unittest.mock import patch
import algopy
from algopy_testing.primitives import Bytes

def test_mock_vrf_verify():
    mock_result = (Bytes(b'mock_output'), True)

    with patch('algopy.op.vrf_verify', MagicMock(return_value=mock_result)) as mock_vrf_verify:
        result = algopy.op.vrf_verify(
            algopy.op.VrfVerify.VrfAlgorand,
            Bytes(b'proof'),
            Bytes(b'message'),
            Bytes(b'public_key')
        )

    assert result == mock_result
    mock_vrf_verify.assert_called_once_with(
        algopy.op.VrfVerify.VrfAlgorand,
        Bytes(b'proof'),
        Bytes(b'message'),
        Bytes(b'public_key')
    )

test_mock_vrf_verify()
```

## algopy.op.EllipticCurve

Elliptic curve operations. Mocking allows testing without actual cryptographic computations.

```{testcode}
import unittest
from unittest.mock import patch
import algopy
from algopy_testing.primitives import Bytes

def test_mock_elliptic_curve_decompress():
    mock_result = (Bytes(b'x_coord'), Bytes(b'y_coord'))

    with patch('algopy.op.EllipticCurve.decompress', MagicMock(return_value=mock_result)) as mock_decompress:
        result = algopy.op.EllipticCurve.decompress(
            algopy.op.EC.BN254g1,
            Bytes(b'compressed_point')
        )

    assert result == mock_result
    mock_decompress.assert_called_once_with(
        algopy.op.EC.BN254g1,
        Bytes(b'compressed_point')
    )

test_mock_elliptic_curve_decompress()
```

These examples demonstrate how to mock key mockable opcodes in `algorand-python-testing`. Use similar techniques (in your preferred testing framework) for other mockable opcodes like `algopy.compile_logicsig`, `algopy.arc4.arc4_create`, and `algopy.arc4.arc4_update`.

Mocking these opcodes allows you to:

1. Control complex operations' behavior not covered by _implemented_ and _emulated_ types.
2. Test edge cases and error conditions.
3. Isolate contract logic from external dependencies.
