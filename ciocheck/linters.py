# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Generic and custom code linters."""

# Standard library imports
import json
import os
import re

# Local imports
from ciocheck.tools import Tool
from ciocheck.utils import run_command


class Linter(Tool):
    """Generic linter with json and regex output support."""

    # Regex matching
    pattern = None

    # Json matching
    json_keys = []  # ((old_key, new_key), ...)
    output_on_stderr = False

    def __init__(self, cmd_root):
        """Generic linter with json and regex output support."""
        super(Linter, self).__init__(cmd_root)
        self.paths = None
        self.regex = None

    def _parse_regex(self, string):
        """Parse output with grouped regex."""
        results = []
        self.regex = re.compile(self.pattern, re.VERBOSE)
        for matches in self.regex.finditer(string):
            results.append(matches.groupdict())
        return results

    def _parse_json(self, string):
        """Parse output with json keys."""
        data = json.loads(string)
        results = []
        for item in data:
            new_item = {}
            for (old_key, new_key) in self.json_keys:
                new_item[new_key] = item.pop(old_key)
            new_item.update(item)
            results.append(new_item)
        return results

    def _parse(self, string):
        """Parse linter output."""
        if self.json_keys:
            results = self._parse_json(string)
        elif self.pattern:
            results = self._parse_regex(string)
        else:
            raise Exception('Either a pattern or a json key mapping has to '
                            'be defined.')
        return results

    def extra_processing(self, results):
        """Override in case extra processing on results is needed."""
        return results

    def run(self, paths):
        """Run linter and return a list of dicts."""
        self.paths = list(paths.keys()) if isinstance(paths, dict) else paths
        if self.paths:
            args = list(self.command)
            args += self.paths
            out, err = run_command(args)
            if self.output_on_stderr:
                string = err
            else:
                string = out
            results = self._parse(string)
            results = self.extra_processing(results)
        else:
            results = []

        return results


class Flake8Linter(Linter):
    """Flake8 python tool runner."""

    language = 'python'
    name = 'flake8'
    extensions = ('py', )
    command = ('flake8', )
    config_file = '.flake8'
    config_sections = [('flake8', 'flake8')]

    # Match lines of the form:
    # path/to/file.py:328: undefined name '_thing'
    pattern = r'''
        (?P<path>.*?):(?P<line>\d{1,1000}):
        (?P<column>\d{1,1000}):\s
        (?P<type>[EWFCNTIBDSQ]\d{3})\s
        (?P<message>.*)
        '''


class Pep8Linter(Linter):
    """Pep8 python tool runner."""

    language = 'python'
    name = 'pycodestyle'
    extensions = ('py', )
    command = ('pycodestyle', )
    config_file = '.pycodestyle'
    config_sections = [('pycodestyle', 'pycodestyle')]

    # Match lines of the form:
    pattern = r'''
        (?P<path>.*?):(?P<line>\d{1,1000}):
        (?P<column>\d{1,1000}):\s
        (?P<type>[EWFCNTIBDSQ]\d{3})\s
        (?P<message>.*)
        '''


class PydocstyleLinter(Linter):
    """Pydocstyle python tool runner."""

    language = 'python'
    name = 'pydocstyle'
    extensions = ('py', )
    command = ('pydocstyle', )
    config_file = '.pydocstyle'
    config_sections = [('pydocstyle', 'pydocstyle')]
    output_on_stderr = True

    # Match lines of the form:
    # ./bootstrap.py:1 at module level:
    #    D400: First line should end with a period (not 't')
    pattern = r'''
        (?P<path>.*?):
        (?P<line>\d{1,1000000})\  # 1 million lines of code :-p ?
        (?P<symbol>.*):\n.*?
        (?P<type>D\d{3}):\s
        (?P<message>.*)
        '''


class PylintLinter(Linter):
    """Pylint python tool runner."""

    language = 'python'
    name = 'pylint'
    extensions = ('py', )
    command = ('pylint', '--output-format', 'json', '-j', '0')
    config_file = '.pydocstyle'
    config_sections = [('pydocstyle', 'pydocstyle')]
    json_keys = (
        ('message', 'message'),
        ('line', 'line'),
        ('column', 'column'),
        ('type', 'type'),
        ('path', 'path'), )

    def extra_processing(self, results):
        """Make path an absolute path."""
        for item in results:
            item['path'] = os.path.join(self.cmd_root, item['path'])
        return results


LINTERS = [
    Pep8Linter,
    PydocstyleLinter,
    Flake8Linter,
    PylintLinter,
]


def test():
    """Main local test."""
    here = os.path.dirname(os.path.realpath(__file__))
    paths = [here]
    linter = PylintLinter(here)
    results = linter.run(paths)
    for result in results:
        print(result)


if __name__ == '__main__':
    test()
