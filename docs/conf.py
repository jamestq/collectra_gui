# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "collectra_gui"
copyright = "2026, James Uy Thinh Quang"
author = "James Uy Thinh Quang"
release = "0.1.0"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys

# Add parent directory to path so Sphinx can find the collectra_gui package
sys.path.insert(0, os.path.abspath(".."))

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

# Napoleon settings for Google/NumPy style docstrings
napoleon_google_docstring = True
napoleon_numpy_docstring = True

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Configure autodoc
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
}


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]

# Theme options
html_theme_options = {
    "description": "GUI for collectra annotation display and editing",
    "github_user": "jamestq",
    "github_repo": "collectra_gui",
    "fixed_sidebar": True,
    "page_width": "1200px",
    "sidebar_width": "250px",
}

# Sidebar configuration
html_sidebars = {
    "**": [
        "about.html",
        "navigation.html",
        "relations.html",
        "searchbox.html",
    ]
}
