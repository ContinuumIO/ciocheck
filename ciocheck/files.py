# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""File manager."""

# Standard library imports
import os

# Local imports
from ciocheck.config import (ALL_FILES, COMMITED_MODE, DEFAULT_BRANCH,
                             MODIFIED_FILES, MODIFIED_LINES, STAGED_MODE,
                             UNSTAGED_MODE)
from ciocheck.utils import filter_files, get_files
from ciocheck.vcs import DiffTool


class FileManager(object):
    """File manager with git support."""

    def __init__(self, folders=None, files=None):
        """File manager with git support."""
        self.folders = folders or []
        self.files = files or []
        self.paths = [os.path.dirname(p) for p in self.files] + self.folders
        self.diff_tool = DiffTool(paths=self.paths)
        self.cache = {}

    def get_files(self,
                  branch=DEFAULT_BRANCH,
                  diff_mode=STAGED_MODE,
                  file_mode=MODIFIED_LINES,
                  extensions=()):
        """Find files in paths."""
        cache_key = (branch, diff_mode, file_mode, tuple(extensions))
        if cache_key in self.cache:
            results = self.cache[cache_key]
        else:
            if file_mode == ALL_FILES:
                results = get_files(paths=self.paths)
                results = filter_files(results, extensions)
            elif file_mode == MODIFIED_FILES:
                results = self.get_modified_files(
                    branch=branch, diff_mode=diff_mode, extensions=extensions)
            elif file_mode == MODIFIED_LINES:
                results = self.get_modified_file_lines(
                    branch=branch, diff_mode=diff_mode, extensions=extensions)
            self.cache[cache_key] = results

        return results

    def get_modified_file_lines(self,
                                branch=DEFAULT_BRANCH,
                                diff_mode=STAGED_MODE,
                                extensions=()):
        """Find modified lines of files in paths."""
        cache_key = (branch, diff_mode, tuple(extensions), 'lines')
        if cache_key in self.cache:
            results = self.cache[cache_key]
        else:
            if diff_mode == COMMITED_MODE:
                results = self.diff_tool.commited_file_lines(branch=branch)
            elif diff_mode == STAGED_MODE:
                results = self.diff_tool.staged_file_lines()
            elif diff_mode == UNSTAGED_MODE:
                results = self.diff_tool.unstaged_file_lines()
            results = filter_files(results, extensions)
            self.cache[cache_key] = results

        return results

    def get_modified_files(self,
                           branch=DEFAULT_BRANCH,
                           diff_mode=STAGED_MODE,
                           extensions=()):
        """Find modified files in paths."""
        cache_key = (branch, diff_mode, tuple(extensions))
        if cache_key in self.cache:
            results = self.cache[cache_key]
        else:
            if diff_mode == COMMITED_MODE:
                results = self.diff_tool.commited_files(branch=branch)
            elif diff_mode == STAGED_MODE:
                results = self.diff_tool.staged_files()
            elif diff_mode == UNSTAGED_MODE:
                results = self.diff_tool.unstaged_files()
            results = filter_files(results, extensions)
            self.cache[cache_key] = results

        return results


def test():
    """Main local test."""
    folders = [os.path.dirname(os.path.realpath(__file__))]
    file_manager = FileManager(folders=folders)
    files = file_manager.get_modified_file_lines(diff_mode=COMMITED_MODE)
    print(files)


if __name__ == '__main__':
    test()
