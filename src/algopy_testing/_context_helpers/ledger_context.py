from __future__ import annotations

import typing
from collections import defaultdict

from algopy_testing.constants import MAX_BOX_SIZE
from algopy_testing.models.account import Account
from algopy_testing.primitives.uint64 import UInt64
from algopy_testing.utils import as_bytes, assert_address_is_valid, get_default_global_fields

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.models.account import AccountFields
    from algopy_testing.models.application import ApplicationContextData, ApplicationFields
    from algopy_testing.models.asset import AssetFields
    from algopy_testing.op.global_values import GlobalFields


class LedgerContext:
    """Context for managing the ledger state."""

    def __init__(self) -> None:
        from algopy_testing.models.account import AccountContextData, get_empty_account

        self.account_data = defaultdict[str, AccountContextData](get_empty_account)
        self.app_data: dict[int, ApplicationContextData] = {}
        self.asset_data: dict[int, AssetFields] = {}
        self.blocks: dict[int, dict[str, int]] = {}
        self.global_fields: GlobalFields = get_default_global_fields()

        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

    def get_next_asset_id(self) -> int:
        while True:
            asset_id = next(self._asset_id)
            if asset_id not in self.asset_data:
                return asset_id

    def get_next_app_id(self) -> int:
        while True:
            app_id = next(self._app_id)
            if app_id not in self.app_data:
                return app_id

    def get_account(self, address: str) -> algopy.Account:
        """Get an account by address.

        Args:
            address (str): The account address.

        Returns:
            algopy.Account: The account object.
        """
        import algopy

        assert_address_is_valid(address)
        return algopy.Account(address)

    def account_exists(self, address: str) -> bool:
        """Check if an account exists.

        Args:
            address (str): The account address.

        Returns:
            bool: True if the account exists, False otherwise.
        """
        assert_address_is_valid(address)
        return address in self.account_data

    def update_account(
        self,
        address: str,
        opted_asset_balances: dict[int, algopy.UInt64] | None = None,
        **account_fields: typing.Unpack[AccountFields],
    ) -> None:
        """Update account fields.

        Args:
            address (str): The account address.
            opted_asset_balances (dict[int, algopy.UInt64] | None): The opted asset balances .
            **account_fields: The fields to update.
        """
        assert_address_is_valid(address)
        self.account_data[address].fields.update(account_fields)

        if opted_asset_balances is not None:
            for asset_id, balance in opted_asset_balances.items():
                self.account_data[address].opted_asset_balances[UInt64(asset_id)] = balance

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        """Get an asset by ID.

        Args:
            asset_id (algopy.UInt64 | int): The asset ID.

        Returns:
            algopy.Asset: The asset object.

        Raises:
            ValueError: If the asset is not found.
        """
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id
        if asset_id not in self.asset_data:
            raise ValueError("Asset not found in testing context!")

        return algopy.Asset(asset_id)

    def asset_exists(self, asset_id: algopy.UInt64 | int) -> bool:
        """Check if an asset exists.

        Args:
            asset_id (algopy.UInt64 | int): The asset ID.

        Returns:
            bool: True if the asset exists, False otherwise.
        """
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id
        return asset_id in self.asset_data

    def update_asset(self, asset_id: int, **asset_fields: typing.Unpack[AssetFields]) -> None:
        """Update asset fields.

        Args:
            asset_id (int): The asset ID.
            **asset_fields: The fields to update.

        Raises:
            ValueError: If the asset is not found.
        """
        if asset_id not in self.asset_data:
            raise ValueError("Asset not found in testing context!")
        self.asset_data[asset_id].update(asset_fields)

    def get_app(self, app: algopy.UInt64 | int) -> algopy.Application:
        """Get an application by ID.

        Args:
            app (algopy.UInt64 | int): The application ID.

        Returns:
            algopy.Application: The application object.
        """
        import algopy

        app_data = self._get_app_data(app)
        return algopy.Application(app_data.app_id)

    def app_exists(self, app: algopy.UInt64 | int) -> bool:
        """Check if an application exists.

        Args:
            app (algopy.UInt64 | int): The application ID.

        Returns:
            bool: True if the application exists, False otherwise.
        """
        app_id = _get_app_id(app)
        return app_id in self.app_data

    def update_app(
        self, app_id: int, **application_fields: typing.Unpack[ApplicationFields]
    ) -> None:
        """Update application fields.

        Args:
            app_id (int): The application ID.
            **application_fields: The fields to update.
        """
        app_data = self._get_app_data(app_id)
        app_data.fields.update(application_fields)

    def get_global_state(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: bytes | algopy.Bytes,
    ) -> int | bytes:
        """Get global state for an application.

        Args:
            app: The application identifier.
            key: The state key.

        Returns:
            int | bytes: The state value.
        """
        return self._get_app_data(app).global_state[as_bytes(key)]

    def set_global_state(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: bytes | algopy.Bytes,
        value: int | bytes | None,
    ) -> None:
        """Set global state for an application.

        Args:
            app: The application identifier.
            key: The state key.
            value: The state value.
        """
        key_bytes = as_bytes(key)
        global_state = self._get_app_data(app).global_state
        if value is None:
            if key_bytes in global_state:
                del global_state[key_bytes]
        else:
            global_state[key_bytes] = value

    def get_local_state(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        account: algopy.Account | str,
        key: algopy.Bytes | bytes,
    ) -> int | bytes:
        """Get local state for an application and account.

        Args:
            app: The application identifier.
            account: The account identifier.
            key: The state key.

        Returns:
            int | bytes: The state value.
        """
        composite_key = (
            (account.public_key if isinstance(account, Account) else account),
            as_bytes(key),
        )
        return self._get_app_data(app).local_state[composite_key]

    def set_local_state(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        account: algopy.Account | str,
        key: algopy.Bytes | bytes,
        value: int | bytes | None,
    ) -> None:
        """Set local state for an application and account.

        Args:
            app: The application identifier.
            account: The account identifier.
            key: The state key.
            value: The state value.
        """
        account_public_key = account.public_key if isinstance(account, Account) else account
        key_bytes = as_bytes(key)
        composite_key = (account_public_key, key_bytes)
        local_state = self._get_app_data(app).local_state
        if value is None:
            if composite_key in local_state:
                del local_state[composite_key]
        else:
            local_state[composite_key] = value

    def get_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
    ) -> bytes:
        """Get box content for an application.

        Args:
            app: The application identifier.
            key: The box key.

        Returns:
            bytes: The box content.
        """
        boxes = self._get_app_data(app).boxes
        return boxes.get(_as_box_key(key), b"")

    def set_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
        value: algopy.Bytes | bytes,
    ) -> None:
        """Set box content for an application.

        Args:
            app: The application identifier.
            key: The box key.
            value: The box content.
        """
        boxes = self._get_app_data(app).boxes
        boxes[_as_box_key(key)] = as_bytes(value, max_size=MAX_BOX_SIZE)

    def delete_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
    ) -> bool:
        """Delete a box for an application.

        Args:
            app: The application identifier.
            key: The box key.

        Returns:
            bool: True if the box was deleted, False if it didn't exist.
        """
        boxes = self._get_app_data(app).boxes
        try:
            del boxes[_as_box_key(key)]
        except KeyError:
            return False
        return True

    def box_exists(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
    ) -> bool:
        """Check if a box exists for an application.

        Args:
            app: The application identifier.
            key: The box key.

        Returns:
            bool: True if the box exists, False otherwise.
        """
        boxes = self._get_app_data(app).boxes
        return _as_box_key(key) in boxes

    def set_block(
        self, index: int, seed: algopy.UInt64 | int, timestamp: algopy.UInt64 | int
    ) -> None:
        """Set block content.

        Args:
            index (int): The block index.
            seed (algopy.UInt64 | int): The block seed.
            timestamp (algopy.UInt64 | int): The block timestamp.
        """
        self.blocks[index] = {"seed": int(seed), "timestamp": int(timestamp)}

    def get_block_content(self, index: int, key: str) -> int:
        """Get block content.

        Args:
            index (int): The block index.
            key (str): The content key.

        Returns:
            int: The block content value.

        Raises:
            ValueError: If the block content is not found.
        """
        content = self.blocks.get(index, {}).get(key, None)
        if content is None:
            raise KeyError(
                f"Block content for index {index} and key {key} not found in testing context!"
            )
        return content

    def patch_global_fields(self, **global_fields: typing.Unpack[GlobalFields]) -> None:
        """Patch global fields.

        Args:
            **global_fields: The fields to patch.

        Raises:
            AttributeError: If invalid fields are provided.
        """
        from algopy_testing.op.global_values import GlobalFields

        invalid_keys = global_fields.keys() - GlobalFields.__annotations__.keys()

        if invalid_keys:
            raise AttributeError(
                f"Invalid field(s) found during patch for `Global`: {', '.join(invalid_keys)}"
            )

        self.global_fields.update(global_fields)

    def _get_app_data(
        self, app: algopy.UInt64 | algopy.Application | algopy.Contract | int
    ) -> ApplicationContextData:
        """Get application data.

        Args:
            app: The application identifier.

        Returns:
            ApplicationContextData: The application context data.

        Raises:
            ValueError: If the application is not found.
        """
        app_id = _get_app_id(app)
        try:
            return self.app_data[app_id]
        except KeyError:
            raise ValueError("Unknown app id, is there an active transaction?") from None


def _as_box_key(key_: algopy.Bytes | bytes) -> bytes:
    """Convert a box key to bytes.

    Args:
        key_: The box key.

    Returns:
        bytes: The box key as bytes.

    Raises:
        ValueError: If the key is invalid.
    """
    key = as_bytes(key_)
    if not key:
        raise ValueError("invalid box key")
    return key


def _get_app_id(app: algopy.UInt64 | algopy.Application | algopy.Contract | int) -> int:
    """Get the application ID from various input types.

    Args:
        app: The application identifier.

    Returns:
        int: The application ID.

    Raises:
        TypeError: If an invalid type is provided.
    """
    from algopy_testing.models import Application, Contract
    from algopy_testing.primitives import UInt64

    if isinstance(app, Contract):
        app_id = app.__app_id__
    elif isinstance(app, Application):
        app_id = app.id.value
    elif isinstance(app, UInt64):
        app_id = app.value
    elif isinstance(app, int):
        app_id = app
    else:
        raise TypeError("invalid type")
    return app_id
