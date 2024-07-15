from algopy import Account, Application, ARC4Contract, Asset, Bytes, UInt64, arc4, op


class StateOpsContract(ARC4Contract):
    @arc4.abimethod()
    def verify_asset_holding_get(self, a: Account, b: Asset) -> UInt64:
        balance, _val = op.AssetHoldingGet.asset_balance(a, b)
        return balance

    @arc4.abimethod()
    def verify_asset_frozen_get(self, a: Account, b: Asset) -> bool:
        frozen, _val = op.AssetHoldingGet.asset_frozen(a, b)
        return frozen

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

    @arc4.abimethod()
    def verify_app_params_app_approval_program(self, a: Application) -> Bytes:
        approval_program, _val = op.AppParamsGet.app_approval_program(a)
        return approval_program

    @arc4.abimethod()
    def verify_app_params_app_clear_state_program(self, a: Application) -> Bytes:
        clear_state_program, _val = op.AppParamsGet.app_clear_state_program(a)
        return clear_state_program

    @arc4.abimethod()
    def verify_app_params_app_global_num_uint(self, a: Application) -> UInt64:
        global_num_uint, _val = op.AppParamsGet.app_global_num_uint(a)
        return global_num_uint

    @arc4.abimethod()
    def verify_app_params_app_global_num_byte_slice(self, a: Application) -> UInt64:
        global_num_byte_slice, _val = op.AppParamsGet.app_global_num_byte_slice(a)
        return global_num_byte_slice

    @arc4.abimethod()
    def verify_app_params_app_local_num_uint(self, a: Application) -> UInt64:
        local_num_uint, _val = op.AppParamsGet.app_local_num_uint(a)
        return local_num_uint

    @arc4.abimethod()
    def verify_app_params_app_local_num_byte_slice(self, a: Application) -> UInt64:
        local_num_byte_slice, _val = op.AppParamsGet.app_local_num_byte_slice(a)
        return local_num_byte_slice

    @arc4.abimethod()
    def verify_app_params_app_extra_program_pages(self, a: Application) -> UInt64:
        extra_program_pages, _val = op.AppParamsGet.app_extra_program_pages(a)
        return extra_program_pages

    @arc4.abimethod()
    def verify_app_params_app_creator(self, a: Application) -> Bytes:
        creator, _val = op.AppParamsGet.app_creator(a)
        return creator.bytes

    @arc4.abimethod()
    def verify_app_params_app_address(self, a: Application) -> Bytes:
        address, _val = op.AppParamsGet.app_address(a)
        return address.bytes
