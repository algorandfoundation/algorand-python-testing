---
title: Test Context
description: The test context manager creates an emulated Algorand environment that mimics AVM behaviour for offline unit testing of smart contracts.
---

The main abstraction for interacting with the testing framework is the [`AlgopyTestContext`](/algorand-python-testing/api/algopy_testing/context/). It creates an emulated Algorand environment that closely mimics AVM behaviour relevant to unit testing contracts and provides a Pythonic interface for interacting with the emulated environment.

```python
from algopy_testing import algopy_testing_context

def test_my_contract():
    # Recommended way to instantiate the test context
    with algopy_testing_context() as ctx:
        # Your test code here
        pass
    # ctx is automatically reset after the test code is executed
```

The context manager interface exposes three main properties:

1. `ledger`: An instance of `LedgerContext` for interacting with and querying the emulated Algorand ledger state.
2. `txn`: An instance of `TransactionContext` for creating and managing transaction groups, submitting transactions, and accessing transaction results.
3. `any`: An instance of `AlgopyValueGenerator` for generating randomized test data — covered in detail under [Value Generators](/algorand-python-testing/concepts/value-generators/).

For detailed method signatures, parameters, and return types, refer to the following API sections:

-   [`algopy_testing.LedgerContext`](/algorand-python-testing/api/algopy_testing/context_helpers/ledger_context/)
-   [`algopy_testing.TransactionContext`](/algorand-python-testing/api/algopy_testing/context_helpers/txn_context/)
-   [`algopy_testing.AVMValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/avm/)
-   [`algopy_testing.TxnValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/txn/)
-   [`algopy_testing.ARC4ValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/arc4/)

## Types of `algopy` stub implementations

As explained in the [introduction](/algorand-python-testing/), `algorand-python-testing` _injects_ test implementations for stubs available in the `algorand-python` package. However, not all of the stubs are implemented in the same manner:

1. **Native**: Fully matches AVM computation in Python. For example, `algopy.op.sha256` and other cryptographic operations behave identically in AVM and unit tests. This implies that the majority of opcodes that are 'pure' functions in AVM also have a native Python implementation provided by this package. These abstractions and opcodes can be used within and outside of the testing context.

2. **Emulated**: Uses `AlgopyTestContext` to mimic AVM behaviour. For example, `Box.put` on an `algopy.Box` within a test context stores data in the test manager, not the real Algorand network, but provides the same interface.

3. **Mockable**: Not implemented, but can be mocked or patched. For example, `algopy.abi_call` can be mocked to return specific values or behaviours; otherwise, it raises a `NotImplementedError`. This category covers cases where native or emulated implementation in a unit test context is impractical or overly complex.

For a full list of all public `algopy` types and their corresponding implementation category, refer to the [Coverage](/algorand-python-testing/reference/coverage/) section.

## Data Validation

Algorand Python and the puya compiler have functionality to perform validation of transaction inputs via the `--validate-abi-args`, `--validate-abi-return` CLI arguments, `arc4.abimethod(validate_encoding=...)` decorator (or its alias, `algopy.public`), `.validate()` methods, and the `validate` parameter of `arc4.decode(...)`.
The Algorand Python Testing library does _NOT_ implement this validation behaviour, as you should test invalid inputs using an integrated test against a real Algorand network.
