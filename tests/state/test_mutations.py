from collections.abc import Generator

import algopy
import algopy_testing
import pytest

from tests.artifacts.StateMutations.statemutations import StateMutations


@pytest.fixture()
def context() -> Generator[algopy_testing.AlgopyTestContext, None, None]:
    with algopy_testing.algopy_testing_context() as ctx:
        yield ctx


def test_state_mutations(
    context: algopy_testing.AlgopyTestContext,
) -> None:
    contract = StateMutations()

    with context.txn.create_group(
        active_txn_overrides={"on_completion": algopy.OnCompleteAction.OptIn}
    ):
        contract.opt_in()

    # get
    response = contract.get()
    assert response.length == 0

    # append
    contract.append()
    response = contract.get()
    assert response.length == 1
    first = response[0]
    assert first.bar == 1
    assert first.baz == "baz"

    # modify
    contract.modify()
    response = contract.get()
    assert response.length == 1
    first = response[0]
    assert first.bar == 1
    assert first.baz == "modified"

    # append
    contract.append()
    response = contract.get()
    assert response.length == 2
    first = response[0]
    assert first.bar == 1
    assert first.baz == "modified"

    second = response[1]
    assert second.bar == 1
    assert second.baz == "baz"
