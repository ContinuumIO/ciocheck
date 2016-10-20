# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Generic tools and custom test runner."""

# Standard library imports
from collections import OrderedDict
import ast
import json
import os

# Third party imports
from six import PY2
from six.moves import configparser

# Local imports
from ciocheck.config import COVERAGE_CONFIGURATION_FILE
from ciocheck.utils import cpu_count, run_command


class Tool(object):
    """Generic tool object."""

    name = None
    language = None
    extensions = None

    command = None

    # Config
    config_file = None  # '.validconfigfilename'
    config_sections = None  # (('ciocheck:section', 'section'))

    def __init__(self, cmd_root):
        """A Generic tool object."""
        self.cmd_root = cmd_root
        self.config = None
        self.config_options = None  # dict version of the config

    def create_config(self, config):
        """Create a config file for for a given config fname and sections."""
        self.config = config

        if self.config_file and self.config_sections:
            new_config = configparser.ConfigParser()
            new_config_file = os.path.join(self.cmd_root, self.config_file)

            for (cio_config_section, config_section) in self.config_sections:
                if config.has_section(cio_config_section):
                    items = config.items(cio_config_section)
                    new_config.add_section(config_section)

                    for option, value in items:
                        new_config.set(config_section, option, value)

            with open(new_config_file, 'w') as file_obj:
                new_config.write(file_obj)

    @classmethod
    def make_config_dictionary(cls):
        """Turn config into a dictionary for later usage."""
        config_path = os.path.join(cls.cmd_root, cls.config_file)
        config_options = {}

        if os.path.exists(config_path):
            config = configparser.ConfigParser()

            with open(config_path, 'r') as file_obj:
                config.readfp(file_obj)

            for section in config.sections():
                for key in config[section]:
                    value = config[section][key]
                    if ',' in value:
                        value = [v for v in value.split(',') if v]
                    elif value.lower() == 'false':
                        value = False
                    elif value.lower() == 'true':
                        value = True
                    else:
                        try:
                            value = ast.literal_eval(value)  # Numbers
                        except Exception as err:
                            pass

                    config_options[key.replace('-', '_')] = value

        return config_options

    @classmethod
    def remove_config(cls, path):
        """Remove config file."""
        if cls.config_file and cls.config_sections:
            remove_file = os.path.join(path, cls.config_file)
            if os.path.isfile(remove_file):
                os.remove(remove_file)

    def run(self, paths):
        """Run the tool."""
        raise NotImplementedError


class CoverageTool(Tool):
    """Coverage tool runner."""

    name = 'coverage'
    language = 'python'
    extensions = ('py', )

    # Config
    config_file = COVERAGE_CONFIGURATION_FILE
    config_sections = [
        ('coverage:run', 'run'),
        ('coverage:report', 'report'),
        ('coverage:html', 'html'),
        ('coverage:xml', 'xml'),
    ]

    def _monkey_path_coverage(self):
        """Enforce the value of `skip_covered`, ignored by pytest-cov.

        pytest-cov ignores the option even if included in the .coveragerc
        configuration file.
        """
#        try:
#            original_init = coverage.summary.SummaryReporter.__init__
#
#            def modified_init(self, coverage, config):
#                config.skip_covered = True
#                original_init(self, coverage, config)
#
#            coverage.summary.SummaryReporter.__init__ = modified_init
#
#            print("\nCoverage monkeypatched to skip_covered")
#        except Exception as e:
#            print("\nFailed to monkeypatch coverage: {0}".format(str(e)),
#                  file=sys.stderr)

    def run(self, paths):
        """Run the tool."""
        return []

    @classmethod
    def remove_config(cls, path):
        """Remove config file."""
        pass


class PytestTool(Tool):
    """Pytest tool runner."""

    name = 'pytest'
    language = 'python'
    extensions = ('py', )

    config_file = 'pytest.ini'
    config_sections = [('pytest', 'pytest')]

    REPORT_FILE = '.pytestreport.json'

    def __init__(self, cmd_root):
        """Pytest tool runner."""
        super(PytestTool, self).__init__(cmd_root)
        self.pytest_args = None
        self.output = None

    def _setup_pytest_coverage_args(self, paths):
        """Setup pytest-cov arguments and config file path."""
        if isinstance(paths, (dict, OrderedDict)):
            paths = list(sorted(paths.keys()))

        # module = os.path.normpath(os.path.basename(self.cmd_root))
        cov = '--cov={0}'.format(self.cmd_root)
        coverage_args = [cov]

        coverage_config_file = os.path.join(self.cmd_root,
                                            COVERAGE_CONFIGURATION_FILE)
        if os.path.isfile(coverage_config_file):
            cov_config = ['--cov-config', coverage_config_file]
            coverage_args = cov_config + coverage_args

        if PY2:
            # xdist appears to lock up the test suite with python2, maybe due
            # to an interaction with coverage
            enable_xdist = []
        else:
            enable_xdist = ['-n', str(cpu_count())]

        self.pytest_args = ['--json={0}'.format(self.REPORT_FILE)]
        self.pytest_args = self.pytest_args + enable_xdist
        self.pytest_args = self.pytest_args + coverage_args
        # print(self.pytest_args)

    def run(self, paths):
        """Run pytest test suite."""
        self._setup_pytest_coverage_args(paths)
        output, error = run_command(
            ['py.test'] + self.pytest_args, cwd=self.cmd_root)

        if error:
            print()
            print(error)

        if output:
            self.output = output

        covered_lines = self.parse_coverage()
        pytest_report = self.parse_pytest_report()

        results = {'coverage': covered_lines}
        if pytest_report is not None:
            results['pytest'] = pytest_report
        return results

    def parse_pytest_report(self):
        """Parse pytest json resport generated by pytest-json."""
        data = None
        pytest_report_path = os.path.join(self.cmd_root, self.REPORT_FILE)
        if os.path.isfile(pytest_report_path):
            with open(pytest_report_path, 'r') as file_obj:
                data = json.load(file_obj)
        return data

    def parse_coverage(self):
        """Parse .coverage json report generated by coverage."""
        coverage_string = ("!coverage.py: This is a private format, don't "
                           "read it directly!")
        coverage_path = os.path.join(self.cmd_root, '.coverage')

        covered_lines = {}
        if os.path.isfile(coverage_path):
            with open(coverage_path, 'r') as file_obj:
                data = file_obj.read()
                data = data.replace(coverage_string, '')

            cov = json.loads(data)
            covered_lines = OrderedDict()
            lines = cov['lines']
            for path in sorted(lines):
                covered_lines[path] = lines[path]
        return covered_lines

    @classmethod
    def remove_config(cls, path):
        """Remove config file."""
        super(PytestTool, cls).remove_config(path)
        remove_file = os.path.join(path, cls.REPORT_FILE)
        if os.path.isfile(remove_file):
            os.remove(remove_file)


TOOLS = [
    CoverageTool,
    PytestTool,
]


def test():
    """Main local test."""
    pass


if __name__ == '__main__':
    test()
