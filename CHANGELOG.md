# CHANGELOG

## v0.3.0-beta.2 (2024-08-16)

### Chore

* chore: refreshing todos (#11)

[skip ci] ([`6df2567`](https://github.com/algorandfoundation/algorand-python-testing/commit/6df256700169d09620db64802ee5177d3cd5803e))

### Refactor

* refactor: moving scratch slots and app logs to TransactionBase (#10)

* refactor: moving scratch slots and app logs to TransactionBase

* build: updated to latest puyapy

* refactor: minor refactors

* refactor: refactor txn group initialization

* refactor: add additional gtxn properties from 2.0 stubs

* refactor: consolidate log and scratch space implementation.

logs can be mocked on the underlying application, or for specific transactions
active txn can append logs

* refactor: defer some imports to reduce circular imports

* chore: add some TODO&#39;s for future work

* test: tweak test for mocking abi_call, by ensuring mocked function is in algopy namespace

* feat: implement gaid op

* fix: added mock implementations for new algopy functions, add util for raising consistent mockable method errors

* chore: add TODO for asset property

---------

Co-authored-by: Daniel McGregor &lt;daniel.mcgregor@makerx.com.au&gt; ([`71801f0`](https://github.com/algorandfoundation/algorand-python-testing/commit/71801f01e49b683d81fa46d2ddb1c8aaf38b89f2))

## v0.3.0-beta.1 (2024-08-14)

### Feature

* feat: deferred app calls, modular test context, refined access to value generators, numerous fixes/improvements (#4)

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

* fix inconsistent usage of field names on application fields
use state total overrides when determining state totals
reduce usage of `import algopy` in implementations

* expose fields property on application to aid debugging

* added section to CONTRIBUTING.md describing relationship between `algopy` and `algopy_testing`

* remove lazy algopy imports from utils
remove some unnecessary ignores
add TODO

* simplify abimethod and add TODO&#39;s

* add TODO for state totals

* add some tests (including currently failing ones) for app transactions

* feat: add arc4factory

* refactor: ensuring underlying _key is properly reflected on local/global states

* refactor: change guards for setting keys to explicitly check for None

* refactor: use implementation types in internal mappings

* refactor: remove usages of `import algopy` from op.py, remove explicit imports from typing module
add TODO&#39;s

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

* refactor: simplify txn implementations
provide default values for unspecified txn fields

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

* refactor: generate arc4 signatures from types
added more robust system for tracking arc4 types
removed unneeded functions on StaticArray

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

* refactor: add active group/txn properties
change local/global state storage to store values against the app, not the contract instance
add UInt64Backed type to simplify serialization to/from int/bytes

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

---------

Co-authored-by: Daniel McGregor &lt;daniel.mcgregor@makerx.com.au&gt; ([`85dd58a`](https://github.com/algorandfoundation/algorand-python-testing/commit/85dd58a60f56a0737de84dcb549c01ca5a7a2851))

### Unknown

* 0.3.0-beta.1

[skip ci] ([`8c12bab`](https://github.com/algorandfoundation/algorand-python-testing/commit/8c12bab417eb9840014bd6cc9190618f6530d29d))

## v0.2.2-beta.5 (2024-07-30)

### Documentation

* docs: patch urls in README.md (#9)

* chore: patch urls in README.md

* ci: relaxing rules around paths-ignore

* docs: patching old namespace name in readme ([`eddf612`](https://github.com/algorandfoundation/algorand-python-testing/commit/eddf612b177a2acddf15d58be3f375e99fb6564b))

### Unknown

* 0.2.2-beta.5

[skip ci] ([`dfa0a1b`](https://github.com/algorandfoundation/algorand-python-testing/commit/dfa0a1b3045b37fb14d69043728fa178466b6100))

## v0.2.2-beta.4 (2024-07-25)

### Ci

* ci: improve cd pipeline to ensure dist is cleaned up before build done by semantic release (#7) ([`6c02d0b`](https://github.com/algorandfoundation/algorand-python-testing/commit/6c02d0b5f08106ac39125f9b1fbbb84203c27bf6))

### Unknown

* 0.2.2-beta.4

[skip ci] ([`01e0adb`](https://github.com/algorandfoundation/algorand-python-testing/commit/01e0adbe68c7c2de1668b90ef4e19844dec0326a))

## v0.2.2-beta.3 (2024-07-25)

### Ci

* ci: tweaking conditional to not perform publish to pypi if no release was generated (#6)

* ci: tweaking conditional to not perform publish to pypi if no release was generated

* chore: tweaking patch tags ([`842f9b5`](https://github.com/algorandfoundation/algorand-python-testing/commit/842f9b55d3bc491f6f32ed3b132a9422b6b7f987))

### Unknown

* 0.2.2-beta.3

[skip ci] ([`0919c42`](https://github.com/algorandfoundation/algorand-python-testing/commit/0919c42e160f76c49c2c8a02acc05a658bbd3fb5))

## v0.2.2-beta.2 (2024-07-25)

### Ci

* ci: bumping version to re trigger semantic releases to fix last failed run (#5)

* ci: bumping version to re trigger semantic releases to fix last failed run

* chore: patching typo in conditionals for workflow dispatch bool params ([`873515c`](https://github.com/algorandfoundation/algorand-python-testing/commit/873515c1f927b34f6863e61c394db0f812949b87))

## v0.2.2-beta.1 (2024-07-24)

### Unknown

* Merge pull request #3 from algorandfoundation/feat/unit-testing-boxes

feat: stub implementation of Box, BoxRef and BoxMap ([`46f7493`](https://github.com/algorandfoundation/algorand-python-testing/commit/46f74935c8b4ff3e96d67a9da3b22bfc4676f3ba))

* make UInt64 backed enums subtypes of UInt64 ([`3b95140`](https://github.com/algorandfoundation/algorand-python-testing/commit/3b9514098c6a361d79275f6d0a36261d24407c2f))

* use `RuntimeError` for when the box does not exists ([`75cc43d`](https://github.com/algorandfoundation/algorand-python-testing/commit/75cc43d22b034b899ca400fde812ff0330b55fdf))

* move low level op.Box into `op.py` for consistency ([`552553e`](https://github.com/algorandfoundation/algorand-python-testing/commit/552553e5763abe6b284bcd22a19ea3acade3326c))

* add notes for higher level Box interfaces to docs ([`7565f8d`](https://github.com/algorandfoundation/algorand-python-testing/commit/7565f8debfaed2e45c3a59eb8625d98c2b2c03b4))

* remove extra bool() call in assertions ([`8c1ef85`](https://github.com/algorandfoundation/algorand-python-testing/commit/8c1ef8576f9db1dce13afe43def3476fda93fd24))

* fix missing imports in __init__ files ([`ec60a6e`](https://github.com/algorandfoundation/algorand-python-testing/commit/ec60a6eea6005915095e5126bb82c1de291e9baf))

* add key property to GlobalState and LocalState ([`5bc6655`](https://github.com/algorandfoundation/algorand-python-testing/commit/5bc665560b756b3bcf152c4bab48dd4b36850766))

* set key and key prefix from contract field name ([`d602578`](https://github.com/algorandfoundation/algorand-python-testing/commit/d602578380d2708285b7ee7cfb11a7fdfd9acdb1))

* add tests for BoxMap implementation ([`7aa6f73`](https://github.com/algorandfoundation/algorand-python-testing/commit/7aa6f7305bc4ff4139b5b511674761e34b063615))

* add tests for BoxRef implementation ([`1ab1aef`](https://github.com/algorandfoundation/algorand-python-testing/commit/1ab1aefa63995a66cb4d8cddc4e9a97ca0acd272))

* add tests for Box implmentation ([`c4c946a`](https://github.com/algorandfoundation/algorand-python-testing/commit/c4c946ab11ae989778df8d670cc7c3048586108e))

* add BoxRef and BoxMap version of contract methods for testing ([`8611266`](https://github.com/algorandfoundation/algorand-python-testing/commit/86112662e30dbb22b849d1b1f62b35fb68d7797a))

* fix typo ([`ca8b07a`](https://github.com/algorandfoundation/algorand-python-testing/commit/ca8b07a9d5ea231e242819fa5c4c78ab5516fabe))

* add stub implementation for BoxRef and BoxMap ([`85a4f4f`](https://github.com/algorandfoundation/algorand-python-testing/commit/85a4f4faeccd6bf29918ffbf49aa5d967fc09598))

* add stub implementation of Box object ([`df901de`](https://github.com/algorandfoundation/algorand-python-testing/commit/df901de83f0c4346ea0bb310acb9b421130a5977))

## v0.2.1 (2024-07-10)

### Chore

* chore: improving codebase; adding semantic releases; fixing scripts &amp; tests post migration (#2)

* fix: patching helper scripts; adding pre-commit; bumping compiler version

* ci: adding semantic releases

* chore: patching pipeline

* chore: improving cd

* chore: patching ci

* chore: refining ci

* chore: refine ci ([`8d43492`](https://github.com/algorandfoundation/algorand-python-testing/commit/8d43492adfeb53fd2824f0ea812a9c30bf6bb339))

* chore: moving out algorand-python-testing from puya repo (#1)

* chore: moving out algorand-python-testing from puya repo

* chore: addressing pr comments; adding ci; adding docs ([`a488ac3`](https://github.com/algorandfoundation/algorand-python-testing/commit/a488ac3091787b63dca90ade43cb8520ff63d612))

* chore: initial commit ([`66ed184`](https://github.com/algorandfoundation/algorand-python-testing/commit/66ed1844ced07bb4a9fc34ba6a7276b469942084))

### Ci

* ci: patch behaviour to ignore commits made by releases bot ([`44000c9`](https://github.com/algorandfoundation/algorand-python-testing/commit/44000c9e42bcd42a8fccf55535ddf5731ae80b9c))

* ci: patch hatch build invocation in cd ([`77aea6e`](https://github.com/algorandfoundation/algorand-python-testing/commit/77aea6ea20266b82c2b7f09c0fc552137740b5d5))

### Unknown

* 0.0.0-beta.1

Automatically generated by python-semantic-release ([`147a734`](https://github.com/algorandfoundation/algorand-python-testing/commit/147a7348018ffed0baadbc40ce1b07a464f7df63))
