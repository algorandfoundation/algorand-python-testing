# Transactions

The testing framework follows the Transaction definitions described in [`algorand-python` docs](https://algorand-python.readthedocs.io/en/latest/algorand_sdk/transactions.html). This section focuses on _value generators_ and interactions with inner transactions, it also explains how the framework identifies _active_ transaction group during contract method/subroutine/logicsig invocation.

```{testsetup}
import algopy
import algopy_testing

# Create the context manager for snippets below
ctx_manager = algopy_testing_context()

# Enter the context
ctx = ctx_manager.__enter__()
```

## Group Transactions

Refers to test implementation of transaction stubs available under `algopy.gtxn.*` namespace. Available under [`algopy.TxnValueGenerator`](../api.md) instance accessible via `ctx.any.txn` property:

```{mermaid}
graph TD
    A[TxnValueGenerator] --> B[payment]
    A --> C[asset_transfer]
    A --> D[application_call]
    A --> E[asset_config]
    A --> F[key_registration]
    A --> G[asset_freeze]
    A --> H[transaction]
```

```{testcode}
... # instantiate test context

# Generate a random payment transaction
pay_txn = ctx.any.txn.payment(
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    receiver=ctx.any.account(),  # Required
    amount=algopy.UInt64(1000000)  # Required
)

# Generate a random asset transfer transaction
asset_transfer_txn = ctx.any.txn.asset_transfer(
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    receiver=ctx.any.account(),  # Required
    asset_id=algopy.UInt64(1),  # Required
    amount=algopy.UInt64(1000)  # Required
)

# Generate a random application call transaction
app_call_txn = ctx.any.txn.application_call(
    app_id=ctx.any.application(),  # Required
    app_args=[algopy.Bytes(b"arg1"), algopy.Bytes(b"arg2")],  # Optional: Defaults to empty list if not provided
    accounts=[ctx.any.account()],  # Optional: Defaults to empty list if not provided
    assets=[ctx.any.asset()],  # Optional: Defaults to empty list if not provided
    apps=[ctx.any.application()],  # Optional: Defaults to empty list if not provided
    approval_program_pages=[algopy.Bytes(b"approval_code")],  # Optional: Defaults to empty list if not provided
    clear_state_program_pages=[algopy.Bytes(b"clear_code")],  # Optional: Defaults to empty list if not provided
    scratch_space={0: algopy.Bytes(b"scratch")}  # Optional: Defaults to empty dict if not provided
)

# Generate a random asset config transaction
asset_config_txn = ctx.any.txn.asset_config(
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    asset_id=algopy.UInt64(1),  # Optional: If not provided, creates a new asset
    total=1000000,  # Required for new assets
    decimals=0,  # Required for new assets
    default_frozen=False,  # Optional: Defaults to False if not provided
    unit_name="UNIT",  # Optional: Defaults to empty string if not provided
    asset_name="Asset",  # Optional: Defaults to empty string if not provided
    url="http://asset-url",  # Optional: Defaults to empty string if not provided
    metadata_hash=b"metadata_hash",  # Optional: Defaults to empty bytes if not provided
    manager=ctx.any.account(),  # Optional: Defaults to sender if not provided
    reserve=ctx.any.account(),  # Optional: Defaults to zero address if not provided
    freeze=ctx.any.account(),  # Optional: Defaults to zero address if not provided
    clawback=ctx.any.account()  # Optional: Defaults to zero address if not provided
)

# Generate a random key registration transaction
key_reg_txn = ctx.any.txn.key_registration(
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    vote_pk=algopy.Bytes(b"vote_pk"),  # Optional: Defaults to empty bytes if not provided
    selection_pk=algopy.Bytes(b"selection_pk"),  # Optional: Defaults to empty bytes if not provided
    vote_first=algopy.UInt64(1),  # Optional: Defaults to 0 if not provided
    vote_last=algopy.UInt64(1000),  # Optional: Defaults to 0 if not provided
    vote_key_dilution=algopy.UInt64(10000)  # Optional: Defaults to 0 if not provided
)

# Generate a random asset freeze transaction
asset_freeze_txn = ctx.any.txn.asset_freeze(
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    asset_id=algopy.UInt64(1),  # Required
    freeze_target=ctx.any.account(),  # Required
    freeze_state=True  # Required
)

# Generate a random transaction of a specified type
generic_txn = ctx.any.txn.transaction(
    type=algopy.TransactionType.Payment,  # Required
    sender=ctx.any.account(),  # Optional: Defaults to context's default sender if not provided
    receiver=ctx.any.account(),  # Required for Payment
    amount=algopy.UInt64(1000000)  # Required for Payment
)
```

## Preparing for execution

When a smart contract instance (application) is interacted with on the Algorand network, it must be performed in relation to a specific transaction or transaction group where one or many transactions are application calls to target smart contract instances.

To emulate this behaviour, the `create_group` context manager is available on [`algopy.TransactionContext`](../api.md) instance that allows setting temporary transaction fields within a specific scope, passing in emulated transaction objects and identifying the active transaction index within the transaction group

```{testcode}
import algopy
from algopy_testing import AlgopyTestContext, algopy_testing_context

class SimpleContract(algopy.ARC4Contract):
    @algopy.arc4.abimethod
    def check_sender(self) -> algopy.Bytes:
        return algopy.Txn.sender

# Create a test context
with algopy_testing_context() as ctx:
    # Create a contract instance
    contract = SimpleContract()
    # Use scoped_txn_fields to temporarily change the sender
    patched_sender = ctx.any.account()
    with ctx.txn.create_group(txn_op_fields={"sender": patched_sender}):
        # Call the contract method
        result = contract.check_sender()

        # Assert that the sender is the default creator
        # NOTE: by default, 'default_sender' property of the test context
        # is set to the creator of the contract
        assert result == patched_sender

    # Assert that the sender is the default creator after exiting the
    # transaction group context
    assert ctx.txn.last_active.sender == patched_sender
    # Assert the size of last transaction group
    assert len(ctx.txn.last_group.txns) == 1
```

## Inner Transaction

Inner transactions are AVM transactions that are signed and executed by AVM applications (instances of deployed smart contracts or signatures).

When testing smart contracts, to stay consistent with AVM, the framework _does not allow you to submit inner transactions outside of contract/subroutine/logicsig invocation_, but you can interact with and manage inner transactions using the test context manager as follows:

```{testcode}
import algopy
from algopy_testing import AlgopyTestContext, algopy_testing_context

class MyContract(algopy.ARC4Contract):
    @algopy.arc4.abimethod
    def pay_via_itxn(self, asset: algopy.Asset) -> None:
        algopy.itxn.Payment(
            receiver=algopy.Txn.sender,
            amount=algopy.UInt64(1)
        ).submit()

# Create a test context
with algopy_testing_context() as ctx:
    # Create a contract instance
    contract = MyContract()

    # Generate a random asset
    asset = ctx.any.asset()

    # Execute the contract method
    contract.pay_via_itxn(asset=asset)

    # Access the last submitted inner transaction
    payment_txn = ctx.txn.last_group.last_itxn.payment

    # Assert properties of the inner transaction
    assert payment_txn.receiver == ctx.txn.last_active.sender
    assert payment_txn.amount == algopy.UInt64(1)

    # Access all inner transactions in the last group
    for itxn in ctx.txn.last_group.itxn_groups[-1]:
        # Perform assertions on each inner transaction
        ...

    # Access a specific inner transaction group
    first_itxn_group = ctx.txn.last_group.get_itxn_group(0)
    first_payment_txn = first_itxn_group.payment(0)
```

In this example, we define a contract method `pay_via_itxn` that creates and submits an inner payment transaction. The test context automatically captures and stores the inner transactions submitted by the contract method.

Note that we don't need to wrap the execution in a `create_group` context manager because the method is decorated with `@algopy.arc4.abimethod`, which automatically creates a transaction group for the method. The `create_group` context manager is only needed when you want to create more complex transaction groups or patch transaction fields for various transaction-related opcodes in AVM.

To access the submitted inner transactions:

1. Use `ctx.txn.last_group.last_itxn` to access the last submitted inner transaction of a specific type.
2. Iterate over all inner transactions in the last group using `ctx.txn.last_group.itxn_groups[-1]`.
3. Access a specific inner transaction group using `ctx.txn.last_group.get_itxn_group(index)`.

These methods provide type validation and will raise an error if the requested transaction type doesn't match the actual type of the inner transaction.

## References

-   [API](../api.md) for more details on the test context manager and inner transactions related methods that perform implicit inner transaction type validation.
-   [Examples](../examples.md) for more examples of smart contracts and associated tests that interact with inner transactions.
