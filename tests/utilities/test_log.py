import typing
from collections.abc import Generator

import algokit_utils as au
import algopy
import pytest
from _algopy_testing import (
    AlgopyTestContext,
    FixedBytes,
    UInt64,
    algopy_testing_context,
    arc4,
)
from _algopy_testing.constants import MAX_UINT64, MAX_UINT512
from _algopy_testing.utilities.log import log, logged_assert, logged_err

from tests.artifacts.PrimitiveOps.contract import PrimitiveOpsContract
from tests.common import AVMInvoker


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:
        yield ctx


def test_log(get_avm_result: AVMInvoker, context: AlgopyTestContext) -> None:
    a = algopy.String("hello")
    b = algopy.UInt64(MAX_UINT64)
    c = algopy.Bytes(b"world")
    d = algopy.BigUInt(MAX_UINT512)
    e = arc4.Bool(True)
    f = arc4.String("greetings")
    g: arc4.UIntN[typing.Literal[64]] = arc4.UIntN[typing.Literal[64]](42)
    h: arc4.BigUIntN[typing.Literal[256]] = arc4.BigUIntN[typing.Literal[256]](512)
    i = arc4.UFixedNxM[typing.Literal[32], typing.Literal[8]]("42.94967295")
    j = arc4.BigUFixedNxM[typing.Literal[256], typing.Literal[16]]("25.5")
    k = arc4.StaticArray[arc4.UInt8, typing.Literal[3]](
        arc4.UInt8(1), arc4.UInt8(2), arc4.UInt8(3)
    )
    m = arc4.DynamicArray(arc4.UInt16(1), arc4.UInt16(2), arc4.UInt16(3))
    n = arc4.Tuple((arc4.UInt32(1), arc4.UInt64(2), arc4.String("hello")))
    o = FixedBytes[typing.Literal[5]](b"hello")

    avm_result = get_avm_result(
        "verify_log",
        a=a.value,
        b=b.value,
        c=c.value,
        d=d.bytes.value,
        e=e.native,
        f=f.native.value,
        g=g.as_uint64().value,
        h=h.as_biguint().value,
        i=int.from_bytes(i.bytes.value),
        j=int.from_bytes(j.bytes.value),
        k=k.bytes.value,
        m=m.bytes.value,
        n=n.bytes.value,
        o=o.bytes.value,
    )
    assert isinstance(avm_result, list)

    with context.txn.create_group([context.any.txn.payment()]):  # noqa: SIM117
        with pytest.raises(RuntimeError, match="Can only add logs to ApplicationCallTransaction!"):
            log(a, b, c, d, e, f, g, h, i, j, k, m, n, o, sep=b"-")

    dummy_app = context.any.application()
    with context.txn.create_group(
        [context.any.txn.application_call(app_id=dummy_app)], active_txn_index=0
    ):
        log(a, b, c, d, e, f, g, h, i, j, k, m, n, o, sep=b"-")

    last_txn = context.txn.last_active
    arc4_result = [last_txn.logs(i) for i in range(last_txn.num_logs)]
    assert avm_result == arc4_result


def test_user_supplied_logs(context: AlgopyTestContext) -> None:
    with context.txn.create_group([context.any.txn.application_call()]):
        log(b"\x81")  # should be logged but user supplied log is overriding it

    last_txn = context.txn.last_active
    logs = [last_txn.logs(i) for i in range(last_txn.num_logs)]
    assert logs == [b"\x81"]


class TestLoggedErrsOnChain:
    @pytest.fixture()
    def contract_ctx(
        self,
    ) -> Generator[tuple[PrimitiveOpsContract, AlgopyTestContext], None, None]:
        with algopy_testing_context() as ctx:
            yield PrimitiveOpsContract(), ctx

    def test_logged_errs(
        self,
        get_avm_result: AVMInvoker,
        contract_ctx: tuple[PrimitiveOpsContract, AlgopyTestContext],
    ) -> None:

        contract, context = contract_ctx

        def call(arg: int, error_message: str) -> None:
            with pytest.raises(au.LogicError, match=error_message):
                get_avm_result("verify_logged_errs", arg=arg)

        def test_call(arg: int, error_message: str) -> None:
            with (
                context.txn.create_group(
                    [context.any.txn.application_call(app_id=context.ledger.get_app(contract))],
                ),
                pytest.raises(RuntimeError, match=error_message),
            ):
                contract.verify_logged_errs(UInt64(arg))

        # arg=0 passes all assertions
        get_avm_result("verify_logged_errs", arg=0)
        contract.verify_logged_errs(UInt64(0))

        # arg=1 fails logged_assert -> "ERR:01"
        call(1, "ERR:01")
        test_call(1, "ERR:01")

        # arg=2 fails logged_assert -> "ERR:arg02:arg is two"
        call(2, "ERR:arg02:arg is two")
        test_call(2, "ERR:arg02:arg is two")

        # arg=3 fails logged_assert -> "AER:arg03"
        call(3, "AER:arg03")
        test_call(3, "AER:arg03")

        # arg=4 fails logged_assert -> "AER:arg04:arg is 4"
        call(4, "AER:arg04:arg is 4")
        test_call(4, "AER:arg04:arg is 4")

        # arg=5 fails logged_err -> "ERR:arg05"
        call(5, "ERR:arg05")
        test_call(5, "ERR:arg05")

        # arg=6 fails logged_err -> "ERR:06:arg was 6"
        call(6, "ERR:06:arg was 6")
        test_call(6, "ERR:06:arg was 6")

        # arg=7 fails logged_err -> "AER:arg07"
        call(7, "AER:arg07")
        test_call(7, "AER:arg07")

        # arg=8 fails logged_err -> "AER:arg08:arg is eight (08)"
        call(8, r"AER:arg08:arg is eight \(08\)")
        test_call(8, r"AER:arg08:arg is eight \(08\)")


class TestLoggedAssert:
    def test_true_condition_does_not_raise(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group([context.any.txn.application_call()]):
            logged_assert(True, "CODE")

    def test_true_condition_produces_no_logs(self, context: AlgopyTestContext) -> None:
        with context.txn.create_group([context.any.txn.application_call()]):
            logged_assert(True, "CODE", "msg")

        last_txn = context.txn.last_active
        assert last_txn.num_logs == 0

    def test_false_condition_logs_and_raises(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="ERR:INVALID"),
        ):
            logged_assert(False, "INVALID")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"ERR:INVALID"

    def test_with_message(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="ERR:CODE:bad value"),
        ):
            logged_assert(False, "CODE", "bad value")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"ERR:CODE:bad value"

    def test_with_aer_prefix(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="AER:CODE"),
        ):
            logged_assert(False, "CODE", prefix="AER")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"AER:CODE"


class TestLoggedErr:
    def test_logs_and_raises(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="ERR:FAIL"),
        ):
            logged_err("FAIL")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"ERR:FAIL"

    def test_with_message(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="ERR:OVERFLOW:too large"),
        ):
            logged_err("OVERFLOW", "too large")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"ERR:OVERFLOW:too large"

    def test_with_aer_prefix(self, context: AlgopyTestContext) -> None:
        with (
            context.txn.create_group([context.any.txn.application_call()]),
            pytest.raises(RuntimeError, match="AER:DENIED"),
        ):
            logged_err("DENIED", prefix="AER")

        last_txn = context.txn.last_active
        assert last_txn.logs(0) == b"AER:DENIED"


class TestErrorDetailsValidation:
    def test_code_with_colon_raises(self) -> None:
        with pytest.raises(ValueError, match="error code must not contain domain separator"):
            logged_err("BAD:CODE")

    def test_message_with_colon_raises(self) -> None:
        with pytest.raises(ValueError, match="error message must not contain domain separator"):
            logged_err("CODE", "bad:msg")

    def test_invalid_prefix_raises(self) -> None:
        with pytest.raises(ValueError, match="error prefix must be one of AER, ERR"):
            logged_err("CODE", prefix="BAD")  # type: ignore[arg-type]
