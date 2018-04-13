set -e

venv/bin/flake8 *.py
venv/bin/python3 unit_tests.py
