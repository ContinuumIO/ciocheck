# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""
"""
# Standard library imports
import os

# Local imports
from ciocheck.config import (STAGED_MODE, UNSTAGED_MODE, COMMITED_MODE,
                             MODIFIED_LINES, MODIFIED_FILES, ALL_FILES,
                             DEFAULT_BRANCH)
from ciocheck.utils import filter_files, get_files
from ciocheck.vcs import DiffTool


class FileManager(object):
    """TODO."""

    def __init__(self, folders=None, files=None):
        """TODO."""
        self.folders = folders or []
        self.files = files or []
        self.paths = [os.path.dirname(p) for p in self.files] + self.folders
        self.diff_tool = DiffTool(paths=self.paths)

    def get_files(self,
                  branch=DEFAULT_BRANCH,
                  diff_mode=STAGED_MODE,
                  file_mode=MODIFIED_LINES,
                  extensions=()):
        """TODO."""
        if file_mode == ALL_FILES:
            results = get_files(paths=self.paths)
            results = filter_files(results, extensions)
        elif file_mode == MODIFIED_FILES:
            results = self.get_modified_files(branch=branch,
                                              diff_mode=diff_mode,
                                              extensions=extensions)
        elif file_mode == MODIFIED_LINES:
            results = self.get_modified_file_lines(branch=branch,
                                                   diff_mode=diff_mode,
                                                   extensions=extensions)
        return results

    def get_modified_file_lines(self,
                                branch=DEFAULT_BRANCH,
                                diff_mode=STAGED_MODE,
                                extensions=()):
        """TODO."""
        if diff_mode == COMMITED_MODE:
            results = self.diff_tool.commited_file_lines(branch=branch)
        elif diff_mode == STAGED_MODE:
            results = self.diff_tool.staged_file_lines()
        elif diff_mode == UNSTAGED_MODE:
            results = self.diff_tool.unstaged_file_lines()
        results = filter_files(results, extensions)
        return results

    def get_modified_files(self,
                           branch=DEFAULT_BRANCH,
                           diff_mode=STAGED_MODE,
                           extensions=()):
        """TODO."""
        if diff_mode == COMMITED_MODE:
            results = self.diff_tool.commited_files(branch=branch)
        elif diff_mode == STAGED_MODE:
            results = self.diff_tool.staged_files()
        elif diff_mode == UNSTAGED_MODE:
            results = self.diff_tool.unstaged_files()
        results = filter_files(results, extensions)
        return results


def test():
    folders = [os.path.dirname(os.path.realpath(__file__))]
    fm = FileManager(folders=folders)
    files = fm.get_modified_file_lines(diff_mode=COMMITED_MODE)
    print(files)


if __name__ == '__main__':
    test()
