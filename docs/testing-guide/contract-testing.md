# Smart Contract Testing

This guide provides an overview of how to test smart contracts using the Algorand Python SDK (`algopy`). We will cover the basics of testing `ARC4Contract` and `Contract` classes, focusing on `abimethod` and `baremethod` decorators.

![](https://mermaid.ink/img/pako:eNqVkrFugzAQhl_Fujnp1ImhEiJrJNREWeoOV9sNVsFG9iEVBd69R5w0JE2llsk2n7-7_-AAymsDGewDtpXYrqQT_GyKFwl5vfcBnRZlT5V3IjYYSCjvKKAiCa-JzXfrObyzgTqsxRpVZZ25YOX2nnRrIomCneZzpszLkllktu0f8ratrUKyjFsXCZ1K2gTH7i01_8dGUjOT_55YeLdUFVr3zRunf5b6R5hZoFnBq9cX72_Br_Cj8bl4vJCHaVucvowYxHk5Xg_sfPkY6SbbphDL5dMgQZu29n0U5DMJwzTVGyApySKZKFSNMXKVxPJYYAGNCQ1azX_VYboqgSrTcAcZLzWGDwnSjcxhR37TOwUZhc4sIPhuX0H2jnXkXddqrrCyyKNpTqfjF5m74B8?type=png)

```{note}
The code snippets showcasing the contract testing capabilities are using [pytest](https://docs.pytest.org/en/latest/) as the test framework. However, note that the `algorand-python-testing` package can be used with any other test framework that supports Python. `pytest` is used for demonstration purposes in this documentation.
```

## ARC4Contract

Classes prefixed with `algopy.ARC4Contract` are **required** to be instantiated withing test context. As part of instantiation, the test context will automatically create a matching `algopy.Application` object instance.

Within the class implementation, methods decorated with `algopy.arc4.abimethod` and `algopy.arc4.baremethod` will automatically assemble an `algopy.gtxn.ApplicationCallTransaction` transaction to emulate the AVM application call. This behavior can be overriden by setting the transaction group manually as part of test setup, this is done via implicit invocation of [algopy_testing.context.any_application()](#algopy_testing.context.AlgopyTestContext.any_application) _value generator_.

```python
from algopy import ARC4Contract, GlobalState, LocalState, UInt64, Txn, arc4
from algopy_testing import algopy_testing_context
import pytest
from algopy import UInt64

class SimpleVotingContract(ARC4Contract):
    def __init__(self):
        self.topic = GlobalState(UInt64(0), key="topic", description="Current voting topic ID")
        self.votes = GlobalState(UInt64(0), key="votes", description="Total votes cast")
        self.has_voted = LocalState(UInt64(0), key="voted", description="Whether an account has voted")

    @arc4.abimethod(create="require")
    def create(self, initial_topic: UInt64) -> None:
        self.topic.value = initial_topic

    @arc4.abimethod
    def vote(self) -> UInt64:
        assert self.has_voted[Txn.sender] == UInt64(0), "Account has already voted"
        self.votes.value += UInt64(1)
        self.has_voted[Txn.sender] = UInt64(1)
        return self.votes.value

    @arc4.abimethod(readonly=True)
    def get_votes(self) -> UInt64:
        return self.votes.value

    @arc4.abimethod
    def change_topic(self, new_topic: UInt64) -> None:
        assert Txn.sender == Txn.application_id.creator_address(), "Only creator can change topic"
        self.topic.value = new_topic
        self.votes.value = UInt64(0)
        # Reset all votes (this is simplified and not efficient for many users)
        self.has_voted.delete()

...

@pytest.fixture
def context():
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()

def test_simple_voting_contract(context):
    # Arrange
    initial_topic = UInt64(1)
    contract = SimpleVotingContract()

    # Act - Create the contract
    contract.create(initial_topic)

    # Assert - Check initial state
    assert contract.topic.value == initial_topic
    assert contract.votes.value == UInt64(0)

    # Act - Vote
    # note how `algopy.Txn` is temporarily overriden to emulate the transaction content
    # the method `.vote()` is decorated with `algopy.arc4.abimethod`, which means it will assemble a transaction to emulate the AVM application call
    with context.scoped_txn_fields(sender=context.default_creator):
        result = contract.vote()

    # Assert - you can access the corresponding auto generated application call transaction via test context
    assert len(context.get_transaction_group()) == 1

    # Assert - Note how local and global state are accessed via regular python instance attributes
    assert result == UInt64(1)
    assert contract.votes.value == UInt64(1)
    assert contract.has_voted[context.default_creator] == UInt64(1)

    # Act - Change topic
    new_topic = UInt64(2)
    with context.scoped_txn_fields(sender=context.default_creator):
        contract.change_topic(new_topic)

    # Assert - Check topic changed and votes reset
    assert contract.topic.value == new_topic
    assert contract.votes.value == UInt64(0)
    assert contract.has_voted[context.default_creator] == UInt64(0)

    # Act - Get votes (should be 0 after reset)
    votes = contract.get_votes()

    # Assert - Check votes
    assert votes == UInt64(0)
```

For more examples of tests using `algopy.ARC4Contract`, see the [examples](../examples.md) section.

## Contract

Classes prefixed with `algopy.Contract` (parent class of `algopy.ARC4Contract`) are **required** to be instantiated withing test context. As part of instantiation, the test context will automatically create a matching `algopy.Application` object instance. This behaviour is identical to `algopy.ARC4Contract` class instances.

Unlike `algopy.ARC4Contract`, `algopy.Contract` requires manual setup of the transaction context and explicit method calls. Here's an example demonstrating how to test a `Contract` class:

```python
import algopy
import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context

class CounterContract(algopy.Contract):
    def __init__(self):
        self.counter = algopy.UInt64(0)

    @algopy.submethod
    def increment(self):
        self.counter.set(self.counter.value + algopy.UInt64(1))
        return algopy.UInt64(1)

    @algopy.baremethod
    def approval_program(self):
        return self.increment()

    @algopy.baremethod
    def clear_state_program(self):
        return algopy.UInt64(1)

@pytest.fixture()
def context():
    with algopy_testing_context() as ctx:
        yield ctx
        ctx.reset()

def test_counter_contract(context: AlgopyTestContext):
    # Instantiate contract as you normally would with a regular python class
    contract = CounterContract()

    # Access the default creator account from the test context (created by default on test context creation)
    user = context.default_creator

    # Set the transaction group to emulate the application call
    context.set_transaction_group(
        gtxn=[
            context.any_application_call_transaction(
                sender=user,
                app_id=context.any_application(),
                app_args=[algopy.Bytes(b"increment")],
            ),
        ],
        active_transaction_index=0,
    )

    # Invoke approval program
    result = contract.approval_program()

    # Assert approval program result
    assert result == algopy.UInt64(1)

    # Assert counter value
    assert contract.counter.value == algopy.UInt64(1)

    # Test clear state program
    assert contract.clear_state_program() == algopy.UInt64(1)
```
