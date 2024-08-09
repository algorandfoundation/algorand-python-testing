# AVM Opcodes

The [coverage](coverage.md) file contains a complete list of all opcodes and respective types as well as whether they are _Mockable_, _Emulated_, or _Native_ within the `algorand-python-testing` package. The following section will highlight common opcodes and types that usually require interaction with test context manager. `Native` opcodes are assumed to function as they are in the Algorand Virtual Machine given that their functionality is stateless, if you experience any issues with any of the `Native` opcodes, please raise an issue in the [`algorand-python-testing` repo](https://github.com/algorandfoundation/algorand-python-testing/issues/new/choose) repository or contribute a PR by following [Contributing](https://github.com/algorandfoundation/algorand-python-testing/blob/main/CONTRIBUTING.md) guide.

## Mockable types

Refer to [coverage](coverage.md) to see which opcodes are of type _Mockable_ - implying that they aren't either emulated or implemented by `algorand-python-testing` due to complexity or edge cases which require real AVM interaction.
