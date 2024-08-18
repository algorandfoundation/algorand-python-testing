# Concepts

The following sections provide an overview of the key concepts and features of the Algorand Python Testing framework.

## Test Context

The main abstraction to interact with the testing framework is the [`AlgopyTestContext`](algopy_testing.AlgopyTestContext). It creates an emulated Algorand environment that closely mimics AVM behavior relevant to unit testing the contracts and provides a Pythonic interface for interacting with the emulated environment.

```python
from algopy_testing import algopy_testing_context

def test_my_contract():
    # 1. Instantiating the test context
    with algopy_testing_context() as ctx:
        ... # your test code here

    # 2. Alternatively, you can instantiate the test context manually
    ctx = AlgopyTestContext()
    ... # your test code here
    ctx.reset()  # Reset the emulated environment
```

### Managing Test Context State

1. **Automatic Reset with Context Manager**:

    ```python
    with algopy_testing_context() as ctx:
        ... # your test code here
    # Context is reset after exiting the block
    ```

    Recommended for its automatic management and efficiency.

2. **Manual Cleanup with `clear()`**:

    ```python
    ctx = AlgopyTestContext()
    ... # your test code here
    ctx.clear()
    ```

    Clears state without resetting counters or recreating default objects. Useful between related tests.

3. **Manual Reset with `reset()`**:
    ```python
    ctx = AlgopyTestContext()
    ... # your test code here
    ctx.reset()
    ```
    Thoroughly resets the context, reinitializing all data structures and settings. Ideal for unrelated test suites.

```{hint}
Use `clear()` for quick state clearance between related tests, and `reset()` for a completely fresh environment.
```

## Types of `algopy` stub implementations

As explained in the [introduction](index.md), `algorand-python-testing` _injects_ test implementations for stubs available in `algorand-python` package. However, not all of the stubs implemented in the same manner:

1. **Native**: Fully matches AVM computation in Python. For example, `algopy.op.sha256` and other cryptographic operations behave identically in AVM and unit tests. This implies the majority of opcodes that are 'pure' functions in AVM also have a native Python implementation provided by this package. These abstractions and opcodes can be used within and outside of the testing context.

2. **Emulated**: Uses `AlgopyTestContext` to mimic AVM behavior. For example, `Box.put` on an `algopy.Box` within a test context stores data in the test manager, not the real Algorand network, but provides the same interface.

3. **Mockable**: Not implemented but can be mocked or patched. For example, `algopy.abi_call` can be mocked to return specific values or behaviors; otherwise, it raises a `NotImplementedError`. In other words, this category covers the cases where native or emulated implementation in a unit test context is impractical or overly complex.

For a full list of all public `algopy` types and their corresponding implementation category, refer to the [Coverage](coverage.md) section.

## Value generators

Testing context provides an range of helper methods called _value generators_ which allow quick generate and/or instantiation of randomized values for specified AVM types, which is also a common building block in _property-based_ testing methodologies. To access them, refer to methods prefixed with word `any_*` or `arc4.any_*` on the test context instance.

For detailed breakdown of all available value generators and their arguments, refer to the [API docs](api.md).

```{note}
Value generators are a powerful tool for generating test data for specified AVM types. Additionally, they allow further constraints on random value generation via arguments, making it easier to generate test data when the exact values are not necessary as long as the generated values meet the constraints.

If used with the 'Arrange, Act, Assert' pattern, value generators can be especially useful in setting up clear and concise test data in arrange steps.
```

### Property-based testing

`algorand-python-testing` aims to be agnostic of the specific Python testing framework being used. The [`value generators`](#value-generators), serve as a base building block that can be integrated/reused with popular Python property-based testing frameworks like [`hypothesis`](https://hypothesis.readthedocs.io/en/latest/).
