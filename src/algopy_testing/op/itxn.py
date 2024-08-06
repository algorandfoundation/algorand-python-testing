import typing
from collections.abc import Callable

from algopy_testing._context_storage import get_test_context


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

        value = getattr(last_itxn, name)
        if value is None:
            raise ValueError(f"'{name}' is not defined for {type(last_itxn).__name__} ")
        # mimic the static functions on ITxn with a lambda
        return lambda: value


ITxn = _ITxn()


# TODO: add tests for these ops
class _ITxnCreate:
    def begin(self) -> None:
        context = get_test_context()
        context._constructing_inner_transaction_group = []

    @classmethod
    def next(cls) -> None:
        context = get_test_context()
        if context._constructing_inner_transaction:
            context._constructing_inner_transaction_group.append(
                context._constructing_inner_transaction
            )
            context._constructing_inner_transaction = None

    @classmethod
    def submit(cls) -> None:
        context = get_test_context()
        if context._constructing_inner_transaction:
            context._constructing_inner_transaction_group.append(
                context._constructing_inner_transaction
            )
            context._constructing_inner_transaction = None
            context._inner_transaction_groups.append(context._constructing_inner_transaction_group)
            context._constructing_inner_transaction_group = []

    def __setattr__(self, name: str, value: typing.Any) -> None:
        if name.startswith("set_"):
            field = name[4:]  # Remove 'set_' prefix
            self._set_field(field, value)
        else:
            super().__setattr__(name, value)

    def _set_field(self, field: str, value: typing.Any) -> None:
        context = get_test_context()
        if not context._constructing_inner_transaction:
            raise ValueError("No active inner transaction. Call ITxnCreate.begin() first.")
        setattr(context._constructing_inner_transaction, field, value)


ITxnCreate = _ITxnCreate()
