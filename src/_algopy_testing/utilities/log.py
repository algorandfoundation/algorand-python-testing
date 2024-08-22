from _algopy_testing.constants import UINT64_BYTES_LENGTH
from _algopy_testing.context_helpers import lazy_context
from _algopy_testing.primitives.bytes import Bytes
from _algopy_testing.primitives.uint64 import UInt64
from _algopy_testing.protocols import BytesBacked
from _algopy_testing.utils import int_to_bytes


def log(
    *args: UInt64 | Bytes | BytesBacked | str | bytes | int,
    sep: Bytes | bytes | str = b"",
) -> None:
    """Concatenates and logs supplied args as a single bytes value.

    UInt64 args are converted to bytes and each argument is separated by `sep`.
    Literal `str` values will be encoded as UTF8.
    """
    logs: list[bytes] = []

    for arg in args:
        if isinstance(arg, UInt64):
            logs.append(int_to_bytes(arg.value, pad_to=UINT64_BYTES_LENGTH))
        elif isinstance(arg, Bytes):
            logs.append(arg.value)
        elif isinstance(arg, str):
            logs.append(arg.encode("utf8"))
        elif isinstance(arg, bytes):
            logs.append(arg)
        elif isinstance(arg, int):
            logs.append(int_to_bytes(arg, pad_to=UINT64_BYTES_LENGTH))
        else:
            logs.append(arg.bytes.value)

    if isinstance(sep, Bytes):
        separator = sep.value
    elif isinstance(sep, str):
        separator = sep.encode("utf8")
    else:
        separator = sep

    active_txn = lazy_context.active_group.active_txn
    active_txn.append_log(separator.join(logs))
