# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------

"""
"""

# Third party imports
from setuptools import setup, find_packages
from setuptools.command.install import install


VERSION = '0.1dev0'


packages = find_packages()
setup(name='ciotest',
      version=VERSION,
      description='Continuum test suite',
      author='Continuum Analytics',
      packages=packages,
      dependencies=['coverage', 'flake8', 'pep257', 'pytest', 'pytest-cov',
                    'yapf==0.6.2', 'pytest-xdist'],
      entry_points={
          'gui_scripts': [
              'ciotest = ciotest.main:main'
          ]
      },
      include_package_data=True,
      )
