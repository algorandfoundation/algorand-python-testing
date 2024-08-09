import contextlib
import typing
from collections.abc import Callable, Sequence

from algopy_testing._context_helpers.context_storage import get_test_context
from algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


class _ITxn:
    def __getattr__(self, name: str) -> Callable[[], typing.Any]:
        context = get_test_context()
        if not context._txn_context.inner_txn_groups:
            raise ValueError(
                "No inner transaction found in the context! Use `with algopy_testing_context()` "
                "to access the context manager."
            )
        last_itxn_group = context._txn_context.inner_txn_groups[-1]

        if not last_itxn_group:
            raise ValueError("No inner transaction found in the testing context!")

        last_itxn = last_itxn_group[-1]
        field = name.removeprefix("set_")
        field = OP_MEMBER_TO_TXN_MEMBER.get(field, field)

        value = getattr(last_itxn, field)
        if value is None:
            raise ValueError(f"'{name}' is not defined for {type(last_itxn).__name__} ")
        # mimic the static functions on ITxn with a lambda
        return lambda: value


ITxn = _ITxn()


class _GITxn:
    def __getattr__(self, name: str) -> Callable[[int], typing.Any]:
        context = get_test_context()
        if not context._txn_context.inner_txn_groups:
            raise ValueError(
                "No inner transaction found in the context! Use `with algopy_testing_context()` "
                "to access the context manager."
            )
        last_itxn_group = context._txn_context.inner_txn_groups[-1]

        if not last_itxn_group:
            raise ValueError("No inner transaction found in the testing context!")

        return lambda index: self._get_value(last_itxn_group, name, index)

    def _get_value(self, itxn_group: Sequence[typing.Any], name: str, index: int) -> object:
        if index >= len(itxn_group):
            raise IndexError("Transaction index out of range")
        itxn = itxn_group[index]
        value = getattr(itxn, OP_MEMBER_TO_TXN_MEMBER.get(name, name))
        if value is None:
            raise ValueError(f"'{name}' is not defined for {type(itxn).__name__}")
        return value


GITxn = _GITxn()


class _ITxnCreate:
    def begin(self) -> None:
        context = get_test_context()
        context.txn.begin_itxn_group()

    def next(self) -> None:
        context = get_test_context()
        context.txn.append_itxn_group()

    def submit(self) -> None:
        context = get_test_context()
        context.txn.submit_itxn_group()

    def __getattr__(self, name: str) -> Callable[[typing.Any], None]:
        context = get_test_context()

        def setter(value: typing.Any) -> None:
            field = OP_MEMBER_TO_TXN_MEMBER.get(
                name.removeprefix("set_"), name.removeprefix("set_")
            )
            citxn = context.txn.constructing_itxn

            # approval_program and clear_state_program act like a set instead of append
            if field in ("approval_program", "clear_state_program"):
                with contextlib.suppress(KeyError):
                    del citxn.fields[field]
            # page variants go to a field without a _page suffix
            elif field in ("approval_program_pages", "clear_state_program_pages"):
                field = field.removesuffix("_pages")
            # treat array fields as append
            if field in (
                "approval_program",
                "clear_state_program",
                "accounts",
                "assets",
                "apps",
                "app_args",
            ):
                existing_value = citxn.fields.get(field, ())
                assert isinstance(existing_value, tuple)
                value = (*existing_value, value)
            citxn.set(**{field: value})

        return setter


ITxnCreate = _ITxnCreate()
