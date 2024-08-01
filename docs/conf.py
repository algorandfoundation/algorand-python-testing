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

import sys
import os

# Add the docs directory to the Python path
sys.path.insert(0, os.path.abspath("."))
# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.githubpages",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx_copybutton",
    "myst_parser",
    "autodoc2",  # Add this line
]

napoleon_google_docstring = True

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

# Add autodoc2 configuration
autodoc2_packages = [
    {
        "path": "../src/algopy_testing",
        "module": "algopy_testing",
        "auto_mode": False,
    },
]
autodoc2_render_plugin = "myst"
autodoc2_hidden_objects = [
    "private",  # single-underscore methods, e.g. _private
    "undoc",
]
autodoc2_docstring_parser_regexes = [
    (
        ".*",
        "_docstrings_parser",
    ),
]
add_module_names = False
autodoc2_index_template = None
myst_enable_extensions = ["fieldlist"]
