# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# Add the path to the code to the system paths

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parents[2] / 'src' / 'pysimtra'))

#import os
#sys.path.insert(0, os.path.abspath('../..'))
#print(sys.path)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'pysimtra'
copyright = '2024, Felix Thelen'
author = 'Felix Thelen'
release = '1.0.0'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
]

templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'pydata_sphinx_theme'
html_static_path = ['_static']

# Define the theme options like title
html_theme_options = {
    "logo": {
        "text": "pySIMTRA"
    }
}

# If True, show link to rst source on rendered HTML pages
html_show_sourcelink = False  # Remove 'view source code' from top of page
# Hide the label "Built with the PyData Sphinx Theme" on the bottom right of the page
html_show_sphinx = False
