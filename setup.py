# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""
"""

# Local imports
from setuptools import find_packages, setup

VERSION = '0.1dev0'

packages = find_packages()
setup(name='ciocheck',
      version=VERSION,
      description='Continuum IO check/test suite',
      author='Continuum Analytics',
      packages=packages,
      dependencies=['coverage', 'flake8', 'pep257', 'pytest', 'pytest-cov',
                    'yapf', 'pytest-xdist', 'isort'],
      entry_points={
          'gui_scripts': [
              'ciocheck = ciocheck.main:main'
          ]
      },
      include_package_data=True, )
