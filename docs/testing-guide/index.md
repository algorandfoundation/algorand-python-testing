# Testing Guide

The Algorand Python Testing framework provides powerful tools for testing Algorand Python smart contracts within a Python interpreter. This guide covers the main features and concepts of the framework, helping you write effective tests for your Algorand applications.

```{note}
For all code examples in the _Testing Guide_ section, assume `context` is an instance of `AlgopyTestContext` instantiated with `with algopy_testing_context() as context:`. All subsequent code is executed within this context manager.
```

[![](https://mermaid.ink/img/pako:eNp1kk1OwzAQha8yMptWClKQEIsIVUob9kiwQTVCbjxJTBM7mtiFqOkRWHEArsgRcGjVJvx4YY3nfR7PG3nLUiORRSwnURdwn3ANfjVutU9w9mAcQYIbLE1dobZwozeKjO5jzvZ4v-IlZ6LMTd3CxLY1QmPdqply9nhi5kfmyWJjlc49ewgyEhW-GFpPr1c0m_hnQRBCgX77_Hh_G1da-Eq1awVMUlPVqkQ66agl13_7iP3jJLSEWzLPmI4MJMsfSGsLoyE12pJI7e_iCZyfz7pvr4XStgGlMyRC6b2YqoN4iB3alOAa77aDxaiGn4GXNkp0MD_2btsSIQZ6jS7CgFq_D4X5UAgyVZbRWRheXYYjavHf9WQosIBVSJVQ0v-EbY9xZguskLPIh1LQup_UznPCWXPX6pRFlhwGjIzLCxZlomz8ydVSWEyU8FOvDtndF7zxxLg?type=png)](https://mermaid.live/edit#pako:eNp1kk1OwzAQha8yMptWClKQEIsIVUob9kiwQTVCbjxJTBM7mtiFqOkRWHEArsgRcGjVJvx4YY3nfR7PG3nLUiORRSwnURdwn3ANfjVutU9w9mAcQYIbLE1dobZwozeKjO5jzvZ4v-IlZ6LMTd3CxLY1QmPdqply9nhi5kfmyWJjlc49ewgyEhW-GFpPr1c0m_hnQRBCgX77_Hh_G1da-Eq1awVMUlPVqkQ66agl13_7iP3jJLSEWzLPmI4MJMsfSGsLoyE12pJI7e_iCZyfz7pvr4XStgGlMyRC6b2YqoN4iB3alOAa77aDxaiGn4GXNkp0MD_2btsSIQZ6jS7CgFq_D4X5UAgyVZbRWRheXYYjavHf9WQosIBVSJVQ0v-EbY9xZguskLPIh1LQup_UznPCWXPX6pRFlhwGjIzLCxZlomz8ydVSWEyU8FOvDtndF7zxxLg)

> _High-level overview of the relationship between your smart contracts project, Algorand Python Testing framework, Algorand Python type stubs, and the compiler_

The Algorand Python Testing framework allows you to:

1. Simulate the Algorand Virtual Machine (AVM) environment
2. Create and manipulate test accounts, assets, and applications
3. Execute and verify smart contract logic
4. Test ARC4 (Algorand ABI) methods
5. Manage global and local state
6. Simulate transactions and transaction groups
7. Test inner transactions
8. Verify opcode behavior

By using this framework, you can ensure your Algorand Python smart contracts function correctly before deploying them to a live network.

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
