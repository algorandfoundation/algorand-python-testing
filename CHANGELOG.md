# CHANGELOG

## v0.2.2-beta.5 (2024-07-30)

### Documentation

* docs: patch urls in README.md (#9)

* chore: patch urls in README.md

* ci: relaxing rules around paths-ignore

* docs: patching old namespace name in readme ([`eddf612`](https://github.com/algorandfoundation/algorand-python-testing/commit/eddf612b177a2acddf15d58be3f375e99fb6564b))

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
