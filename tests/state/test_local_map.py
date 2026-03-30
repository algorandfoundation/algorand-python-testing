import typing
from collections.abc import Generator

import algopy
import pytest
from _algopy_testing import algopy_testing_context, arc4
from _algopy_testing.context import AlgopyTestContext
from _algopy_testing.primitives.biguint import BigUInt
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.string import String
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.state.local_map import LocalMap
from _algopy_testing.state.local_state import LocalState
from _algopy_testing.utils import as_bytes, as_string

from tests.artifacts.StateOps.contract import LocalMapContract

LOCAL_MAP_KEY_NOT_DEFINED_ERROR = "LocalMap key has not been defined"
LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR = "LocalMap key prefix is not defined"


class Swapped(arc4.Struct):
    b: arc4.UInt64
    c: arc4.Bool
    d: arc4.Address


class MyStruct(typing.NamedTuple):
    a: UInt64
    b: bool
    c: arc4.Bool
    d: arc4.UInt64
    e: Swapped


class ATestContract(algopy.Contract):
    def __init__(self) -> None:
        self.local_map = LocalMap(UInt64, Bytes)


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:  # noqa: SIM117
        with ctx.txn.create_group([ctx.any.txn.application_call()]):
            yield ctx


def test_init_without_key_prefix() -> None:
    with algopy_testing_context():
        contract = ATestContract()
        assert contract.local_map.key_prefix == b"local_map"


@pytest.mark.parametrize(
    ("key_type", "value_type", "key_prefix", "key"),
    [
        (Bytes, UInt64, "key_prefix", Bytes()),
        (String, Bytes, b"key_prefix", String()),
        (BigUInt, String, Bytes(b"key_prefix"), BigUInt()),
        (arc4.String, BigUInt, String("key_prefix"), arc4.String()),
        (UInt64, arc4.String, "key_prefix", UInt64()),
        (String, arc4.DynamicArray[arc4.DynamicBytes], b"key_prefix", String()),
        (
            tuple[UInt64, bool],
            arc4.DynamicArray[arc4.DynamicBytes],
            b"key_prefix",
            (UInt64(), True),
        ),
        (
            Swapped,
            Swapped,
            "key_prefix",
            Swapped(arc4.UInt64(), arc4.Bool(), arc4.Address()),
        ),
        (
            MyStruct,
            MyStruct,
            b"key_prefix",
            MyStruct(
                UInt64(),
                True,
                arc4.Bool(),
                arc4.UInt64(),
                Swapped(arc4.UInt64(), arc4.Bool(), arc4.Address()),
            ),
        ),
    ],
)
def test_init_with_key_prefix(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key_prefix: bytes | str | Bytes | String,
    key: typing.Any,
) -> None:
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    assert lm.key_type == key_type
    assert lm.value_type == value_type
    assert len(lm.key_prefix) > 0

    key_prefix_bytes = (
        String(as_string(key_prefix)).bytes
        if isinstance(key_prefix, str | String)
        else Bytes(as_bytes(key_prefix))
    )
    assert lm.key_prefix == key_prefix_bytes

    with pytest.raises(RuntimeError, match=LOCAL_MAP_KEY_NOT_DEFINED_ERROR):
        _ = lm[context.default_sender, key]

    assert (context.default_sender, key) not in lm


test_data_array = (
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (BigUInt, String, BigUInt(123), String("Test")),
        (arc4.String, BigUInt, arc4.String("ghi"), BigUInt(100)),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
        (
            String,
            arc4.DynamicArray[arc4.UInt64],
            String("jkl"),
            arc4.DynamicArray(*[arc4.UInt64(100), arc4.UInt64(200)]),
        ),
        (
            tuple[UInt64, bool],
            tuple[bool, UInt64],
            (UInt64(0), True),
            (True, UInt64(0)),
        ),
        (
            Swapped,
            Swapped,
            Swapped(arc4.UInt64(0), arc4.Bool(False), arc4.Address(algopy.Bytes(b"\x00" * 32))),
            Swapped(arc4.UInt64(1), arc4.Bool(True), arc4.Address(algopy.Bytes(b"\x01" * 32))),
        ),
        (
            MyStruct,
            MyStruct,
            MyStruct(
                UInt64(1),
                True,
                arc4.Bool(False),
                arc4.UInt64(2),
                Swapped(arc4.UInt64(3), arc4.Bool(True), arc4.Address(algopy.Bytes(b"\x00" * 32))),
            ),
            MyStruct(
                UInt64(11),
                False,
                arc4.Bool(True),
                arc4.UInt64(12),
                Swapped(
                    arc4.UInt64(13), arc4.Bool(False), arc4.Address(algopy.Bytes(b"\x01" * 32))
                ),
            ),
        ),
    ],
)


def _assert_content_equality(expected_value: typing.Any, actual_value: typing.Any) -> None:
    if hasattr(expected_value, "bytes"):
        assert actual_value.bytes == expected_value.bytes
    elif isinstance(expected_value, UInt64):
        assert actual_value == expected_value
    else:
        assert actual_value == expected_value


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_value_setter(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    lm[context.default_sender, key] = value
    content = lm[context.default_sender, key]

    _assert_content_equality(value, content)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_value_deleter(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    lm[context.default_sender, key] = value

    del lm[context.default_sender, key]

    with pytest.raises(RuntimeError, match=LOCAL_MAP_KEY_NOT_DEFINED_ERROR):
        _ = lm[context.default_sender, key]

    assert (context.default_sender, key) not in lm


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_contains(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]

    assert (context.default_sender, key) not in lm

    lm[context.default_sender, key] = value
    assert (context.default_sender, key) in lm

    del lm[context.default_sender, key]
    assert (context.default_sender, key) not in lm


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_get_with_default(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]

    result = lm.get(context.default_sender, key, default=value)
    _assert_content_equality(value, result)

    lm[context.default_sender, key] = value
    result = lm.get(context.default_sender, key, default=None)
    _assert_content_equality(value, result)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_maybe_when_exists(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    lm[context.default_sender, key] = value

    content, exists = lm.maybe(context.default_sender, key)
    assert exists
    _assert_content_equality(value, content)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_maybe_when_not_exists(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    lm[context.default_sender, key] = value

    del lm[context.default_sender, key]

    content, exists = lm.maybe(context.default_sender, key)
    assert not exists


@pytest.mark.parametrize(
    ("key_type", "value_type", "key", "value"),
    [
        (Bytes, UInt64, Bytes(b"abc"), UInt64(100)),
        (String, Bytes, String("def"), Bytes(b"Test")),
        (UInt64, arc4.String, UInt64(456), arc4.String("Test")),
    ],
)
def test_state_method(
    context: AlgopyTestContext,
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    lm = LocalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    lm[context.default_sender, key] = value

    ls = lm.state(key)
    assert isinstance(ls, LocalState)
    assert ls.key == lm._full_key(key)
    assert ls.app_id == lm.app_id

    _assert_content_equality(value, ls[context.default_sender])


def test_key_prefix_not_set_error(
    context: AlgopyTestContext,
) -> None:
    lm = LocalMap(UInt64, Bytes)
    account = context.default_sender

    with pytest.raises(RuntimeError, match=LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = lm.key_prefix

    with pytest.raises(RuntimeError, match=LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = lm[account, UInt64(1)]

    with pytest.raises(RuntimeError, match=LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        lm[account, UInt64(1)] = Bytes(b"test")

    with pytest.raises(RuntimeError, match=LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        del lm[account, UInt64(1)]

    with pytest.raises(RuntimeError, match=LOCAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = (account, UInt64(1)) in lm


def test_app_id(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    lm = LocalMap(UInt64, Bytes, key_prefix=b"test")
    assert lm.app_id > 0


def test_multiple_accounts(
    context: AlgopyTestContext,
) -> None:
    lm = LocalMap(UInt64, Bytes, key_prefix=b"test")
    account1 = context.default_sender
    account2 = context.any.account()
    key = UInt64(1)

    lm[account1, key] = Bytes(b"value1")
    lm[account2, key] = Bytes(b"value2")

    assert lm[account1, key] == Bytes(b"value1")
    assert lm[account2, key] == Bytes(b"value2")

    del lm[account1, key]
    assert (account1, key) not in lm
    assert (account2, key) in lm


def test_multiple_keys(
    context: AlgopyTestContext,
) -> None:
    lm = LocalMap(UInt64, Bytes, key_prefix=b"test")
    account = context.default_sender

    lm[account, UInt64(1)] = Bytes(b"one")
    lm[account, UInt64(2)] = Bytes(b"two")
    lm[account, UInt64(3)] = Bytes(b"three")

    assert lm[account, UInt64(1)] == Bytes(b"one")
    assert lm[account, UInt64(2)] == Bytes(b"two")
    assert lm[account, UInt64(3)] == Bytes(b"three")


def test_get_missing_key_raises(
    context: AlgopyTestContext,
) -> None:
    lm = LocalMap(UInt64, Bytes, key_prefix=b"test")
    with pytest.raises(RuntimeError, match=LOCAL_MAP_KEY_NOT_DEFINED_ERROR):
        _ = lm[context.default_sender, UInt64(404)]


class TestLocalMapContract:
    @pytest.fixture()
    def contract_ctx(self) -> Generator[tuple[LocalMapContract, AlgopyTestContext], None, None]:
        with algopy_testing_context() as ctx:
            contract = LocalMapContract()
            with ctx.txn.create_group(
                active_txn_overrides={"on_completion": algopy.OnCompleteAction.OptIn}
            ):
                contract.opt_in()
            yield contract, ctx

    @pytest.mark.parametrize(
        ("method_suffix", "key", "value"),
        [
            ("implicit_key_arc4_uint", UInt64(1), arc4.UInt64(42)),
            ("implicit_key_arc4_string", UInt64(1), arc4.String("Hello")),
            ("implicit_key_arc4_byte", UInt64(1), arc4.Byte(255)),
            ("implicit_key_arc4_bool", UInt64(1), arc4.Bool(True)),
            ("implicit_key_arc4_address", UInt64(1), arc4.Address(Bytes(b"\x01" * 32))),
            ("implicit_key_arc4_uint128", UInt64(1), arc4.UInt128(2**100)),
            ("implicit_key_arc4_dynamic_bytes", UInt64(1), arc4.DynamicBytes(b"dynamic")),
            ("arc4_uint", UInt64(10), arc4.UInt64(99)),
            ("arc4_string", UInt64(10), arc4.String("World")),
            ("arc4_bool", UInt64(10), arc4.Bool(False)),
            ("implicit_key_tuple", (UInt64(10), Bytes(b"test"), False), UInt64(1)),
        ],
    )
    def test_set_and_get(
        self,
        contract_ctx: tuple[LocalMapContract, AlgopyTestContext],
        method_suffix: str,
        key: typing.Any,
        value: typing.Any,
    ) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        getattr(contract, f"set_{method_suffix}")(account, key, value)
        result = getattr(contract, f"get_{method_suffix}")(account, key)
        _assert_content_equality(value, result)

    def test_key_prefix(self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]) -> None:
        contract, _ = contract_ctx
        assert contract.implicit_key_arc4_uint.key_prefix == Bytes(b"implicit_key_arc4_uint")
        assert contract.arc4_uint.key_prefix == Bytes(b"explicit_arc4_uint")
        assert contract.arc4_bool.key_prefix == Bytes(b"explicit_arc4_bool")

    def test_delete(self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        key = UInt64(5)
        contract.set_implicit_key_arc4_uint(account, key, arc4.UInt64(100))
        assert contract.contains_implicit_key_arc4_uint(account, key)
        contract.delete_implicit_key_arc4_uint(account, key)
        assert not contract.contains_implicit_key_arc4_uint(account, key)

    def test_contains(self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        key = UInt64(7)
        assert not contract.contains_implicit_key_arc4_uint(account, key)
        contract.set_implicit_key_arc4_uint(account, key, arc4.UInt64(50))
        assert contract.contains_implicit_key_arc4_uint(account, key)

    def test_maybe_exists(self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        key = UInt64(3)
        contract.set_implicit_key_arc4_uint(account, key, arc4.UInt64(77))
        value, exists = contract.maybe_implicit_key_arc4_uint(account, key)
        assert exists
        assert value == arc4.UInt64(77)

    def test_maybe_not_exists(
        self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]
    ) -> None:
        contract, ctx = contract_ctx
        key = UInt64(99)
        _value, exists = contract.maybe_implicit_key_arc4_uint(ctx.default_sender, key)
        assert not exists

    def test_get_default_when_exists(
        self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]
    ) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        key = UInt64(4)
        contract.set_implicit_key_arc4_uint(account, key, arc4.UInt64(88))
        result = contract.get_default_implicit_key_arc4_uint(account, key, arc4.UInt64(0))
        assert result == arc4.UInt64(88)

    def test_get_default_when_not_exists(
        self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]
    ) -> None:
        contract, ctx = contract_ctx
        key = UInt64(999)
        result = contract.get_default_implicit_key_arc4_uint(
            ctx.default_sender, key, arc4.UInt64(42)
        )
        assert result == arc4.UInt64(42)

    def test_multiple_keys(self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        contract.set_implicit_key_arc4_uint(account, UInt64(1), arc4.UInt64(10))
        contract.set_implicit_key_arc4_uint(account, UInt64(2), arc4.UInt64(20))
        contract.set_implicit_key_arc4_uint(account, UInt64(3), arc4.UInt64(30))

        assert contract.get_implicit_key_arc4_uint(account, UInt64(1)) == arc4.UInt64(10)
        assert contract.get_implicit_key_arc4_uint(account, UInt64(2)) == arc4.UInt64(20)
        assert contract.get_implicit_key_arc4_uint(account, UInt64(3)) == arc4.UInt64(30)

    def test_get_missing_key_raises(
        self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]
    ) -> None:
        contract, ctx = contract_ctx
        with pytest.raises(RuntimeError, match="LocalMap key has not been defined"):
            contract.get_implicit_key_arc4_uint(ctx.default_sender, UInt64(404))

    def test_maps_independent(
        self, contract_ctx: tuple[LocalMapContract, AlgopyTestContext]
    ) -> None:
        contract, ctx = contract_ctx
        account = ctx.default_sender
        key = UInt64(1)
        contract.set_implicit_key_arc4_uint(account, key, arc4.UInt64(42))
        contract.set_arc4_uint(account, key, arc4.UInt64(99))

        assert contract.get_implicit_key_arc4_uint(account, key) == arc4.UInt64(42)
        assert contract.get_arc4_uint(account, key) == arc4.UInt64(99)
