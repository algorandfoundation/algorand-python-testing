from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.utils import static_size_of


def size_of(typ: type | object, /) -> UInt64:
    result = static_size_of(typ)
    if result is None:
        raise ValueError(f"{typ} is dynamically sized")
    return result
