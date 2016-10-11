# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Configuration module and parameters."""

# Standard library imports
import os
import sys

PY2 = sys.version_info[0] == 2

if PY2:
    # Python 2
    import ConfigParser as configparser
else:
    # Python 3
    import configparser

# Version control modes
STAGED_MODE = 'staged'
UNSTAGED_MODE = 'unstaged'
COMMITED_MODE = 'commited'

# File modes
MODIFIED_LINES = 'lines'
MODIFIED_FILES = 'files'
ALL_FILES = 'all'

# Python formatters
YAPF_CODE = 10
ISORT_CODE = 11
YAPF_ISORT_CODE = 12

# Configuration constants
DEFAULT_BRANCH = 'origin/master'
DEFAULT_IGNORE_EXTENSIONS = ('orig', 'pyc')
DEFAULT_IGNORE_FOLDERS = ('build', '__pychache__')
MAIN_CONFIG_SECTION = 'ciocheck'
CONFIGURATION_FILE = '.ciocheck'
COVERAGE_CONFIGURATION_FILE = '.coveragerc'

ENCODING_HEADER_FILE = '.cioencoding'
COPYRIGHT_HEADER_FILE = '.ciocopyright'

DEFAULT_ENCODING_HEADER = u"# -*- coding: utf-8 -*-\n"
DEFAULT_COPYRIGHT_HEADER = u"""
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
""".lstrip()

DEFAULT_CIOCHECK_CONFIG = {
    # Global options
    'branch': DEFAULT_BRANCH,
    'diff_mode': STAGED_MODE,
    'file_mode': MODIFIED_LINES,
    # Python specific
    'add_copyright': True,
    'add_header': True,
    'add_init': True,
    # Linters
    'check': ['pep8'],
    'enforce': [],
    }


class CustomConfigParser(configparser.ConfigParser):
    """
    Custom config parser that turns options into python objects.

    Support for bool, and lists only.
    """
    SECTION = MAIN_CONFIG_SECTION

    def get_value(self, option, section=MAIN_CONFIG_SECTION):
        """ #TODO:"""
        default_value = DEFAULT_CIOCHECK_CONFIG.get(option)
        val = self.get(self.SECTION, option)
        if isinstance(default_value, bool):
            value = True if val.lower() == 'true' else False
        elif isinstance(default_value, list):
            if val:
                value = val.split(',')
            else:
                value = ''
            value = [v.strip() for v in value]
        else:
            value = val
        return value

    def set_value(self, option, value, section=MAIN_CONFIG_SECTION):
        """ #TODO:"""
        default_value = DEFAULT_CIOCHECK_CONFIG.get(option)
        if not self.has_section(self.SECTION):
            self.add_section(self.SECTION)

        if isinstance(default_value, bool):
            val = 'true' if value else 'false'
            self.set(self.SECTION, option, val)
        elif isinstance(default_value, list):
            if default_value:
                val = ','.join(value)
            else:
                val = ''
            self.set(self.SECTION, option, val)
        else:
            self.set(self.SECTION, option, value)


def load_config(folder, cli_args):
    """Load the configuration located at `folder` and return the parser."""
    config_file = os.path.join(folder, CONFIGURATION_FILE)
    if os.path.isfile(config_file):
        config = CustomConfigParser()
        with open(config_file, 'r') as f:
            config.readfp(f)

    for key, value in DEFAULT_CIOCHECK_CONFIG.items():
        if hasattr(cli_args, key):
            cli_value = getattr(cli_args, key)
            if cli_value:
                value = cli_value

        if not config.has_option('ciocheck', key):
            config.set_value(key, value)

    return config
