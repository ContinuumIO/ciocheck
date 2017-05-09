# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Configuration module and parameters."""

# Standard library imports
import os

# Third party imports
from six.moves import configparser

# Version control modes
STAGED_MODE = 'staged'
UNSTAGED_MODE = 'unstaged'
COMMITED_MODE = 'commited'

# File modes
MODIFIED_LINES = 'lines'
MODIFIED_FILES = 'files'
ALL_FILES = 'all'

# Configuration constants
DEFAULT_BRANCH = 'origin/master'
DEFAULT_IGNORE_EXTENSIONS = ('orig', 'pyc')
DEFAULT_IGNORE_FOLDERS = ('build', '__pychache__')
MAIN_CONFIG_SECTION = 'ciocheck'
CONFIGURATION_FILE = '.ciocheck'
COVERAGE_CONFIGURATION_FILE = '.coveragerc'

COPYRIGHT_HEADER_FILE = '.ciocopyright'

DEFAULT_ENCODING_HEADER = u"# -*- coding: utf-8 -*-\n"
DEFAULT_COPYRIGHT_HEADER = u"""
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
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
    # Python specific/ pyformat
    'header': DEFAULT_ENCODING_HEADER,
    'copyright_file': COPYRIGHT_HEADER_FILE,
    'add_copyright': True,
    'add_header': True,
    'add_init': True,
    # Linters/Formatters/Testers
    'check': ['pycodestyle'],
    'enforce': [],
}


class CustomConfigParser(configparser.ConfigParser):
    """
    Custom config parser that turns options into python objects.

    Support for bool, and lists only.
    """

    SECTION = MAIN_CONFIG_SECTION

    def get_value(self, option, section=MAIN_CONFIG_SECTION):
        """Get config value from the defailt main section."""
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
        """Set config value on the defailt main section."""
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


def load_file_config(folder, file_name=None):
    """
    Load configuration at `folder` or `file_name` and return the parser.

    file_name is assumed to be located on folder.
    """
    if file_name is None:
        config_path = os.path.join(folder, CONFIGURATION_FILE)
    else:
        config_path = os.path.join(folder, file_name)

    config = CustomConfigParser()
    if os.path.isfile(config_path):
        with open(config_path, 'r') as file_obj:
            config.readfp(file_obj)

        if config.has_option(MAIN_CONFIG_SECTION, 'inherit_config'):
            base_config_file = config[MAIN_CONFIG_SECTION]['inherit_config']
            base_config_path = os.path.join(folder, base_config_file)

            # If a config file refers to itself, avoid entering and endless
            # recursion
            if config_path != base_config_path:
                base_config = load_file_config(
                    folder=folder, file_name=base_config_file)

                # Merge the config files
                for section in config:
                    for opt in config[section]:
                        base_config[section][opt] = config[section][opt]

                config = base_config

    return config


def load_config(folder, cli_args):
    """Load the configuration, load defaults and return the parser."""
    config = load_file_config(folder, file_name=cli_args.config_file)

    for key, value in DEFAULT_CIOCHECK_CONFIG.items():
        if not config.has_option(MAIN_CONFIG_SECTION, key):
            config.set_value(key, value)

        if hasattr(cli_args, key):
            cli_value = getattr(cli_args, key)
            if cli_value:
                config.set_value(key, cli_value)

    return config
