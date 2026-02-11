# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
sys.path.insert(0,os.path.abspath('../../system'))

# -- Project information -----------------------------------------------------

project = 'APMT Profiler - USEA-Payload'
copyright = '2026, nke Instrumentation'
author = 'Christophe SCHAEFFER'
version = '1.0'
release = '1.0.1'

# -- General configuration ---------------------------------------------------

extensions = [
 'sphinx.ext.autodoc',
 'recommonmark'
]
source_suffix = {
 '.rst':'restructuredtext',
 '.md':'markdown',
}
templates_path = ['_templates']
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

html_theme = 'nature'
html_theme_options = {
 'nosidebar':'false',
 'sidebarwidth':'400',
}
html_title = 'USEA-Payload documentation'
html_favicon = '../image/Picto32x32.ico'
html_sidebars = {
 '**': ['localtoc.html','searchbox.html'],
}
html_show_sphinx = False
html_static_path = ['_static']
