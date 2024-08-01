# Usage

The Algorand Python Testing framework provides tools for testing Algorand Python smart contracts within a Python interpreter. This guide covers the main features and concepts of the framework.

```{note}
For references on this page, assume `ctx` as an instance of `AlgopyTestContext` instantiated with `with algopy_testing_context() as ctx:`.
```

## Test Context Manager

The core of the framework is the `algopy_testing_context` context manager. It creates a simulated Algorand environment that mimics AVM behavior.

```python
from algopy_testing import algopy_testing_context

def test_my_contract():
    with algopy_testing_context() as ctx:
        # Your test code here
        pass
```

The context manager provides an `AlgopyTestContext` object, giving you access to various methods for interacting with the simulated environment.

## AVM Types

These types are available directly under the `algopy` namespace. They represent the basic AVM primitive types and can be instantiated as such:

### UInt64

```python
from algopy import UInt64

# Integer type
uint64_value = UInt64(100)

# Generate a random UInt64 value
random_uint64 = ctx.any_uint64()

# Specify a range
random_uint64 = ctx.any_uint64(min_value=1000, max_value=9999)
```

### Bytes

```python
from algopy import Bytes

# Byte string
bytes_value = Bytes(b"Hello, Algorand!")

# Generate random byte sequences
random_bytes = ctx.any_bytes()

# Specify the length
random_bytes = ctx.any_bytes(length=32)
```

### String

```python
from algopy import String

# UTF-8 encoded string
string_value = String("Hello, Algorand!")

# Generate random strings
random_string = ctx.any_string()

# Specify the length
random_string = ctx.any_string(length=16)
```

### BigUInt

```python
from algopy import BigUInt

# Arbitrary-precision unsigned integer
biguint_value = BigUInt(100)
```

### Asset

```python
from algopy import Asset

# Asset
asset = Asset(id=1, name="TestCoin", total=1000000, decimals=6)

# Generate a random asset
random_asset = ctx.any_asset(
    id=None,  # Optional: Specify a custom ID, defaults to a random ID
    creator=None,  # Optional: Specify the creator account
    name=None,  # Optional: Specify the asset name
    unit_name=None,  # Optional: Specify the unit name
    total=None,  # Optional: Specify the total supply
    decimals=None,  # Optional: Specify the number of decimals
    default_frozen=None,  # Optional: Specify if the asset is frozen by default
    url=None,  # Optional: Specify the asset URL
    metadata_hash=None,  # Optional: Specify the metadata hash
    manager=None,  # Optional: Specify the manager address
    reserve=None,  # Optional: Specify the reserve address
    freeze=None,  # Optional: Specify the freeze address
    clawback=None  # Optional: Specify the clawback address
)
```

### Account

```python
from algopy import Account

# Account
account = Account(address="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ", balance=1000000)

# Generate a random account
random_account = ctx.any_account(
    address=None,  # Optional: Specify a custom address, defaults to a random address
    balance=None,  # Optional: Specify an initial balance
    min_balance=None,  # Optional: Specify a minimum balance
    auth_addr=None,  # Optional: Specify an auth address
    total_assets=None,  # Optional: Specify the total number of assets
    total_created_assets=None,  # Optional: Specify the total number of created assets
    total_apps_created=None,  # Optional: Specify the total number of created applications
    total_apps_opted_in=None,  # Optional: Specify the total number of applications opted into
    total_extra_app_pages=None,  # Optional: Specify the total number of extra application pages
    rewards=None,  # Optional: Specify the rewards
    status=None  # Optional: Specify the account status
)
```

### Application

```python
from algopy import Application

# Application
application = Application(id=1, approval_program=b"approval_code", clear_state_program=b"clear_code")

# Generate a random application
random_app = ctx.any_application(
    id=None,  # Optional: Specify a custom ID, defaults to a random ID
    approval_program=None,  # Optional: Specify a custom approval program
    clear_state_program=None,  # Optional: Specify a custom clear state program
    global_state=None,  # Optional: Specify initial global state
    local_state=None,  # Optional: Specify initial local state
    extra_pages=None,  # Optional: Specify extra pages for the application
    creator=None,  # Optional: Specify the creator account
    address=None  # Optional: Specify a custom address for the application
)
```

### Transaction

```python
from algopy import Transaction

# Payment transaction
transaction = Transaction(
    sender="AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ",
    receiver="BBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB",
    amount=1000000,
    type="pay"
)

# Generate a random payment transaction
pay_txn = ctx.any_payment_transaction(
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    receiver=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    amount=algopy.UInt64(1000000)  # Specified amount
)

# Generate a random asset transfer transaction
asset_transfer_txn = ctx.any_asset_transfer_transaction(
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    receiver=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    asset_id=algopy.UInt64(1),  # Specified asset ID
    amount=algopy.UInt64(1000)  # Specified amount
)

# Generate a random application call transaction
app_call_txn = ctx.any_application_call_transaction(
    app_id=ctx.any_application(),  # Defaults to a random application generated by ctx.any_application()
    app_args=[algopy.Bytes(b"arg1"), algopy.Bytes(b"arg2")],  # Specified application arguments
    accounts=[ctx.any_account()],  # Defaults to a list with a single random account generated by ctx.any_account()
    assets=[ctx.any_asset()],  # Defaults to a list with a single random asset generated by ctx.any_asset()
    apps=[ctx.any_application()],  # Defaults to a list with a single random application generated by ctx.any_application()
    approval_program_pages=[algopy.Bytes(b"approval_code")],  # Specified approval program pages
    clear_state_program_pages=[algopy.Bytes(b"clear_code")],  # Specified clear state program pages
    scratch_space={0: algopy.Bytes(b"scratch")}  # Specified scratch space
)

# Generate a random asset config transaction
asset_config_txn = ctx.any_asset_config_transaction(
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    asset_id=algopy.UInt64(1),  # Specified asset ID
    params=algopy.AssetParams(
        total=1000000,  # Specified total
        decimals=0,  # Specified decimals
        default_frozen=False,  # Specified default frozen state
        unit_name="UNIT",  # Specified unit name
        asset_name="Asset",  # Specified asset name
        url="http://asset-url",  # Specified URL
        metadata_hash=b"metadata_hash",  # Specified metadata hash
        manager=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
        reserve=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
        freeze=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
        clawback=ctx.any_account()  # Defaults to a random account generated by ctx.any_account()
    )
)

# Generate a random key registration transaction
key_reg_txn = ctx.any_key_registration_transaction(
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    vote_pk=algopy.Bytes(b"vote_pk"),  # Specified vote public key
    selection_pk=algopy.Bytes(b"selection_pk"),  # Specified selection public key
    vote_first=algopy.UInt64(1),  # Specified vote first round
    vote_last=algopy.UInt64(1000),  # Specified vote last round
    vote_key_dilution=algopy.UInt64(10000)  # Specified vote key dilution
)

# Generate a random asset freeze transaction
asset_freeze_txn = ctx.any_asset_freeze_transaction(
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    asset_id=algopy.UInt64(1),  # Specified asset ID
    freeze_target=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    freeze_state=True  # Specified freeze state
)

# Generate a random transaction of a specified type
generic_txn = ctx.any_transaction(
    type=algopy.TransactionType.Payment,  # Specified transaction type
    sender=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    receiver=ctx.any_account(),  # Defaults to a random account generated by ctx.any_account()
    amount=algopy.UInt64(1000000)  # Specified amount
)
```

## ARC4 Types

These types are available under the `algopy.arc4` namespace. Refer to the [ARC4 specification](https://arc.algorand.foundation/ARCs/arc-0004) for more details.

### Unsigned Integers

```python
from algopy import arc4

# Integer types
uint8_value = arc4.UInt8(255)
uint16_value = arc4.UInt16(65535)
uint32_value = arc4.UInt32(4294967295)
uint64_value = arc4.UInt64(18446744073709551615)

# Generate a random unsigned integer
uint8 = ctx.arc4.any_uint_n(8)
uint16 = ctx.arc4.any_uint_n(16)
uint32 = ctx.arc4.any_uint_n(32)
uint64 = ctx.arc4.any_uint_n(64)
```

### Address

```python
from algopy import arc4

# Address type
address_value = arc4.Address("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAY5HFKQ")

# Generate a random address
random_address = ctx.arc4.any_address()
```

### Dynamic Bytes

```python
from algopy import arc4

# Dynamic byte string
bytes_value = arc4.DynamicBytes(b"Hello, Algorand!")

# Generate random dynamic bytes
random_dynamic_bytes = ctx.arc4.any_dynamic_bytes()
```

### String

```python
from algopy import arc4

# UTF-8 encoded string
string_value = arc4.String("Hello, Algorand!")
```

## State Management

## Smart Signatures

Smart signatures, also known as logic signatures or LogicSigs, are programs that can be used to sign transactions. The Algorand Python Testing framework provides support for testing these programs.

### Defining a Logic Signature

To define a logic signature, you can use the `algopy.LogicSig` class:

```python
from algopy import LogicSig, Bytes, UInt64

def my_logic_sig() -> UInt64:
    # Your logic signature code here
    return UInt64(1)  # Approve the transaction
```

### Executing a Logic Signature

To test a logic signature, use the `execute_logicsig` method of the `AlgopyTestContext`:

```python
from algopy import LogicSig, Bytes, UInt64

def my_logic_sig() -> UInt64:
    # Your logic signature code here
    return UInt64(1)  # Approve the transaction

# note, lsig_args represent a list of any Bytes
result = ctx.execute_logicsig(my_logic_sig, lsig_args=[])
```

The `execute_logicsig` method takes two parameters:

1. `lsig`: An instance of `algopy.LogicSig` containing the logic signature program.
2. `lsig_args`: An optional sequence of `algopy.Bytes` objects representing the arguments to the logic signature.

The method returns the result of executing the logic signature, which can be either a `bool` or a `UInt64`:

-   If the logic signature returns `0`, it's interpreted as `False` (rejection).
-   If it returns `1`, it's interpreted as `True` (approval).
-   Any other non-zero value is returned as a `UInt64`.

## Opcodes

### Cryptographic Operations

All cryptographic operations have matching Python implementations for use within the test context. These are available under the `algopy.op` namespace.

#### Hashing Functions

```python
from algopy import op, Bytes

# SHA256
sha256_result = op.sha256(Bytes(b"data"))

# SHA3-256
sha3_256_result = op.sha3_256(Bytes(b"data"))

# Keccak256
keccak256_result = op.keccak256(Bytes(b"data"))

# SHA512-256
sha512_256_result = op.sha512_256(Bytes(b"data"))
```

#### Signature Verification

```python
from algopy import op, Bytes

# Ed25519 verification
data = Bytes(b"message")
signature = Bytes(b"signature")
public_key = Bytes(b"public_key")
ed25519verify_result = op.ed25519verify(data, signature, public_key)

# Ed25519 verification (bare)
ed25519verify_bare_result = op.ed25519verify_bare(data, signature, public_key)

# ECDSA verification
from algopy.enums import ECDSA

curve = ECDSA.Secp256k1  # or ECDSA.Secp256r1
data = Bytes(b"message")
sig_r = Bytes(b"r_component")
sig_s = Bytes(b"s_component")
pubkey_x = Bytes(b"public_key_x")
pubkey_y = Bytes(b"public_key_y")
ecdsa_verify_result = op.ecdsa_verify(curve, data, sig_r, sig_s, pubkey_x, pubkey_y)
```

#### ECDSA Operations

```python
from algopy import op, Bytes, UInt64
from algopy.enums import ECDSA

# ECDSA public key recovery
curve = ECDSA.Secp256k1
data = Bytes(b"message")
recovery_id = UInt64(0)
sig_r = Bytes(b"r_component")
sig_s = Bytes(b"s_component")
pubkey_x, pubkey_y = op.ecdsa_pk_recover(curve, data, recovery_id, sig_r, sig_s)

# ECDSA public key decompression
curve = ECDSA.Secp256k1
compressed_pubkey = Bytes(b"compressed_public_key")
pubkey_x, pubkey_y = op.ecdsa_pk_decompress(curve, compressed_pubkey)
```

##### VRF Verification

```python
from algopy import op, Bytes
from algopy.enums import VrfVerify

vrf_verify_result, is_valid = op.vrf_verify(VrfVerify.VrfAlgorand, proof, message, public_key)
```

Note: The `vrf_verify` function is not fully implemented in the current version of the framework. You may need to mock its behavior using your preferred testing tools.

These cryptographic operations allow you to test various aspects of your smart contracts that involve hashing, signature verification, and other cryptographic functions within the Algorand Python Testing framework.

## Property-Based Testing

Use the `any_*` methods with custom [hypothesis](https://hypothesis.readthedocs.io/en/latest/) strategies for property-based testing. Note: Requires separate installation of the `hypothesis` package.

```python
# Example usage with hypothesis
```
