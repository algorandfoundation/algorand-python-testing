# Smart Signature testing

Smart signatures, also known as logic signatures or LogicSigs, are programs that can be used to sign transactions. The Algorand Python Testing framework provides support for testing these programs.

## Defining a Logic Signature

To define a logic signature, you can use the `algopy.LogicSig` class:

```python
from algopy import LogicSig, Bytes, UInt64

def my_logic_sig() -> UInt64:
    # Your logic signature code here
    return UInt64(1)  # Approve the transaction
```

## Executing a Logic Signature

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
