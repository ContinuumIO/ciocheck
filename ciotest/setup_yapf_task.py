# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------

"""
Setup script auxiliary process so we can "yapf" in parallel.
"""

# Standard library imports
from __future__ import absolute_import, print_function
import codecs
import os
import platform
import sys

# Third party imports
from yapf.yapflib.yapf_api import FormatFile

# Local imports
from ciotest import CONFIGURATION_FILE
from ciotest.setup_atomic_replace import atomic_replace


def _format_file(path):
    """
    """
    root_path = os.environ.get('CIOTEST_PROJECT_ROOT', None)
    style_config = None

    if root_path:
        style_config_path = os.path.join(root_path, CONFIGURATION_FILE)
        if os.path.isfile(style_config_path):
            style_config = style_config_path

    try:
        # It might be tempting to use the "inplace" option to FormatFile, but
        # it doesn't do an atomic replace, which is dangerous, so don't use
        # it unless you submit a fix to yapf.
        (contents, encoding, changed) = FormatFile(path,
                                                   style_config=style_config)
        if platform.system() == 'Windows':
            # yapf screws up line endings on windows
            with codecs.open(path, 'r', encoding) as f:
                old_contents = f.read()

            contents = contents.replace("\r\n", "\n")
            if len(old_contents) == 0:
                # Windows yapf seems to force a newline? I dunno
                contents = ""
            changed = (old_contents != contents)
    except Exception as e:
        error = "yapf crashed on {path}: {error}".format(path=path, error=e)
        print(error, file=sys.stderr)
        return False

    if changed:
        atomic_replace(path, contents, encoding)
        print("Reformatted:     {path}".format(path=path))
        return False
    else:
        return True


exit_code = 0
for filename in sys.argv[1:]:
    if not _format_file(filename):
        exit_code = 1

sys.exit(exit_code)
