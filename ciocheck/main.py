# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""CLI Parser for `ciocheck`."""

# Standard library imports
import argparse
import os


def main():
    """CLI `Parser for ciocheck`."""
    description = 'Run Continuum IO test suite.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('folder_or_file',
                        help='module (folder) or file to analize')
    parser.add_argument('--format-imports',
                        dest='format_imports',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Run isort to format python import statements')
    parser.add_argument('--format-code',
                        dest='format_code',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Run the yapf code formatter')
    parser.add_argument('--staged',
                        dest='git_staged_only',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Run the options on all python files')
    parser.add_argument('--profile',
                        dest='profile_formatting',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Profile the linter and formatter steps')
    parser.add_argument('--add-init',
                        dest='add_init',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Add missing __init__.py files')
    parser.add_argument('--add-headers',
                        dest='add_headers',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Add encoding and copyright headers')
    parser.add_argument('--test',
                        dest='test',
                        action='store_const',
                        const=True,
                        default=False,
                        help='Run pytest')
    args = parser.parse_args()

    root = os.getcwd()
    from ciocheck.test import Test
    test = Test(root,
                folder_or_file=args.folder_or_file,
                format_code=args.format_code,
                format_imports=args.format_imports,
                git_staged_only=args.git_staged_only,
                profile_formatting=args.profile_formatting,
                add_init=args.add_init,
                add_headers=args.add_headers,
                run_test=args.test)
    test.run()


if __name__ == '__main__':
    main()
