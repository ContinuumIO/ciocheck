# Ciocheck

## Build Status

[![Build Status](https://travis-ci.org/ContinuumIO/ciocheck.svg?branch=master)](https://travis-ci.org/ContinuumIO/ciocheck)
[![Build status](https://ci.appveyor.com/api/projects/status/ylipp3kgn5t4hpdw?svg=true)](https://ci.appveyor.com/project/ContinuumAnalytics/ciocheck)
[![CircleCI](https://circleci.com/gh/ContinuumIO/ciocheck/tree/master.svg?style=shield)](https://circleci.com/gh/ContinuumIO/ciocheck/tree/master)
[![Coverage Status](https://coveralls.io/repos/github/ContinuumIO/ciocheck/badge.svg?branch=master)](https://coveralls.io/github/ContinuumIO/ciocheck?branch=master)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/ccc68df612024e7e8fd386ffe2252a95/badge.svg)](https://www.quantifiedcode.com/app/project/ccc68df612024e7e8fd386ffe2252a95)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/ContinuumIO/ciocheck/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/ContinuumIO/ciocheck/?branch=master)

## Description
Continuum Analytics linter, formatter and test suite helper.

## How does ciocheck work?

It leverages on the different available linting, formatting and testing tools 
availbale for Python (but other languages could also be added), including:

### Linters
- [pep8](https://pep8.readthedocs.io/)  (Style check for code)
- [pydocstyle](https://pydocstyle.readthedocs.io/en/latest/)  (Style check for docstrings)
- [flake8](https://flake8.readthedocs.io/en/latest/)  (Style check based on [pep8](https://pep8.readthedocs.io/) and [pyflakes](https://github.com/pyflakes/pyflakes))
- [pylint](https://pylint.readthedocs.io/)  (Code quality check)

### Formatters
- [autopep8](https://github.com/hhatto/autopep8)  (Code formatter)
- [yapf](https://github.com/google/yapf)  (Code formatter)
- [isort](https://github.com/timothycrosley/isort/)  (Import statements formatter)

### Test and coverage
- [pytest-cov](https://pytest-cov.readthedocs.io/en/latest/)  (Run code [coverage](https://coverage.readthedocs.io/en/latest) with the [pytest](http://pytest.org/latest/) library)

Plus some extra goodies, like:
- Single file configuration for all the tools (still working on eliminating 
  redundancy)
- Auto addition of `__init__.py` files for folders containing python files
- Auto addition of custom encoding and copyright header for python files
- Run the tools for staged/unstaged or committed diffs only (git support only)
- Run the tools for modified lines, modified files or all files.

## Why ciocheck?
There are many post commit tools out there for testing code quality, but the
idea of ciocheck is to perform checks and autoformating before a commit-push,
and to use it as part of the CI system, so that if any of the enforced checks
does not comply, CI will fail.

## Example config file
Configuration is saved in a single file named `.ciocheck`

```ini
# -----------------------------------------------------------------------------
# ciocheck
# https://github.com/ContinuumIO/ciocheck
# -----------------------------------------------------------------------------
[ciocheck]
inherit_config = .ciocheck
branch = origin/master
diff_mode = committed
file_mode = lines
check = pep8,pydocstyle,flake8,pylint,pyformat,isort,autopep8,yapf,coverage,pytest
enforce = pep8,pydocstyle,flake8,pylint,pyformat,isort,autopep8,yapf,coverage,pytest

# Python (pyformat)
header = # -*- coding: utf-8 -*-
copyright_file = .ciocopyright
add_copyright = true
add_header = true
add_init = true

# -----------------------------------------------------------------------------
# pep8
# https://pep8.readthedocs.io/en/release-1.7.x/intro.html#configuration
# -----------------------------------------------------------------------------
[pep8]
exclude = */tests/*
ignore = E126,
max-line-length = 79

# -----------------------------------------------------------------------------
# pydocstyle
# http://www.pydocstyle.org/en/latest/usage.html#example
# -----------------------------------------------------------------------------
[pydocstyle]
add-ignore = D203,
inherit = false

# -----------------------------------------------------------------------------
# Flake 8
# https://flake8.readthedocs.io/en/latest/user/configuration.html
# -----------------------------------------------------------------------------
[flake8]
exclude = */tests/*
ignore = E126,
max-line-length = 79
max-complexity = 64

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
known_first_party = ciocheck
known_third_party = six,pytest,autopep8,yapf,pylint
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
# autopep8
# https://pep8.readthedocs.io/en/latest/intro.html#configuration
# -----------------------------------------------------------------------------
[autopep8]
exclude = */tests/*
ignore = E126,
max-line-length = 99
aggressive = 0

# -----------------------------------------------------------------------------
# Coverage
# https://coverage.readthedocs.io/en/latest/config.html
# -----------------------------------------------------------------------------
[coverage:run]
omit =
    */tests/*

[coverage:report]
fail_under = 0
show_missing = true
skip_covered = true
exclude_lines =
    pragma: no cover
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

## Usage

```text
usage: ciocheck [-h] [--disable-formatters] [--disable-linters]
                [--disable-tests] [--file-mode {lines,files,all}]
                [--diff-mode {committed,staged,unstaged}] [--branch BRANCH]
                [--check {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,autopep8,coverage,pytest}
                [--enforce {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,autopep8,coverage,pytest}
                [--config CONFIG_FILE]
                folders [folders ...]

Run Continuum Analytics test suite.

positional arguments:
  folder                     Folder to analize. Use from repo root.'

optional arguments:
  --help, -h                 Show this help message and exit

  --disable-formatters, -df  Skip all configured formatters

  --disable-linters, -dl     Skip all configured linters

  --disable-tests, -dt       Skip running tests

  --file-mode, -fm           {lines,files,all}
                             Define if the tool should run on modified lines of
                             files (default), modified files or all files

  --diff-mode, -dm           {committed,staged,unstaged}
                             Define diff mode. Default mode is committed.

  --branch, -b BRANCH        Define branch to compare to. Default branch is
                             "origin/master"

  --check, -c                {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,autopep8,coverage,pytest}
                             Select tools to run. Default is "pep8"

  --enforce, -e              {pep8,pydocstyle,flake8,pylint,pyformat,isort,yapf,autopep8,coverage,pytest}
                             Select tools to enforce. Enforced tools will fail if a
                             result is obtained. Default is none.

  --config, -cf CONFIG_FILE  Select a config file to use. Default is none.

```

Check format of imports only in `some_module`.

Use ciocheck from the root of the git repo (for now...).

```bash
$ ciocheck some_module/
```

## Installation

```bash
$ conda install ciocheck -c conda-forge
```

## For development

```bash
$ conda install ciocheck -c conda-forge
$ python setup.py develop
```
