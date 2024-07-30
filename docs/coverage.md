# Coverage

See which `algorand-python` stubs are implemented by the `algorand-python-testing` library. There are 3 general categories:

1. **Implemented**: Fully matches AVM computation in Python. E.g., `algopy.op.sha256` and other cryptographic operations behave identically in AVM and unit tests.

2. **Emulated**: Uses `AlgopyTestContext` to mimic AVM behavior. E.g., `Box.put` on an `algopy.Box` within a test context stores data in the test manager, not the real Algorand network, but provides the same interface.

3. **Mockable**: Not implemented but can be mocked or patched. E.g., `algopy.abi_call` can be mocked to return specific values or behaviors; otherwise, it raises a "not implemented" exception. These are cases where implementation in a unit test context is impractical or overly complex.

> Note, below table not exhaustive yet, but will be expanded along with initial stable release.

| Name                                                                        | Implementation Status |
| --------------------------------------------------------------------------- | --------------------- |
| Primitives (UInt64, BigUInt, Bytes, String)                                 | Implemented           |
| urange                                                                      | Implemented           |
| All crypto ops in op.\* namespace (e.g., sha256, sha3_256, keccak256, etc.) | Implemented           |
| arc4.\* namespace (e.g., UIntN, BigUIntN, UFixedNxM, etc.)                  | Implemented           |
| uenumerate                                                                  | Implemented           |
| StateTotals                                                                 | Implemented           |
| Txn                                                                         | Emulated              |
| GTxn                                                                        | Emulated              |
| ITxn                                                                        | Emulated              |
| Asset                                                                       | Emulated              |
| Account                                                                     | Emulated              |
| Application                                                                 | Emulated              |
| subroutine                                                                  | Emulated              |
| Global                                                                      | Emulated              |
| op.Box.\* (e.g., Box.create, Box.delete, Box.extract, etc.)                 | Emulated              |
| Box                                                                         | Emulated              |
| BoxRef                                                                      | Emulated              |
| BoxMap                                                                      | Emulated              |
| Block                                                                       | Emulated              |
| logicsig                                                                    | Emulated              |
| log                                                                         | Emulated              |
| itxn.\* namespace (inner transactions)                                      | Emulated              |
| gtxn.\* namespace (group transactions)                                      | Emulated              |
| op.ITxnCreate                                                               | Emulated              |
| op.AssetParamsGet                                                           | Emulated              |
| op.AppParamsGet                                                             | Emulated              |
| op.AppLocal                                                                 | Emulated              |
| op.AppGlobal                                                                | Emulated              |
| op.AcctParamsGet                                                            | Emulated              |
| ensure_budget                                                               | Mockable              |
| op.EllipticCurve                                                            | Mockable              |
