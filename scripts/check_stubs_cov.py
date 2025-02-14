import ast
import importlib
import inspect
import site
import sys
import typing
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

from prettytable import PrettyTable

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
SITE_PACKAGES = Path(site.getsitepackages()[0])
STUBS_ROOT = SITE_PACKAGES / "algopy-stubs"
IMPL = PROJECT_ROOT / "src"
ROOT_MODULE = "algopy"
_ADDITIONAL_GLOBAL_IMPLS = [
    "_algopy_testing.op.global_values._Global",
    "_algopy_testing.op.global_values.GlobalFields",
]
_ADDITIONAL_TXN_IMPLS = [
    "_algopy_testing.models.txn_fields.TransactionFields",
    "_algopy_testing.models.txn_fields.TransactionFieldsGetter",
    "_algopy_testing.op.constants.OP_MEMBER_TO_TXN_MEMBER",
]

# mapping of stub types to additional implementation types to scan for members
_ADDITIONAL_TYPE_IMPLS = {
    "algopy.Asset": ["_algopy_testing.models.asset.AssetFields"],
    "algopy.Account": ["_algopy_testing.models.account.AccountFields"],
    "algopy.Application": ["_algopy_testing.models.application.ApplicationFields"],
    "algopy.Global": _ADDITIONAL_GLOBAL_IMPLS,
    "algopy.Txn": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.Global": _ADDITIONAL_GLOBAL_IMPLS,
    "algopy.op.GTxn": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.GITxn": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.Txn": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.ITxn": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.ITxnCreate": _ADDITIONAL_TXN_IMPLS,
    "algopy.op.AppParamsGet": ["_algopy_testing.op.misc._AppParamsGet"],
    "algopy.op.AssetHoldingGet": ["_algopy_testing.op.misc._AssetHoldingGet"],
    "algopy.op.AppGlobal": ["_algopy_testing.op.misc._AppGlobal"],
    "algopy.op.AppLocal": ["_algopy_testing.op.misc._AppLocal"],
    "algopy.op.Scratch": ["_algopy_testing.op.misc._Scratch"],
}

# mapping of stub types to members that may be present but not found when discovering members
_ADDITIONAL_MEMBERS = {
    "algopy.Asset": ["id"],
}


class ASTNodeDefinition(NamedTuple):
    node: ast.AST
    path: Path
    name: str
    object_type: str


class CoverageResult(NamedTuple):
    full_name: str
    impl_file: str | None
    stub_file: str
    coverage: float
    missing: str


class ImplCoverage:
    def __init__(
        self, path: Path, defined: list[str] | None = None, missing: list[str] | None = None
    ):
        self.path = path
        self.defined = defined or []
        self.missing = missing or []

    @property
    def coverage(self) -> float:
        if not self.defined:
            return 1
        total = len(self.defined)
        implemented = total - len(self.missing)
        return implemented / total


def main() -> None:
    clear_algopy_content()
    stubs = collect_public_stubs()
    coverage = collect_coverage(stubs)
    print_results(coverage)


def clear_algopy_content() -> None:
    algopy_path = SITE_PACKAGES / "algopy.py"
    if algopy_path.exists():
        algopy_path.write_text("")


def collect_public_stubs() -> dict[str, ASTNodeDefinition]:
    stubs_root = STUBS_ROOT / "__init__.pyi"
    stubs_ast = _parse_python_file(stubs_root)
    result = dict[str, ASTNodeDefinition]()
    for stmt in stubs_ast.body:
        if isinstance(stmt, ast.ImportFrom):
            if stmt.module is None:
                raise NotImplementedError
            for name in stmt.names:
                if isinstance(name, ast.alias):
                    result.update(collect_imports(stmt, name))
                else:
                    raise NotImplementedError
    return result


def collect_imports(
    stmt: ast.ImportFrom, alias: ast.alias
) -> Iterable[tuple[str, ASTNodeDefinition]]:
    assert stmt.module is not None
    # remove algopy.
    relative_module = stmt.module.split(".", maxsplit=1)[-1]
    src = alias.name
    dest = alias.asname
    # from module import *
    if src == "*" and dest is None:
        for defn_name, defn in collect_stubs(STUBS_ROOT, relative_module).items():
            yield f"{ROOT_MODULE}.{defn_name}", defn
    # from root import src as src
    elif stmt.module == ROOT_MODULE and dest == src:
        for defn_name, defn in collect_stubs(STUBS_ROOT, src).items():
            yield f"{ROOT_MODULE}.{dest}.{defn_name}", defn
    # from foo.bar import src as src
    elif dest == src:
        stubs = collect_stubs(STUBS_ROOT, relative_module)
        yield f"{ROOT_MODULE}.{src}", stubs[src]
    else:
        raise NotImplementedError


def collect_stubs(stubs_dir: Path, relative_module: str) -> dict[str, ASTNodeDefinition]:
    if "." in relative_module:
        raise NotImplementedError("Nested modules not implemented")
    module_path = (stubs_dir / relative_module).with_suffix(".pyi")
    stubs_ast = _parse_python_file(module_path)
    result = dict[str, ASTNodeDefinition]()
    for stmt in stubs_ast.body:
        name = ""
        node_type = ""
        node: ast.AST | None = None
        match stmt:
            case ast.ClassDef(name=name) as node:
                node_type = "Class"
            case ast.FunctionDef(name=name) as node:
                node_type = "Function"
            case ast.Assign(targets=[ast.Name(id=name)], value=node) | ast.AnnAssign(
                target=ast.Name(id=name), value=node
            ):
                node_type = type(node).__name__
        if node and not name.startswith("_"):
            result[name] = ASTNodeDefinition(node, module_path, name, node_type)
    return result


def collect_coverage(stubs: dict[str, ASTNodeDefinition]) -> list[CoverageResult]:
    result = []
    for full_name, stub in stubs.items():
        coverage = _get_impl_coverage(full_name, stub)
        if coverage:
            try:
                impl_path = coverage.path.relative_to(IMPL)
            except ValueError:
                # if not in stub path, assume it is a built-in type
                # probably from a generic that has had type vars specified
                impl_path = coverage.path.relative_to(Path(sys.base_prefix).resolve())
            impl_file = str(impl_path)
        else:
            impl_file = ""
        result.append(
            CoverageResult(
                full_name=full_name,
                stub_file=str(stub.path.relative_to(STUBS_ROOT)),
                impl_file=impl_file or "MISSING!",
                coverage=coverage.coverage if coverage else 0,
                missing=", ".join(coverage.missing if coverage else []),
            )
        )
    return result


def print_results(results: list[CoverageResult]) -> None:
    table = PrettyTable(
        field_names=["Name", "Implementation", "Source Stub", "Coverage", "Missing"],
        header=True,
        border=True,
        padding_width=2,
        left_padding_width=0,
        right_padding_width=1,
        align="l",
        max_width=100,
    )

    for result in sorted(results, key=lambda c: c.coverage):
        table.add_row(
            [
                result.full_name,
                result.impl_file,
                result.stub_file,
                f"{result.coverage:.2%}",
                result.missing,
            ],
            divider=True,
        )

    print(table)


def _parse_python_file(filepath: Path) -> ast.Module:
    """Parse a Python file and return its AST."""
    with filepath.open() as file:
        tree = ast.parse(file.read(), filename=str(filepath))
    return tree


def _get_impl_coverage(symbol: str, stub: ASTNodeDefinition) -> ImplCoverage | None:
    import importlib
    import sys
    from pathlib import Path

    # Add the src directory to the Python path
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    module, name = symbol.rsplit(".", maxsplit=1)
    try:
        # Use importlib.import_module for both algopy and non-algopy modules
        mod = importlib.import_module(module)
    except ImportError as ex:
        print(f"Error importing {module}: {ex}")
        return None

    try:
        impl = getattr(mod, name)
    except AttributeError:
        return None

    try:
        impl_path = Path(inspect.getfile(impl))
    except TypeError:
        # If impl is an instance, try to get the file of its class
        if hasattr(impl, "__class__"):
            try:
                impl_path = Path(inspect.getfile(impl.__class__))
            except TypeError:
                print(f"Warning: Could not determine file for {symbol}")
                return None
        else:
            print(f"Warning: Could not determine file for {symbol}")
            return None

    return _compare_stub_impl(stub.node, symbol, impl, impl_path)


def _get_impl_members(impl_name: str, impl: object) -> set[str]:
    if isinstance(impl, type):
        impl_mros: list[object] = [
            typ for typ in impl.mro() if typ.__module__.startswith("_algopy_testing")
        ]
    else:
        impl_mros = []
    for additional_type in _ADDITIONAL_TYPE_IMPLS.get(impl_name, []):
        impl_mros.append(_resolve_fullname(additional_type))

    impl_members = set[str](_ADDITIONAL_MEMBERS.get(impl_name, []))
    for impl_typ in impl_mros:
        if typing.is_typeddict(impl_typ) and isinstance(impl_typ, type):
            for typed_dict_mro in impl_typ.mro():
                ann = getattr(typed_dict_mro, "__annotations__", None)
                if isinstance(ann, dict):
                    impl_members.update(ann.keys())
        elif isinstance(impl_typ, dict):
            impl_members.update(impl_typ.keys())
        elif isinstance(impl_typ, type):
            members = list(vars(impl_typ).keys())
            impl_members.update(members)
        else:
            raise ValueError(f"unexpected implementation type, {impl_typ}")
    # special case for ITxnCreate
    if impl_name == "algopy.op.ITxnCreate":
        impl_members = {f"set_{member}" for member in impl_members}
        impl_members.update(("begin", "next", "submit"))
    return impl_members


def _resolve_fullname(fullname: str) -> object:
    # note this assumes no nested classes
    module_name, type_name = fullname.rsplit(".", maxsplit=1)
    module = importlib.import_module(module_name)
    return getattr(module, type_name)


def _compare_stub_impl(
    stub: ast.AST, impl_name: str, impl: object, impl_path: Path
) -> ImplCoverage:
    # classes are really the only types that can be "partially implemented"
    # from a typing perspective
    # algopy.uenumerate is typed as a class, but is really just a function
    if not isinstance(stub, ast.ClassDef) or impl_name == "algopy.uenumerate":
        return ImplCoverage(impl_path)
    impl_members = _get_impl_members(impl_name, impl)
    stub_members = set()
    for stmt in stub.body:
        if isinstance(stmt, ast.FunctionDef):
            stub_members.add(stmt.name)
        elif isinstance(stmt, ast.AnnAssign):
            # Handle annotated class variables
            if isinstance(stmt.target, ast.Name):
                stub_members.add(stmt.target.id)
        elif isinstance(stmt, ast.Assign):
            # Handle regular class variables
            for target in stmt.targets:
                if isinstance(target, ast.Name):
                    stub_members.add(target.id)

    if not stub_members:  # no members?
        return ImplCoverage(impl_path)

    # exclude some default implementations
    default_impls = {
        f"__{op}__"
        for op in (
            "ipow",
            "imod",
            "ifloordiv",
            "irshift",
            "ilshift",
            "ior",
            "iand",
            "iadd",
            "ixor",
            "imul",
            "isub",
            "ne",
        )
    }
    # excluding special fields used in typing hints
    default_impls.update(("__match_args__", "__match_value__"))
    missing = sorted(stub_members.difference({*impl_members, *default_impls}))
    return ImplCoverage(impl_path, sorted(stub_members), missing)


if __name__ == "__main__":
    main()
