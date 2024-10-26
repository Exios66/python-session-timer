import os
import sys
sys.path.insert(0, os.path.abspath('..'))

project = 'Python Session Timer'
copyright = '2024'
author = 'Exios66'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

html_theme = 'sphinx_rtd_theme'
