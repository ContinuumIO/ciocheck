# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2016 Continuum Analytics, Inc.
#
# Licensed under the terms of the MIT License
# (see LICENSE.txt for details)
# -----------------------------------------------------------------------------
"""Generic and custom code formatters."""

# Standard library imports
import codecs
import json
import os
import platform
import re
import subprocess
import sys

# Third party imports
from yapf.yapflib.yapf_api import FormatCode
import autopep8
import isort

# Local imports
from ciocheck.config import DEFAULT_COPYRIGHT_HEADER
from ciocheck.tools import Tool
from ciocheck.utils import atomic_replace, cpu_count, diff

HERE = os.path.dirname(os.path.realpath(__file__))


class Formatter(Tool):
    """Generic formatter tool."""

    @classmethod
    def format_task(cls, path):
        """Forma trask executed by parallel script helper."""
        changed = False
        old_contents, new_contents = '', ''
        error = None
        try:
            old_contents, new_contents, encoding = cls.format_file(path)
            changed = new_contents != old_contents
        except Exception as err:
            error = "{name} crashed on {path}: {error}".format(
                name=cls.name, path=path, error=err)

        if changed:
            result = {
                'path': path,
                'error': error,
                #            'new-contents': new_contents,
                #            'old-contents': old_contents,
                'diff': diff(old_contents, new_contents),
                'created': False,  # pyformat might create new init files.
            }
            atomic_replace(path, new_contents, encoding)
        else:
            return {}

        return result

    @classmethod
    def format_string(cls, old_contents):
        """Format content of a file."""
        raise NotImplementedError

    @classmethod
    def format_file(cls, path):
        """Format file for use with task queue."""
        with open(path, 'r') as file_obj:
            old_contents = file_obj.read()
        return cls.format_string(old_contents)

    def run(self, paths):
        """Format paths."""
        raise NotImplementedError


class IsortFormatter(Formatter):
    """Isort code formatter."""

    language = 'python'
    name = 'isort'
    extensions = ('py', )

    # Config
    config_file = '.isort.cfg'
    config_sections = [('isort', 'settings')]

    def run(self, paths):
        """Format paths."""
        pass

    @classmethod
    def format_string(cls, old_contents):
        """Format content of a file."""
        new_contents = isort.SortImports(file_contents=old_contents).output
        return old_contents, new_contents, 'utf-8'


class YapfFormatter(Formatter):
    """Yapf code formatter."""

    language = 'python'
    name = 'yapf'
    extensions = ('py', )

    # Config
    config_file = '.style.yapf'
    config_sections = [('yapf:style', 'style')]

    def run(self, paths):
        """Format paths."""
        pass

    @classmethod
    def format_string(cls, old_contents):
        """Format file for use with task queue."""
        # cmd_root is assigned to formatter inside format_task... ugly!
        style_config = os.path.join(cls.cmd_root, cls.config_file)
        # It might be tempting to use the "inplace" option to FormatFile, but
        # it doesn't do an atomic replace, which is dangerous, so don't use
        # it unless you submit a fix to yapf.
        (new_contents, changed) = FormatCode(
            old_contents, style_config=style_config)

        if platform.system() == 'Windows':
            # yapf screws up line endings on windows
            new_contents = new_contents.replace("\r\n", "\n")

            if len(old_contents) == 0:
                # Windows yapf seems to force a newline? I dunno
                new_contents = ""
        return old_contents, new_contents, 'utf-8'


class Autopep8Formatter(Formatter):
    """Autopep8 code formatter."""

    language = 'python'
    name = 'autopep8'
    extensions = ('py', )

    # Config
    config_file = '.autopep8'
    config_sections = [('autopep8', 'pep8')]

    def run(self, paths):
        """Format paths."""
        pass

    @classmethod
    def format_string(cls, old_contents):
        """Format file for use with task queue."""
        config_options = cls.make_config_dictionary()
        config_options = {}
        new_contents = autopep8.fix_code(old_contents, options=config_options)
        return old_contents, new_contents, 'utf-8'


class MultiFormatter(object):
    """Formatter handling multiple formatters in parallel."""

    language = 'generic'
    name = 'multiformatter'

    def __init__(self, cmd_root, check):
        """Formatter handling multiple formatters in parallel."""
        self.cmd_root = cmd_root
        self.check = check

    def _format_files(self, paths):
        """Helper method to start a seaparate subprocess."""
        cmd = [sys.executable, os.path.join(HERE, 'format_task.py')]
        env = os.environ.copy()
        env['CIOCHECK_PROJECT_ROOT'] = self.cmd_root
        env['CIOCHECK_CHECK'] = str(self.check)
        proc = subprocess.Popen(
            cmd + paths,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        return proc

    def _format_results(self, results):
        """Rearrange results for standard consumption."""
        new_results = {}
        for item in results:
            for key, value in item.items():
                if key not in new_results:
                    new_results[key] = []
                new_results[key].append(value)

        # Sort by path
        for key, values in new_results.items():
            new_results[key] = sorted(values, key=lambda dic: dic['path'])
        return new_results

    @property
    def extensions(self):
        """Return all extensions of the used multiformatters."""
        all_extensions = []
        for formatter in MULTI_FORMATTERS:
            all_extensions += list(formatter.extensions)
        return all_extensions

    def run(self, paths):
        """
        Run formatters.

        This uses some silly multi-process stuff because Yapf is very slow and
        CPU-bound.

        Not using a multiprocessing because not sure how its "magic" (pickling,
        __main__ import) really works.
        """
        processes = []
        if isinstance(paths, dict):
            paths = list(sorted(paths.keys()))

        def await_one_process():
            """Wait for one process and parse output."""
            if processes:
                # We pop(0) because the first process is the oldest
                proc = processes.pop(0)
                output, error = proc.communicate()

                if isinstance(output, bytes):
                    output = output.decode()

                if isinstance(error, bytes):
                    error = error.decode()

                output = json.loads(output)
                if error:
                    print(error)

                return output, error

        def await_all_processes():
            """Wait for all processes."""
            results = []
            while processes:
                output, error = await_one_process()
                output = [o for o in output if o]
                if output:
                    results += output
                if error:
                    print(error)
            return results

        def take_n(items, amount):
            """Take n items to pass to the processes."""
            result = []
            while amount > 0 and items:
                result.append(items.pop(0))  # Keep order
                amount = amount - 1
            return list(sorted(result))

        while paths:
            # We send a few files to each process to try to reduce per-process
            # setup time
            some_files = take_n(paths, 3)
            processes.append(self._format_files(some_files))

            # Don't run too many at once, this is a goofy algorithm
            if len(processes) > (cpu_count() * 3):
                while len(processes) > cpu_count():
                    await_one_process()

        assert [] == paths
        results = await_all_processes()
        results = self._format_results(results)
        assert [] == processes
        return results


class PythonFormatter(Formatter):
    """Handle __init__.py addition and headers (copyright and encoding)."""

    language = 'python'
    name = 'pyformat'
    extensions = ('py', )

    COPYRIGHT_RE = re.compile('# *Copyright ')

    def __init__(self, cmd_root):
        """Handle __init__.py addition and headers (copyright and encoding)."""
        super(PythonFormatter, self).__init__(cmd_root)
        self.config = None
        self.copyright_header = None
        self.encoding_header = None

    def _setup_headers(self):
        """Load custom encoding and copyright headers if defined."""
        self.encoding_header = self.config.get_value('header')

        copyright_file = self.config.get_value('copyright_file')
        copyright_path = os.path.join(self.cmd_root, copyright_file)
        if os.path.isfile(copyright_path):
            with open(copyright_path, 'r') as file_obj:
                self.copyright_header = file_obj.read()
        else:
            self.copyright_header = DEFAULT_COPYRIGHT_HEADER

    def _add_headers(self, path, header, copy):
        """Add headers as needed in file."""
        with codecs.open(path, 'r', 'utf-8') as file_obj:
            old_contents = file_obj.read()

        have_encoding = (self.encoding_header in old_contents)
        have_copyright = (self.COPYRIGHT_RE.search(old_contents) is not None)

        if have_encoding and have_copyright:
            return {}

        # Note: do NOT automatically change the copyright owner or date. The
        # copyright owner/date is a statement of legal reality, not a way to
        # create legal reality. All we do here is add an owner/date if there
        # is none; if it's incorrect, the person creating/reviewing the pull
        # request will need to fix it. If there's already an owner/date then
        # we leave it as-is assuming someone has manually chosen it.
        contents = ''
        if have_encoding and not have_copyright:
            # Remove the header from old content so that it is positioned
            # correctly
            lines = old_contents.splitlines(True)
            # FIXME: Is this safe on win and linux?
            lines = [l for l in lines if self.encoding_header not in l]
            old_contents = ''.join(lines)
            contents = self.encoding_header

        if not have_encoding and header:
            contents += self.encoding_header

        if not have_copyright and copy:
            contents += self.copyright_header
        new_contents = contents + old_contents
        if new_contents != old_contents:
            results = {
                'path': path,
                'diff': diff(old_contents, new_contents),
                'created': False,
                'error': None,
                'added-copy': not have_encoding and header,
                'added-header': not have_copyright and copy,
            }
            atomic_replace(path, new_contents, 'utf-8')
        else:
            results = {}
        return results

    def _add_missing_init_py(self, paths):
        """Add missing __init__.py files in the module subdirectories."""
        results = []
        folders = [os.path.dirname(p) for p in paths]

        # Avoid adding an init on repo level if setup.py or other script on the
        # top level has changed
        if self.cmd_root in folders:
            folders.remove(self.cmd_root)

        for folder in folders:
            init_py = os.path.join(folder, "__init__.py")
            exists = os.path.exists(init_py)
            if not exists:
                with codecs.open(init_py, 'w', 'utf-8') as handle:
                    handle.flush()
                result = {
                    'path': init_py,
                    'created': not exists,
                    'diff': diff('', ''),
                    'error': None,
                }
                results.append(result)
        return results

    def format_string(self, string):
        """Format content of a file."""
        pass

    def run(self, paths):
        """Run pyformat formatter."""
        paths = list(sorted([p for p in paths]))
        add_copyright = self.config.get_value('add_copyright')
        add_header = self.config.get_value('add_header')
        add_init = self.config.get_value('add_init')

        results_init = []
        if add_init:
            results_init = self._add_missing_init_py(paths)
            new_paths = [item['path'] for item in results_init]
            paths += new_paths
            paths = list(sorted(paths))

        results_header_copyright = []
        if add_header or add_copyright:
            self._setup_headers()
            for path in paths:
                result = self._add_headers(
                    path, header=add_header, copy=add_copyright)
                if result:
                    results_header_copyright.append(result)

        for result in results_header_copyright:
            path = result['path']
            res = [item for item in results_init]

            if res:
                result['created'] = res[0]['created']

        if add_copyright or add_header:
            results = results_header_copyright
        elif add_init:
            results = results_init
        else:
            results = []
        return results


MULTI_FORMATTERS = [
    IsortFormatter,
    YapfFormatter,
    Autopep8Formatter,
]
FORMATTERS = [
    PythonFormatter,
    IsortFormatter,
    YapfFormatter,
    Autopep8Formatter,
]


def test():
    """Main local test."""
    pass


if __name__ == '__main__':
    test()
