import contextlib
import typing
from collections.abc import Callable, Sequence

from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.op.constants import OP_MEMBER_TO_TXN_MEMBER


class _ITxn:
    def __getattr__(self, name: str) -> Callable[[], typing.Any]:
        inner_txn_groups = lazy_context.active_group.itxn_groups
        if not inner_txn_groups or not inner_txn_groups[-1]:
            raise RuntimeError("no previous inner transactions")

        last_itxn = inner_txn_groups[-1][-1]
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
        inner_txn_groups = lazy_context.active_group.itxn_groups
        if not inner_txn_groups or not inner_txn_groups[-1]:
            raise RuntimeError("no previous inner transactions")
        last_itxn_group = inner_txn_groups[-1]

        return lambda index: self._get_value(last_itxn_group, name, index)

    def _get_value(self, itxn_group: Sequence[typing.Any], name: str, index: int) -> object:
        try:
            itxn = itxn_group[index]
        except IndexError:
            raise ValueError("invalid group index") from None
        value = getattr(itxn, OP_MEMBER_TO_TXN_MEMBER.get(name, name))
        if value is None:
            raise ValueError(f"'{name}' is not defined for {type(itxn).__name__}")
        return value


GITxn = _GITxn()


class _ITxnCreate:
    def begin(self) -> None:
        lazy_context.active_group._begin_itxn_group()

    def next(self) -> None:
        lazy_context.active_group._append_itxn_group()

    def submit(self) -> None:
        lazy_context.active_group._submit_itxn_group()

    def __getattr__(self, name: str) -> Callable[[typing.Any], None]:
        def setter(value: typing.Any) -> None:
            field = OP_MEMBER_TO_TXN_MEMBER.get(
                name.removeprefix("set_"), name.removeprefix("set_")
            )
            citxn = lazy_context.active_group._constructing_itxn

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
