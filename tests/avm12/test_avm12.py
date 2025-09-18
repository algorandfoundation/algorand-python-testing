import typing
from collections.abc import Generator

import pytest
from _algopy_testing import AlgopyTestContext, algopy_testing_context
from _algopy_testing.compiled import CompiledContract
from _algopy_testing.itxn import ApplicationCallInnerTransaction
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from algokit_utils import AlgoAmount
from pytest_mock import MockerFixture

from tests.artifacts.AVM12.contract import Contract
from tests.common import AVMInvoker


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_reject_version(
    get_avm_result: AVMInvoker, context: AlgopyTestContext, mocker: MockerFixture
) -> None:
    dummy_app = context.any.application()

    class MockArc4Create:
        def __call__(
            self, *_args: typing.Any, **_kwargs: typing.Any
        ) -> ApplicationCallInnerTransaction:
            return ApplicationCallInnerTransaction(created_app=dummy_app)

        def __getitem__(self, _item: object) -> typing.Self:
            return self

    class MockArc4Update:
        def __call__(
            self, *_args: typing.Any, **kwargs: typing.Any
        ) -> ApplicationCallInnerTransaction:
            kwargs["app_id"].version = 1
            return ApplicationCallInnerTransaction()

        def __getitem__(self, _item: object) -> typing.Self:
            return self

    mocker.patch("algopy.arc4.arc4_create", MockArc4Create())
    mocker.patch("algopy.arc4.arc4_update", MockArc4Update())
    mock_compile_contract = mocker.patch("tests.artifacts.AVM12.contract.compile_contract")
    mock_compile_contract.return_value = CompiledContract(
        approval_program=(Bytes(b""), Bytes(b"")),
        clear_state_program=(Bytes(b""), Bytes(b"")),
        extra_program_pages=UInt64(0),
        global_uints=UInt64(0),
        global_bytes=UInt64(0),
        local_uints=UInt64(0),
        local_bytes=UInt64(0),
    )

    contract = Contract()
    get_avm_result(
        "test_reject_version",
        static_fee=AlgoAmount(algo=1),
    )

    contract.test_reject_version()
