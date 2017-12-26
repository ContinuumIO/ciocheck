# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
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
import sys

# Local imports
from ciocheck.config import ALL_FILES, load_config
from ciocheck.files import FileManager
from ciocheck.formatters import FORMATTERS, MULTI_FORMATTERS, MultiFormatter
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
        self.folders = folders
        self.files = files
        self.all_results = OrderedDict()
        self.all_tools = {}
        self.test_results = None
        self.failed_checks = set()

        self.check = self.config.get_value('check')
        self.enforce = self.config.get_value('enforce')
        self.diff_mode = self.config.get_value('diff_mode')
        self.file_mode = self.config.get_value('file_mode')
        self.branch = self.config.get_value('branch')
        self.disable_formatters = cli_args.disable_formatters
        self.disable_linters = cli_args.disable_linters
        self.disable_tests = cli_args.disable_tests

    def run(self):
        """Run tools."""
        msg = 'Running ciocheck'
        print('')
        print('=' * len(msg))
        print(msg)
        print('=' * len(msg))
        print('')
        self.clean()

        check_linters = [l for l in LINTERS if l.name in self.check]
        check_formatters = [f for f in FORMATTERS if f.name in self.check]
        check_testers = [t for t in TOOLS if t.name in self.check]
        run_multi = any(f for f in MULTI_FORMATTERS if f.name in self.check)

        # Format before lint, linters may complain about bad formatting

        # Formatters
        if not self.disable_formatters:
            for formatter in check_formatters:
                print('Running "{}" ...'.format(formatter.name))
                tool = formatter(self.cmd_root)
                files = self.file_manager.get_files(
                    branch=self.branch,
                    diff_mode=self.diff_mode,
                    file_mode=self.file_mode,
                    extensions=tool.extensions)
                tool.create_config(self.config)
                self.all_tools[tool.name] = tool
                results = tool.run(files)
                # Pyformat might include files in results that are not in files
                # like when an init is created
                if results:
                    self.all_results[tool.name] = {
                        'files': files,
                        'results': results,
                    }

            # The result of the the multi formatter is special!
            if run_multi:
                print('Running "Multi formatter"')
                tool = MultiFormatter(self.cmd_root, self.check)
                files = self.file_manager.get_files(
                    branch=self.branch,
                    diff_mode=self.diff_mode,
                    file_mode=self.file_mode,
                    extensions=tool.extensions)
                multi_results = tool.run(files)
                for key, values in multi_results.items():
                    self.all_results[key] = {
                        'files': files,
                        'results': values,
                    }

        # Linters
        if not self.disable_linters:
            for linter in check_linters:
                print('Running "{}" ...'.format(linter.name))
                tool = linter(self.cmd_root)
                files = self.file_manager.get_files(
                    branch=self.branch,
                    diff_mode=self.diff_mode,
                    file_mode=self.file_mode,
                    extensions=tool.extensions)
                self.all_tools[tool.name] = tool
                tool.create_config(self.config)
                self.all_results[tool.name] = {
                    'files': files,
                    'results': tool.run(files),
                }

        # Tests
        if not self.disable_tests:
            for tester in check_testers:
                print('Running "{}" ...'.format(tester.name))
                tool = tester(self.cmd_root)
                tool.create_config(self.config)
                self.all_tools[tool.name] = tool

                if tool.name == 'pytest':
                    tool.setup_pytest_coverage_args(self.folders)

                files = self.file_manager.get_files(
                    branch=self.branch,
                    diff_mode=self.diff_mode,
                    file_mode=ALL_FILES,
                    extensions=tool.extensions)
                results = tool.run(files)
                if results:
                    results['files'] = files
                    self.test_results = results

        for tool in LINTERS + FORMATTERS + TOOLS:
            tool.remove_config(self.cmd_root)
        self.clean()

        self.process_results(self.all_results)
        if self.enforce_checks():
            msg = 'Ciocheck successful run'
            print('\n\n' + '=' * len(msg))
            print(msg)
            print('=' * len(msg))
            print('')

    def process_results(self, all_results):
        """Group all results by file path."""
        all_changed_paths = []
        for tool_name, data in all_results.items():
            if data:
                files, results = data['files'], data['results']
                all_changed_paths += [result['path'] for result in results]

        all_changed_paths = list(sorted(set(all_changed_paths)))

        if self.test_results:
            test_files = self.test_results.get('files')
            test_coverage = self.test_results.get('coverage')
        else:
            test_files = []
            test_coverage = []

        for path in all_changed_paths:
            short_path = path.replace(self.cmd_root, '...')
            print('')
            print(short_path)
            print('-' * len(short_path))
            for tool_name, data in all_results.items():
                if data:
                    files, results = data['files'], data['results']
                    lines = [[-1], range(100000)]

                    if isinstance(files, dict):
                        added_lines = files.get(path, lines)[-1]
                    else:
                        added_lines = lines[-1]

                    messages = []
                    for result in results:
                        res_path = result['path']
                        if path == res_path:
                            # LINTERS
                            line = int(result.get('line', -1))
                            created = result.get('created')
                            added_copy = result.get('added-copy')
                            added_header = result.get('added-header')
                            diff = result.get('diff')
                            if line and line in list(added_lines):
                                spaces = (8 - len(str(line))) * ' '
                                args = result.copy()
                                args['spaces'] = spaces
                                msg = ('    {line}:{spaces}'
                                       '{type}: {message}').format(**args)
                                messages.append(msg)

                            # Formatters
                            if created:
                                msg = '    __init__ file created.'
                                messages.append(msg)
                            if added_copy:
                                msg = '    added copyright.'
                                messages.append(msg)
                            if added_header:
                                msg = '    added header.'
                                messages.append(msg)
                            if diff:
                                msg = self.format_diff(diff)
                                messages.append(msg)

                            # TESTERS / COVERAGE

                    test = [r['path'] for r in results if path == r['path']]
                    if test and messages:
                        print('\n  ' + tool_name)
                        print('  ' + '-' * len(tool_name))
                        self.failed_checks.add(tool_name)
                        for message in messages:
                            print(message)

            if isinstance(test_files, dict) and test_files:
                # Asked for lines changed
                if test_coverage:
                    lines_changed_not_covered = []
                    lines = test_files.get(path)
                    lines_added = lines[-1] if lines else []
                    lines_covered = test_coverage.get(path)
                    for line in lines_added:
                        if line not in lines_covered:
                            lines_changed_not_covered.append(str(line))

                    if lines_changed_not_covered:
                        uncov_perc = ((1.0 * len(lines_changed_not_covered)) /
                                      (1.0 * len(lines_added)))
                        cov_perc = (1 - uncov_perc) * 100
                        tool_name = 'coverage'
                        print('\n  ' + tool_name)
                        print('  ' + '-' * len(tool_name))
                        print('    The following lines changed and are not '
                              'covered by tests ({0}%):'.format(cov_perc))
                        print('    ' + ', '.join(lines_changed_not_covered))

        print('')
        pytest_tool = self.all_tools.get('pytest')
        if pytest_tool:
            if pytest_tool.coverage_fail:
                self.failed_checks.add('coverage')

    def enforce_checks(self):
        """Check that enforced checks did not generate reports."""
        if self.test_results:
            if 'pytest' in self.test_results:
                test_summary = self.test_results['pytest']['report']['summary']
                if test_summary.get('failed'):
                    self.failed_checks.add('pytest')
            else:
                self.failed_checks.add('pytest')

        for enforce_tool in self.enforce:
            if enforce_tool in self.failed_checks:
                msg = "Ciocheck failures in: {0}".format(
                    repr(self.failed_checks))
                print('\n\n' + '=' * len(msg))
                print(msg)
                print('=' * len(msg))
                print('')
                sys.exit(1)
                break

        return True

    def format_diff(self, diff, indent='    '):
        """Format diff to include an indentation for console printing."""
        lines = diff.split('\n')
        new_lines = []
        for line in lines:
            new_lines.append(indent + line)
        return '\n'.join(new_lines)

    def clean(self):
        """Remove build directories and temporal config files."""
        # Clean up leftover trash as best we can
        build_tmp = os.path.join(self.cmd_root, 'build', 'tmp')
        if os.path.isdir(build_tmp):
            try:
                shutil.rmtree(build_tmp, ignore_errors=True)
            except Exception:
                pass


def main():
    """CLI `Parser for ciocheck`."""
    description = 'Run Continuum IO test suite.'
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        'folders', help='Folders to analyze. Use from repo root.', nargs='+')
    parser.add_argument(
        '--disable-formatters',
        '-df',
        action='store_true',
        default=False,
        help=('Skip all configured formatters'))
    parser.add_argument(
        '--disable-linters',
        '-dl',
        action='store_true',
        default=False,
        help=('Skip all configured linters'))
    parser.add_argument(
        '--disable-tests',
        '-dt',
        action='store_true',
        default=False,
        help=('Skip running tests'))
    parser.add_argument(
        '--file-mode',
        '-fm',
        dest='file_mode',
        choices=['lines', 'files', 'all'],
        default=None,
        help=('Define if the tool should run on modified '
              'lines of files (default), modified files or '
              'all files'))
    parser.add_argument(
        '--diff-mode',
        '-dm',
        dest='diff_mode',
        choices=['commited', 'staged', 'unstaged'],
        default=None,
        help='Define diff mode. Default mode is committed.')
    parser.add_argument(
        '--branch',
        '-b',
        dest='branch',
        default=None,
        help=('Define branch to compare to. Default branch is '
              '"origin/master"'))
    parser.add_argument(
        '--check',
        '-c',
        dest='check',
        nargs='+',
        choices=[
            'pep8', 'pydocstyle', 'flake8', 'pylint', 'pyformat', 'isort',
            'yapf', 'autopep8', 'coverage', 'pytest'
        ],
        default=None,
        help='Select tools to run. Default is "pep8"')
    parser.add_argument(
        '--enforce',
        '-e',
        dest='enforce',
        choices=[
            'pep8', 'pydocstyle', 'flake8', 'pylint', 'pyformat', 'isort',
            'yapf', 'autopep8', 'coverage', 'pytest'
        ],
        default=None,
        nargs='+',
        help=('Select tools to enforce. Enforced tools will '
              'fail if a result is obtained. Default is '
              'none.'))
    parser.add_argument(
        '--config',
        '-cf',
        dest='config_file',
        default=None,
        help=('Select a config file to use. Default is none.'))

    cli_args = parser.parse_args()
    root = os.getcwd()
    folders = []
    files = []
    for folder_or_file in cli_args.folders:
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
