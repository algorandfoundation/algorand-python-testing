# AVM Types

These types are available directly under the `algopy` namespace. They represent the basic AVM primitive types and can be instantiated directly or via _value generators_:

```{note}
For 'primitive `algopy` types such as `Account`, `Application`, `Asset`, `UInt64`, `BigUint`, `Bytes`, `Sting` with and without respective _value generator_, instantiation can be performed directly. If you have a suggestion for a new _value generator_ implementation, please open an issue in the [`algorand-python-testing`](https://github.com/algorandfoundation/algorand-python-testing) repository or contribute by following the [contribution guide](https://github.com/algorandfoundation/algorand-python-testing/blob/main/CONTRIBUTING.md).
```

```{testsetup}
import algopy
import algopy_testing

# Create the context manager for snippets below
ctx_manager = algopy_testing_context()

# Enter the context
ctx = ctx_manager.__enter__()
```

## UInt64

```{testcode}
# Direct instantiation
uint64_value = algopy.UInt64(100)

# Instantiate test context
...

# Generate a random UInt64 value
random_uint64 = ctx.any.uint64()

# Specify a range
random_uint64 = ctx.any.uint64(min_value=1000, max_value=9999)
```

## Bytes

```{testcode}
# Direct instantiation
bytes_value = algopy.Bytes(b"Hello, Algorand!")


# Instantiate test context
...

# Generate random byte sequences
random_bytes = ctx.any.bytes()

# Specify the length
random_bytes = ctx.any.bytes(length=32)
```

## String

```{testcode}
# Direct instantiation
string_value = algopy.String("Hello, Algorand!")

# Generate random strings
random_string = ctx.any.string()

# Specify the length
random_string = ctx.any.string(length=16)
```

## BigUInt

```{testcode}
# Direct instantiation
biguint_value = algopy.BigUInt(100)

# Generate a random BigUInt value
random_biguint = ctx.any.biguint()
```

## Asset

```{testcode}
# Direct instantiation
asset = algopy.Asset(asset_id=1001)

# Instantiate test context
...

# Generate a random asset
random_asset = ctx.any.asset(
    id=...,  # Optional: Uses next value under asset id counter in test context
    creator=...,  # Optional: Creator account
    name=...,  # Optional: Asset name
    unit_name=...,  # Optional: Unit name
    total=...,  # Optional: Total supply
    decimals=...,  # Optional: Number of decimals
    default_frozen=...,  # Optional: Default frozen state
    url=...,  # Optional: Asset URL
    metadata_hash=...,  # Optional: Metadata hash
    manager=...,  # Optional: Manager address
    reserve=...,  # Optional: Reserve address
    freeze=...,  # Optional: Freeze address
    clawback=...  # Optional: Clawback address
)

# Get an asset by ID
asset = ctx.ledger.get_asset(asset_id=random_asset.id)

# Update an asset
ctx.ledger.update_asset(
    asset_id=random_asset.id,
    name=...,  # Optional: New asset name
    total=...,  # Optional: New total supply
    decimals=...,  # Optional: Number of decimals
    default_frozen=...,  # Optional: Default frozen state
    url=...,  # Optional: New asset URL
    metadata_hash=...,  # Optional: New metadata hash
    manager=...,  # Optional: New manager address
    reserve=...,  # Optional: New reserve address
    freeze=...,  # Optional: New freeze address
    clawback=...  # Optional: New clawback address
)
```

## Account

```{testcode}
# Direct instantiation
raw_address = 'PUYAGEGVCOEBP57LUKPNOCSMRWHZJSU4S62RGC2AONDUEIHC6P7FOPJQ4I'
account = algopy.Account(raw_address) # zero address by default

# Instantiate test context
...

# Generate a random account
random_account = ctx.any.account(
    address=str(raw_address),  # Optional: Specify a custom address, defaults to a random address
    opted_asset_balances=...,  # Optional: Specify opted asset balances as dict of algopy.UInt64 as key and algopy.UInt64 as value
    opted_apps=[],  # Optional: Specify opted apps as sequence of algopy.Application objects
    balance=...,  # Optional: Specify an initial balance
    min_balance=...,  # Optional: Specify a minimum balance
    auth_address=...,  # Optional: Specify an auth address
    total_assets=...,  # Optional: Specify the total number of assets
    total_assets_created=...,  # Optional: Specify the total number of created assets
    total_apps_created=...,  # Optional: Specify the total number of created applications
    total_apps_opted_in=...,  # Optional: Specify the total number of applications opted into
    total_extra_app_pages=...,  # Optional: Specify the total number of extra
)

# Generate a random account that is opted into a specific asset
mock_asset = ctx.any.asset()
mock_account = ctx.any.account(
    opted_asset_balances={mock_asset.id: algopy.UInt64(123)}
)

# Get an account by address
account = ctx.ledger.get_account(str(mock_account))

# Update an account
ctx.ledger.update_account(
    str(mock_account),
    balance=...,  # Optional: New balance
    min_balance=...,  # Optional: New minimum balance
    auth_address=ctx.any.account(),  # Optional: New auth address
    total_assets=...,  # Optional: New total number of assets
    total_created_assets=...,  # Optional: New total number of created assets
    total_apps_created=...,  # Optional: New total number of created applications
    total_apps_opted_in=...,  # Optional: New total number of applications opted into
    total_extra_app_pages=...,  # Optional: New total number of extra application pages
    rewards=...,  # Optional: New rewards
    status=...  # Optional: New account status
)

# Check if an account is opted into a specific asset
opted_in = account.is_opted_in(mock_asset)
```

## Application

```{testcode}
# Direct instantiation
application = algopy.Application()

# Instantiate test context
...

# Generate a random application
random_app = ctx.any.application(
    address=...,  # Optional: Specify a custom address for the application
    approval_program=algopy.Bytes(b''),  # Optional: Specify a custom approval program
    clear_state_program=algopy.Bytes(b''),  # Optional: Specify a custom clear state program
    global_num_uint=algopy.UInt64(1),  # Optional: Number of global uint values
    global_num_bytes=algopy.UInt64(1),  # Optional: Number of global byte values
    local_num_uint=algopy.UInt64(1),  # Optional: Number of local uint values
    local_num_bytes=algopy.UInt64(1),  # Optional: Number of local byte values
    extra_program_pages=algopy.UInt64(1),  # Optional: Number of extra program pages
    creator=ctx.default_sender  # Optional: Specify the creator account
)

# Get an application by ID
app = ctx.ledger.get_app(app_id=random_app.id)

# Update an application
ctx.ledger.update_app(
    app_id=random_app.id,
    approval_program=...,  # Optional: New approval program
    clear_state_program=...,  # Optional: New clear state program
    global_num_uint=...,  # Optional: New number of global uint values
    global_num_bytes=...,  # Optional: New number of global byte values
    local_num_uint=...,  # Optional: New number of local uint values
    local_num_bytes=...,  # Optional: New number of local byte values
    extra_program_pages=...,  # Optional: New number of extra program pages
    creator=...  # Optional: New creator account
)

# Patch logs for an application. When accessing via transactions or inner transaction related opcodes, will return the patched logs unless new logs where added into the transaction during execution.
test_app = ctx.any.application(logs=b"log entry" or [b"log entry 1", b"log entry 2"])

# Get app associated with the active contract
class MyContract(algopy.ARC4Contract):
    ...

contract = MyContract()
active_app = ctx.get_app_for_contract(contract)
```
