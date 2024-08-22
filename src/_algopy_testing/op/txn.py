from __future__ import annotations

import typing

from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


class _Txn:
    def __getattr__(self, name: str) -> typing.Any:
        active_txn = lazy_context.active_group.active_txn
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
        txn_group = lazy_context.active_group

        # for gtxn all fields are functions with at least one argument (the group_index)
        def get_field(group_index: int, array_index: int | None = None) -> typing.Any:
            try:
                txn = txn_group.txns[group_index]
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
