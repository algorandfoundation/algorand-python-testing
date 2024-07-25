import algopy
from algopy import (
    Account,
    Application,
    ARC4Contract,
    Asset,
    Bytes,
    Global,
    GlobalState,
    LocalState,
    UInt64,
    arc4,
    op,
)


class StateAcctParamsGet(ARC4Contract):
    @arc4.abimethod()
    def verify_acct_balance(self, a: algopy.Account) -> algopy.UInt64:
        balance, _val = op.AcctParamsGet.acct_balance(a)
        return balance

    @arc4.abimethod()
    def verify_acct_min_balance(self, a: algopy.Account) -> algopy.UInt64:
        min_balance, _val = op.AcctParamsGet.acct_min_balance(a)
        return min_balance

    @arc4.abimethod()
    def verify_acct_auth_addr(self, a: algopy.Account) -> algopy.Bytes:
        auth_addr, _val = op.AcctParamsGet.acct_auth_addr(a)
        return auth_addr.bytes

    @arc4.abimethod()
    def verify_acct_total_num_uint(self, a: algopy.Account) -> algopy.UInt64:
        total_num_uint, _val = op.AcctParamsGet.acct_total_num_uint(a)
        return total_num_uint

    @arc4.abimethod()
    def verify_acct_total_num_byte_slice(self, a: algopy.Account) -> algopy.UInt64:
        total_num_byte_slice, _val = op.AcctParamsGet.acct_total_num_byte_slice(a)
        return total_num_byte_slice

    @arc4.abimethod()
    def verify_acct_total_extra_app_pages(self, a: algopy.Account) -> algopy.UInt64:
        total_extra_app_pages, _val = op.AcctParamsGet.acct_total_extra_app_pages(a)
        return total_extra_app_pages

    @arc4.abimethod()
    def verify_acct_total_apps_created(self, a: algopy.Account) -> algopy.UInt64:
        total_apps_created, _val = op.AcctParamsGet.acct_total_apps_created(a)
        return total_apps_created

    @arc4.abimethod()
    def verify_acct_total_apps_opted_in(self, a: algopy.Account) -> algopy.UInt64:
        total_apps_opted_in, _val = op.AcctParamsGet.acct_total_apps_opted_in(a)
        return total_apps_opted_in

    @arc4.abimethod()
    def verify_acct_total_assets_created(self, a: algopy.Account) -> algopy.UInt64:
        total_assets_created, _val = op.AcctParamsGet.acct_total_assets_created(a)
        return total_assets_created

    @arc4.abimethod()
    def verify_acct_total_assets(self, a: algopy.Account) -> algopy.UInt64:
        total_assets, _val = op.AcctParamsGet.acct_total_assets(a)
        return total_assets

    @arc4.abimethod()
    def verify_acct_total_boxes(self, a: algopy.Account) -> algopy.UInt64:
        total_boxes, _val = op.AcctParamsGet.acct_total_boxes(a)
        return total_boxes

    @arc4.abimethod()
    def verify_acct_total_box_bytes(self, a: algopy.Account) -> algopy.UInt64:
        total_box_bytes, _val = op.AcctParamsGet.acct_total_box_bytes(a)
        return total_box_bytes


class StateAssetHoldingContract(ARC4Contract):
    @arc4.abimethod()
    def verify_asset_holding_get(self, a: Account, b: Asset) -> UInt64:
        balance, _val = op.AssetHoldingGet.asset_balance(a, b)
        return balance

    @arc4.abimethod()
    def verify_asset_frozen_get(self, a: Account, b: Asset) -> bool:
        frozen, _val = op.AssetHoldingGet.asset_frozen(a, b)
        return frozen


class StateAssetParamsContract(ARC4Contract):
    @arc4.abimethod()
    def verify_asset_params_get_total(self, a: Asset) -> UInt64:
        total, _val = op.AssetParamsGet.asset_total(a)
        return total

    @arc4.abimethod()
    def verify_asset_params_get_decimals(self, a: Asset) -> UInt64:
        decimals, _val = op.AssetParamsGet.asset_decimals(a)
        return decimals

    @arc4.abimethod()
    def verify_asset_params_get_default_frozen(self, a: Asset) -> bool:
        default_frozen, _val = op.AssetParamsGet.asset_default_frozen(a)
        return default_frozen

    @arc4.abimethod()
    def verify_asset_params_get_unit_name(self, a: Asset) -> Bytes:
        unit_name, _val = op.AssetParamsGet.asset_unit_name(a)
        return unit_name

    @arc4.abimethod()
    def verify_asset_params_get_name(self, a: Asset) -> Bytes:
        name, _val = op.AssetParamsGet.asset_name(a)
        return name

    @arc4.abimethod()
    def verify_asset_params_get_url(self, a: Asset) -> Bytes:
        url, _val = op.AssetParamsGet.asset_url(a)
        return url

    @arc4.abimethod()
    def verify_asset_params_get_metadata_hash(self, a: Asset) -> Bytes:
        metadata_hash, _val = op.AssetParamsGet.asset_metadata_hash(a)
        return metadata_hash

    @arc4.abimethod()
    def verify_asset_params_get_manager(self, a: Asset) -> Bytes:
        manager, _val = op.AssetParamsGet.asset_manager(a)
        return manager.bytes

    @arc4.abimethod()
    def verify_asset_params_get_reserve(self, a: Asset) -> Bytes:
        reserve, _val = op.AssetParamsGet.asset_reserve(a)
        return reserve.bytes

    @arc4.abimethod()
    def verify_asset_params_get_freeze(self, a: Asset) -> Bytes:
        freeze, _val = op.AssetParamsGet.asset_freeze(a)
        return freeze.bytes

    @arc4.abimethod()
    def verify_asset_params_get_clawback(self, a: Asset) -> Bytes:
        clawback, _val = op.AssetParamsGet.asset_clawback(a)
        return clawback.bytes

    @arc4.abimethod()
    def verify_asset_params_get_creator(self, a: Asset) -> Bytes:
        creator, _val = op.AssetParamsGet.asset_creator(a)
        return creator.bytes


class StateAppParamsContract(ARC4Contract):
    @arc4.abimethod()
    def verify_app_params_get_approval_program(self, a: Application) -> Bytes:
        approval_program, _val = op.AppParamsGet.app_approval_program(a)
        return approval_program

    @arc4.abimethod()
    def verify_app_params_get_clear_state_program(self, a: Application) -> Bytes:
        clear_state_program, _val = op.AppParamsGet.app_clear_state_program(a)
        return clear_state_program

    @arc4.abimethod()
    def verify_app_params_get_global_num_uint(self, a: Application) -> UInt64:
        global_num_uint, _val = op.AppParamsGet.app_global_num_uint(a)
        return global_num_uint

    @arc4.abimethod()
    def verify_app_params_get_global_num_byte_slice(self, a: Application) -> UInt64:
        global_num_byte_slice, _val = op.AppParamsGet.app_global_num_byte_slice(a)
        return global_num_byte_slice

    @arc4.abimethod()
    def verify_app_params_get_local_num_uint(self, a: Application) -> UInt64:
        local_num_uint, _val = op.AppParamsGet.app_local_num_uint(a)
        return local_num_uint

    @arc4.abimethod()
    def verify_app_params_get_local_num_byte_slice(self, a: Application) -> UInt64:
        local_num_byte_slice, _val = op.AppParamsGet.app_local_num_byte_slice(a)
        return local_num_byte_slice

    @arc4.abimethod()
    def verify_app_params_get_extra_program_pages(self, a: Application) -> UInt64:
        extra_program_pages, _val = op.AppParamsGet.app_extra_program_pages(a)
        return extra_program_pages

    @arc4.abimethod()
    def verify_app_params_get_creator(self, a: Application) -> Bytes:
        creator, _val = op.AppParamsGet.app_creator(a)
        return creator.bytes

    @arc4.abimethod()
    def verify_app_params_get_address(self, a: Application) -> Bytes:
        address, _val = op.AppParamsGet.app_address(a)
        return address.bytes


class StateAppLocalExContract(ARC4Contract):
    def __init__(self) -> None:
        self.local_uint64 = LocalState(
            UInt64,
            key="local_uint64",
        )

        self.local_bytes = LocalState(
            Bytes,
            key="local_bytes",
        )

    @arc4.abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        self.local_bytes[Global.creator_address] = Bytes(b"dummy_bytes_from_external_contract")
        self.local_uint64[Global.creator_address] = UInt64(99)


class StateAppLocalContract(ARC4Contract):
    def __init__(self) -> None:
        self.local_uint64 = LocalState(
            UInt64,
            key="local_uint64",
        )

        self.local_bytes = LocalState(
            Bytes,
            key="local_bytes",
        )

    @arc4.abimethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        self.local_bytes[Global.creator_address] = Bytes(b"dummy_bytes")
        self.local_uint64[Global.creator_address] = UInt64(999)

    @arc4.abimethod()
    def verify_get_bytes(self, a: Account, b: Bytes) -> Bytes:
        value = op.AppLocal.get_bytes(a, b)
        return value

    @arc4.abimethod()
    def verify_get_uint64(self, a: Account, b: Bytes) -> UInt64:
        value = op.AppLocal.get_uint64(a, b)
        return value

    @arc4.abimethod()
    def verify_get_ex_bytes(self, a: Account, b: Application, c: Bytes) -> Bytes:
        value, _val = op.AppLocal.get_ex_bytes(a, b, c)
        return value

    @arc4.abimethod()
    def verify_get_ex_uint64(self, a: Account, b: Application, c: Bytes) -> UInt64:
        value, _val = op.AppLocal.get_ex_uint64(a, b, c)
        return value

    @arc4.abimethod()
    def verify_delete(self, a: Account, b: Bytes) -> None:
        op.AppLocal.delete(a, b)

    @arc4.abimethod()
    def verify_put_uint64(self, a: Account, b: Bytes, c: UInt64) -> None:
        op.AppLocal.put(a, b, c)

    @arc4.abimethod()
    def verify_put_bytes(self, a: Account, b: Bytes, c: Bytes) -> None:
        op.AppLocal.put(a, b, c)


class StateAppGlobalExContract(ARC4Contract):
    def __init__(self) -> None:
        self.global_uint64 = GlobalState(
            UInt64(2),
            key="global_uint64",
        )
        self.global_bytes = GlobalState(
            Bytes(b"dummy_bytes"),
            key="global_bytes",
        )
        self.global_uint64_explicit = algopy.UInt64(2)
        self.global_bytes_explicit = algopy.Bytes(b"dummy_bytes")


class StateAppGlobalContract(ARC4Contract):
    def __init__(self) -> None:
        self.global_uint64 = GlobalState(
            UInt64,
            key="global_uint64",
        )

        self.global_bytes = GlobalState(
            Bytes,
            key="global_bytes",
        )

    @arc4.abimethod()
    def verify_get_bytes(self, a: Bytes) -> Bytes:
        value = op.AppGlobal.get_bytes(a)
        return value

    @arc4.abimethod()
    def verify_get_uint64(self, a: Bytes) -> UInt64:
        value = op.AppGlobal.get_uint64(a)
        return value

    @arc4.abimethod()
    def verify_get_ex_bytes(self, a: Application, b: Bytes) -> tuple[Bytes, bool]:
        return op.AppGlobal.get_ex_bytes(a, b)

    @arc4.abimethod()
    def verify_get_ex_uint64(self, a: Application, b: Bytes) -> tuple[UInt64, bool]:
        return op.AppGlobal.get_ex_uint64(a, b)

    @arc4.abimethod()
    def verify_delete(self, a: Bytes) -> None:
        op.AppGlobal.delete(a)

    @arc4.abimethod()
    def verify_put_uint64(self, a: Bytes, b: UInt64) -> None:
        op.AppGlobal.put(a, b)

    @arc4.abimethod()
    def verify_put_bytes(self, a: Bytes, b: Bytes) -> None:
        op.AppGlobal.put(a, b)
