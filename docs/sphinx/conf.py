# Isolated Sphinx configuration for API-only markdown generation.
# This config is used by docs/api_build.py to generate API reference
# markdown that is consumed by Starlight. It intentionally omits HTML
# themes and other presentation-layer extensions.

from docutils import nodes

project = "Algorand Python Testing API"
author = "Algorand Foundation"
copyright = "2026, Algorand Foundation"  # noqa: A001

extensions = ["autoapi.extension"]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autoapi_dirs = [
    "../../src/_algopy_testing",
]
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
]

autoapi_ignore = [
    "*_algopy_testing/op/txn.py",
    "*_algopy_testing/op/itxn.py",
    "*_algopy_testing/op/constants.py",
]


def _process_docstring(_app, _what, _name, _obj, _options, lines):
    # TypedDict subclasses without their own docstring inherit dict.__doc__,
    # which contains `dict(**kwargs)` — Sphinx parses `**` as inline emphasis
    # and the markdown builder emits an orphan fenced `**` block. Drop it.
    if lines and lines[0].startswith("dict() -> new empty dictionary"):
        lines[:] = []


def _skip_member(_app, _what, name, _obj, skip, _options):
    # Allow the top-level package itself even though its name starts with `_`;
    # without this, autoapi treats the entire package as private and renders
    # nothing.
    if name == "_algopy_testing":
        return False
    short = name.rsplit(".", 1)[-1]
    if short.startswith("_") and not (short.startswith("__") and short.endswith("__")):
        return True
    return skip


def _strip_pycon_prompts(text: str) -> str:
    """Return text with leading REPL prompts (>>>/...) stripped from each line."""
    cleaned_lines: list[str] = []
    for line in text.splitlines():
        if line.startswith(">>> "):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith(">>>"):
            cleaned_lines.append(line[3:].lstrip())
            continue
        if line.startswith("... "):
            cleaned_lines.append(line[4:])
            continue
        if line.startswith("..."):
            cleaned_lines.append(line[3:].lstrip())
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _convert_pycon_blocks_to_python(app, doctree, _docname):
    """Convert pycon/doctest code blocks to python and strip prompts.

    Starlight's Expressive Code highlighter doesn't recognise the ``pycon``
    lexer that inherited stdlib docstrings (e.g. ``enum.Enum``) emit, so
    rewrite them to plain Python with the REPL prompts stripped.
    """
    if app.builder.name != "markdown":
        return

    for node in list(doctree.traverse(nodes.literal_block)):
        if node.get("language") in {"pycon", "doctest"}:
            text = node.astext()
            node["language"] = "python"
            node.children = [nodes.Text(_strip_pycon_prompts(text))]

    doctest_block = getattr(nodes, "doctest_block", None)
    if doctest_block is not None:
        for node in list(doctree.traverse(doctest_block)):
            text = node.astext()
            code_text = _strip_pycon_prompts(text)
            replacement = nodes.literal_block(code_text, code_text)
            replacement["language"] = "python"
            node.replace_self(replacement)


def setup(app):
    app.connect("autoapi-skip-member", _skip_member)
    app.connect("autodoc-process-docstring", _process_docstring)
    app.connect("doctree-resolved", _convert_pycon_blocks_to_python)
