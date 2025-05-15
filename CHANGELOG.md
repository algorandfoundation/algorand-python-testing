# CHANGELOG
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

* ability to pass kw_only flag to dataclass when defining struct subclass (#23) ([`24bcf9d`](https://github.com/algorandfoundation/algorand-python-testing/commit/24bcf9d8af34eb2675ddf85ce9d71802f82f2d6a))

  * fix: ability to pass kw_only flag to dataclass when defining struct subclass

  * chore: add dependabot yaml

  * chore: adding ability to pass args to struct init subclass

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

## v0.3.0-beta.9 (2024-08-22)

## v0.3.0-beta.8 (2024-08-22)

### Features

* include ARC4 results in log, and handle > 15 ARC4 arguments (#18) ([`fd83ee8`](https://github.com/algorandfoundation/algorand-python-testing/commit/fd83ee8525a393d4a1a66f20acdb661906d84b51))

## v0.3.0-beta.7 (2024-08-21)

## v0.3.0-beta.6 (2024-08-21)

### Documentation

* documentation for initial stable release of `algorand-python-testing` (#8) ([`9d97d0d`](https://github.com/algorandfoundation/algorand-python-testing/commit/9d97d0de5ff9897e642ec3f11a186f2fb95375bb))

  * docs: wip

  * chore: refresh pyproject

  * docs: refining docs (wip)

  * chore: integrating doctests

  * docs: revamping docs with latest features

  * docs: minor consistency with main readme; patching doctests

  * docs: removing the box from examples

  * docs: refine op codes section

  * chore: merge conflicts

  * chore: apply suggestions from code review

  Co-authored-by: Daniel McGregor <daniel.mcgregor@makerx.com.au>

  * docs: addressing docs pr comments

## v0.3.0-beta.5 (2024-08-21)

### Bug fixes

* ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types) (#14) ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

  * fix: add default __eq__ implementation for ARC4 types

  * fix: ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types)

  * feat: add __str__ and __repr__ implementations for ARC4 types

  * refactor: make ARC4 type_info private

  * refactor: make ARC4 struct inherit _ABIEncoded

  * refactor: removing get_app_for_contract; expanding get_app; parsing on_complete

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

## v0.3.0-beta.1 (2024-08-14)

### Features

* deferred app calls, modular test context, refined access to value generators, numerous fixes/improvements (#4) ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

  * feat: work in progress on asset, application related state ops

  * test: adding extra tests

  * feat: extra tests and implementation wrappers around AppLocal

  * chore: wip

  * chore: update src/algopy_testing/op.py

  Co-authored-by: Daniel McGregor <daniel.mcgregor@makerx.com.au>

  * feat: adding acctparamsget; extra tests; pr comments

  * refactor: adding final bits around AcctParamsGet; unit tests and fixes

  * refactor: adding lookup by index to acct/app/asset get ops; tweaking ci

  * refactor: addressing pr comments

  * chore: fixing failing test

  * refactor: simplifying test_context validation

  * use specific enum types in box example with latest puya version

  * include box types in algopy_testing

  * fix inconsistent usage of field names on application fields use state total overrides when determining state totals reduce usage of `import algopy` in implementations

  * expose fields property on application to aid debugging

  * added section to CONTRIBUTING.md describing relationship between `algopy` and `algopy_testing`

  * remove lazy algopy imports from utils remove some unnecessary ignores add TODO

  * simplify abimethod and add TODO's

  * add TODO for state totals

  * add some tests (including currently failing ones) for app transactions

  * feat: add arc4factory

  * refactor: ensuring underlying _key is properly reflected on local/global states

  * refactor: change guards for setting keys to explicitly check for None

  * refactor: use implementation types in internal mappings

  * refactor: remove usages of `import algopy` from op.py, remove explicit imports from typing module add TODO's

  * test: use non-abstract contract base

  * allow empty box prefix

  * refactor

  * use immutable param defaults

  * fix: handle populating foreign arrays correctly for abi method calls

  * refactor: remove lazy import algopy

  * remove irrelevant comment

  * initialize accounts correctly

  * build: adding post install command into examples venv in hatch settings

  * refactor: refine arc4 factory; add corresponding tests

  * chore: adding the missing clear methods

  * chore: merging everything from docs branch except docs changes

  * chore: merge conflicts

  * refactor: simplify txn implementations provide default values for unspecified txn fields

  * docs: adding pep257 formatter; using reST docstrings style for context.py

  * test: adding tests for scratch slots

  * refactor: renaming set_txn_fields -> scoped_txn_fields

  * chore: adding `amount` field and open question under TODO;

  also adding adding get_box_map  that reuses get_box but appends the bytes box_map prefix

  * chore: bumping ruff

  * refactor: adding context manager for lsig args setup (similar to algopy.Txn)

  also running latest ruff - some rules are updated

  * refactor: move helper classes into their own file

  * refactor: simplify itxn loader

  * refactor: isolate get_test_context to reduce circular imports

  * chore: using multiprocessing in refresh test artifacts script

  * refactor: adding tests for ITxn, ITxnCreate and GITxn, fixing related bugs

  * refactor: default_creator -> default_sender; setting creator as default_sender

  * chore: parsing name to op name in ITxn

  * chore: updating default extension for mypy to use ms-python

  * test: remove incorrect test and replace with TODO

  * chore: add TODO about subroutine support

  * add stricter type checks for primitives

  * track when contracts are in a "creating" state or not

  * todos

  * refactor: moving GITxn class to itxn.py

  * refactor: generate arc4 signatures from types added more robust system for tracking arc4 types removed unneeded functions on StaticArray

  * only support native tuples when handling generic aliases in arc4 tuples

  * refactor: 1/2 adding paged access to clear state program in txn fields

  * refactor: consolidating txn and itxn related context attributes/methods

  * minor refactors

  * support arc4 structs

  * refactor: simplify logic sig implementation, and remove mapping

  * refactor: fix itxn op behaviour with program pages, and other array like fields

  * refactor: simplify account properties

  * refactor: move crypto ops into their own module

  * refactor: move pure ops into their own module

  * refactor: move other misc ops

  * refactor: consolidating value generators; ledger and txn contexts;

  * refactor: add active group/txn properties change local/global state storage to store values against the app, not the contract instance add UInt64Backed type to simplify serialization to/from int/bytes

  * refactor: remove nested private modules, replace usages of get_test_context with lazy_context

  * refactor: move inner transactions onto transaction group

  * refactor: remove scoped_lsig_args

  * refactor: remove maybe_active_app_id

  * refactor: include bool in test for uint64

  * refactor: ensure arc4 values always have fully parametrized types

  * refactor: use _paramatize_type

  * refactor: addressing TODOs

  refactor: removing txn from method names inside txn context manager prop

  chore: restoring initial pre-commit

  refactor: expanding scoped_execution

  chore: remove redundant fields

  chore: addressing minor todos and removing the ones already addressed

  * refactor: adding unit tests for global/local state with implicit keys

  * refactor: improving handling of initial value for implicit global/local state keys

  * test: extra test cases for accessing implicit/explicit keyed local/global state

  * refactor: wip adding txn_group_for method

  * chore: fix linting errors

  * feat: continue with txn_group_for and add a test

  * chore: remove scoped_txn_fields methods

  * add some additional TODO's for scoped_execution

  * remove TODO

  * expand gaid TODO

  * tweak op.exit implementation and add TODO

  * remove arc4 property from AlgopyTestContext

  * add more TODOs

  * refactor: addressing TODOs; adding marketplace contract example (devrel bootcamps)

  * test: fixing failing tests

## v0.2.2-beta.5 (2024-07-30)

### Documentation

* patch urls in README.md (#9) ([`eddf612`](https://github.com/algorandfoundation/algorand-python-testing/commit/eddf612b177a2acddf15d58be3f375e99fb6564b))

  * chore: patch urls in README.md

  * ci: relaxing rules around paths-ignore

  * docs: patching old namespace name in readme

## v0.2.2-beta.4 (2024-07-25)

## v0.2.2-beta.3 (2024-07-25)

## v0.2.2-beta.2 (2024-07-25)

## v0.2.2-beta.1 (2024-07-24)

## v0.2.1 (2024-07-10)
