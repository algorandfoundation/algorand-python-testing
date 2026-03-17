project = "Algorand Python Testing API"
author = "Algorand Foundation"
copyright = "2026, Algorand Foundation"  # noqa: A001

extensions = [
    "myst_parser",
    "autodoc2",
]

autodoc2_packages = [
    {
        "path": "../../src/algopy_testing",
        "auto_mode": True,
    },
    {
        "path": "../../src/_algopy_testing",
        "auto_mode": True,
    },
]
autodoc2_render_plugin = "myst"
autodoc2_hidden_objects = [
    "dunder",
    "private",
    "undoc",
]
add_module_names = False

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

source_suffix = {
    ".md": "markdown",
}
master_doc = "index"

myst_enable_extensions = ["colon_fence", "fieldlist"]
