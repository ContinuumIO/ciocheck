# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""Test pytest runners."""

# Local imports
from ciocheck.linters import Flake8Linter, Pep8Linter


def test_true():
    """Mock test for checking ciocheck is working."""
    linter = Flake8Linter('')
    assert linter.name == 'flake8'


def test_false():
    """Mock test for checking ciocheck is working."""
    linter = Pep8Linter('')
    assert linter.name == 'pycodestyle'
