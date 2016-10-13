# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""Test pytest runners."""

# Local imports
from ciocheck.linters import Flake8Linter


def test_true():
    l = Flake8Linter('')
    l
    assert 1 == 1


def test_false():
    l = Flake8Linter('')
    l
    assert 1 == 1
