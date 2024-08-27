# CHANGELOG
## v0.4.0 (2024-08-27)

## v0.4.0-beta.2 (2024-08-27)

## v0.4.0-beta.1 (2024-08-27)

### Feature

* add support for frozen on asset holdings, including a new ledger function `update_asset_holdings` for setting asset holding balances and frozen states ([`d777ca0`](https://github.com/algorandfoundation/algorand-python-testing/commit/d777ca0a318a8ade7a20363c9ce77fe8a8bf5d68))

* expand accepted types when interacting with accounts, applications and assets ([`f448a97`](https://github.com/algorandfoundation/algorand-python-testing/commit/f448a97cb154c9f90ecf42c599b240f12928af20))

  wip

* replaced `account_exists` with `account_is_funded` as the later is more useful ([`4d08690`](https://github.com/algorandfoundation/algorand-python-testing/commit/4d086903eb93a70ce1d485cdd7b12d8472ef16db))

### Fix

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

### Feature

* include ARC4 results in log, and handle &gt; 15 ARC4 arguments (#18) ([`fd83ee8`](https://github.com/algorandfoundation/algorand-python-testing/commit/fd83ee8525a393d4a1a66f20acdb661906d84b51))

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

  Co-authored-by: Daniel McGregor &lt;daniel.mcgregor@makerx.com.au&gt;

  * docs: addressing docs pr comments

## v0.3.0-beta.5 (2024-08-21)

### Fix

* ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types) (#14) ([`1f1f2ea`](https://github.com/algorandfoundation/algorand-python-testing/commit/1f1f2ea43a2f4f906cbcd5709b8e86b5c1f2bc63))

  * fix: add default __eq__ implementation for ARC4 types

  * fix: ensure mutable types (ARC4 tuple, array and structs) have their changes propagated back to container-like types (global/local state, boxes, ARC4 mutable types)

  * feat: add __str__ and __repr__ implementations for ARC4 types

  * refactor: make ARC4 type_info private

  * refactor: make ARC4 struct inherit _ABIEncoded

  * refactor: removing get_app_for_contract; expanding get_app; parsing on_complete

## v0.3.0-beta.4 (2024-08-21)

### Feature

* rename txn_op_fields to active_txn_overrides to better reflect purpose, add additional checks to ensure crate_group parameters are used correctly ([`973fc28`](https://github.com/algorandfoundation/algorand-python-testing/commit/973fc288836d09ba4657642c980ca9f916d38823))

### Fix

* fix equality implementation for Account, to allow comparison with arc4.Address ([`6ec2dd4`](https://github.com/algorandfoundation/algorand-python-testing/commit/6ec2dd4f2b4119987a5ea7c3c670bdd554c4fe30))

* ensure new Account&#39;s have field defaults populated ([`54432b0`](https://github.com/algorandfoundation/algorand-python-testing/commit/54432b03cef13008b16fab84dcc250824e2e2da1))

* ensure Global.current_application* properties match AVM ([`ae84ae2`](https://github.com/algorandfoundation/algorand-python-testing/commit/ae84ae27e49ef977babe7abb10d8994446d6b5f7))

* when generating app/asset id&#39;s skip any that might already be reserved ([`0bb5eba`](https://github.com/algorandfoundation/algorand-python-testing/commit/0bb5eba3ec75ffdb16cfbac5b3c4837f64f8a58a))

### Documentation

* integrating pydoclint; formatting docs; removing docs from stub implementation ([`d729bf9`](https://github.com/algorandfoundation/algorand-python-testing/commit/d729bf9b70ef885cd1b2ef705c4f5e2582d853ab))

## v0.3.0-beta.3 (2024-08-16)

## v0.3.0-beta.2 (2024-08-16)

## v0.3.0-beta.1 (2024-08-14)

### Feature

* deferred app calls, modular test context, refined access to value generators, numerous fixes/improvements (#4) ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

  * feat: work in progress on asset, application related state ops

  * test: adding extra tests

  * feat: extra tests and implementation wrappers around AppLocal

  * chore: wip

  * chore: update src/algopy_testing/op.py

  Co-authored-by: Daniel McGregor &lt;daniel.mcgregor@makerx.com.au&gt;

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

  * simplify abimethod and add TODO&#39;s

  * add TODO for state totals

  * add some tests (including currently failing ones) for app transactions

  * feat: add arc4factory

  * refactor: ensuring underlying _key is properly reflected on local/global states

  * refactor: change guards for setting keys to explicitly check for None

  * refactor: use implementation types in internal mappings

  * refactor: remove usages of `import algopy` from op.py, remove explicit imports from typing module add TODO&#39;s

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

  * refactor: renaming set_txn_fields -&gt; scoped_txn_fields

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

  * refactor: default_creator -&gt; default_sender; setting creator as default_sender

  * chore: parsing name to op name in ITxn

  * chore: updating default extension for mypy to use ms-python

  * test: remove incorrect test and replace with TODO

  * chore: add TODO about subroutine support

  * add stricter type checks for primitives

  * track when contracts are in a &#34;creating&#34; state or not

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

  * add some additional TODO&#39;s for scoped_execution

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
