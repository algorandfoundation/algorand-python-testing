# Smart Signature testing

Smart signatures, also known as logic signatures or LogicSigs, are programs that can be used to sign transactions. The Algorand Python Testing framework provides support for testing these programs.

## Defining a Logic Signature

To define a logic signature, you can use the `@logicsig` decorator:

```python
from algopy import logicsig, Account, Txn, Global, UInt64, Bytes

@logicsig
def hashed_time_locked_lsig() -> bool:
    # Your logic signature code here
    return True  # Approve the transaction
```

## Executing a Logic Signature

To test a logic signature, use the `execute_logicsig` method of the `AlgopyTestContext`. You can provide arguments to the logic signature using the `scoped_lsig_args` context manager:

```python
from algopy_testing import AlgopyTestContext

def test_logic_signature(context: AlgopyTestContext) -> None:
    # Set up the transaction group
    context.set_transaction_group(
        [
            context.any_payment_transaction(
                # Transaction fields...
            ),
        ],
        active_transaction_index=0,
    )

    # Execute the logic signature with arguments
    with context.scoped_lsig_args([algopy.Bytes(b"secret")]):
        result = context.execute_logicsig(hashed_time_locked_lsig)

    assert result is True
```

The `execute_logicsig` method takes one parameter which is an `lsig` itself, an instance of the logic signature function decorated with `@logicsig`.

The method returns the result of executing the logic signature, which is a `bool`:

-   If the logic signature returns `True`, it emulates approval of the transaction.
-   If it returns `False`, it emulates rejection of the transaction.

## Using `scoped_lsig_args`

The [`scoped_lsig_args`](#algopy_testing.context.AlgopyTestContext.scoped_lsig_args) context manager allows you to provide arguments to the logic signature for the duration of its execution. This is particularly useful when your logic signature expects input parameters accessed via `algopy.op.arg(n)`.

```python
with context.scoped_lsig_args([algopy.Bytes(b"secret")]):
    result = context.execute_logicsig(hashed_time_locked_lsig)
```

In this example, `b"secret"` is passed as an argument to the logic signature. Inside the logic signature, you can access this argument using `algopy.op.arg(0)`.

## Accessing Arguments in the Logic Signature

Within your logic signature, you can access the provided arguments using the `algopy.op.arg()` function:

```python
@logicsig
def hashed_time_locked_lsig() -> bool:
    secret = algopy.op.arg(0)
    # Use the secret in your logic
    is_secret_correct = algopy.op.sha256(secret) == expected_hash
    # ... rest of the logic
```

```{hint}
For coverage details on `algopy.op.arg` and other available operations, see the [Algorand Python Testing Framework Reference](../coverage.md).
```
