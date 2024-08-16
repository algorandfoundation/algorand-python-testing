from __future__ import annotations

import typing

from algopy_testing.protocols import UInt64Backed

if typing.TYPE_CHECKING:
    import algopy


T = typing.TypeVar("T")


class AssetFields(typing.TypedDict, total=False):
    total: algopy.UInt64
    decimals: algopy.UInt64
    default_frozen: bool
    unit_name: algopy.Bytes
    name: algopy.Bytes
    url: algopy.Bytes
    metadata_hash: algopy.Bytes
    manager: algopy.Account
    reserve: algopy.Account
    freeze: algopy.Account
    clawback: algopy.Account
    creator: algopy.Account


class Asset(UInt64Backed):
    def __init__(self, asset_id: algopy.UInt64 | int = 0):
        from algopy import UInt64

        self.id = asset_id if isinstance(asset_id, UInt64) else UInt64(asset_id)

    @property
    def int_(self) -> int:
        return self.id.value

    @classmethod
    def from_int(cls, value: int, /) -> typing.Self:
        return cls(value)

    def balance(self, account: algopy.Account) -> algopy.UInt64:
        from algopy_testing._context_helpers import lazy_context

        account_data = lazy_context.get_account_data(account.public_key)

        if not account_data:
            raise ValueError("Account not found in testing context!")

        if int(self.id) not in account_data.opted_asset_balances:
            raise ValueError(
                "The asset is not opted into the account! "
                "Use `account.opt_in()` to opt the asset into the account."
            )

        return account_data.opted_asset_balances[self.id]

    def frozen(self, _account: algopy.Account) -> bool:
        # TODO: 1.0 expand data structure on AccountContextData.opted_asset_balances
        #       to support frozen attribute
        raise NotImplementedError(
            "The 'frozen' method is being executed in a python testing context. "
            "Please mock this method using your python testing framework of choice."
        )

    def __getattr__(self, name: str) -> object:
        from algopy_testing._context_helpers import lazy_context

        if int(self.id) not in lazy_context.ledger.asset_data:
            # check if its not 0 (which means its not
            # instantiated/opted-in yet, and instantiated directly
            # without invoking any_asset).
            if self.id == 0:
                # Handle dunder methods specially
                if name.startswith("__") and name.endswith("__"):
                    return getattr(type(self), name)
                # For non-dunder attributes, check in __dict__
                if name in self.__dict__:
                    return self.__dict__[name]
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                )

            raise ValueError(
                "`algopy.Asset` is not present in the test context! "
                "Use `context.add_asset()` or `context.any.asset()` to add the asset to "
                "your test setup."
            )

        return_value = lazy_context.get_asset_data(self.id).get(name)
        if return_value is None:
            raise AttributeError(
                f"The value for '{name}' in the test context is None. "
                f"Make sure to patch the global field '{name}' using your `AlgopyTestContext` "
                "instance."
            )

        return return_value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Asset):
            return self.id == other.id
        return self.id == other

    def __bool__(self) -> bool:
        return self.id != 0

    def __hash__(self) -> int:
        return hash(self.id)
