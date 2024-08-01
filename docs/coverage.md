# Coverage

See which `algorand-python` stubs are implemented by the `algorand-python-testing` library. There are 3 general categories:

1. **Implemented**: Fully matches AVM computation in Python. E.g., `algopy.op.sha256` and other cryptographic operations behave identically in AVM and unit tests.

2. **Emulated**: Uses `AlgopyTestContext` to mimic AVM behavior. E.g., `Box.put` on an `algopy.Box` within a test context stores data in the test manager, not the real Algorand network, but provides the same interface.

3. **Mockable**: Not implemented but can be mocked or patched. E.g., `algopy.abi_call` can be mocked to return specific values or behaviors; otherwise, it raises a "not implemented" exception. These are cases where implementation in a unit test context is impractical or overly complex.

> Note, below table not exhaustive yet, but will be expanded along with initial stable release.

| Name                                 | Implementation Status |
| ------------------------------------ | --------------------- |
| UInt64                               | Implemented           |
| BigUInt                              | Implemented           |
| Bytes                                | Implemented           |
| String                               | Implemented           |
| urange                               | Implemented           |
| op.sha256                            | Implemented           |
| op.sha3_256                          | Implemented           |
| op.keccak256                         | Implemented           |
| arc4.UIntN                           | Implemented           |
| arc4.BigUIntN                        | Implemented           |
| arc4.UFixedNxM                       | Implemented           |
| arc4.BigUFixedNxM                    | Implemented           |
| arc4.Byte                            | Implemented           |
| arc4.UInt8                           | Implemented           |
| arc4.UInt16                          | Implemented           |
| arc4.UInt32                          | Implemented           |
| arc4.UInt64                          | Implemented           |
| arc4.UInt128                         | Implemented           |
| arc4.UInt256                         | Implemented           |
| arc4.UInt512                         | Implemented           |
| arc4.Bool                            | Implemented           |
| arc4.Address                         | Implemented           |
| arc4.DynamicBytes                    | Implemented           |
| arc4.arc4_signature                  | Implemented           |
| arc4.StaticArray                     | Implemented           |
| arc4.DynamicArray                    | Implemented           |
| arc4.Tuple                           | Implemented           |
| arc4.Struct                          | Implemented           |
| arc4.ARC4Client                      | Mockable              |
| arc4.emit                            | Emulated              |
| arc4.baremethod                      | Emulated              |
| arc4.abimethod                       | Emulated              |
| arc4.abi_call                        | Mockable              |
| ARC4Contract, arc4.ARC4Contract      | Emulated              |
| StateTotals                          | Implemented           |
| Txn                                  | Emulated              |
| GTxn                                 | Emulated              |
| ITxn                                 | Emulated              |
| Asset                                | Emulated              |
| Account                              | Emulated              |
| Application                          | Emulated              |
| subroutine                           | Emulated              |
| Global                               | Emulated              |
| op.Box.create                        | Emulated              |
| op.Box.delete                        | Emulated              |
| op.Box.extract                       | Emulated              |
| op.EllipticCurve                     | Mockable              |
| Box                                  | Emulated              |
| BoxRef                               | Emulated              |
| BoxMap                               | Emulated              |
| Block                                | Emulated              |
| logicsig                             | Emulated              |
| log                                  | Emulated              |
| itxn.submit_txns                     | Emulated              |
| itxn.PaymentInnerTransaction         | Emulated              |
| itxn.Payment                         | Emulated              |
| itxn.KeyRegistrationInnerTransaction | Emulated              |
| itxn.KeyRegistration                 | Emulated              |
| itxn.InnerTransactionResult          | Emulated              |
| itxn.InnerTransaction                | Emulated              |
| itxn.AssetTransferInnerTransaction   | Emulated              |
| itxn.AssetTransfer                   | Emulated              |
| itxn.AssetFreezeInnerTransaction     | Emulated              |
| itxn.AssetFreeze                     | Emulated              |
| itxn.AssetConfigInnerTransaction     | Emulated              |
| itxn.AssetConfig                     | Emulated              |
| itxn.ApplicationCall                 | Emulated              |
| gtxn.TransactionBase                 | Emulated              |
| gtxn.Transaction                     | Emulated              |
| gtxn.PaymentTransaction              | Emulated              |
| gtxn.KeyRegistrationTransaction      | Emulated              |
| gtxn.AssetTransferTransaction        | Emulated              |
| gtxn.AssetFreezeTransaction          | Emulated              |
| gtxn.AssetConfigTransaction          | Emulated              |
| gtxn.ApplicationCallTransaction      | Emulated              |
| Contract                             | Emulated              |
| ensure_budget                        | Mockable              |
