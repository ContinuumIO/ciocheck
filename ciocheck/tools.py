# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""TODO:"""

# Standard librry imports
from collections import OrderedDict
import json
import os

# Local imports
from ciocheck.config import PY2, COVERAGE_CONFIGURATION_FILE
from ciocheck.utils import cpu_count, run_command

if PY2:
    # Python 2
    import ConfigParser as configparser
else:
    # Python 3
    import configparser


class Tool(object):
    """A Generic tool object."""
    name = None
    language = None
    extensions = None
    command = None

    # Config
    config_file = None  # '.validconfigfilename'
    config_sections = None  # (('ciocheck:section', 'section'))

    def __init__(self, cmd_root):
        """"""
        self.cmd_root = cmd_root
        self.config = None

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
    
                    with open(new_config_file, 'w') as f:
                        new_config.write(f)

    @classmethod
    def remove_config(cls, path):
        """Remove config file."""
        # Remove config files
        if cls.config_file and cls.config_sections:
            remove_file = os.path.join(path, cls.config_file)
            if os.path.isfile(remove_file):
                os.remove(remove_file)

    def run(self):
        """Run the tool."""
        raise NotImplementedError


class CoverageTool(Tool):
    """TODO:"""
    name = 'coverage'
    language = 'python'
    extensions = ('py',)

    # Config
    config_file = COVERAGE_CONFIGURATION_FILE
    config_sections = [('coverage:run', 'run'),
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
        return []

    @classmethod
    def remove_config(cls, path):
        pass


class PytestTool(Tool):
    """ """
    name = 'pytest'
    language = 'python'
    extensions = ('py',)

    config_file = 'pytest.ini'
    config_sections = [('pytest', 'pytest')]

    REPORT_FILE = '.pytestreport.json'
    def _setup_pytest_coverage_args(self, paths):
        """Setup pytest-cov arguments and config file path."""

        paths = list(sorted(paths.keys()))
        # FIXME: take into account more paths?
        cov = '--cov={0}'.format(self.cmd_root)
#        cov = '--cov={0}'.format('ciocheck')
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
            enable_xdist = []

        self.pytest_args = ['--json={0}'.format(self.REPORT_FILE)] + enable_xdist
        self.pytest_args = self.pytest_args + coverage_args
        print(self.pytest_args)

    def run(self, paths):
        """Run pytest test suite."""
        # If used with qtpy and pytest-qt
        self._setup_pytest_coverage_args(paths)
        output, error = run_command(['py.test'] + self.pytest_args,
                                    cwd=self.cmd_root)        
        if error:
            print(error)

        if output:
            print(output)
        covered_lines = self.parse_coverage()
        pytest_report = self.parse_pytest_report()

        results = {'coverage': covered_lines,
                   'pytest': pytest_report}
        return results

    def parse_pytest_report(self):
        """ """
        pytest_report_path = os.path.join(self.cmd_root, self.REPORT_FILE)
        if os.path.isfile(pytest_report_path):
            with open(pytest_report_path, 'r') as f:
                data = json.load(f)
        return data

    def parse_coverage(self):
        """ """
        coverage_string = ("!coverage.py: This is a private format, don't "
                           "read it directly!")
        coverage_path = os.path.join(self.cmd_root, '.coverage')

        covered_lines = {}
        if os.path.isfile(coverage_path):
            with open(coverage_path, 'r') as f:
                data = f.read()
                data = data.replace(coverage_string, '')
    
            cov = json.loads(data)
            covered_lines = OrderedDict()
            lines = cov['lines']
            for path in sorted(lines):
                covered_lines[path] = lines[path]

        return covered_lines


TOOLS = [
    CoverageTool,
    PytestTool,
    ]


def test():
    pass


if __name__ == '__main__':
    test()
