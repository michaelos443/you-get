#!/usr/bin/env python3
"""Setup script for you-get package.

This module configures the installation of you-get, a command-line utility
for downloading videos and other media from various websites including
YouTube, Youku, Niconico, and many others.
"""

PROJ_NAME = 'you-get'
PACKAGE_NAME = 'you_get'

PROJ_METADATA = '%s.json' % PROJ_NAME

import importlib.util
import importlib.machinery

from types import ModuleType
from typing import Optional, cast

def load_source(modname: str, filename: str) -> ModuleType:
    """
    Load and execute a Python source file as a module.

    Parameters
    ----------
    modname : str
        The name to assign to the loaded module.
    filename : str
        Absolute or relative path to the source file to load.

    Returns
    -------
    ModuleType
        The loaded and executed module object. The module is not cached in
        ``sys.modules`` by default (see Notes).

    Notes
    -----
    - This function mirrors ``importlib``-based loading, creating a new module
      object from a module ``spec`` and executing it with the provided loader.
    - The module is intentionally not inserted into ``sys.modules`` to avoid
      side-effects. If you need caching, assign it manually:

        ``sys.modules[module.__name__] = module``

    Examples
    --------
    >>> m = load_source('my_mod', 'path/to/file.py')
    >>> hasattr(m, '__file__')
    True
    """
    loader = importlib.machinery.SourceFileLoader(modname, filename)
    spec: Optional[importlib.machinery.ModuleSpec] = importlib.util.spec_from_file_location(
        modname, filename, loader=loader
    )
    if spec is None:
        raise ImportError(f"Could not create a module spec for {filename}")

    module = importlib.util.module_from_spec(cast(importlib.machinery.ModuleSpec, spec))
    # The module is always executed and not cached in sys.modules.
    # Uncomment the following line to cache the module.
    # sys.modules[module.__name__] = module
    loader.exec_module(module)
    return module

import os, json
here = os.path.abspath(os.path.dirname(__file__))
proj_info = json.loads(open(os.path.join(here, PROJ_METADATA), encoding='utf-8').read())
try:
    README = open(os.path.join(here, 'README.rst'), encoding='utf-8').read()
except:
    README = ""
CHANGELOG = open(os.path.join(here, 'CHANGELOG.rst'), encoding='utf-8').read()
VERSION = load_source('version', os.path.join(here, 'src/%s/version.py' % PACKAGE_NAME)).__version__

from setuptools import setup, find_packages
setup(
    name = proj_info['name'],
    version = VERSION,

    author = proj_info['author'],
    author_email = proj_info['author_email'],
    url = proj_info['url'],
    license = proj_info['license'],

    description = proj_info['description'],
    keywords = proj_info['keywords'],

    long_description = README,

    packages = find_packages('src'),
    package_dir = {'' : 'src'},

    test_suite = 'tests',

    platforms = 'any',
    zip_safe = True,
    include_package_data = True,

    classifiers = proj_info['classifiers'],

    entry_points = {'console_scripts': proj_info['console_scripts']},

    install_requires = ['dukpy'],
    extras_require = {
        'socks': ['PySocks'],
    }
)
