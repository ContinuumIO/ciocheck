# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""ciocheck setup script."""

# Standard library imports
import ast
import os

# Third party imports
from setuptools import find_packages, setup

HERE = os.path.abspath(os.path.dirname(__file__))


def get_version():
    """Get ciocheck version."""
    with open(os.path.join(HERE, 'ciocheck', '__init__.py')) as file_obj:
        lines = file_obj.read().split('\n')
    version_info = [l for l in lines if l.startswith('VERSION_INFO')][0]
    version_info = ast.literal_eval(version_info.split('=')[-1].strip())
    return '.'.join(map(str, version_info))


def get_readme():
    """Get ciocheck README."""
    with open('README.md') as file_obj:
        readme = str(file_obj.read())
    return readme


packages = find_packages()
setup(
    name='ciocheck',
    version=get_version(),
    description='Continuum IO check/test suite',
    long_description=get_readme(),
    author='Gonzalo Peña-Castellanos',
    author_email='goanpeca@gmail.com',
    maintainer='Gonzalo Peña-Castellanos',
    maintainer_email='goanpeca@gmail.com',
    packages=packages,
    dependencies=[
        'autopep8',
        'coverage',
        'flake8',
        'isort',
        'pydocstyle',
        'pylint',
        'pytest',
        'pytest-cov',
        'pytest-json',
        'pytest-xdist',
        'six',
        'yapf',
    ],
    entry_points={
        'gui_scripts': [
            'ciocheck = ciocheck.main:main'
        ]
    },
    include_package_data=True, )
