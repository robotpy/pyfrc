#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#
# Imports
#

import sys
import os
from os.path import abspath, dirname

# Project must be built+installed to generate docs
import pyfrc
import pyfrc.config

pyfrc.config.config_obj["pyfrc"] = dict(game_specific_messages=[])

# -- RTD configuration ------------------------------------------------

# on_rtd is whether we are on readthedocs.org, this line of code grabbed from docs.readthedocs.org
on_rtd = os.environ.get("READTHEDOCS", None) == "True"

# This is used for linking and such so we link to the thing we're building
rtd_version = os.environ.get("READTHEDOCS_VERSION", "latest")
if rtd_version not in ["stable", "latest"]:
    rtd_version = "stable"

# -- General configuration ------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.mathjax",
    "sphinx.ext.viewcode",
    "sphinx.ext.intersphinx",
    "sphinx_autodoc_typehints",
]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "pyfrc"
copyright = "2014-2020, RobotPy development team"

autoclass_content = "both"

intersphinx_mapping = {
    "robotpy": ("https://robotpy.readthedocs.io/en/%s/" % rtd_version, None),
    "wpilib": (
        "https://robotpy.readthedocs.io/projects/wpilib/en/%s/" % rtd_version,
        None,
    ),
}

# The version info for the project you're documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#

# The short X.Y version.
from pyfrc.version import version

# The full version, including alpha/beta/rc tags.
release = version

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build"]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = "sphinx"

# -- Options for HTML output ----------------------------------------------

if not on_rtd:  # only import and set the theme if we're building docs locally
    import sphinx_rtd_theme

    html_theme = "sphinx_rtd_theme"
    html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
else:
    html_theme = "default"

# Output file base name for HTML help builder.
htmlhelp_basename = "pyfrcdoc"


# -- Options for LaTeX output ---------------------------------------------

latex_elements = {}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title,
#  author, documentclass [howto, manual, or own class]).
latex_documents = [
    ("index", "pyfrc.tex", "pyfrc Documentation", "Dustin Spicuzza", "manual")
]


# -- Options for manual page output ---------------------------------------

# One entry per manual page. List of tuples
# (source start file, name, description, authors, manual section).
man_pages = [("index", "pyfrc", "pyfrc Documentation", ["Dustin Spicuzza"], 1)]

# -- Options for Texinfo output -------------------------------------------

# Grouping the document tree into Texinfo files. List of tuples
# (source start file, target name, title, author,
#  dir menu entry, description, category)
texinfo_documents = [
    (
        "index",
        "pyfrc",
        "pyfrc Documentation",
        "Dustin Spicuzza",
        "pyfrc",
        "One line description of project.",
        "Miscellaneous",
    )
]

# -- Custom Document processing ----------------------------------------------

from robotpy_sphinx.sidebar import generate_sidebar

generate_sidebar(
    globals(),
    "pyfrc",
    "https://raw.githubusercontent.com/robotpy/docs-sidebar/master/sidebar.toml",
)

import sphinx.addnodes
import docutils.nodes


def process_child(node):
    """This function changes class references to not have the
    intermediate module name by hacking at the doctree"""

    # Edit descriptions to be nicer
    if isinstance(node, sphinx.addnodes.desc_addname):
        if len(node.children) == 1:
            child = node.children[0]
            text = child.astext()
            if text.startswith("wpilib.") and text.endswith("."):
                # remove the last element
                text = ".".join(text.split(".")[:-2]) + "."
                node.children[0] = docutils.nodes.Text(text)

    # Edit literals to be nicer
    elif isinstance(node, docutils.nodes.literal):
        child = node.children[0]
        text = child.astext()

        # Remove the imported module name
        if text.startswith("wpilib."):
            stext = text.split(".")
            text = ".".join(stext[:-2] + [stext[-1]])
            node.children[0] = docutils.nodes.Text(text)

    for child in node.children:
        process_child(child)


def doctree_read(app, doctree):
    for child in doctree.children:
        process_child(child)


def setup(app):
    app.connect("doctree-read", doctree_read)
