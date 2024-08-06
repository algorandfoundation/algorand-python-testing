from __future__ import annotations

import typing

from algopy_testing._context_storage import get_test_context
from algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


class _Txn:
    def __getattr__(self, name: str) -> typing.Any:
        context = get_test_context()
        active_txn = context.get_active_transaction()
        txn_name = OP_MEMBER_TO_TXN_MEMBER.get(name, name)
        field = getattr(active_txn, txn_name)
        # fields with multiple values are exposed as functions in the stubs
        if isinstance(field, tuple):

            def get_field(index: int) -> typing.Any:
                try:
                    return field[index]
                except ValueError:
                    raise ValueError("invalid array index") from None

            return get_field
        else:
            return field


class _GTxn:
    def __getattr__(self, name: str) -> typing.Any:
        context = get_test_context()
        txn_group = context._current_transaction_group
        if not txn_group:
            raise ValueError(
                "No group transactions found in the context! Use `with algopy_testing_context()` "
                "to access the context manager."
            )

        # for gtxn all fields are functions with at least one argument (the group_index)
        def get_field(group_index: int, array_index: int | None = None) -> typing.Any:
            try:
                txn = txn_group[group_index]
            except IndexError:
                raise ValueError("invalid group index") from None

            field_name = OP_MEMBER_TO_TXN_MEMBER.get(name, name)
            field = txn.fields[field_name]
            match field, array_index:
                case [[*items], int(index)]:
                    try:
                        return items[index]
                    except ValueError:
                        raise ValueError("invalid array index") from None
                case _, None:
                    return field
                case _:
                    raise ValueError("invalid number of arguments")

        return get_field


Txn = _Txn()
GTxn = _GTxn()
