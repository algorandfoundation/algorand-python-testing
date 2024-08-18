# State Management

`algorand-python-testing` provides functionality to unit test all state related abstractions available in AVM and represented by `algorand-python` stubs:

1. `algopy.Global`
2. `algopy.LocalState`
3. `algopy.GlobalState`
4. `algopy.Box`, `algopy.BoxRef`, `algopy.BoxMap`
5. `algopy.op.Box` ops
6. `algopy.op.Scratch` ops

## Patching State

### Distinction between Global and GlobalState

In the context of Algorand smart contracts, it is important to understand the distinction between `Global` and `GlobalState` as represented in the `algorand-python` stubs.

#### Global

`Global` is a class that provides access to global properties and values within the Algorand Virtual Machine (AVM). These properties are not specific to any particular application but are instead global to the entire blockchain. Examples of such properties include the current round number, the minimum transaction fee, and the latest confirmed block timestamp. The `Global` class allows smart contracts to query these values using native TEAL opcodes.

```python
... # instantiate test context
ctx.patch_global_fields(
    min_txn_fee=...,  # Optional: Minimum transaction fee
    min_balance=...,  # Optional: Minimum balance
    max_txn_life=...,  # Optional: Maximum transaction lifetime
    zero_address=...,  # Optional: Zero address
    creator_address=...,  # Optional: Creator address
    asset_create_min_balance=...,  # Optional: Minimum balance for asset creation
    asset_opt_in_min_balance=...,  # Optional: Minimum balance for asset opt-in
    genesis_hash=...,  # Optional: Genesis hash
    latest_timestamp=...  # Optional: Latest timestamp
)
```

## GlobalState

Global state within the test context is represented as instance attributes on instances of `algopy.Contract` and `algopy.ARC4Contract` classes.

Therefore, to modify values of global state of particular contract instance, you would do so as if you were modifying a regular Python instance attribute.

```python
# Assume some contract instance
class SomeContract(algopy.ARC4Contract):
    def __init__(self) -> None:
        # Notice that `state_a` defines global state via `GlobalState` proxy class
        self.state_a =  algopy.GlobalState(algopy.UInt64, key="global_uint64")
        # `state_b` showcases global state declaration as a regular Python instance attribute
        self.state_b = algopy.UInt64(1)

... # instantiate test context
contract = SomeContract()

# Modify global state
contract.state_a = algopy.UInt64(10)
contract.state_b = algopy.UInt64(20)
```

## Local State

Similar to global state, local state is defined as a regular Python instance attribute on contract instances.

```python
# Assume some contract instance
class SomeContract(algopy.ARC4Contract):
    def __init__(self) -> None:
        # Notice that `state_a` defines global state via `GlobalState` proxy class
        self.local_state_a =  algopy.LocalState(algopy.UInt64, key="state_a")

... # instantiate test context
contract = SomeContract()

# Modify local state
account = ctx.any_account()

## Access is done via account address as key. Existence of specific key represents whether account is opted-in to the contract to store local state.
contract.local_state_a[account] = algopy.UInt64(10)
```

## Boxes

The testing framework covers whole set of Box abstractions available in `algorand-python`. Below demonstrates usage of test context to access Boxes used during contract 'execution' in an emulated AVM environment.

```python
class SomeContract(algopy.ARC4Contract):
    def __init(self) -> None:
        self.box_map = algopy.BoxMap(algopy.Bytes, algopy.UInt64)

    def some_method(self, key_a: algopy.Bytes, key_b: algopy.Bytes, key_c: algopy.Bytes) -> None:
        # Notice that `state_a` defines global state via `GlobalState` proxy class
        self.box = algopy.Box(algopy.UInt64, key=key_a)
        self.box.value = algopy.UInt64(1)
        self.box_map[key_b] = algopy.UInt64(1)
        self.box_map[key_c] = algopy.UInt64(2)

        # or use low level ops
        algopy.op.Box.put(key_a, algopy.op.itobytes(algopy.UInt64(1)))
        algopy.op.Box.put(key_b, algopy.op.itobytes(algopy.UInt64(1)))
        algopy.op.Box.put(key_c, algopy.op.itobytes(algopy.UInt64(2)))

... # instantiate test context
contract = SomeContract()

key_a = ctx.any_uint64()
key_b = ctx.any_uint64()
key_c = ctx.any_uint64()

contract.some_method(key_a, key_b, key_c)

# access boxes
box_from_context = context.get_box({BOX_KEY})

# Check if box exists
context.does_box_exist({BOX_KEY})

# Set box content on test context manually
# Can be useful if a certain value has to be preset prior to test execution
context.set_box_value({BOX_KEY}, algopy.op.itob(algopy.UInt64(1)))
```

## Scratch space

The test context represents scratch slots as a dictionary mapping transactions to lists of 256 bytes. When executing a method, scratch slots are allocated for the transaction in the test context. To use scratch storage:

```python
class MyContract(Contract, scratch_slots=(1, TWO, urange(3, TWENTY))):
    def approval_program(self) -> bool:
        op.Scratch.store(1, UInt64(5))

        assert op.Scratch.load_uint64(1) == UInt64(5)

        return True

... # instantiate test context
contract = MyContract()
contract.some_method()

# access scratch space
context.get_scratch_value(1)

# Set scratch space for a transaction
context.set_scratch_space(txn, {1: algopy.UInt64(5), 2: algopy.Bytes(b"hello")})

# Set a specific scratch slot for a transaction
context.set_scratch_slot(txn, 3, algopy.UInt64(10))

# Get the whole scratch space list for a specific transaction
scratch_space = context.get_scratch_space(txn)
```
