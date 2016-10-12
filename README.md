[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/ContinuumIO/ciocheck/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/ContinuumIO/ciocheck/?branch=master)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ccc68df612024e7e8fd386ffe2252a95/badge.svg)](https://www.quantifiedcode.com/app/project/ccc68df612024e7e8fd386ffe2252a95)

# ciocheck
Continuum Analytics linter, formater and test suite helper.

# How does ciocheck work?

It leverages on the different available linting, formatting and testing tools 
availbale for Python, including:
- [pytest-cov](http://pytest-cov.readthedocs.io/en/latest/)  (Run code [coverage](http://coverage.readthedocs.io/en/latest) with the [pytest](http://pytest.org/latest/) library)
- [Flake8](http://flake8.readthedocs.io/en/latest/)  (Style check based on [pep8](https://github.com/PyCQA/pycodestyle) and [pyflakes](https://github.com/pyflakes/pyflakes))
- [pydocstyle](https://pydocstyle.readthedocs.io/en/latest/)  (Style check docstrings)
- [pep8](https://github.com/PyCQA/pycodestyle)  (Style check docstrings)
- [YAPF](https://github.com/google/yapf)  (Formatter for code)
- [isort](https://github.com/timothycrosley/isort/)  (Formatter for import statements)

Plus some extra goodies, like:
- Single file configuration for all the tools (still working on eliminating 
  redundancy)
- Auto addition of `__init__.py` files
- Auto addition of custom encoding and copyright header files

# Why ciocheck?
There are many post commit tools out there for testing code quality, but the
idea of ciocheck is to perform check before a commit-push.

# Example config file
Configuration is saved in a single file named `.ciocheck`

```ini
# -----------------------------------------------------------------------------
# ciocheck
# https://github.com/ContinuumIO/ciocheck
# -----------------------------------------------------------------------------
[ciocheck]
branch = origin/master
diff_mode = commited
file_mode = lines
#check = pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest
#enforce = pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest
check = pyformat

# Python (pyformat)
add_copyright = true
add_header = true
add_init = true

# -----------------------------------------------------------------------------
# Flake 8
# http://flake8.readthedocs.io/en/latest/config.html
# -----------------------------------------------------------------------------
[flake8]
exclude = */tests/*
ignore = E126
max-line-length = 79
max-complexity = 64

# -----------------------------------------------------------------------------
# pep8
# 
# -----------------------------------------------------------------------------
[pep8]
exclude = */tests/*
ignore = E126
max-line-length = 79

# -----------------------------------------------------------------------------
# pydocstyle
# http://www.pydocstyle.org/en/latest/usage.html#example
# -----------------------------------------------------------------------------
[pydocstyle]
add-ignore = D203
inherit = false

# -----------------------------------------------------------------------------
# pylint
# https://pylint.readthedocs.io/en/latest/
# -----------------------------------------------------------------------------
#[pylint:messages]


# -----------------------------------------------------------------------------
# isort
# https://github.com/timothycrosley/isort/wiki/isort-Settings
# -----------------------------------------------------------------------------
[isort]
from_first = true
import_heading_stdlib = Standard library imports
import_heading_firstparty = Local imports
import_heading_thirdparty = Third party imports
indent = '    '
known_first_party = anaconda_navigator
known_third_party = six,_license,pytestqt
line_length = 79
sections = FUTURE,STDLIB,THIRDPARTY,FIRSTPARTY,LOCALFOLDER

# -----------------------------------------------------------------------------
# YAPF
# https://github.com/google/yapf#formatting-style
# -----------------------------------------------------------------------------
[yapf:style]
based_on_style = pep8
column_limit = 79
spaces_before_comment = 2

# -----------------------------------------------------------------------------
# Coverage
# http://coverage.readthedocs.io/en/latest/config.html
# -----------------------------------------------------------------------------
[coverage:run]
omit =
    */tests/*
    */Navigator.app/*

[coverage:report]
fail_under = 0
show_missing = true
skip_covered = true
exclude_lines =
    # Have to re-enable the standard pragma
    pragma: no cover
    # Ignore local file testing
    def test():
    if __name__ == .__main__.:

# -----------------------------------------------------------------------------
# pytest
# http://doc.pytest.org/en/latest/usage.html
# -----------------------------------------------------------------------------
[pytest]
addopts = -rfew --durations=10
python_functions = test_*
```

# Copyright and encoding headers

TODO

# Usage

```bash
usage: ciocheck [-h] [--file-mode {lines,files,all}]
                [--diff-mode {commited,staged,unstaged}] [--branch BRANCH]
                [--check {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest}
                [--enforce {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest}
                folders_or_files [folders_or_files ...]

Run Continuum IO test suite.

positional arguments:
  folders_or_files      folders or files to analize

optional arguments:
  -h, --help            show this help message and exit
  --file-mode {lines,files,all}
                        Define if the tool should run on modified lines of
                        files (default), modified files or all files
  --diff-mode {commited,staged,unstaged}
                        Define diff mode. Default mode is commited.
  --branch BRANCH       Define branch to compare to. Default branch is
                        "origin/master"
  --check {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest}
                        Select tools to run. Default is "pep8"
  --enforce {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,pytest}
                        Select tools to enforce. Enforced tools will fail if a
                        result is obtained. Default is none.
```

Check format of imports only in `some_module`.

```bash
$ ciocheck some_module/
```

