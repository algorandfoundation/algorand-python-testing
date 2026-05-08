# Isolated Sphinx configuration for API-only markdown generation.
# This config is used by docs/api_build.py to generate API reference
# markdown that is consumed by Starlight. It intentionally omits HTML
# themes and other presentation-layer extensions.

project = "Algorand Python Testing API"
author = "Algorand Foundation"
copyright = "2026, Algorand Foundation"  # noqa: A001

extensions = ["autoapi.extension"]

templates_path = []
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

autoapi_dirs = [
    "../../src/algopy_testing",
    "../../src/_algopy_testing",
]
autoapi_options = [
    "members",
    "undoc-members",
    "private-members",
    "show-inheritance",
    "show-module-summary",
]
