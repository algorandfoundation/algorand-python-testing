# AVM Types

These types are available directly under the `algopy` namespace. They represent the basic AVM primitive types and can be instantiated as follows:

## UInt64

```python
# Direct instantiation
uint64_value = algopy.UInt64(100)

# Instantiate test context
...

# Generate a random UInt64 value
random_uint64 = ctx.any_uint64()

# Specify a range
random_uint64 = ctx.any_uint64(min_value=1000, max_value=9999)
```

## Bytes

```python
# Direct instantiation
bytes_value = algopy.Bytes(b"Hello, Algorand!")

# Instantiate test context
...

# Generate random byte sequences
random_bytes = ctx.any_bytes()

# Specify the length
random_bytes = ctx.any_bytes(length=32)
```

## String

```python
# Direct instantiation
string_value = algopy.String("Hello, Algorand!")

# Instantiate test context
...

# Generate random strings
random_string = ctx.any_string()

# Specify the length
random_string = ctx.any_string(length=16)
```

## BigUInt

```python
# Direct instantiation
biguint_value = algopy.BigUInt(100)

# Instantiate test context
...

# Generate a random BigUInt value
random_biguint128 = ctx.any_biguint128()

# Specify a range for UInt128
random_biguint128 = ctx.any_biguint128(min_value=1000, max_value=999999999999)

# Generate a random UInt256 value
random_biguint256 = ctx.any_biguint256()

# Specify a range for UInt256
random_biguint256 = ctx.any_biguint256(min_value=1000, max_value=999999999999)

# Generate a random UInt512 value
random_biguint512 = ctx.any_biguint512()

# Specify a range for UInt512
random_biguint512 = ctx.any_biguint512(min_value=1000, max_value=999999999999)
```

## Asset

```python
# Direct instantiation
asset = algopy.Asset(asset_id=1001)

# Instantiate test context
...

# Generate a random asset
random_asset = ctx.any_asset(
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
asset = ctx.get_asset(asset_id={ID})

# Update an asset
ctx.update_asset(
    asset_id={ID},
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

# Clear an asset by ID
ctx.clear_asset(asset_id=1)
```

## Account

```python
# Direct instantiation
account = algopy.Account({ADDRESS})

# Instantiate test context
...

# Generate a random account
random_account = ctx.any_account(
    address=...,  # Optional: Specify a custom address, defaults to a random address
    opted_asset_balances=...,  # Optional: Specify opted asset balances as dict of algopy.UInt64 as key and algopy.UInt64 as value
    opted_apps=...,  # Optional: Specify opted apps as sequence of algopy.Application objects
    balance=...,  # Optional: Specify an initial balance
    min_balance=...,  # Optional: Specify a minimum balance
    auth_addr=...,  # Optional: Specify an auth address
    total_assets=...,  # Optional: Specify the total number of assets
    total_created_assets=...,  # Optional: Specify the total number of created assets
    total_apps_created=...,  # Optional: Specify the total number of created applications
    total_apps_opted_in=...,  # Optional: Specify the total number of applications opted into
    total_extra_app_pages=...,  # Optional: Specify the total number of extra application pages
    rewards=...,  # Optional: Specify the rewards
    status=...  # Optional: Specify the account status
)

# Generate a random account that is opted into a specific asset
mock_asset = ctx.any_asset()
mock_account = ctx.any_account(
    opted_asset_balances={mock_asset.id: algopy.UInt64({TEST_BALANCE})}
)

# Get an account by address
account = ctx.get_account(str(mock_account))

# Update an account
ctx.update_account(
    "{ADDRESS}",
    balance=...,  # Optional: New balance
    min_balance=...,  # Optional: New minimum balance
    auth_addr=...,  # Optional: New auth address
    total_assets=...,  # Optional: New total number of assets
    total_created_assets=...,  # Optional: New total number of created assets
    total_apps_created=...,  # Optional: New total number of created applications
    total_apps_opted_in=...,  # Optional: New total number of applications opted into
    total_extra_app_pages=...,  # Optional: New total number of extra application pages
    rewards=...,  # Optional: New rewards
    status=...  # Optional: New account status
)

# Get opted asset balance for an account
opted_asset_balance = ctx.get_opted_asset_balance(account, asset_id)

# Clear all accounts
ctx.clear_accounts()
```

## Application

```python
# Direct instantiation
application = algopy.Application(application_id=1001)

# Instantiate test context
...

# Generate a random application
random_app = ctx.any_application(
    id=...,  # Optional: Specify a custom ID, defaults to the next available ID in test context
    address=...,  # Optional: Specify a custom address for the application
    approval_program=...,  # Optional: Specify a custom approval program
    clear_state_program=...,  # Optional: Specify a custom clear state program
    global_num_uint=...,  # Optional: Number of global uint values
    global_num_bytes=...,  # Optional: Number of global byte values
    local_num_uint=...,  # Optional: Number of local uint values
    local_num_bytes=...,  # Optional: Number of local byte values
    extra_program_pages=...,  # Optional: Number of extra program pages
    creator=...  # Optional: Specify the creator account
)

# Get an application by ID
app = ctx.get_application(app_id={ID})

# Update an application
ctx.update_application(
    app_id={ID},
    approval_program=...,  # Optional: New approval program
    clear_state_program=...,  # Optional: New clear state program
    global_num_uint=...,  # Optional: New number of global uint values
    global_num_bytes=...,  # Optional: New number of global byte values
    local_num_uint=...,  # Optional: New number of local uint values
    local_num_bytes=...,  # Optional: New number of local byte values
    extra_program_pages=...,  # Optional: New number of extra program pages
    creator=...  # Optional: New creator account
)

# Add logs for an application
ctx.add_application_logs(
    app_id={ID},
    logs=b"log entry" or [b"log entry 1", b"log entry 2"],
    prepend_arc4_prefix=False  # Optional: Prepend ARC4 prefix to logs
)

# Get logs for an application
app_logs = ctx.get_application_logs(app_id={ID})

# Set the active application
ctx.set_active_contract(contract)

# Get the active application
active_app = ctx.get_active_application()

# Clear all applications
ctx.clear_applications()

# Clear all application logs
ctx.clear_application_logs()
```
