# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""ciocheck check/tester tool."""


version_info = (0, 1, 0, 'dev0')
__version__ = '.'.join(map(str, version_info))


CONFIGURATION_FILE = '.ciocheck'
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
