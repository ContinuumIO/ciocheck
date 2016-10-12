# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""CLI Parser for `ciocheck`."""

# Standard library imports
from collections import OrderedDict
import argparse
import os
import shutil

# Local imports
from ciocheck.config import load_config
from ciocheck.files import FileManager
from ciocheck.formaters import FORMATERS, MULTI_FORMATERS, MultiFormater
from ciocheck.linters import LINTERS
from ciocheck.tools import TOOLS


class Runner(object):
    """Main tool runner."""

    def __init__(self, cmd_root, cli_args, folders=None, files=None):
        """Main tool runner."""
        # Run options
        self.cmd_root = cmd_root  # Folder on which the command was executed
        self.config = load_config(cmd_root, cli_args)
        self.file_manager = FileManager(folders=folders, files=files)
        self.all_results = OrderedDict()

        self.check = self.config.get_value('check')
        self.enforce = self.config.get_value('enforce')
        self.diff_mode = self.config.get_value('diff_mode')
        self.file_mode = self.config.get_value('file_mode')
        self.branch = self.config.get_value('branch')

    def run(self):
        """Run tools."""
        self.clean()

        CHECK_LINTERS = [l for l in LINTERS if l.name in self.check]
        CHECK_FORMATERS = [f for f in FORMATERS if f.name in self.check]
        run_multi = any(f for f in MULTI_FORMATERS if f.name in self.check)

        all_tools = []

        # Linters
        for tool in CHECK_LINTERS:
            print('Running "{}"...'.format(tool.name))
            t = tool(self.cmd_root)
            files = self.file_manager.get_files(branch=self.branch,
                                                diff_mode=self.diff_mode,
                                                file_mode=self.file_mode,
                                                extensions=t.extensions)
            all_tools.append(t)
            t.create_config(self.config)
            self.all_results[t.name] = {
                'files': files,
                'results': t.check(files),
                }

        # Formaters
        for tool in CHECK_FORMATERS:
            print('Running "{}"'.format(tool.name))
            t = tool(self.cmd_root)
            files = self.file_manager.get_files(branch=self.branch,
                                                diff_mode=self.diff_mode,
                                                file_mode=self.file_mode,
                                                extensions=t.extensions)
            t.create_config(self.config)
            all_tools.append(t)
            results = t.format(files)
            # Pyformat might include files in results that are not in files
            # like when an init is created
            if results:
                self.all_results[t.name] = {
                    'files': files,
                    'results': results,
                    }

        if run_multi:
            t = MultiFormater(self.cmd_root, self.check)
            files = self.file_manager.get_files(branch=self.branch,
                                                diff_mode=self.diff_mode,
                                                file_mode=self.file_mode,
                                                extensions=t.extensions)
            self.all_results[t.name] = {
                'files': files,
                'results': t.format(files),
                }

        # Tests
        for tool in TOOLS:
            print('Running "{}"'.format(tool.name))
            t = tool(self.cmd_root)
            t.create_config(self.config)
            all_tools.append(t)
            files = self.file_manager.get_files(branch=self.branch,
                                                diff_mode=self.diff_mode,
                                                file_mode=self.file_mode,
                                                extensions=t.extensions)
            results = t.run(files)
            self.all_results.update(results)

        for tool in LINTERS + FORMATERS + TOOLS:
            tool.remove_config(self.cmd_root)
        self.clean()

        print(self.all_results)

    def process_results(self, results):
        """Group all results by file path."""
        pass

    def clean(self):
        """Remove build directories and temporal config files."""
        # Clean up leftover trash as best we can
        BUILD_TMP = os.path.join(self.cmd_root, 'build', 'tmp')
        if os.path.isdir(BUILD_TMP):
            try:
                shutil.rmtree(BUILD_TMP, ignore_errors=True)
            except Exception:
                pass
            else:
                pass


def main():
    """CLI `Parser for ciocheck`."""
    description = 'Run Continuum IO test suite.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('folders_or_files',
                        help='Folder to analize. Use from repo root.',
                        nargs=1)
    parser.add_argument('--file-mode',
                        dest='file_mode',
                        nargs=1,
                        choices=['lines', 'files', 'all'],
                        default=None,
                        help=('Define if the tool should run on modified '
                              'lines of files (default), modified files or '
                              'all files'))
    parser.add_argument('--diff-mode',
                        dest='diff_mode',
                        nargs=1,
                        choices=['commited', 'staged', 'unstaged'],
                        default=None,
                        help='Define diff mode. Default mode is commited.')
    parser.add_argument('--branch',
                        dest='branch',
                        nargs=1,
                        default=None,
                        help=('Define branch to compare to. Default branch is '
                              '"origin/master"'))
    parser.add_argument('--check',
                        dest='check',
                        nargs='+',
                        choices=['pep8', 'pydocstyle', 'flake8', 'pylint',
                                 'pyformat', 'isort', 'yapf', 'pytest'],
                        default=None,
                        help='Select tools to run. Default is "pep8"')
    parser.add_argument('--enforce',
                        dest='enforce',
                        choices=['pep8', 'pydocstyle', 'flake8', 'pylint',
                                 'pyformat', 'isort', 'yapf', 'pytest'],
                        default=None,
                        nargs='+',
                        help=('Select tools to enforce. Enforced tools will '
                              'fail if a result is obtained. Default is '
                              'none.'))
    cli_args = parser.parse_args()
    root = os.getcwd()
    folders = []
    files = []
    for folder_or_file in cli_args.folders_or_files:
        folder_or_file = os.path.abspath(folder_or_file)
        if os.path.isfile(folder_or_file):
            files.append(folder_or_file)
        elif os.path.isdir(folder_or_file):
            folders.append(folder_or_file)

    if folders or files:
        test = Runner(root, cli_args, folders=folders, files=files)
        test.run()
    elif not folders and not files:
        print('Invalid folders or files!')


if __name__ == '__main__':
    main()
