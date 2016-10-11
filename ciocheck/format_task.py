# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Setup auxiliary process so we can run formaters in parallel."""
from __future__ import absolute_import, print_function

# Standard library imports
import ast
import json
import os
import sys

# Local imports
from ciocheck.formaters import MULTI_FORMATERS
from ciocheck.utils import filter_files


def format_file(path):
    """Format a file (path) using the available formaters."""
    root_path = os.environ.get('CIOCHECK_PROJECT_ROOT')
    check = ast.literal_eval(os.environ.get('CIOCHECK_CHECK'))
    results = {}
    CHECK_MULTI_FORMATERS = [f for f in MULTI_FORMATERS if f.name in check]
    for formater in CHECK_MULTI_FORMATERS:
        paths = filter_files([path], formater.extensions)
        if paths:
            formater.cmd_root = root_path
            result = formater.format_task(paths[0])
            results[formater.name] = result

    if results:
        results[path] = path

    return results


for filename in sys.argv[1:]:
    results = []
    result = format_file(filename)
    results.append(result)

print(json.dumps(results))
sys.exit(0)
