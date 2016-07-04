# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""ciocheck setup script."""

# Standard library imports
import os

# Third party imports
from setuptools import find_packages, setup


HERE = os.path.abspath(os.path.dirname(__file__))
VERSION_NS = {}


with open(os.path.join(HERE, 'ciocheck', '__init__.py')) as f:
    exec(f.read(), {}, VERSION_NS)


VERSION = VERSION_NS.get('__version__')


def get_readme():
    """ """
    with open('README.rst') as f:
        readme = str(f.read())
    return readme


packages = find_packages()
setup(
    name='ciocheck',
    version=VERSION,
    description='Continuum IO check/test suite',
    author='Gonzalo Peña-Castellanos',
    author_email='goanpeca@gmail.com',
    maintainer='Gonzalo Peña-Castellanos',
    maintainer_email='goanpeca@gmail.com',
    description='A stand alone PyQt/PySide GUI application for managing conda '
                'packages and environments.',
    packages=packages,
    dependencies=['coverage',
                  'flake8',
                  'isort',
                  'pytdocstyle',
                  'pytest',
                  'pytest-cov',
                  'pytest-xdist',
                  'yapf',
                  ],
    entry_points={
        'gui_scripts': [
            'ciocheck = ciocheck.main:main'
        ]
    },
    include_package_data=True,
    )
