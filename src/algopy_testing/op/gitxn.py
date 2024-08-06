import typing
from collections.abc import Callable, Sequence

from algopy_testing._context_storage import get_test_context
from algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


# TODO: combine with itxn
class _GITxn:
    def __getattr__(self, name: str) -> Callable[[int], typing.Any]:
        context = get_test_context()
        if not context._inner_transaction_groups:
            raise ValueError(
                "No inner transaction found in the context! Use `with algopy_testing_context()` "
                "to access the context manager."
            )
        last_itxn_group = context._inner_transaction_groups[-1]

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
