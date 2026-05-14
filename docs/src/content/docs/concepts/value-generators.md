---
title: Value Generators
description: Value generators produce constrained random values for AVM, transaction, and ARC4 types — handy for setting up test data without hand-crafting every field.
---

The [`AlgopyTestContext`](/algorand-python-testing/concepts/test-context/) exposes value generators via its `any` property. They produce randomized but constrained values for AVM entities (accounts, assets, applications, transactions, ARC4 types) so tests can focus on behaviour rather than fixture plumbing.

```python
import algopy
from algopy_testing import algopy_testing_context

with algopy_testing_context() as ctx:
    sender = ctx.any.account()
    payment = ctx.any.txn.payment(sender=sender, amount=algopy.UInt64(10_000))
    arc4_string = ctx.any.arc4.string(n=10)
```

## Generator namespaces

The `any` property exposes three generator surfaces:

-   `AVMValueGenerator`: Base abstractions for AVM types. All methods are available directly on the instance returned from `any` (e.g. `any.account()`, `any.asset()`, `any.uint64()`).
-   `TxnValueGenerator`: Accessible via `any.txn`, for transaction-related data (e.g. `any.txn.payment(...)`, `any.txn.application_call(...)`).
-   `ARC4ValueGenerator`: Accessible via `any.arc4`, for ARC4 type data (e.g. `any.arc4.string(...)`, `any.arc4.uint64(...)`).

For full method signatures, see the API reference:

-   [`algopy_testing.AVMValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/avm/)
-   [`algopy_testing.TxnValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/txn/)
-   [`algopy_testing.ARC4ValueGenerator`](/algorand-python-testing/api/algopy_testing/value_generators/arc4/)

> [!TIP]
> Value generators are powerful tools for generating test data for specified AVM types. They allow further constraints on random value generation via arguments, making it easier to generate test data when exact values are not necessary.
>
> When used with the 'Arrange, Act, Assert' pattern, value generators can be especially useful in setting up clear and concise test data in arrange steps.
>
> They can also serve as a base building block that can be integrated/reused with popular Python property-based testing frameworks like [`hypothesis`](https://hypothesis.readthedocs.io/en/latest/).
