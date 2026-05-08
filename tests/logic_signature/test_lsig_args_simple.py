from collections.abc import Generator

import pytest
from algopy import Bytes, UInt64
from algopy_testing import AlgopyTestContext, algopy_testing_context

from tests.artifacts.LogicSignature.lsig_args_simple import args_simple


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_args_simple_with_large_arg0(context: AlgopyTestContext) -> None:
    result = context.execute_logicsig(args_simple, UInt64(42), Bytes(b"hello"), True)
    assert result == 42


def test_args_simple_with_small_arg0(context: AlgopyTestContext) -> None:
    result = context.execute_logicsig(args_simple, UInt64(5), Bytes(b"hello"), True)
    assert result == 10


def test_args_simple_with_false_arg2(context: AlgopyTestContext) -> None:
    result = context.execute_logicsig(args_simple, UInt64(42), Bytes(b"data"), False)
    # arg2 becomes True after `not arg2`, so total = arg0 + arg1.length
    # arg1 = b"data" + b"suffix" = 10 bytes
    assert result == 42 + 10
