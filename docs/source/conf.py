# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# Add the path to the code to the system paths

import sys
from pathlib import Path
sys.path.insert(0, str(Path('..', 'src').resolve()))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pysimtra'
copyright = '2024, Felix Thelen'
author = 'Felix Thelen'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'nbsphinx',
    'sphinx.ext.autodoc',
    'sphinx.ext.autosummary'
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

# Define the theme options like title
html_theme_options = {
    'logo': {
        'text': 'pySIMTRA'
    },
    'github_url': 'https://github.com/felixthln/pysimtra'
}

# If True, show link to rst source on rendered HTML pages
html_show_sourcelink = False  # Remove 'view source code' from top of page
# Disable the execution of the notebooks as they cannot be run by readthedocs
nbsphinx_execute = 'never'
