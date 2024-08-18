# Subroutines

Any python function decorated with `@algopy.subroutine` is accessible as regular python function when accessed within the testing context. Which implies no additional setup or teardown is required, simply instantiate the class holding the function and access the function as a regular python instance attribute.

See `simple_voting` examples under [examples](../examples.md) for a showcase of testing subroutines.

```{hint}
Testing `subroutines` is a unique feature of `algorand-python-testing`, in contrast with integration tests against real AVM network, this approach allows validating critical logic of narrowly scoped business logic of the contract class without the need to access it via public method that relies on it. In a real AVM network, a user would have to deploy a contract, assemble and submit application call/group to the network, and await for the right results to be implcitly hit by the `subroutine`.
```
