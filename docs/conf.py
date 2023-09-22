import os
import sys

sys.path.append(os.path.dirname(__file__) + "/..")

root_doc = "README"
extensions = ["sphinx_markdown_builder", "sphinx.ext.autodoc"]

autodoc_typehints = "none"
autodoc_preserve_defaults = True
