# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright © 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Utilities module."""

from __future__ import absolute_import, print_function

# Standard library imports
from collections import OrderedDict
import codecs
import cProfile
import difflib
import errno
import os
import pstats
import subprocess
import sys
import uuid

# Third party imports
from six.moves import cStringIO as StringIO

# Local imports
from ciocheck.config import DEFAULT_IGNORE_EXTENSIONS, DEFAULT_IGNORE_FOLDERS


class Profiler(object):
    """Context manager profiler."""

    def __init__(self):
        """Context manager profiler."""
        self._profiler = cProfile.Profile()

    def __enter__(self):
        """Enable profiler."""
        self._profiler.enable()

    def __exit__(self, type_, value, traceback):
        """Disable profiler and print stats."""
        self._profiler.disable()
        profile_stat = pstats.Stats(
            self._profiler, stream=sys.stdout).sort_stats('cumulative')
        profile_stat.print_stats()


class ShortOutput(object):
    """Context manager for capturing and formating stdout and stderr."""

    def __init__(self, root):
        """Context manager for capturing and formating stdout and stderr.

        Parameter
        ---------
        root : str
            Path where ciocheck script was called (root directory).
        """
        self._root = root
        self._stdout = None
        self._stderr = None
        self._stringio_output = None
        self._stringio_error = None

    def __enter__(self):
        """Capture stdout and stderr in a StringIO."""
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self._stringio_output = StringIO()
        sys.stderr = self._stringio_error = StringIO()
        return self

    def __exit__(self, *args):
        """Restore stdout and stderr and format found values."""
        out = self._stringio_output.getvalue().splitlines()
        err = self._stringio_error.getvalue().splitlines()
        sys.stdout = self._stdout
        sys.stderr = self._stderr

        self.output = out
        self.error = err
        for output in [out, err]:
            for line in output:
                print(line)


def run_command(args, cwd=None):
    """Run command."""
    process = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd, )
    output, error = process.communicate()

    if isinstance(output, bytes):
        output = output.decode()
    if isinstance(error, bytes):
        error = error.decode()

    return output, error


def get_files(paths,
              exts=(),
              ignore_exts=DEFAULT_IGNORE_EXTENSIONS,
              ignore_folders=DEFAULT_IGNORE_FOLDERS):
    """Return all files matching the defined conditions."""
    all_files = []
    for path in paths:
        if os.path.isfile(path):
            all_files.append(path)
        else:
            for root, folders, files in os.walk(path):
                # Chop out hidden directories
                new_folders = []
                for folder in folders:
                    if folder[0] != '.':
                        tests = [folder != ignore_folder
                                 for ignore_folder in ignore_folders]
                        if all(tests):
                            new_folders.append(folder)
                folders[:] = new_folders

                # Chop out hidden files and walk files
                files = [f for f in files if f[0] != '.']
                for file in files:
                    tests, pass_tests = [True], [True]
                    if ignore_exts:
                        tests = [not file.endswith('.' + ext)
                                 for ext in ignore_exts]
                    if exts:
                        pass_tests = [file.endswith('.' + ext) for ext in exts]

                    if all(tests) and any(pass_tests):
                        all_files.append(os.path.join(root, file))

    return list(sorted(all_files))


def filter_files(files, extensions):
    """Filter files based on a list of extensions."""
    copy_of_files = files.copy()
    for file in files:
        if extensions:
            tests = [file.endswith('.' + ext) for ext in extensions]
        else:
            tests = [True]

        if not any(tests):
            if isinstance(files, dict):
                copy_of_files.pop(file)
            else:
                copy_of_files.remove(file)
    return copy_of_files


def _rename_over_existing(src, dest):
    try:
        # On Windows, this will throw EEXIST, on Linux it won't.
        os.rename(src, dest)
    except IOError as err:
        if err.errno == errno.EEXIST:
            # Clearly this song-and-dance is not in fact atomic,
            # but if something goes wrong putting the new file in
            # place at least the backup file might still be
            # around.
            backup = "{0}.bak-{1}".format(dest, str(uuid.uuid4()))
            os.rename(dest, backup)
            try:
                os.rename(src, dest)
            except Exception as err:
                os.rename(backup, dest)
                raise err
            finally:
                try:
                    os.remove(backup)
                except Exception as err:
                    pass


def atomic_replace(path, contents, encoding):
    """Try to do an atomic replace."""
    tmp = "{0}tmp-{1}".format(path, str(uuid.uuid4()))
    try:
        with codecs.open(tmp, 'w', encoding) as file_obj:
            file_obj.write(contents)
            file_obj.flush()
            file_obj.close()
        _rename_over_existing(tmp, path)
    finally:
        try:
            os.remove(tmp)
        except (IOError, OSError):
            pass


def diff(string_a, string_b):
    """Return unified diff of strings."""
    string_a = string_a.splitlines(1)
    string_b = string_b.splitlines(1)
    result = difflib.unified_diff(string_a, string_b)
    return ''.join(result)


def cpu_count():
    """Return the cpu count."""
    try:
        import multiprocessing
        count = multiprocessing.cpu_count()
    except Exception:
        print("Using fallback CPU count", file=sys.stderr)
        count = 4
    return count


def make_sorted_dict(dic):
    """Turn a dict into an ordered dict by sorting the keys."""
    ordered_results = OrderedDict()
    for key in sorted(dic.keys()):
        ordered_results[key] = dic[key]
    return ordered_results


def test():
    """Main local test."""
    paths = [os.path.dirname(os.path.realpath(__file__))]
    files = get_files(paths, exts=('py', ))
    for file in files:
        print(file)


if __name__ == '__main__':
    test()
