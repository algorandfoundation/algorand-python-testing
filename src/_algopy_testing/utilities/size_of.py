from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.utils import get_static_size_of


def size_of(typ: type | object, /) -> UInt64:
    size = get_static_size_of(typ)
    if size is None:
        raise ValueError(f"{typ} is dynamically sized")
    return UInt64(size)
