# ciocheck
Continuum check/test suite helper


```bash
usage: ciocheck [-h] [--format] [--staged] [--profile] [--pytestqt] module

Run Continuum IO test suite.

positional arguments:
  module

optional arguments:
  -h, --help  show this help message and exit
  --format    Only run the linters and formatters not the actual tests
  --staged    Only run the linters and formatters on files added to the commit
  --profile   Profile the linter and formatter steps
  --pytestqt  If using pytestqt, qtpy is imported first to avoid qt shim issues.
```

# Example config file
Configuration is saved in a single file named `.ciocheck`

```config
# -----------------------------------------------------------------------------
# isort
# https://github.com/timothycrosley/isort#configuring-isort
# -----------------------------------------------------------------------------
[settings]
line_length = 80
known_future_library = future,pies
known_standard_library = std,std2
known_third_party = randomthirdparty
known_first_party = mylib1,mylib2
indent='    '
multi_line_output = 3
length_sort = 1

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
# PEP257
# https://pep257.readthedocs.io/en/latest/usage.html#example
# -----------------------------------------------------------------------------
[pep257]
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
based_on_style = pep8
column_limit = 79
spaces_before_comment = 2
split_before_logical_operator = true
```

# Usage

Check format only in `some_module`.

```bash
$ ciocheck some_module/ --format
```

