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
    check_multi_formaters = [f for f in MULTI_FORMATERS if f.name in check]

    results = {}
    for formater in check_multi_formaters:
        paths = filter_files([path], formater.extensions)
        if paths:
            formater.cmd_root = root_path
            result = formater.format_task(paths[0])
            if result:
                results[formater.name] = result

    if results:
        results[path] = path

    return results


for filename in sys.argv[1:]:
    task_results = []
    task_result = format_file(filename)
    task_results.append(task_result)

print(json.dumps(task_results))
sys.exit(0)
