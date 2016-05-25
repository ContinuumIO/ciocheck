# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------

"""
Tests script.
"""

# Standard library imports
import argparse
import os


def main():
    description = 'Run Continuum IO test suite.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('module', help='')
    parser.add_argument('--format', dest='format_only',
                        action='store_const', const=True, default=False,
                        help='Only run the linters and formatters not the '
                             'actual tests')
    parser.add_argument('--staged', dest='git_staged_only',
                        action='store_const', const=True, default=False,
                        help='Only run the linters and formatters on files '
                             'added to the commit')
    parser.add_argument('--profile', dest='profile_formatting',
                        action='store_const', const=True, default=False,
                        help='Profile the linter and formatter steps')
    parser.add_argument('--pytestqt', dest='pytestqt',
                        action='store_const', const=True, default=False,
                        help='If using pytestqt, qtpy is imported first.')
    args = parser.parse_args()

    root = os.getcwd()
    from ciotest.test import Test
    test = Test(root,
                module=args.module,
                format_only=args.format_only,
                git_staged_only=args.git_staged_only,
                profile_formatting=args.profile_formatting,
                pytestqt=args.pytestqt)
    test.run()


if __name__ == '__main__':
    main()
