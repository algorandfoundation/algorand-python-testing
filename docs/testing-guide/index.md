# Testing Guide

The Algorand Python Testing framework provides tools for testing Algorand Python smart contracts within a Python interpreter. This guide covers the main features and concepts of the framework.

```{note}
For all code examples in the _Testing Guide_ section, assume `ctx` as an instance of `AlgopyTestContext` instantiated with `with algopy_testing_context() as ctx:` and all subsequent code is executed within the context manager.
```

```{mermaid}
graph TD
    subgraph "Your Virtual Environment"
        A["algorand-python (mypy stubs)"]
        B["algorand-python-testing (mypy stubs)<br>(You are here 📍)"]
        C["puyapy (compiler)"]
    end

    subgraph "Your Python Project"
        D[Your Algorand Python contract]
    end

    D -->|types hints inferred from| A
    D -->|compiled using| C
    D -->|tested via| B

    style A rx:10,ry:10
    style B rx:10,ry:10,fill:#006400
    style C rx:10,ry:10
    style D rx:10,ry:10
```

> _High level overview of the relationship between your smart contracts project, Algorand Python Testing framework, Algorand Python stubs and the compiler_

## Table of Contents

```{toctree}
---
maxdepth: 3
---

concepts
avm-types
arc4-types
transactions
contract-testing
signature-testing
state-management
subroutines
opcodes
```
