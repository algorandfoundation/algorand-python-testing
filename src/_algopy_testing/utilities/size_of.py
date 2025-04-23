import inspect
import typing

from _algopy_testing.primitives.uint64 import UInt64


def size_of(typ: type | object, /) -> UInt64:
    from _algopy_testing.arc4 import _TupleTypeInfo, _TypeInfo, get_max_bytes_static_len
    from _algopy_testing.models.account import Account
    from _algopy_testing.models.application import Application
    from _algopy_testing.models.asset import Asset
    from _algopy_testing.serialize import get_native_to_arc4_serializer

    # Check for types with _type_info attribute
    if hasattr(typ, "_type_info") or isinstance(typ, _TypeInfo):
        size = get_max_bytes_static_len(typ if isinstance(typ, _TypeInfo) else typ._type_info)
        if size is not None:
            return UInt64(size)
        else:
            raise ValueError(f"{typ} is dynamically sized")

    # Fixed-size types
    fixed_sizes = {UInt64: 8, Account: 32, Application: 8, Asset: 8, bool: 8}

    # Check if type matches any fixed-size type
    for cls, size in fixed_sizes.items():
        if isinstance(typ, cls) or typ == cls:
            return UInt64(size)

    # Handle tuple types
    is_tuple = (isinstance(typ, type) and issubclass(typ, tuple)) or typing.get_origin(
        typ
    ) is tuple
    if is_tuple:
        if typing.NamedTuple in getattr(typ, "__orig_bases__", []):
            tuple_fields = list(
                inspect.get_annotations(typ if isinstance(typ, type) else typ.__class__).values()
            )
        else:
            tuple_fields = list(typing.get_args(typ))

        type_infos = [get_native_to_arc4_serializer(f).arc4_type._type_info for f in tuple_fields]
        return size_of(_TupleTypeInfo(type_infos))

    raise ValueError(f"{typ} is dynamically sized")
