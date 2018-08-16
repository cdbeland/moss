set -e

venv/bin/flake8 *.py
venv/bin/nosetests
