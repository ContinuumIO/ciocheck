# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright 2016 Continuum Analytics, Inc.
#
# May be copied and distributed freely only as part of an Anaconda or
# Miniconda installation.
# -----------------------------------------------------------------------------
"""Tests script."""

from __future__ import print_function

# Standard library imports
from os.path import dirname, realpath
import codecs
import cProfile
import os
import os.path as osp
import pstats
import re
import shutil
import subprocess
import sys

# Third party imports
import coverage.summary
import flake8.engine
import pydocstyle
import pylint.epylint
import pytest_cov.plugin

# Local imports
from ciocheck import (CONFIGURATION_FILE, COPYRIGHT_HEADER_FILE,
                      DEFAULT_COPYRIGHT_HEADER, DEFAULT_ENCODING_HEADER,
                      ENCODING_HEADER_FILE)
from ciocheck.setup_atomic_replace import atomic_replace

YAPF_CODE = 10
ISORT_CODE = 11
YAPF_ISORT_CODE = 12

HERE = dirname(realpath(__file__))
PY2 = sys.version_info[0] == 2

if PY2:
    # Python 2
    from cStringIO import StringIO
    import ConfigParser as configparser
else:
    # Python 3
    from io import StringIO
    import configparser


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
            count = 0
            for line in output:
                if self._root in line:
                    count += 1
                print(line.replace(self._root, '\n{0}.\t.'.format(count)))


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


class Test(object):
    """Main test/check linter tool."""

    CONFIG_SECTIONS = {'.flake8': ['flake8'],
                       '.pydocstyle': ['pydocstyle'],
                       '.isort.cfg': ['settings'],
                       '.pylintrc': ['MESSAGES CONTROL'], }
    COPYRIGHT_RE = re.compile('# *Copyright ')

    def __init__(self,
                 root,
                 folder_or_file,
                 format_code=False,
                 format_imports=False,
                 git_staged_only=False,
                 profile_formatting=False,
                 add_init=False,
                 add_headers=False,
                 run_test=False):
        """Main test/check linter tool.

        Parameters
        ----------
        root : str
            Path where ciocheck script was called (root directory).
        folder_or_file : str
            Path of module or file to analize.
        format_only : bool (optional)
            Only apply format checks.
        git_staged_only : bool (optional)
            Use git staged files only.
        profile_formatting : bool (optional)
            Profile yapf formating.
        """
        # Run options
        self.root = root
        self.format_code = format_code
        self.format_imports = format_imports
        self.git_staged_only = git_staged_only
        self.profile_formatting = profile_formatting
        self.add_init = add_init
        self.add_headers = add_headers
        self.run_test = run_test

        if osp.isfile(folder_or_file):
            self.root_modules = None
            self.file = folder_or_file
        else:
            self.root_modules = [folder_or_file]
            self.file = None

        # Variables
        self._cpu_count = None
        self.copyright_header = DEFAULT_COPYRIGHT_HEADER
        self.encoding_header = DEFAULT_ENCODING_HEADER
        self.failed = set()
        self.git_staged_pyfiles = None
        self.pyfiles = None
        self.step = 0
        self.config_file = os.path.join(self.root, CONFIGURATION_FILE)

        # Setup
        self._clean()
        self._create_linters_config()
        self._setup_pytest_coverage_args()
        self._setup_headers()

    # --- Helpers
    # -------------------------------------------------------------------------
    def _setup_pytest_coverage_args(self):
        """Setup pytest-cov arguments and config file path."""
        if self.file:
            module = self.file
        else:
            module = self.root_modules[0]

        cov = '--cov={0}'.format(module)
        coverage_args = [cov, '--no-cov-on-fail']

        if os.path.isfile(self.config_file):
            cov_config = ['--cov-config', self.config_file]
            coverage_args = cov_config + coverage_args

        if PY2:
            # xdist appears to lock up the test suite with python2, maybe due
            # to an interaction with coverage
            enable_xdist = []
        else:
            enable_xdist = ['-n', str(self.cpu_count)]

        self.pytest_args = ['-rfew', '--durations=10'] + enable_xdist
        self.pytest_args = self.pytest_args + coverage_args

    def _setup_headers(self):
        """Load custom encoding and copyright headers if defined."""
        encoding_path = osp.join(self.root, COPYRIGHT_HEADER_FILE)
        if osp.isfile(encoding_path):
            with open(encoding_path, 'r') as f:
                self.copyright_header = f.read()

        header_path = osp.join(self.root, ENCODING_HEADER_FILE)
        if osp.isfile(header_path):
            with open(header_path, 'r') as f:
                self.encoding_header = f.read()

    def _clean(self):
        """Remove build directories and temporal config files."""
        # Clean up leftover trash as best we can
        BUILD_TMP = os.path.join(self.root, 'build', 'tmp')
        if os.path.isdir(BUILD_TMP):
            print("Cleaning up {0}".format(BUILD_TMP))
            try:
                shutil.rmtree(BUILD_TMP, ignore_errors=True)
            except Exception as e:
                print("Failed to remove {0}: {1}".format(BUILD_TMP, str(e)))
            else:
                print("Done removing {0}".format(BUILD_TMP))

        # Remove config files
        remove_files = [osp.join(self.root, fname)
                        for fname in self.CONFIG_SECTIONS]
        for fpath in remove_files:
            if osp.isfile(fpath):
                os.remove(fpath)

    def _create_config(self, config, sections, fname):
        """Create a config file for for a given config fname and sections."""
        new_config = configparser.ConfigParser()
        new_config_file = os.path.join(self.root, fname)

        for section in sections:
            if config.has_section(section):
                items = config.items(section)
                new_config.add_section(section)

                for option, value in items:
                    new_config.set(section, option, value)

                with open(new_config_file, 'w') as f:
                    new_config.write(f)

    def _create_linters_config(self):
        """Create a config file for the differet tools based on `.checkio`."""
        if os.path.isfile(self.config_file):
            config = configparser.ConfigParser()
            with open(self.config_file, 'r') as f:
                config.readfp(f)

            for configfile in self.CONFIG_SECTIONS:
                section = self.CONFIG_SECTIONS[configfile]
                self._create_config(config, section, configfile)

            # Additional check for coveragerc
            if config.has_section('report'):
                if config.has_option('report', 'skip_covered'):
                    skip = config.get('report', 'skip_covered').lower()
                    if skip == 'true':
                        self._monkey_path_coverage()

    def _monkey_path_coverage(self):
        """Enforce the value of `skip_covered`, ignored by pytest-cov.

        pytest-cov ignores the option even if included in the .coveragerc
        configuration file.
        """
        try:
            original_init = coverage.summary.SummaryReporter.__init__

            def modified_init(self, coverage, config):
                config.skip_covered = True
                original_init(self, coverage, config)

            coverage.summary.SummaryReporter.__init__ = modified_init

            print("\nCoverage monkeypatched to skip_covered")
        except Exception as e:
            print("\nFailed to monkeypatch coverage: {0}".format(str(e)),
                  file=sys.stderr)

    @property
    def cpu_count(self):
        """Return the cpu count."""
        if self._cpu_count is None:
            try:
                import multiprocessing
                self._cpu_count = multiprocessing.cpu_count()
            except Exception:
                print("Using fallback CPU count", file=sys.stderr)
                self._cpu_count = 4
        return self._cpu_count

    def get_py_files(self):
        """Return all python files in the module."""
        if self.file:
            self.pyfiles = [osp.join(self.root, self.file)]
        else:
            module_path = osp.join(self.root, self.root_modules[0])
            if self.pyfiles is None:
                pyfiles = []
                for root, dirs, files in os.walk(module_path):
                    # Chop out hidden directories
                    files = [f for f in files if not f[0] == '.']
                    dirs[:] = [d for d in dirs
                               if (d[0] != '.' and d != 'build' and d !=
                                   '__pycache__')]

                    # Now walk files
                    for f in files:
                        if f.endswith(".py"):
                            pyfiles.append(os.path.join(root, f))
                self.pyfiles = pyfiles

        return self.pyfiles

    def get_git_staged_py_files(self):
        """Return the git staged python files in the module."""
        if self.git_staged_pyfiles is None:
            # --diff-filter=AM means "added" and "modified"
            # -z means nul-separated names
            out = subprocess.check_output(
                ['git', 'diff', '--cached', '--name-only', '--diff-filter=AM',
                 '-z'])
            git_changed = set(out.decode('utf-8').split('\x00'))
            git_changed.discard('')  # There's an empty line in git output
            git_changed = {osp.join(self.root, fname) for fname in git_changed}
            self.git_staged_pyfiles = [fname for fname in self.get_py_files()
                                       if fname in git_changed]

            print("Found {0} files: {1}".format(len(git_changed), git_changed))

        return self.git_staged_pyfiles

    def get_files(self):
        """Return all (or only staged) python files in the module."""
        if self.git_staged_only:
            return self.get_git_staged_py_files()
        else:
            return self.get_py_files()

    def add_missing_init_py(self):
        """Add missing __init__.py files in the module subdirectories."""
        if self.file:
            return

        for srcdir in self.root_modules:
            for root, dirs, files in os.walk(os.path.join(self.root, srcdir)):
                dirs[:] = [d for d in dirs
                           if not (d[0] == '.' or d == '__pycache__')]
                for d in dirs:
                    init_py = os.path.join(root, d, "__init__.py")
                    if not os.path.exists(init_py):
                        print("Creating {0}".format(init_py))
                        with codecs.open(init_py, 'w', 'utf-8') as handle:
                            handle.flush()

    def _add_headers(self, path):
        """Add headers as needed in file.

        This is a helper method for `check_headers`.
        """
        short_path = self.shorten_path(path)
        with codecs.open(path, 'r', 'utf-8') as f:
            old_contents = f.read()

        have_coding = (self.encoding_header in old_contents)
        have_copyright = (self.COPYRIGHT_RE.search(old_contents) is not None)

        if have_coding and have_copyright:
            return

        if not have_coding:
            print("\nNo encoding header comment in \t" + short_path)
            if "encoding_header" not in self.failed:
                self.failed.add("encoding_header")

        if not have_copyright:
            print("\nNo copyright header comment in \t" + short_path)
            if "copyright_header" not in self.failed:
                self.failed.add("copyright_header")

        # Note: do NOT automatically change the copyright owner or date. The
        # copyright owner/date is a statement of legal reality, not a way to
        # create legal reality. All we do here is add an owner/date if there
        # is none; if it's incorrect, the person creating/reviewing the pull
        # request will need to fix it. If there's already an owner/date then
        # we leave it as-is assuming someone has manually chosen it.
        contents = old_contents

        if not have_copyright:
            print("\nAdding copyright header to: \t" + short_path)
            contents = self.copyright_header + contents

        if not have_coding:
            print("\nAdding encoding header to: \t" + short_path)
            contents = self.encoding_header + contents

        atomic_replace(path, contents, 'utf-8')

    def _start_format_files(self, paths):
        """check_yapf helper method to start a seaparate subprocess."""
        cmd = [sys.executable, os.path.join(HERE, 'setup_yapf_task.py')]
        env = os.environ.copy()
        env['CIOCHECK_PROJECT_ROOT'] = self.root
        env['CIOCHECK_YAPF'] = str(self.format_code)
        env['CIOCHECK_ISORT'] = str(self.format_imports)
        proc = subprocess.Popen(cmd + paths, env=env)
        return proc

    def shorten_path(self, path):
        """Remove the `root` part from the path."""
        return path.replace(self.root, '.')

    def print_section(self, text):
        """Pretty print section and numbering."""
        max_line_size = 80
        self.step += 1
        new_text = " {0}. {1} ".format(self.step, text)

        left = int((max_line_size - len(new_text)) / 2)
        right = max_line_size - left - len(new_text)
        print('\n')
        print('=' * left + new_text + '=' * right)
        print()

    # --- Checks
    # -------------------------------------------------------------------------
    def check_headers(self):
        """Run headers formatter."""
        self.print_section("Checking file headers")
        for pyfile in self.get_files():
            self._add_headers(pyfile)

    def check_yapf(self):
        """
        Run yapf formatter.

        This uses some silly multi-process stuff because Yapf is very very
        slow and CPU-bound.

        Not using a multiprocessing because not sure how its "magic" (pickling,
        __main__ import) really works.
        """
        self.print_section("Running YAPF")
        print("{0} CPUs to run yapf processes".format(self.cpu_count))
        processes = []

        def await_one_process():
            if processes:
                # we pop(0) because the first process is the oldest
                proc = processes.pop(0)
                proc.wait()
                code = proc.returncode
                print([code])
                if code != 0:
                    print(code)
                    # We fail the tests if we reformat anything, because
                    # we want CI to complain if a PR didn't run yapf
                    if code == YAPF_CODE and not self.format_imports:
                        self.failed.add("yapf")
                    elif code == ISORT_CODE and not self.format_code:
                        self.failed.add("isort")
                    elif (code == YAPF_ISORT_CODE and self.format_code and
                            self.format_imports):
                        self.failed.add("yapf-isort")

        def await_all_processes():
            while processes:
                await_one_process()

        def take_n(items, n):
            result = []
            while n > 0 and items:
                result.append(items.pop())
                n = n - 1
            return result

        all_files = list(self.get_files())
        while all_files:
            # We send a few files to each process to try to reduce
            # per-process setup time
            some_files = take_n(all_files, 3)
            processes.append(self._start_format_files(some_files))

            # Don't run too many at once, this is a goofy algorithm
            if len(processes) > (self.cpu_count * 3):
                while len(processes) > self.cpu_count:
                    await_one_process()

        assert [] == all_files
        await_all_processes()
        assert [] == processes

    def check_flake8(self):
        """Run flake8 checks."""
        self.print_section("Running flake8")
        flake8_style = flake8.engine.get_style_guide(paths=self.get_files())

        with ShortOutput(self.root):
            report = flake8_style.check_files()

        if report.total_errors > 0:
            print("\n{0} flake8 errors, see above to fix "
                  "them".format(str(report.total_errors)))
            self.failed.add('flake8')
        else:
            print("\nflake8 passed!")

    def check_pydocstyle(self):
        """Run pydocstyle checks."""
        self.print_section("Running pydocstyle")

        # Hack pydocstyle not to spam enormous amounts of debug logging if you
        # use pytest -s. run_pydocstyle() below calls log.setLevel
        def ignore_set_level(level):
            pass

        pydocstyle.log.setLevel = ignore_set_level

        # Hack (replacing argv temporarily because pydocstyle looks at it)
        old_argv = sys.argv

        try:
            if self.file:
                path = os.path.join(self.root, self.file)
            else:
                path = os.path.join(self.root, self.root_modules[0])

            sys.argv = ['pydocstyle', path]
            with ShortOutput(self.root):
                code = pydocstyle.run_pydocstyle()
        finally:
            sys.argv = old_argv

        if code == pydocstyle.INVALID_OPTIONS_RETURN_CODE:
            print("\npydocstyle found invalid configuration.")
            self.failed.add('pydocstyle')
        elif code == pydocstyle.VIOLATIONS_RETURN_CODE:
            print("\npydocstyle reported some violations.")
            self.failed.add('pydocstyle')
        elif code == pydocstyle.NO_VIOLATIONS_RETURN_CODE:
            print("\npydocstyle says docstrings look good.")
        else:
            raise RuntimeError("unexpected code from pydocstyle: "
                               "{0}".format(str(code)))

    def check_pylint(self):
        """Run pylint checks."""
        self.print_section("Running PyLint")
        lint = pylint.epylint
        count = 0
        failed = False
        for module_name in self.get_files():
            out, err = lint.py_run(module_name, return_std=True)
            for output in [out.read().split('\n'), err.read().split('\n')]:
                for line in output:
                    if self.root in line:
                        count += 1
                    new_line = line.replace(' error ', '\n\terror ')
                    new_line = new_line.replace(' warning ', '\n\twarning ')

                    if new_line.strip():
                        print(new_line.replace(self.root,
                                               '\n{0}.\t.'.format(count)))
                    if '\n\terror ' in new_line and not failed:
                        failed = True

        if count and failed:
            self.failed.add('pylint')

    def check_pytest(self):
        """Run pytest test suite."""
        self.print_section("Running pytest")

        # If used with qtpy and pytest-qt
        try:
            from qtpy.QtCore import Qt  # analysis:ignore
            Qt
        except ImportError:
            pass
        import pytest

        try:
            errno = pytest.main(self.pytest_args)
            if errno != 0:
                print("\npytest failed, code {errno}".format(errno=errno))
                self.failed.add('pytest')
        except pytest_cov.plugin.CoverageError as e:
            print("\nTest coverage failure: {0}".format(str(e)))
            self.failed.add('pytest-coverage')

    def run(self):
        """Run all checks."""
        if self.git_staged_only:
            print("Only formatting {0} git-staged python files, skipping {1} "
                  "files".format(
                      len(self.get_git_staged_py_files()), len(
                          self.get_py_files())))

        if self.add_init:
            self.add_missing_init_py()

        if self.add_headers:
            self.check_headers()

        # Only yapf is slow enough to really be worth profiling
        if self.profile_formatting:
            if self.format_code or self.format_imports:
                with Profiler():
                    self.check_yapf()
        elif self.format_code or self.format_imports:
            self.check_yapf()

        self.check_flake8()
        self.check_pydocstyle()
#        self.check_pylint()

        if self.run_test:
            self.check_pytest()

        self._clean()
        if os.path.exists(os.path.join(self.root, '.eggs')):
            print(".eggs directory exists which means some dependency was "
                  "not installed via conda/pip")
            print("  (if this happens on binstar, this may need fixing "
                  "in .binstar.yml)")
            print("  (if this happens on your workstation, try conda/pip "
                  "installing the deps and deleting .eggs")
            self.failed.add("eggs-directory-exists")

        self.print_section('Summary')
        if len(self.failed) > 0:
            print("Failures in: {0}\n".format(repr(self.failed)))
            sys.exit(1)
        else:
            if self.git_staged_only:
                print("Skipped some files (only checked {0} added/modified "
                      "files).\n".format(len(self.get_git_staged_py_files())))
            if not self.run_test:
                print("Formatting looks good, but didn't run tests.\n")
            else:
                print("All tests passed!\n")
