"""Namespace shim for the Reflex pyi generator.

``reflex component build`` imports the component as
``custom_components.reflex_xtermjs.xtermjs`` when it regenerates the ``.pyi``
stubs, which only works if this directory is a package. It is excluded from the
built distribution: ``[tool.setuptools.packages.find] where = ["custom_components"]``
publishes the contents of this folder, not the folder itself.
"""
