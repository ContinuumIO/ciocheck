# ciocheck
Continuum check/test suite helper.

# How does ciocheck work?

It leverages on the different available linting, formatting and testing tools 
availbale for Python, including:
- [pytest-cov](http://pytest-cov.readthedocs.io/en/latest/)  (Run code [coverage](http://coverage.readthedocs.io/en/latest) with the [pytest](http://pytest.org/latest/) library)
- [Flake8](http://flake8.readthedocs.io/en/latest/)  (Style check based on [pep8](https://github.com/PyCQA/pycodestyle) and [pyflakes](https://github.com/pyflakes/pyflakes))
- [pydocstyle](https://pydocstyle.readthedocs.io/en/latest/)  (Style check docstrings)
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
# isort
# https://github.com/timothycrosley/isort/wiki/isort-Settings
# -----------------------------------------------------------------------------
[settings]
from_first = true
import_heading_stdlib = Standard library imports
import_heading_firstparty = Local imports
import_heading_thirdparty = Third party imports
indent='    '
line_length = 79
sections=FUTURE,STDLIB,THIRDPARTY,FIRSTPARTY,LOCALFOLDER

# -----------------------------------------------------------------------------
# Flake 8
# http://flake8.readthedocs.io/en/latest/config.html
# -----------------------------------------------------------------------------
[flake8]
exclude = tests/*
ignore = E126,E401
max-line-length = 79
max-complexity = 10

# -----------------------------------------------------------------------------
# pydocstyle
# https://pydocstyle.readthedocs.io/en/latest/usage.html#example
# -----------------------------------------------------------------------------
[pydocstyle]
add-ignore = D203
inherit = false

# -----------------------------------------------------------------------------
# Coverage RC to control coverage.py
# http://coverage.readthedocs.io/en/latest/config.html
# -----------------------------------------------------------------------------
[run]
omit = tests/*

[report]
fail_under = 100
show_missing = true
skip_covered = true

[html]
directory = coverage_html_report

# -----------------------------------------------------------------------------
# YAPF
# https://github.com/google/yapf#formatting-style
# -----------------------------------------------------------------------------
[style]
column_limit = 79
spaces_before_comment = 2
```

# Copyright and encoding headers

TODO

# Usage

```bash
usage: ciocheck [-h] [--format-imports] [--format-code] [--staged] [--profile]
                [--add-init] [--add-headers] [--test]
                folder_or_file

Run Continuum IO test suite.

positional arguments:
  folder_or_file    module (folder) or file to analize

optional arguments:
  -h, --help        show this help message and exit
  --format-imports  Run isort to format python import statements
  --format-code     Run the yapf code formatter
  --staged          Run the options on all python files
  --profile         Profile the linter and formatter steps
  --add-init        Add missing __init__.py files
  --add-headers     Add encoding and copyright headers
  --test            Run pytest

```

Check format of imports only in `some_module`.

```bash
$ ciocheck some_module/ --format-imports
```

