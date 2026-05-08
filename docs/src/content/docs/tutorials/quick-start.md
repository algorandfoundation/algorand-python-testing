---
title: Quick Start
description: Install algorand-python-testing and write your first contract test in minutes.
---

This tutorial walks through installing `algorand-python-testing`, writing a small ARC4 contract, and exercising it inside a test context.

## Install

`algorand-python-testing` is distributed via [PyPI](https://pypi.org/project/algorand-python-testing/) and requires Python 3.12+. [Algorand Python (`algopy`)](https://github.com/algorandfoundation/puya) is a peer dependency that ships the type stubs your contract code targets.

```bash
pip install algorand-python-testing
```

> [!NOTE]
> While `algorand-python-testing` offers valuable unit testing capabilities, it's not a replacement for comprehensive testing. Use it alongside other test types — particularly those running against the actual Algorand Network — for thorough contract validation.

## Write a contract

A small voting contract demonstrates ARC4 methods, payment-transaction guards, and global/local state:

```python
import algopy
from algopy import arc4

class VotingContract(algopy.ARC4Contract):
    def __init__(self) -> None:
        self.topic = algopy.GlobalState(algopy.Bytes(b"default_topic"), key="topic", description="Voting topic")
        self.votes = algopy.GlobalState(
            algopy.UInt64(0),
            key="votes",
            description="Votes for the option",
        )
        self.voted = algopy.LocalState(algopy.UInt64, key="voted", description="Tracks if an account has voted")

    @algopy.arc4.abimethod
    def set_topic(self, topic: arc4.String) -> None:
        self.topic.value = topic.bytes

    @arc4.abimethod
    def vote(self, pay: algopy.gtxn.PaymentTransaction) -> arc4.Bool:
        assert algopy.op.Global.group_size == algopy.UInt64(2), "Expected 2 transactions"
        assert pay.amount == algopy.UInt64(10_000), "Incorrect payment amount"
        assert pay.sender == algopy.Txn.sender, "Payment sender must match transaction sender"

        _value, exists = self.voted.maybe(algopy.Txn.sender)
        if exists:
            return arc4.Bool(False)  # Already voted
        self.votes.value += algopy.UInt64(1)
        self.voted[algopy.Txn.sender] = algopy.UInt64(1)
        return arc4.Bool(True)

    @algopy.arc4.abimethod(readonly=True)
    def get_votes(self) -> arc4.UInt64:
        return arc4.UInt64(self.votes.value)

    def clear_state_program(self) -> bool:
        return True
```

## Test it

Drive the contract with `algopy_testing_context()`. The context manager exposes value generators (`any`), an emulated ledger, and transaction-group helpers — enough to invoke ABI methods directly and assert against state changes.

```python
from algopy_testing import algopy_testing_context
from algopy import arc4

with algopy_testing_context() as context:
    contract = VotingContract()

    # Vote with a payment transaction
    voter = context.default_sender
    payment = context.any.txn.payment(
        sender=voter,
        amount=algopy.UInt64(10_000),
    )
    result = contract.vote(payment)
    assert result.native is True
    assert contract.votes.value == 1
    assert contract.voted[voter] == 1

    # Update the topic
    new_topic = context.any.arc4.string(10)
    contract.set_topic(new_topic)
    assert contract.topic.value == new_topic.bytes

    # Read votes back
    contract.votes.value = algopy.UInt64(5)
    assert contract.get_votes().native == 5
```

This example exercises every layer of the framework:

1. **ARC4 contracts**: `algopy.ARC4Contract` base class, `@arc4.abimethod` (and its `@algopy.arc4.abimethod` alias), and ARC4 types like `arc4.String`, `arc4.Bool`, `arc4.UInt64`.
2. **Test data**: `context.any.txn` for transactions, `context.any.arc4` for ARC4 values.
3. **Direct invocation**: ABI methods are called directly on the contract instance — no deployment.
4. **State verification**: assert against `self.votes.value`, `self.voted[...]`, etc.

## Next steps

- [Concepts → Test Context](/algorand-python-testing/concepts/test-context/) — deeper dive into the context manager
- [Concepts → Value Generators](/algorand-python-testing/concepts/value-generators/) — `any.*` generator surface
- [Guide → Contract Testing](/algorand-python-testing/guide/contract-testing/) — patterns for `ARC4Contract` and `Contract`
- [Examples](/algorand-python-testing/examples/) — full contracts with tests
- [API Reference](/algorand-python-testing/api/algopy_testing/) — complete module docs
