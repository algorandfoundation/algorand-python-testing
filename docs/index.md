# Algorand Python Testing

`algorand-python-testing` is a companion package to [Algorand Python](https://github.com/algorandfoundation/puya) that enables efficient unit testing of Algorand Python smart contracts in an offline environment. This package emulates key AVM behaviors without requiring a network connection, offering fast and reliable testing capabilities with a familiar Pythonic interface.

The `algorand-python-testing` package provides:

-   A simple interface for fast and reliable unit testing
-   An offline testing environment that simulates core AVM functionality
-   A familiar Pythonic experience, compatible with testing frameworks like [pytest](https://docs.pytest.org/en/latest/), [unittest](https://docs.python.org/3/library/unittest.html), and [hypothesis](https://hypothesis.readthedocs.io/en/latest/)

## Quick Start

`algorand-python` is a prerequisite for `algorand-python-testing`, providing stubs and type annotations for Algorand Python syntax. It enhances code completion and type checking when writing smart contracts. Note that this code isn't directly executable in standard Python interpreters; it's compiled by `puya` into TEAL for Algorand Network deployment.

Traditionally, testing Algorand smart contracts involved deployment on sandboxed networks and interacting with live instances. While robust, this approach can be inefficient and lacks versatility for testing Algorand Python code.

Enter `algorand-python-testing`: it leverages Python's rich testing ecosystem for unit testing without network deployment. This enables rapid iteration and granular logic testing.

> **NOTE**: While `algorand-python-testing` offers valuable unit testing capabilities, it's not a replacement for comprehensive testing. Use it alongside other test types, particularly those running against the actual Algorand Network, for thorough contract validation.

### Prerequisites

-   Python 3.12 or later
-   [Algorand Python](https://github.com/algorandfoundation/puya)

### Installation

`algorand-python-testing` is distributed via [pypi](https://pypi.org/project/algorand-python-testing/),

install the package using `pip`:

```bash
pip install algopy-python-testing

```

or using `poetry`

```bash
poetry add algopy-python-testing
```

### Testing your first contract

Let's write a "Hello World" contract and test it using the `algopy-testing-python` framework.

Assume the following starter contract (available as starter on all `algokit init -t python` based templates):

#### Contract Definition

```python
from algopy import ARC4Contract, arc4

class HelloWorld(ARC4Contract):
    @arc4.abimethod()
    def hello(self, name: arc4.String) -> arc4.String:
        return "Hello, " + name
```

#### Test Definition

```python
from algopy_testing import algopy_testing_context
from contracts.hello_world import HelloWorld

def test_hello_world():
    with algopy_testing_context() as ctx:
        # Arrange
        input_size = 10
        random_input = ctx.any_string(length=input_size)
        contract = HelloWorld()

        # Act
        result = contract.hello(random_input)

        # Assert
        assert result == f"Hello, {random_input}"
```

The `test_hello_world()` function demonstrates key aspects of testing with `algopy-testing-python`, following the Arrange-Act-Assert pattern:

1. Arrange:

    - Simulated Environment: Utilizes `algopy_testing_context()` to mimic the Algorand Virtual Machine. It also provides access to an array of utilities and so called [_value generators_](testing-guide/concepts.md#value-generators) which allow quick instantiation of random values of specific types where the value itself is not important, it also serves as a backbone for property based testing capabilities.
    - Test Data Generation: Leverages `ctx.any_string()` for creating random, typed inputs of type `algopy.String`. Note that this differs from `algopy.arc4` types, for which context manager provides separate `any_*` methods accessible via `arc4` property on context instance.
    - Contract Instantiation: Creates an instance of `HelloWorld` contract within the test context. Test context automatically instantiates a corresponding `algopy.Application` and links it with the class instance which is loaded in the python interpreter.

2. Act:

    - Method Invocation: Calls `hello()` in a Python interpreter, enabling state inspection and debugging. When you run methods decorated with `abimethod` or `baremethod`, test context will automatically assemble a respective `appl` transaction which can be accessed via `context.get_active_transaction`, note that it will also automatically pre populate foreign references passed, as include the appropriate method signature in the application args.

3. Assert:
    - Behavior Verification: Asserts the expected output matches the actual result.

Additionally, the `any_*` methods facilitate diverse random input generation. This approach aligns well with the "Arrange, Act, Assert" testing pattern, which forces developers to think about the contract's behaviour in a more self-contained manner.

```{hint}
Keep in mind the critical role of thorough testing in smart contract development. Given their often immutable nature once deployed, comprehensive unit and integration tests are essential for ensuring contract validity and reliability. Additionally, optimizing your contracts for efficiency can significantly impact user experience by reducing transaction fees and simplifying interactions. Investing time in robust testing and optimization practices will pay dividends in the long run, both for you as a smart contract developer and for the users of the deployed contracts.
```

### Next steps

To dig deeper into the capabilities of `algorand-python-testing`, continue with the following sections.

```{toctree}
---
maxdepth: 2
caption: Contents
hidden: true
---

testing-guide/index
examples
coverage
glossary
api
```
