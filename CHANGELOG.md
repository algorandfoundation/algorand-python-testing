# CHANGELOG
## v1.2.0-beta.3 (2025-12-08)

### Features

* add stage and submit_staged functions to support submitting dynamic number of inner transactions in a group ([`84ad031`](https://github.com/algorandfoundation/algorand-python-testing/commit/84ad03166442dadc10c7c1fe70e4cd07a63600cc))

## v1.2.0-beta.2 (2025-12-08)

### Features

* add algopy.public alias for algopy.arc4.abimethod decorator ([`32a2787`](https://github.com/algorandfoundation/algorand-python-testing/commit/32a27877a30f03e5330aa1bdb7a4fadbea543529))

## v1.2.0-beta.1 (2025-12-05)

### Features

* add fixed size variant of bytes as a separate `FixedBytes` type ([`9a2ab8e`](https://github.com/algorandfoundation/algorand-python-testing/commit/9a2ab8e3f94e9e7a2a416a94a54cf51b57599089))

## v1.1.0 (2025-10-20)

## v1.1.0-beta.1 (2025-10-20)

### Features

* add mock implementations for validation functionality ([`ccde074`](https://github.com/algorandfoundation/algorand-python-testing/commit/ccde0740889bd68ef0fba418182d71ac0fc9f76a))

### Documentation

* add note about data validation in the testing library ([`bc47a68`](https://github.com/algorandfoundation/algorand-python-testing/commit/bc47a6838cf00907f2a718ddb8cb45fe97947d77))

* add missing native types in coverage table ([`a95116c`](https://github.com/algorandfoundation/algorand-python-testing/commit/a95116c567dc77cfcf4f7ec517df60bb3d9d1eb5))

## v1.0.0 (2025-10-06)

## v1.0.0-beta.8 (2025-10-06)

### Documentation

* fix typos and broken links ([`f221910`](https://github.com/algorandfoundation/algorand-python-testing/commit/f221910b54a2cdc76aa99b8883d75d4ddae78ee3))

## v1.0.0-beta.7 (2025-09-26)

### Bug fixes

* bump puyapy dependencies ([`8b2064d`](https://github.com/algorandfoundation/algorand-python-testing/commit/8b2064dc8bd94b0dadf6f283e8d639543241eadc))

  Update to latest release candidates, so dependencies projects using both puyapy, language server and algorand python testing can resolve to a consistent version

## v1.0.0-beta.6 (2025-09-18)

### Features

* update langspec to 4.3.0 ([`c05bdc0`](https://github.com/algorandfoundation/algorand-python-testing/commit/c05bdc053f4b6aa52206cbeeaddb40609688b052))

## v1.0.0-beta.5 (2025-09-16)

## v1.0.0-beta.4 (2025-09-12)

### Features

* make BoxRef methods directly accessible on Box class ([`38e12f6`](https://github.com/algorandfoundation/algorand-python-testing/commit/38e12f6d595c204eb6f7dcd74c393c46f166e3d4))

## v1.0.0-beta.3 (2025-09-08)

### Features

* add .as_uint64 and .as_biguint methods to replace native property ([`0f9c6c0`](https://github.com/algorandfoundation/algorand-python-testing/commit/0f9c6c06b6e1b986c4e512cbbe0098aea32615b7))

## v1.0.0-beta.2 (2025-09-03)

### Features

* add stub implementations of array types ([`b7b831d`](https://github.com/algorandfoundation/algorand-python-testing/commit/b7b831da7570367494e823485910bc7191376e48))

## v1.0.0-beta.1 (2025-07-16)

### Features

* support storing tuples in state ([`911cd3c`](https://github.com/algorandfoundation/algorand-python-testing/commit/911cd3cb54f69f8fdded5c677f32c1969e8827bf))

## v0.6.0-beta.3 (2025-05-16)

### Bug fixes

* fixes type checking of tuples with primitive types ([`e971ad6`](https://github.com/algorandfoundation/algorand-python-testing/commit/e971ad6b125f269cd0874c09d58d8962f7622f8d))

  Adds checks to ensure that type validation applies to classes only.

## v0.6.0-beta.2 (2025-05-15)

### Features

* add stubs for box create function ([`1fe6fe5`](https://github.com/algorandfoundation/algorand-python-testing/commit/1fe6fe55358630a6abea2f69406821cb6031a4d5))

## v0.6.0-beta.1 (2025-05-09)

### Features

* add stub implementation of algopy.size_of function for calculating static storage size of types ([`98e6816`](https://github.com/algorandfoundation/algorand-python-testing/commit/98e6816a48f1cff206f2c99d1384af1855d352c2))

### Bug fixes

* ensure size_of is exported from algopy module ([`01c055a`](https://github.com/algorandfoundation/algorand-python-testing/commit/01c055a4d2bd1fe17324bd91f7a83810900baa4e))

### Documentation

* include size_of in coverage doc ([`2c73646`](https://github.com/algorandfoundation/algorand-python-testing/commit/2c7364626357844437fd80b6039c112a87b277bb))

## v0.5.0 (2025-02-20)

### Features

* accept abi method reference as a parameter to arc4_signature method ([`a1cb365`](https://github.com/algorandfoundation/algorand-python-testing/commit/a1cb365f2be1eb1965d9b86a5193498772131412))

## v0.5.0-beta.1 (2025-02-19)

### Features

* support `algopy.Array` and `algopy.ImmutableArray` from algorand-python 2.7 ([`fd8d19f`](https://github.com/algorandfoundation/algorand-python-testing/commit/fd8d19f25b9f8e0a48f58ae8f45e4d546b965f83))

* support mocking new `algopy.op` functions `falcon_verify`, `mimc`, `online_stake`, `sumhash512` and `VoterParamsGet` ([`83ddcbb`](https://github.com/algorandfoundation/algorand-python-testing/commit/83ddcbb8f83f72a5e0bc247c14e250c55496febf))

* update `algopy.op.Block` with fields added in AVM 11 ([`90d857d`](https://github.com/algorandfoundation/algorand-python-testing/commit/90d857d248d7b1b5a4b3791ccb0e10c20c478325))

* update `algopy.op.AcctParamsGet` with fields added in AVM 11 ([`059b669`](https://github.com/algorandfoundation/algorand-python-testing/commit/059b6690441e99a709fc47691bcb0e4f2453cd26))

* add `avm_version` to `algopy.Contract` class options ([`fc53b0f`](https://github.com/algorandfoundation/algorand-python-testing/commit/fc53b0fda5f0d22b6dbb99abf1ba024284fa52a4))

* update `algopy.op.Global` with fields added in AVM 11 ([`0cc9807`](https://github.com/algorandfoundation/algorand-python-testing/commit/0cc9807bbfc7084d54425c40889065ae2fd7d856))

* add `algopy.arc4.Struct._replace` introduced in algorand-python 2.5.0 ([`75d6847`](https://github.com/algorandfoundation/algorand-python-testing/commit/75d6847b80498d637c7f0b0e3915afd7af6f132c))

* add inline option to subroutine decorator ([`2cc15b3`](https://github.com/algorandfoundation/algorand-python-testing/commit/2cc15b3dc706eb8585b9658bf67b38da215e2e38))

### Bug fixes

* add missing mappings for `algopy.op.Txn` members ([`fddfe6f`](https://github.com/algorandfoundation/algorand-python-testing/commit/fddfe6f7ff9d6d4e0434f65e19dd0b0cf2aef6bd))

* include `ARC4Contract` in `algopy.arc4` namespace ([`f19d46f`](https://github.com/algorandfoundation/algorand-python-testing/commit/f19d46f5663c9fbe4e9b2e8c3bd1e2f7ddc89c3a))

* update `algopy.CompiledContract` and `algopy.CompiledLogicSig` to be NamedTuples ([`84be408`](https://github.com/algorandfoundation/algorand-python-testing/commit/84be4082348e3d89b40a65a69b599594a5531828))

* added missing __contains__ implementation for `algopy.Bytes` ([`8b2efa2`](https://github.com/algorandfoundation/algorand-python-testing/commit/8b2efa20b37e3043ac6a228d6706da4203373a7e))

### Documentation

* fix doctest example for `algopy.EllipticCurve` ([`7d0bb0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/7d0bb0dfe9a5ea2d67b130fa300fb80cef52fda5))

## v0.4.1 (2024-09-03)

## v0.4.1-beta.1 (2024-09-03)

### Bug fixes

* ability to pass kw_only flag to dataclass when defining struct subclass ([`24bcf9d`](https://github.com/algorandfoundation/algorand-python-testing/commit/24bcf9d8af34eb2675ddf85ce9d71802f82f2d6a))

* ability to pass kw_only flag to dataclass when defining struct subclass ([`24bcf9d`](https://github.com/algorandfoundation/algorand-python-testing/commit/24bcf9d8af34eb2675ddf85ce9d71802f82f2d6a))

## v0.4.0 (2024-08-27)

## v0.4.0-beta.2 (2024-08-27)

## v0.4.0-beta.1 (2024-08-27)

### Features

* add support for frozen on asset holdings, including a new ledger function `update_asset_holdings` for setting asset holding balances and frozen states ([`d777ca0`](https://github.com/algorandfoundation/algorand-python-testing/commit/d777ca0a318a8ade7a20363c9ce77fe8a8bf5d68))

* expand accepted types when interacting with accounts, applications and assets ([`f448a97`](https://github.com/algorandfoundation/algorand-python-testing/commit/f448a97cb154c9f90ecf42c599b240f12928af20))

  wip

* replaced `account_exists` with `account_is_funded` as the later is more useful ([`4d08690`](https://github.com/algorandfoundation/algorand-python-testing/commit/4d086903eb93a70ce1d485cdd7b12d8472ef16db))

### Bug fixes

* use correct type for Globals.caller_application_id ([`a30d85a`](https://github.com/algorandfoundation/algorand-python-testing/commit/a30d85a4416dfc2c5d901f3ace2265384ef60c01))

* do not allow specifying `address` for applications, it is derived from the app_id ([`00fe1bc`](https://github.com/algorandfoundation/algorand-python-testing/commit/00fe1bc8ea247dcc36b01154db36b984b151e396))

* do not treat asset and application ids as possible foreign array indexes ([`94a989f`](https://github.com/algorandfoundation/algorand-python-testing/commit/94a989f77169da2ae437c629cd5f4d8a872263f6))

* removed incorrect deduction in `algopy.op.balance` ([`76e67c5`](https://github.com/algorandfoundation/algorand-python-testing/commit/76e67c5e3dd1cda388a2a948d452ba89805add6a))

* ensure all comparable types return `NotImplemented` when a comparison is not possible ([`b055fa6`](https://github.com/algorandfoundation/algorand-python-testing/commit/b055fa68531e0b7923773ec10c2097a3d64b9dbe))

* `arc4_prefix` annotated to also accept `algopy.Bytes` ([`40328ca`](https://github.com/algorandfoundation/algorand-python-testing/commit/40328ca3701b3e255193e206e8a7b1bdb441a346))

### Documentation

* include usage of `algopy_testing_context` in README.md quick start ([`4702f60`](https://github.com/algorandfoundation/algorand-python-testing/commit/4702f60cfe7d09956a5ae6dbdcd72da29fdda808))

## v0.3.0 (2024-08-22)

## v0.3.0-beta.10 (2024-08-22)

### Documentation

* refining docs ([`b714783`](https://github.com/algorandfoundation/algorand-python-testing/commit/b714783b4cf15d31f91dc1c776d304bd2eb9a154))

* note on future refinement ([`b714783`](https://github.com/algorandfoundation/algorand-python-testing/commit/b714783b4cf15d31f91dc1c776d304bd2eb9a154))

* further refining the api section ([`b714783`](https://github.com/algorandfoundation/algorand-python-testing/commit/b714783b4cf15d31f91dc1c776d304bd2eb9a154))

## v0.3.0-beta.9 (2024-08-22)

### Bug fixes

* Make Global.latest_timestamp constant for a transaction ([`51c2817`](https://github.com/algorandfoundation/algorand-python-testing/commit/51c2817c262d686996e2aa4d639d259409dc8d43))

## v0.3.0-beta.8 (2024-08-22)

### Features

* include ARC4 results in log, and handle > 15 ARC4 arguments ([`fd83ee8`](https://github.com/algorandfoundation/algorand-python-testing/commit/fd83ee8525a393d4a1a66f20acdb661906d84b51))

## v0.3.0-beta.7 (2024-08-21)

## v0.3.0-beta.6 (2024-08-21)

### Documentation

* documentation for initial stable release of `algorand-python-testing` ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

  docs: wip

* refining docs (wip) ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

* revamping docs with latest features ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

* minor consistency with main readme; patching doctests ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

* removing the box from examples ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

* refine op codes section ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

* addressing docs pr comments ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

## v0.3.0-beta.5 (2024-08-21)

### Features

* add __str__ and __repr__ implementations for ARC4 types ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

### Bug fixes

* ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types) ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

* add default __eq__ implementation for ARC4 types ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

* ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types) ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

## v0.3.0-beta.4 (2024-08-21)

### Features

* rename txn_op_fields to active_txn_overrides to better reflect purpose, add additional checks to ensure crate_group parameters are used correctly ([`973fc28`](https://github.com/algorandfoundation/algorand-python-testing/commit/973fc288836d09ba4657642c980ca9f916d38823))

### Bug fixes

* fix equality implementation for Account, to allow comparison with arc4.Address ([`6ec2dd4`](https://github.com/algorandfoundation/algorand-python-testing/commit/6ec2dd4f2b4119987a5ea7c3c670bdd554c4fe30))

* ensure new Account's have field defaults populated ([`54432b0`](https://github.com/algorandfoundation/algorand-python-testing/commit/54432b03cef13008b16fab84dcc250824e2e2da1))

* ensure Global.current_application* properties match AVM ([`ae84ae2`](https://github.com/algorandfoundation/algorand-python-testing/commit/ae84ae27e49ef977babe7abb10d8994446d6b5f7))

* when generating app/asset id's skip any that might already be reserved ([`0bb5eba`](https://github.com/algorandfoundation/algorand-python-testing/commit/0bb5eba3ec75ffdb16cfbac5b3c4837f64f8a58a))

### Documentation

* integrating pydoclint; formatting docs; removing docs from stub implementation ([`d729bf9`](https://github.com/algorandfoundation/algorand-python-testing/commit/d729bf9b70ef885cd1b2ef705c4f5e2582d853ab))

## v0.3.0-beta.3 (2024-08-16)

## v0.3.0-beta.2 (2024-08-16)

### Features

* implement gaid op ([`71801f0`](https://github.com/algorandfoundation/algorand-python-testing/commit/71801f01e49b683d81fa46d2ddb1c8aaf38b89f2))

### Bug fixes

* added mock implementations for new algopy functions, add util for raising consistent mockable method errors ([`71801f0`](https://github.com/algorandfoundation/algorand-python-testing/commit/71801f01e49b683d81fa46d2ddb1c8aaf38b89f2))

## v0.3.0-beta.1 (2024-08-14)

### Features

* deferred app calls, modular test context, refined access to value generators, numerous fixes/improvements ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

* work in progress on asset, application related state ops ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

* extra tests and implementation wrappers around AppLocal ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

  chore: wip

* adding acctparamsget; extra tests; pr comments ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

* add arc4factory ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

* continue with txn_group_for and add a test ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

### Bug fixes

* handle populating foreign arrays correctly for abi method calls ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

### Documentation

* adding pep257 formatter; using reST docstrings style for context.py ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

## v0.2.2-beta.5 (2024-07-30)

### Documentation

* patch urls in README.md ([`eddf612`](https://github.com/algorandfoundation/algorand-python-testing/commit/eddf612b177a2acddf15d58be3f375e99fb6564b))

* patching old namespace name in readme ([`eddf612`](https://github.com/algorandfoundation/algorand-python-testing/commit/eddf612b177a2acddf15d58be3f375e99fb6564b))

## v0.2.2-beta.4 (2024-07-25)

## v0.2.2-beta.3 (2024-07-25)

## v0.2.2-beta.2 (2024-07-25)

## v0.2.2-beta.1 (2024-07-24)

## v0.2.1 (2024-07-10)

### Bug fixes

* patching helper scripts; adding pre-commit; bumping compiler version ([`8d43492`](https://github.com/algorandfoundation/algorand-python-testing/commit/8d43492adfeb53fd2824f0ea812a9c30bf6bb339))
