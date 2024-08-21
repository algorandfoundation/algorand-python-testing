from algopy import (
    Account,
    ARC4Contract,
    Box,
    BoxMap,
    GlobalState,
    LocalState,
    Txn,
    arc4,
    subroutine,
)


class MyStruct(arc4.Struct):
    bar: arc4.UInt64
    baz: arc4.String


MyArray = arc4.DynamicArray[MyStruct]


class StateMutations(ARC4Contract):
    def __init__(self) -> None:
        self.no_proxy = MyArray()
        self.glob_assign = GlobalState(MyArray)
        self.glob = GlobalState(MyArray)
        self.loc = LocalState(MyArray)
        self.box = Box(MyArray)
        self.map = BoxMap(Account, MyArray)

    @arc4.baremethod(allow_actions=["OptIn"])
    def opt_in(self) -> None:
        self.glob_assign.value = MyArray()
        self.glob.value = MyArray()
        self.box.value = MyArray()
        self.loc[Txn.sender] = MyArray()
        self.map[Txn.sender] = MyArray()

    @arc4.abimethod
    def append(self) -> None:
        struct = get_struct()
        arr = self.glob_assign.value.copy()
        arr.append(struct.copy())

        self.glob_assign.value = arr.copy()
        self.no_proxy.append(struct.copy())
        self.glob.value.append(struct.copy())
        self.loc[Txn.sender].append(struct.copy())
        self.box.value.append(struct.copy())
        self.map[Txn.sender].append(struct.copy())

    @arc4.abimethod
    def modify(self) -> None:
        modified = arc4.String("modified")

        arr = self.glob_assign.value.copy()
        arr[0].baz = modified
        self.glob_assign.value = arr.copy()

        self.no_proxy[0].baz = modified
        self.glob.value[0].baz = modified
        self.loc[Txn.sender][0].baz = modified
        self.box.value[0].baz = modified
        self.map[Txn.sender][0].baz = modified

    @arc4.abimethod
    def get(self) -> MyArray:
        a0 = self.no_proxy.copy()
        a1 = self.glob_assign.value.copy()
        a2 = self.glob.value.copy()
        a3 = self.loc[Txn.sender].copy()
        a4 = self.box.value.copy()
        a5 = self.map[Txn.sender].copy()

        assert a0 == a1, "expected global assign == no_proxy"
        assert a0 == a2, "expected global == no_proxy"
        assert a0 == a3, "expected local == no_proxy"
        assert a0 == a4, "expected box == no_proxy"
        assert a0 == a5, "expected map == no_proxy"
        return a0


@subroutine
def get_struct() -> MyStruct:
    return MyStruct(
        bar=arc4.UInt64(1),
        baz=arc4.String("baz"),
    )
