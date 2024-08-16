from __future__ import annotations

import typing
from collections import defaultdict

from algopy_testing.utils import assert_address_is_valid, get_default_global_fields

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
        # TODO: 1.0 move boxes onto application data
        self.boxes: dict[bytes, bytes] = {}
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

    def get_application(self, app_id: algopy.UInt64 | int) -> algopy.Application:
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id

        if app_id not in self.application_data:
            raise ValueError("Application not found in testing context!")

        return algopy.Application(app_id)

    def app_exists(self, app_id: algopy.UInt64 | int) -> bool:
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id
        return app_id in self.application_data

    def update_application(
        self, app_id: int, **application_fields: typing.Unpack[ApplicationFields]
    ) -> None:
        if app_id not in self.application_data:
            raise ValueError("Application not found in testing context!")

        self.application_data[app_id].fields.update(application_fields)

    # TODO: 1.0 add app ids, access the boxes from application data
    def get_box(self, name: algopy.Bytes | bytes) -> bytes:
        name_bytes = name if isinstance(name, bytes) else name.value
        return self.boxes.get(name_bytes, b"")

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        name_bytes = name if isinstance(name, bytes) else name.value
        content_bytes = content if isinstance(content, bytes) else content.value
        self.boxes[name_bytes] = content_bytes

    def delete_box(self, name: algopy.Bytes | bytes) -> bool:
        name_bytes = name if isinstance(name, bytes) else name.value
        if name_bytes in self.boxes:
            del self.boxes[name_bytes]
            return True
        return False

    def box_exists(self, name: algopy.Bytes | bytes) -> bool:
        name_bytes = name if isinstance(name, bytes) else name.value
        return name_bytes in self.boxes

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
