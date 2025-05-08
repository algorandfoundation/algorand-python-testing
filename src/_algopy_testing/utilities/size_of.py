import types

from _algopy_testing.primitives.uint64 import UInt64


def size_of(typ: type | object, /) -> UInt64:
    from _algopy_testing.arc4 import get_max_bytes_static_len
    from _algopy_testing.serialize import get_native_to_arc4_serializer

    if isinstance(typ, types.GenericAlias):
        pass
    elif not isinstance(typ, type):
        typ = type(typ)

    if typ is bool:  # treat bool on its own as a uint64
        typ = UInt64
    serializer = get_native_to_arc4_serializer(typ)  # type: ignore[arg-type]
    type_info = serializer.arc4_type._type_info
    size = get_max_bytes_static_len(type_info)
    if size is None:
        raise ValueError(f"{typ} is dynamically sized")
    return UInt64(size)
