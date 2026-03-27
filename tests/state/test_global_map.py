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
from _algopy_testing.state.global_map import GlobalMap
from _algopy_testing.state.global_state import GlobalState
from _algopy_testing.utils import as_bytes, as_string

from tests.artifacts.StateOps.contract import GlobalMapContract

GLOBAL_MAP_KEY_NOT_DEFINED_ERROR = "GlobalMap key has not been defined"
GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR = "GlobalMap key prefix is not defined"


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
        self.global_map = GlobalMap(UInt64, Bytes)


@pytest.fixture()
def context() -> Generator[AlgopyTestContext, None, None]:
    with algopy_testing_context() as ctx:  # noqa: SIM117
        with ctx.txn.create_group([ctx.any.txn.application_call()]):
            yield ctx


def test_init_without_key_prefix() -> None:
    with algopy_testing_context():
        contract = ATestContract()
        assert contract.global_map.key_prefix == b"global_map"


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
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key_prefix: bytes | str | Bytes | String,
    key: typing.Any,
) -> None:
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    assert gm.key_type == key_type
    assert gm.value_type == value_type
    assert len(gm.key_prefix) > 0

    key_prefix_bytes = (
        String(as_string(key_prefix)).bytes
        if isinstance(key_prefix, str | String)
        else Bytes(as_bytes(key_prefix))
    )
    assert gm.key_prefix == key_prefix_bytes

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_KEY_NOT_DEFINED_ERROR):
        _ = gm[key]

    assert key not in gm


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


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_value_setter(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    gm[key] = value
    content = gm[key]

    _assert_content_equality(value, content)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_value_deleter(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    gm[key] = value

    del gm[key]

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_KEY_NOT_DEFINED_ERROR):
        _ = gm[key]

    assert key not in gm


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_contains(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]

    assert key not in gm

    gm[key] = value
    assert key in gm

    del gm[key]
    assert key not in gm


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_get_with_default(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]

    result = gm.get(key, default=value)
    _assert_content_equality(value, result)

    gm[key] = value
    result = gm.get(key, default=None)
    _assert_content_equality(value, result)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_maybe_when_exists(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    gm[key] = value

    content, exists = gm.maybe(key)
    assert exists
    _assert_content_equality(value, content)


@pytest.mark.parametrize(("key_type", "value_type", "key", "value"), *test_data_array)
def test_maybe_when_not_exists(
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    gm[key] = value

    del gm[key]

    content, exists = gm.maybe(key)
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
    context: AlgopyTestContext,  # noqa: ARG001
    key_type: type,
    value_type: type,
    key: typing.Any,
    value: typing.Any,
) -> None:
    key_prefix = b"test_key_prefix"
    gm = GlobalMap(key_type, value_type, key_prefix=key_prefix)  # type: ignore[var-annotated]
    gm[key] = value

    gs = gm.state(key)
    assert isinstance(gs, GlobalState)
    assert gs.key == gm._full_key(key)
    assert gs.app_id == gm.app_id

    _assert_content_equality(value, gs.value)


def test_key_prefix_not_set_error(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    gm = GlobalMap(UInt64, Bytes)

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = gm.key_prefix

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = gm[UInt64(1)]

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        gm[UInt64(1)] = Bytes(b"test")

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        del gm[UInt64(1)]

    with pytest.raises(RuntimeError, match=GLOBAL_MAP_PREFIX_NOT_DEFINED_ERROR):
        _ = UInt64(1) in gm


def test_app_id(
    context: AlgopyTestContext,  # noqa: ARG001
) -> None:
    gm = GlobalMap(UInt64, Bytes, key_prefix=b"test")
    assert gm.app_id > 0


def _assert_content_equality(expected_value: typing.Any, actual_value: typing.Any) -> None:
    if hasattr(expected_value, "bytes"):
        assert actual_value.bytes == expected_value.bytes
    elif isinstance(expected_value, UInt64):
        assert actual_value == expected_value
    else:
        assert actual_value == expected_value


class TestGlobalMapContract:
    @pytest.fixture()
    def contract(self) -> Generator[GlobalMapContract, None, None]:
        with algopy_testing_context():
            yield GlobalMapContract()

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
        contract: GlobalMapContract,
        method_suffix: str,
        key: UInt64,
        value: typing.Any,
    ) -> None:
        getattr(contract, f"set_{method_suffix}")(key, value)
        result = getattr(contract, f"get_{method_suffix}")(key)
        _assert_content_equality(value, result)

    def test_key_prefix(self, contract: GlobalMapContract) -> None:
        assert contract.implicit_key_arc4_uint.key_prefix == Bytes(b"implicit_key_arc4_uint")
        assert contract.arc4_uint.key_prefix == Bytes(b"explicit_arc4_uint")
        assert contract.arc4_bool.key_prefix == Bytes(b"explicit_arc4_bool")

    def test_delete(self, contract: GlobalMapContract) -> None:
        key = UInt64(5)
        contract.set_implicit_key_arc4_uint(key, arc4.UInt64(100))
        assert contract.contains_implicit_key_arc4_uint(key)
        contract.delete_implicit_key_arc4_uint(key)
        assert not contract.contains_implicit_key_arc4_uint(key)

    def test_contains(self, contract: GlobalMapContract) -> None:
        key = UInt64(7)
        assert not contract.contains_implicit_key_arc4_uint(key)
        contract.set_implicit_key_arc4_uint(key, arc4.UInt64(50))
        assert contract.contains_implicit_key_arc4_uint(key)

    def test_maybe_exists(self, contract: GlobalMapContract) -> None:
        key = UInt64(3)
        contract.set_implicit_key_arc4_uint(key, arc4.UInt64(77))
        value, exists = contract.maybe_implicit_key_arc4_uint(key)
        assert exists
        assert value == arc4.UInt64(77)

    def test_maybe_not_exists(self, contract: GlobalMapContract) -> None:
        key = UInt64(99)
        value, exists = contract.maybe_implicit_key_arc4_uint(key)
        assert not exists

    def test_get_default_when_exists(self, contract: GlobalMapContract) -> None:
        key = UInt64(4)
        contract.set_implicit_key_arc4_uint(key, arc4.UInt64(88))
        result = contract.get_default_implicit_key_arc4_uint(key, arc4.UInt64(0))
        assert result == arc4.UInt64(88)

    def test_get_default_when_not_exists(self, contract: GlobalMapContract) -> None:
        key = UInt64(999)
        result = contract.get_default_implicit_key_arc4_uint(key, arc4.UInt64(42))
        assert result == arc4.UInt64(42)

    def test_multiple_keys(self, contract: GlobalMapContract) -> None:
        contract.set_implicit_key_arc4_uint(UInt64(1), arc4.UInt64(10))
        contract.set_implicit_key_arc4_uint(UInt64(2), arc4.UInt64(20))
        contract.set_implicit_key_arc4_uint(UInt64(3), arc4.UInt64(30))

        assert contract.get_implicit_key_arc4_uint(UInt64(1)) == arc4.UInt64(10)
        assert contract.get_implicit_key_arc4_uint(UInt64(2)) == arc4.UInt64(20)
        assert contract.get_implicit_key_arc4_uint(UInt64(3)) == arc4.UInt64(30)

    def test_get_missing_key_raises(self, contract: GlobalMapContract) -> None:
        with pytest.raises(RuntimeError, match="GlobalMap key has not been defined"):
            contract.get_implicit_key_arc4_uint(UInt64(404))

    def test_maps_independent(self, contract: GlobalMapContract) -> None:
        key = UInt64(1)
        contract.set_implicit_key_arc4_uint(key, arc4.UInt64(42))
        contract.set_arc4_uint(key, arc4.UInt64(99))

        assert contract.get_implicit_key_arc4_uint(key) == arc4.UInt64(42)
        assert contract.get_arc4_uint(key) == arc4.UInt64(99)
