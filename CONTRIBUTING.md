# Contributing to `algorand-python-testing`

Welcome to the Algorand Python Testing library! This guide will help you get started with the project and contribute to its development.

# Development Dependencies

Our development environment relies on the following tools:

-   **Python 3.12**
-   **[Hatch](https://hatch.pypa.io/1.9/install/)**: A modern, extensible Python project manager.
-   **[pre-commit](https://pre-commit.com/)**: A framework for managing and maintaining code quality.

## Common Commands

Here are some common commands you will use with Hatch:

-   **Pre-commit checks:** `hatch run pre_commit`
-   **Run tests:** `hatch run tests`
-   **Build project:** `hatch build`
-   **Open shell:** `hatch shell`
-   **Reset environments:** `hatch env prune`

# Development Scripts

-   **Regenerate typed clients for example contracts:** `hatch run refresh_test_artifacts`
-   **Coverage check of existing progress on implementing AlgoPy Stubs:** `hatch run check_stubs_cov`

# Using `pre-commit`

Execute `pre-commit install` to ensure auto run of hatch against `src` and `examples` folders

# Examples folder

Examples folder uses a dedicated 'venv.examples' virtual environment managed by Hatch that simulates a user environment with both algorand-python and algorand-python-testing installed explicitly. This is useful for testing new features or bug fixes in the testing library.

-   **Pre-commit checks against examples:** `hatch run examples:pre-commit`

# Release automation

Project relies on [python-semantic-release](https://python-semantic-release.readthedocs.io/en/latest/) for release automation.

Releases are triggered by a `workflow_dispatch` event on the `main` branch with `prerelease` set to accordingly using the `.github/workflows/cd.yaml` file.

# Implementation vs Stubs

The canonical definition of the algopy API comes from the [`alogrand-python`](https://pypi.org/project/algorand-python/) package which consists only of typing information defined in the `algopy-stubs` module.
In this library the testing implementation should follow the "shape" of the API defined in these stubs. In particular, types, methods and attributes should reflect what is described in the stubs.

However, implementation specific details can diverge from what is described in the stubs. For example methods marked as `@staticmethod` in the stubs do not need to be static methods in the implementation.
Implementation types may provide more methods or properties than described in the stubs, the stubs are just the minimal set of what should be defined.

The `algopy_testing` module contains the implementation of the stubs and additional parts of the testing framework.
The `algopy` module is used to alias the relevant `algopy_testing` implementations into the correct namespaces defined in the stubs.

Implementations within `algopy_testing` should use `algopy_testing` types as much as possible, except for typing annotations which should use the `algopy` equivalents instead. A rule of thumb to follow is 
withing the `algopy_testing` module, `import algopy` should only be used for type definitions e.g.

```python
import typing

if typing.TYPE_CHECKING:
    import algopy

def do_something_with_bytes(a: algopy.Bytes) -> algopy.Bytes:
    ...
```

Instance checks should be done via the `algopy_testing` namespace, this will ensure any additional attributes on the implementation will be type checked correctly e.g.

```python
import algopy_testing


def do_something(value: object) -> None:
    if isinstance(value, algopy_testing.Bytes):
        raw_bytes: bytes = value.value
        ...
```

Occasionally this will require silencing Mypy warnings, within the scope of the implementation code this is considered acceptable.

```python
import typing

import algopy_testing

if typing.TYPE_CHECKING:
    import algopy

def get_some_bytes() -> algopy.Bytes:
    value = algopy_testing.Bytes(b"42")
    # in the following statement, the return type warning is silenced as 
    # algopy.Bytes is an alias of algopy_testing.Bytes
    return value # type: ignore[return-value]
```
 


