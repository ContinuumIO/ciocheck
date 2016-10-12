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
import codecs
import difflib
import errno
import cProfile
import pstats
import os
import subprocess
import uuid
import sys

# Local imports
from ciocheck.config import (PY2, DEFAULT_IGNORE_EXTENSIONS,
                             DEFAULT_IGNORE_FOLDERS)


if PY2:
    # Python 2
    from cStringIO import StringIO
else:
    # Python 3
    from io import StringIO


class Profiler(object):
    """Context manager profiler."""

    def __init__(self):
        """Context manager profiler."""
        self._profiler = cProfile.Profile()

    def __enter__(self):
        """Enable profiler."""
        self._profiler.enable()

    def __exit__(self, type, value, traceback):
        """Disable profiler and print stats."""
        self._profiler.disable()
        ps = pstats.Stats(self._profiler,
                          stream=sys.stdout).sort_stats('cumulative')
        ps.print_stats()


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

    def __enter__(self):
        """Capture stdout and stderr in a StringIO."""
        self._stdout = sys.stdout
        self._stderr = sys.stderr
        sys.stdout = self._stringio_output = StringIO()
        sys.stderr = self._stringio_error = StringIO()

    def __exit__(self, *args):
        """Restore stdout and stderr and format found values."""
        out = self._stringio_output.getvalue().splitlines()
        err = self._stringio_error.getvalue().splitlines()
        sys.stdout = self._stdout
        sys.stderr = self._stderr

        for output in [out, err]:
            for line in output:
                print(line)


def run_command(args, cwd=None):
    """Run command."""
    p = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        )
    output, error = p.communicate()

    if isinstance(output, bytes):
        output = output.decode()
    if isinstance(error, bytes):
        error = error.decode()

    return output, error


def get_files(paths,
              exts=(),
              ignore_exts=DEFAULT_IGNORE_EXTENSIONS,
              ignore_dirs=DEFAULT_IGNORE_FOLDERS):
    """Return all files matching the defined conditions."""
    all_files = []
    for path in paths:
        for root, dirs, files in os.walk(path):
            # Chop out hidden directories
            new_dirs = []
            for d in dirs:
                if d[0] != '.':
                    tests = [d != ignore_dir for ignore_dir in ignore_dirs]
                    if all(tests):
                        new_dirs.append(d)
            dirs[:] = new_dirs

            # Chop out hidden files and walk files
            files = [f for f in files if f[0] != '.']
            for f in files:
                tests, pass_tests = [True], [True]
                if ignore_exts:
                    tests = [not f.endswith('.' + ext) for ext in ignore_exts]
                if exts:
                    pass_tests = [f.endswith('.' + ext) for ext in exts]

                if all(tests) and any(pass_tests):
                    all_files.append(os.path.join(root, f))

    return list(sorted(all_files))


def filter_files(files, extensions):
    """Filter files based on a list of extensions."""
    for f in files.copy():
        if extensions:
            tests = [f.endswith('.' + ext) for ext in extensions]
        else:
            tests = [True]

        if not any(tests):
            if isinstance(files, dict):
                files.pop(f)
            else:
                files.remove(f)
    return files


def _rename_over_existing(src, dest):
    try:
        # On Windows, this will throw EEXIST, on Linux it won't.
        os.rename(src, dest)
    except IOError as e:
        if e.errno == errno.EEXIST:
            # Clearly this song-and-dance is not in fact atomic,
            # but if something goes wrong putting the new file in
            # place at least the backup file might still be
            # around.
            backup = "{0}.bak-{1}".format(dest, str(uuid.uuid4()))
            os.rename(dest, backup)
            try:
                os.rename(src, dest)
            except Exception as e:
                os.rename(backup, dest)
                raise e
            finally:
                try:
                    os.remove(backup)
                except Exception as e:
                    pass


def atomic_replace(path, contents, encoding):
    """Try to do an atomic replace."""
    tmp = "{0}tmp-{1}".format(path, str(uuid.uuid4()))
    try:
        with codecs.open(tmp, 'w', encoding) as f:
            f.write(contents)
            f.flush()
            f.close()
        _rename_over_existing(tmp, path)
    finally:
        try:
            os.remove(tmp)
        except (IOError, OSError):
            pass


def diff(s1, s2):
    """Return unified diff of strings."""
    s1 = s1.splitlines(1)
    s2 = s2.splitlines(1)
    diff = difflib.unified_diff(s1, s2)
    return ''.join(diff)


def cpu_count():
    """Return the cpu count."""
    try:
        import multiprocessing
        count = multiprocessing.cpu_count()
    except Exception:
        print("Using fallback CPU count", file=sys.stderr)
        count = 4
    return count


def test():
    paths = [os.path.dirname(os.path.realpath(__file__))]
    files = get_files(paths, exts=('py',))
    for f in files:
        print(f)


if __name__ == '__main__':
    test()
