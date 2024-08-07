import typing
from collections.abc import Callable, Sequence

from algopy_testing._context_storage import get_test_context
from algopy_testing.itxn import InnerTransactionResult
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
        get_test_context()._txn_context.begin_constructing_itxn_group()

    def next(self) -> None:
        get_test_context()._txn_context.add_to_constructing_itxn_group()

    def submit(self) -> None:
        get_test_context()._txn_context.submit_constructing_itxn_group()

    def __getattr__(self, name: str) -> Callable[[typing.Any], None]:
        context = get_test_context()._txn_context

        if context.constructing_inner_txn is None:
            context.constructing_inner_txn = InnerTransactionResult()

        def setter(value: typing.Any) -> None:
            field = OP_MEMBER_TO_TXN_MEMBER.get(
                name.removeprefix("set_"), name.removeprefix("set_")
            )
            setattr(context.constructing_inner_txn, field, value)

        return setter


ITxnCreate = _ITxnCreate()
