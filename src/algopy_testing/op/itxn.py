import typing
from collections.abc import Callable

import algopy_testing
from algopy_testing._context_storage import get_test_context
from algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


class _ITxn:
    def __getattr__(self, name: str) -> Callable[[], typing.Any]:
        context = get_test_context()
        if not context._inner_transaction_groups:
            raise ValueError(
                "No inner transaction found in the context! Use `with algopy_testing_context()` "
                "to access the context manager."
            )
        last_itxn_group = context._inner_transaction_groups[-1]

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


class _ITxnCreate:
    def begin(self) -> None:
        context = get_test_context()
        context._constructing_inner_transaction_group = []

    def next(cls) -> None:
        context = get_test_context()
        if context._constructing_inner_transaction:
            context._constructing_inner_transaction_group.append(
                context._constructing_inner_transaction
            )
            context._constructing_inner_transaction = None

    def submit(cls) -> None:
        context = get_test_context()
        if context._constructing_inner_transaction:
            context._constructing_inner_transaction_group.append(
                context._constructing_inner_transaction
            )
            context._constructing_inner_transaction = None
            context._inner_transaction_groups.append(context._constructing_inner_transaction_group)
            context._constructing_inner_transaction_group = []

    def __getattr__(self, name: str) -> Callable[[typing.Any], None]:
        context = get_test_context()

        if not context._constructing_inner_transaction:
            context._constructing_inner_transaction = algopy_testing.itxn.InnerTransactionResult()

        def setter(value: typing.Any) -> None:
            self._set_field(name, value)

        return setter

    def _set_field(self, field: str, value: typing.Any) -> None:
        context = get_test_context()
        field = field.removeprefix("set_")
        field = OP_MEMBER_TO_TXN_MEMBER.get(field, field)
        if not context._constructing_inner_transaction:
            raise ValueError("No active inner transaction. Call ITxnCreate.begin() first.")
        setattr(context._constructing_inner_transaction, field, value)


ITxnCreate = _ITxnCreate()
