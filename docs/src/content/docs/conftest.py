from collections.abc import Iterator

import pytest
from algopy_testing import AlgopyTestContext, algopy_testing_context


@pytest.fixture()
def context() -> Iterator[AlgopyTestContext]:
    with algopy_testing_context() as ctx:
        yield ctx
