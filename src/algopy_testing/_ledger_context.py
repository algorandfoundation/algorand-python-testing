from __future__ import annotations

import typing
from collections import ChainMap, defaultdict

import algosdk

from algopy_testing._context_storage import get_test_context
from algopy_testing.constants import ALWAYS_APPROVE_TEAL_PROGRAM
from algopy_testing.models.account import AccountContextData, AccountFields, get_empty_account
from algopy_testing.models.application import ApplicationContextData, ApplicationFields
from algopy_testing.models.asset import AssetFields
from algopy_testing.utils import assert_address_is_valid, get_default_global_fields

if typing.TYPE_CHECKING:
    import algopy

    from algopy_testing.op.global_values import GlobalFields


class LedgerContext:
    def __init__(self, default_sender: algopy.Account | None = None) -> None:
        import algopy

        self.default_sender: algopy.Account = default_sender or algopy.Account(
            algosdk.account.generate_account()[1]
        )
        self._account_data = defaultdict[str, AccountContextData](get_empty_account)
        self._account_data[self.default_sender.public_key] = get_empty_account()
        self._application_data: dict[int, ApplicationContextData] = {}
        self._asset_data: dict[int, AssetFields] = {}
        self._boxes: dict[bytes, bytes] = {}
        self._blocks: dict[int, dict[str, int]] = {}
        self._global_fields: GlobalFields = get_default_global_fields(
            creator_address=self.default_sender
        )

        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

    def get_account(self, address: str) -> algopy.Account:
        import algopy

        if address not in self._account_data:
            raise ValueError("Account not found in testing context!")

        return algopy.Account(address)

    def get_asset(self, asset_id: algopy.UInt64 | int) -> algopy.Asset:
        import algopy

        asset_id = int(asset_id) if isinstance(asset_id, algopy.UInt64) else asset_id
        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")

        return algopy.Asset(asset_id)

    def update_account(self, address: str, **account_fields: typing.Unpack[AccountFields]) -> None:
        assert_address_is_valid(address)
        self._account_data[address].fields.update(account_fields)

    def update_asset(self, asset_id: int, **asset_fields: typing.Unpack[AssetFields]) -> None:
        if asset_id not in self._asset_data:
            raise ValueError("Asset not found in testing context!")
        self._asset_data[asset_id].update(asset_fields)

    def get_application(self, app_id: algopy.UInt64 | int) -> algopy.Application:
        import algopy

        app_id = int(app_id) if isinstance(app_id, algopy.UInt64) else app_id

        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        return algopy.Application(app_id)

    def update_application(
        self, app_id: int, **application_fields: typing.Unpack[ApplicationFields]
    ) -> None:
        if app_id not in self._application_data:
            raise ValueError("Application not found in testing context!")

        self._application_data[app_id].fields.update(application_fields)

    def get_box(self, name: algopy.Bytes | bytes) -> bytes:
        name_bytes = name if isinstance(name, bytes) else name.value
        return self._boxes.get(name_bytes, b"")

    def set_box(self, name: algopy.Bytes | bytes, content: algopy.Bytes | bytes) -> None:
        name_bytes = name if isinstance(name, bytes) else name.value
        content_bytes = content if isinstance(content, bytes) else content.value
        self._boxes[name_bytes] = content_bytes

    def delete_box(self, name: algopy.Bytes | bytes) -> bool:
        name_bytes = name if isinstance(name, bytes) else name.value
        if name_bytes in self._boxes:
            del self._boxes[name_bytes]
            return True
        return False

    def box_exists(self, name: algopy.Bytes | bytes) -> bool:
        name_bytes = name if isinstance(name, bytes) else name.value
        return name_bytes in self._boxes

    def set_block(
        self, index: int, seed: algopy.UInt64 | int, timestamp: algopy.UInt64 | int
    ) -> None:
        self._blocks[index] = {"seed": int(seed), "timestamp": int(timestamp)}

    def get_block_content(self, index: int, key: str) -> int:
        content = self._blocks.get(index, {}).get(key, None)
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

        self._global_fields.update(global_fields)

    def clear(self) -> None:
        self._account_data.clear()
        self._application_data.clear()
        self._asset_data.clear()
        self._boxes.clear()
        self._blocks.clear()
        self._global_fields = get_default_global_fields(creator_address=self.default_sender)
        self._asset_id = iter(range(1001, 2**64))
        self._app_id = iter(range(1001, 2**64))

    # Value generators =========================================================

    def any_account(
        self,
        address: str | None = None,
        opted_asset_balances: dict[algopy.UInt64, algopy.UInt64] | None = None,
        opted_apps: typing.Sequence[algopy.Application] = (),
        **account_fields: typing.Unpack[AccountFields],
    ) -> algopy.Account:
        import algopy

        if address is not None:
            assert_address_is_valid(address)

        # TODO: ensure passed fields are valid names and types
        if address in self._account_data:
            raise ValueError(
                "Account with such address already exists in testing context! "
                "Use `context.get_account(address)` to retrieve the existing account."
            )

        for key in account_fields:
            if key not in AccountFields.__annotations__:
                raise AttributeError(f"Invalid field '{key}' for Account")

        new_account_address = address or algosdk.account.generate_account()[1]
        new_account = algopy.Account(new_account_address)
        new_account_fields = AccountFields(**account_fields)
        new_account_data = AccountContextData(
            fields=new_account_fields,
            opted_asset_balances=opted_asset_balances or {},
            opted_apps={app.id: app for app in opted_apps},
        )

        self._account_data[new_account_address] = new_account_data

        return new_account

    def any_asset(
        self, asset_id: int | None = None, **asset_fields: typing.Unpack[AssetFields]
    ) -> algopy.Asset:
        """Generate and add a new asset with a unique ID.

        :param asset_id: Optional asset ID. If not provided, a new ID
            will be generated.
        :type asset_id: int | None :param **asset_fields: Additional
            asset fields.
        :param asset_id: int | None: (Default value = None) :param
            **asset_fields: Unpack[AssetFields]:
        :returns: The newly generated asset.
        :rtype: algopy.Asset
        """
        import algopy

        if asset_id and asset_id in self._asset_data:
            raise ValueError("Asset with such ID already exists in testing context!")

        # TODO: ensure passed fields are valid names and types
        context = get_test_context()
        new_asset = algopy.Asset(asset_id or next(self._asset_id))
        default_asset_fields = {
            "total": context.any_uint64(),
            "decimals": context.any_uint64(1, 6),
            "default_frozen": False,
            "unit_name": context.any_bytes(4),
            "name": context.any_bytes(32),
            "url": context.any_bytes(10),
            "metadata_hash": context.any_bytes(32),
            "manager": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "freeze": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "clawback": algopy.Account(algosdk.constants.ZERO_ADDRESS),
            "creator": self.default_sender,
            "reserve": algopy.Account(algosdk.constants.ZERO_ADDRESS),
        }
        merged_fields = dict(ChainMap(asset_fields, default_asset_fields))  # type: ignore[arg-type]
        self._asset_data[int(new_asset.id)] = AssetFields(**merged_fields)  # type: ignore[typeddict-item]
        return new_asset

    def any_application(  # type: ignore[misc]
        self,
        id: int | None = None,
        address: algopy.Account | None = None,
        **application_fields: typing.Unpack[ApplicationFields],
    ) -> algopy.Application:
        """Generate and add a new application with a unique ID.

        :param id: Optional application ID. If not provided, a new ID
            will be generated.
        :type id: int | None
        :param address: Optional application address. If not provided,
        :type address: algopy.Account | None
        :param address: Optional application address. If not provided,
            it will be generated.
        :type address: algopy.Account | None :param
            **application_fields: Additional application fields. :param
            # type: ignore[misc]self:
        :param id: int | None:  (Default value = None)
        :param address: algopy.Account | None: (Default value = None)
            :param **application_fields: Unpack[ApplicationFields]:
        :returns: The newly generated application.
        :rtype: algopy.Application
        """
        import algopy_testing

        new_app_id = id if id is not None else next(self._app_id)

        if new_app_id in self._application_data:
            raise ValueError(
                f"Application id {new_app_id} has already been configured in test context!"
            )

        new_app = algopy_testing.Application(new_app_id)

        # Set sensible defaults
        app_fields: ApplicationFields = {
            "approval_program": algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "clear_state_program": algopy_testing.Bytes(ALWAYS_APPROVE_TEAL_PROGRAM),
            "global_num_uint": algopy_testing.UInt64(0),
            "global_num_bytes": algopy_testing.UInt64(0),
            "local_num_uint": algopy_testing.UInt64(0),
            "local_num_bytes": algopy_testing.UInt64(0),
            "extra_program_pages": algopy_testing.UInt64(0),
            "creator": self.default_sender,
            "address": address
            or algopy_testing.Account(algosdk.logic.get_application_address(new_app_id)),
        }

        # Merge provided fields with defaults, prioritizing provided fields
        for field, value in application_fields.items():
            try:
                default_value = app_fields[field]  # type: ignore[literal-required]
            except KeyError:
                raise ValueError(f"invalid field: {field!r}") from None
            if not issubclass(type(value), type(default_value)):
                raise TypeError(f"incorrect type for {field!r}")
            app_fields[field] = value  # type: ignore[literal-required]

        self._application_data[new_app_id] = ApplicationContextData(
            fields=app_fields,
            app_id=new_app_id,
        )

        return new_app
