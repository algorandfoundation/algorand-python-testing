# ruff: noqa
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Algorand Python Testing"
copyright = "2024, Algorand Foundation"  # noqa: A001
author = "Algorand Foundation"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "myst_parser",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# warning exclusions
suppress_warnings = [
    "myst.xref_missing",
    "autodoc2.dup_item",
]
nitpick_ignore = [
    ("py:class", "algopy.arc4.AllowedOnCompletes"),
]
nitpick_ignore_regex = [
    ("py:class", r"algopy.*\._.*"),
]

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
html_css_files = [
    "custom.css",
]

python_maximum_signature_line_length = 80

# -- Options for myst ---
myst_enable_extensions = [
    "colon_fence",
    "fieldlist",
]
