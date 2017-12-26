# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Version control helpers. Find staged, committed, modified files/lines."""

# Standard library imports
import os
import re

# Local imports
from ciocheck.config import (COMMITED_MODE, DEFAULT_BRANCH, STAGED_MODE,
                             UNSTAGED_MODE)
from ciocheck.utils import get_files, make_sorted_dict, run_command


class DiffToolBase(object):
    """Base version control diff tool."""

    # --- Public API
    # -------------------------------------------------------------------------
    @property
    def top_level(self):
        """Return the top level for the repo."""
        raise NotImplementedError

    def is_repo(self):
        """Return if it is a repo of the type."""
        raise NotImplementedError

    def commited_files(self, branch=DEFAULT_BRANCH):
        """Return list of committed files."""
        raise NotImplementedError

    def staged_files(self):
        """Return list of staged files."""
        raise NotImplementedError

    def unstaged_files(self):
        """Return list of unstaged files."""
        raise NotImplementedError

    def commited_file_lines(self, branch=DEFAULT_BRANCH):
        """Return committed files and lines modified."""
        raise NotImplementedError

    def staged_file_lines(self):
        """Return unstaged files and lines modified."""
        raise NotImplementedError

    def unstaged_file_lines(self):
        """Return staged files and lines modified."""
        raise NotImplementedError


class HgDiffTool(DiffToolBase):
    """Mercurial diff tool."""

    def __init__(self, path):
        """Mercurial diff tool."""
        self.path = path
        self._top_level = None

    @property
    def top_level(self):
        """Return the top level for the repo."""
        return ''

    def is_repo(self):
        """Return if it is a repo of the type."""
        return False

    def commited_files(self, branch=DEFAULT_BRANCH):
        """Return list of committed files."""
        return []

    def staged_files(self):
        """Return list of staged files."""
        return []

    def unstaged_files(self):
        """Return list of unstaged files."""
        return []

    def commited_file_lines(self, branch=DEFAULT_BRANCH):
        """Return committed files and lines modified."""
        return {}

    def staged_file_lines(self):
        """Return unstaged files and lines modified."""
        return {}

    def unstaged_file_lines(self):
        """Return staged files and lines modified."""
        return {}


class GitDiffTool(DiffToolBase):
    """Thin wrapper for a subset of the `git diff` command."""

    # Regular expressions used to parse the diff output
    SRC_FILE_RE = re.compile(r'^diff --git "?a/.*"? "?b/([^ \n"]*)"?')
    MERGE_CONFLICT_RE = re.compile(r'^diff --cc ([^ \n]*)')
    HUNK_LINE_RE = re.compile(r'\+([0-9]*)')

    def __init__(self, path):
        """Thin wrapper for a subset of the `git diff` command."""
        self.path = path
        self._top_level = None
        self._is_repo = None

    def _git_run_helper(self,
                        branch=DEFAULT_BRANCH,
                        files_only=False,
                        mode=None):
        """Build git diff command to generate different types of diffs."""
        command = [
            'git',
            '-c',
            'diff.mnemonicprefix=no',
            'diff',
        ]

        if mode == COMMITED_MODE:
            command.append("{branch}...HEAD".format(branch=branch))
        elif mode == STAGED_MODE:
            command.append('--cached')

        command += [
            '--no-color',
            '--no-ext-diff',
            '--diff-filter=AM',  # Means "added" and "modified"
        ]

        if files_only:
            command += [
                '--name-only',
                '-z',  # Means nul-separated names
            ]

            output, error = run_command(command, cwd=self.path)
            print(error)
            result = set(output.split('\x00'))
            result.discard('')  # There's an empty line in git output
            result = [os.path.join(self.top_level, i) for i in sorted(result)]
            result = [i for i in result if i.startswith(self.path)]
        else:
            result, error = run_command(command, cwd=self.path)

        return result

    def _parse_diff_str(self, diff_str):
        """
        Parse the output of `git diff` into a dictionary.

        Dictionary in the form:
            { SRC_PATH: (ADDED_LINES, DELETED_LINES) }
        where `ADDED_LINES` and `DELETED_LINES` are lists of line numbers
        added/deleted respectively.
        """
        # Create a dict to hold results
        diff_dict = dict()

        # Parse the diff string into sections by source file
        sections_dict = self._parse_source_sections(diff_str)
        for (src_path, diff_lines) in sections_dict.items():
            full_src_path = os.path.join(self.top_level, src_path)
            # Parse the hunk information for the source file
            # to determine lines changed for the source file
            diff_dict[full_src_path] = self._parse_lines(diff_lines)

        ordered_diff_dict = make_sorted_dict(diff_dict)
        return ordered_diff_dict

    def _parse_source_sections(self, diff_str):
        """Parse source sections from git diff."""
        # Create a dict to map source files to lines in the diff output
        source_dict = dict()

        # Keep track of the current source file
        src_path = None

        # Signal that we've found a hunk (after starting a source file)
        found_hunk = False

        # Parse the diff string into sections by source file
        for line in diff_str.split('\n'):

            # If the line starts with "diff --git"
            # or "diff --cc" (in the case of a merge conflict)
            # then it is the start of a new source file
            if line.startswith('diff --git') or line.startswith('diff --cc'):

                # Retrieve the name of the source file
                src_path = self._parse_source_line(line)

                # Create an entry for the source file, if we don't
                # already have one.
                if src_path not in source_dict:
                    source_dict[src_path] = []

                # Signal that we're waiting for a hunk for this source file
                found_hunk = False

            # Every other line is stored in the dictionary for this source file
            # once we find a hunk section
            else:

                # Only add lines if we're in a hunk section
                # (ignore index and files changed lines)
                if found_hunk or line.startswith('@@'):

                    # Remember that we found a hunk
                    found_hunk = True

                    if src_path is not None:
                        source_dict[src_path].append(line)

                    else:
                        # We tolerate other information before we have
                        # a source file defined, unless it's a hunk line
                        if line.startswith("@@"):
                            msg = "Hunk has no source file: '{0}'".format(line)
                            raise Exception(msg)

        return source_dict

    def _parse_source_line(self, line):
        """Return path to source given a source line in `git diff`."""
        if '--git' in line:
            regex = self.SRC_FILE_RE
        elif '--cc' in line:
            regex = self.MERGE_CONFLICT_RE
        else:
            msg = ("Do not recognize format of source in line "
                   "'{0}'".format(line))
            raise Exception(msg)

        # Parse for the source file path
        groups = regex.findall(line)

        if len(groups) == 1:
            return groups[0]

        else:
            msg = "Could not parse source path in line '{0}'".format(line)
            raise Exception(msg)

    def _parse_lines(self, diff_lines):
        """
        Return  `(ADDED_LINES, DELETED_LINES)` for a source file in diff.

        `ADDED_LINES` and `DELETED_LINES` are lists of line numbers
        added/deleted respectively.
        """
        added_lines = []
        deleted_lines = []

        current_line_new = None
        current_line_old = None

        for line in diff_lines:

            # If this is the start of the hunk definition, retrieve
            # the starting line number
            if line.startswith('@@'):
                line_num = self._parse_hunk_line(line)
                current_line_new, current_line_old = line_num, line_num

            # This is an added/modified line, so store the line number
            elif line.startswith('+'):

                # Since we parse for source file sections before
                # calling this method, we're guaranteed to have a source
                # file specified.  We check anyway just to be safe.
                if current_line_new is not None:

                    # Store the added line
                    added_lines.append(current_line_new)

                    # Increment the line number in the file
                    current_line_new += 1

            # This is a deleted line that does not exist in the final
            # version, so skip it
            elif line.startswith('-'):

                # Since we parse for source file sections before
                # calling this method, we're guaranteed to have a source
                # file specified.  We check anyway just to be safe.
                if current_line_old is not None:

                    # Store the deleted line
                    deleted_lines.append(current_line_old)

                    # Increment the line number in the file
                    current_line_old += 1

            # This is a line in the final version that was not modified.
            # Increment the line number, but do not store this as a changed
            # line.
            else:
                if current_line_old is not None:
                    current_line_old += 1

                if current_line_new is not None:
                    current_line_new += 1

                # If we are not in a hunk, then ignore the line
                else:
                    pass

        return added_lines, deleted_lines

    def _parse_hunk_line(self, line):
        """
        Return the line number at the start of a hunk in a given line.

        A hunk is a segment of code that contains changes.

        The format of the hunk line is:
            @@ -k,l +n,m @@ TEXT
        where `k,l` represent the start line and length before the changes
        and `n,m` represent the start line and length after the changes.
        `git diff` will sometimes put a code excerpt from within the hunk
        in the `TEXT` section of the line.
        """
        # Split the line at the @@ terminators (start and end of the line)
        components = line.split('@@')

        # The first component should be an empty string, because
        # the line starts with '@@'.  The second component should
        # be the hunk information, and any additional components
        # are excerpts from the code.
        if len(components) >= 2:

            hunk_info = components[1]
            groups = self.HUNK_LINE_RE.findall(hunk_info)

            if len(groups) == 1:

                try:
                    return int(groups[0])

                except ValueError:
                    msg = ("Could not parse '{0}' as a line "
                           "number".format(groups[0]))
                    raise Exception(msg)

            else:
                msg = "Could not find start of hunk in line '{0}'".format(line)
                raise Exception(msg)

        else:
            msg = "Could not parse hunk in line '{0}'".format(line)
            raise Exception(msg)

    def _diff_committed(self, branch='origin/master'):
        """Return changes for committed files."""
        result = self._git_run_helper(
            branch=branch, files_only=False, mode=COMMITED_MODE)
        return result

    def _diff_staged(self):
        """Return diff for staged changes."""
        result = self._git_run_helper(files_only=False, mode=STAGED_MODE)
        return result

    def _diff_unstaged(self):
        """Return diff for unstaged changes."""
        result = self._git_run_helper(files_only=False, mode=UNSTAGED_MODE)
        return result

    # --- Public API
    # -------------------------------------------------------------------------
    def is_repo(self):
        """Return if it is a git repo."""
        if self._is_repo is None:
            args = ['git', 'rev-parse']
            output, error = run_command(args, cwd=self.path)
            if error:
                print(error)
                return False
            else:
                self._is_repo = (not bool(error) and not bool(output))
        return self._is_repo

    @property
    def top_level(self):
        """Return the top level for the git repo."""
        if self._top_level is None:
            output, error = run_command(
                ['git', 'rev-parse', '--show-toplevel', '--encoding=utf-8'],
                cwd=self.path, )
            if error:
                print(error)
                return None
            else:
                self._top_level = output.split('\n')[0]
        return self._top_level

    def commited_files(self, branch=DEFAULT_BRANCH):
        """Return list of committed files."""
        result = self._git_run_helper(
            branch=branch, files_only=True, mode=COMMITED_MODE)
        return result

    def staged_files(self):
        """Return list of staged files."""
        result = self._git_run_helper(files_only=True, mode=STAGED_MODE)
        return result

    def unstaged_files(self):
        """Return list of unstaged files."""
        result = self._git_run_helper(files_only=True, mode=UNSTAGED_MODE)
        return result

    def commited_file_lines(self, branch=DEFAULT_BRANCH):
        """Return committed files and lines modified."""
        result = self._parse_diff_str(self._diff_committed(branch=branch))
        return result

    def staged_file_lines(self):
        """Return unstaged files and lines modified."""
        result = self._parse_diff_str(self._diff_staged())
        return result

    def unstaged_file_lines(self):
        """Return staged files and lines modified."""
        result = self._parse_diff_str(self._diff_unstaged())
        return result


class NoDiffTool(DiffToolBase):
    """Thin wrapper for a folder not under version control."""

    def __init__(self, path):
        """Thin wrapper for a folder not under version control."""
        self.path = path

    def _get_files_helper(self, lines=False):
        paths = get_files(paths=[self.path])
        if lines:
            paths_dic = {}
            for path in paths:
                paths_dic[path] = (
                    [-1],
                    range(100000), )
            results = paths_dic
        else:
            results = paths
        return results

    # --- Public API
    # -------------------------------------------------------------------------
    @property
    def top_level(self):
        """Return the top level for the repo."""
        return self.path

    def is_repo(self):
        """Return always True as this handles folders not under VC."""
        return True

    def commited_files(self, branch=DEFAULT_BRANCH):
        """Return list of committed files."""
        return self._get_files_helper()

    def staged_files(self):
        """Return list of staged files."""
        return self._get_files_helper()

    def unstaged_files(self):
        """Return list of unstaged files."""
        return self._get_files_helper()

    def commited_file_lines(self, branch=DEFAULT_BRANCH):
        """Return committed files and lines modified."""
        return self._get_files_helper(lines=True)

    def staged_file_lines(self):
        """Return unstaged files and lines modified."""
        return self._get_files_helper(lines=True)

    def unstaged_file_lines(self):
        """Return staged files and lines modified."""
        return self._get_files_helper(lines=True)


class DiffTool(object):
    """Generic diff tool for handling mercurial, git and no vcs folders."""

    TOOLS = [
        GitDiffTool,
        HgDiffTool,
        NoDiffTool,
    ]

    def __init__(self, paths):
        """Generic diff tool for handling mercurial, git and no vcs folders."""
        self.paths = paths
        self.diff_tools = {}

        for path in self.paths:
            for diff_tool in self.TOOLS:
                tool = diff_tool(path)
                if tool.is_repo():
                    if tool.top_level not in self.diff_tools:
                        self.diff_tools[tool.top_level] = tool
                    break

    # --- Public API
    # -------------------------------------------------------------------------
    def commited_files(self, branch=DEFAULT_BRANCH):
        """Return list of committed files."""
        results = []
        for diff_tool in self.diff_tools.values():
            results += diff_tool.commited_files(branch=branch)
        return list(sorted(results))

    def staged_files(self):
        """Return list of staged files."""
        results = []
        for diff_tool in self.diff_tools.values():
            results += diff_tool.staged_files()
        return list(sorted(results))

    def unstaged_files(self):
        """Return list of unstaged files."""
        results = []
        for diff_tool in self.diff_tools.values():
            results += diff_tool.unstaged_files()
        return list(sorted(results))

    def commited_file_lines(self, branch=DEFAULT_BRANCH):
        """Return committed files and lines modified."""
        results = {}
        for diff_tool in self.diff_tools.values():
            results.update(diff_tool.commited_file_lines(branch=branch))
        return make_sorted_dict(results)

    def staged_file_lines(self):
        """Return unstaged files and lines modified."""
        results = {}
        for diff_tool in self.diff_tools.values():
            results.update(diff_tool.staged_file_lines())
        return make_sorted_dict(results)

    def unstaged_file_lines(self):
        """Return staged files and lines modified."""
        results = {}
        for diff_tool in self.diff_tools.values():
            results.update(diff_tool.unstaged_file_lines())
        return make_sorted_dict(results)


def test():
    """Local main test."""
    paths = [os.path.dirname(os.path.realpath(__file__))]
    diff_tool = DiffTool(paths)
    print(diff_tool.unstaged_file_lines())


if __name__ == '__main__':
    test()
