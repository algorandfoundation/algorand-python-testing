from __future__ import annotations

import typing
from collections import defaultdict

from algopy_testing.constants import MAX_BOX_SIZE
from algopy_testing.utils import as_bytes, assert_address_is_valid, get_default_global_fields

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.models.account import AccountFields
    from algopy_testing.models.application import ApplicationContextData, ApplicationFields
    from algopy_testing.models.asset import AssetFields
    from algopy_testing.op.global_values import GlobalFields


class LedgerContext:
    def __init__(self) -> None:
        from algopy_testing.models.account import AccountContextData, get_empty_account

        self.account_data = defaultdict[str, AccountContextData](get_empty_account)
        self.application_data: dict[int, ApplicationContextData] = {}
        self.asset_data: dict[int, AssetFields] = {}
        self.blocks: dict[int, dict[str, int]] = {}
        self.global_fields: GlobalFields = get_default_global_fields()

        self.asset_id = iter(range(1001, 2**64))
        self.app_id = iter(range(1001, 2**64))

    def get_account(self, address: str) -> algopy.Account:
        import algopy

        assert_address_is_valid(address)
        return algopy.Account(address)

    def account_exists(self, address: str) -> bool:
        assert_address_is_valid(address)
        return address in self.account_data

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id
        if asset_id not in self.asset_data:
            raise ValueError("Asset not found in testing context!")

        return algopy.Asset(asset_id)

    def asset_exists(self, asset_id: algopy.UInt64 | int) -> bool:
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id
        return asset_id in self.asset_data

    def update_account(self, address: str, **account_fields: typing.Unpack[AccountFields]) -> None:
        assert_address_is_valid(address)
        self.account_data[address].fields.update(account_fields)

    def update_asset(self, asset_id: int, **asset_fields: typing.Unpack[AssetFields]) -> None:
        if asset_id not in self.asset_data:
            raise ValueError("Asset not found in testing context!")
        self.asset_data[asset_id].update(asset_fields)

    def get_application(self, app: algopy.UInt64 | int) -> algopy.Application:
        import algopy

        app_data = self._get_app_data(app)
        return algopy.Application(app_data.app_id)

    def _get_app_data(
        self, app: algopy.UInt64 | algopy.Application | algopy.Contract | int
    ) -> ApplicationContextData:
        app_id = _get_app_id(app)
        try:
            return self.application_data[app_id]
        except KeyError:
            raise ValueError("Unknown app id, is there an active transaction?") from None

    def app_exists(self, app: algopy.UInt64 | int) -> bool:
        app_id = _get_app_id(app)
        return app_id in self.application_data

    def update_application(
        self, app_id: int, **application_fields: typing.Unpack[ApplicationFields]
    ) -> None:
        app_data = self._get_app_data(app_id)
        app_data.fields.update(application_fields)

    def get_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
    ) -> bytes:
        boxes = self._get_app_data(app).boxes
        return boxes.get(_as_box_key(key), b"")

    def set_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
        value: algopy.Bytes | bytes,
    ) -> None:
        boxes = self._get_app_data(app).boxes
        boxes[_as_box_key(key)] = as_bytes(value, max_size=MAX_BOX_SIZE)

    def delete_box(
        self,
        app: algopy.Contract | algopy.Application | algopy.UInt64 | int,
        key: algopy.Bytes | bytes,
    ) -> bool:
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
        boxes = self._get_app_data(app).boxes
        return _as_box_key(key) in boxes

    def set_block(
        self, index: int, seed: algopy.UInt64 | int, timestamp: algopy.UInt64 | int
    ) -> None:
        self.blocks[index] = {"seed": int(seed), "timestamp": int(timestamp)}

    def get_block_content(self, index: int, key: str) -> int:
        content = self.blocks.get(index, {}).get(key, None)
        if content is None:
            raise ValueError(
                f"Block content for index {index} and key {key} not found in testing context!"
            )
        return content

    def patch_global_fields(self, **global_fields: typing.Unpack[GlobalFields]) -> None:
        from algopy_testing.op.global_values import GlobalFields

        invalid_keys = global_fields.keys() - GlobalFields.__annotations__.keys()

        if invalid_keys:
            raise AttributeError(
                f"Invalid field(s) found during patch for `Global`: {', '.join(invalid_keys)}"
            )

        self.global_fields.update(global_fields)


def _as_box_key(key_: algopy.Bytes | bytes) -> bytes:
    key = as_bytes(key_)
    if not key:
        raise ValueError("invalid box key")
    return key


def _get_app_id(app: algopy.UInt64 | algopy.Application | algopy.Contract | int) -> int:
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
