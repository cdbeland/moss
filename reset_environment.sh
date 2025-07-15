#!/usr/bin/bash

set -e

rm -rf venv/
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install wheel
venv/bin/pip install -r requirements.txt
venv/bin/python -c "import nltk; nltk.download('punkt')"
venv/bin/python -c "import nltk; nltk.download('punkt_tab')"
venv/bin/python -c "import nltk; nltk.download('averaged_perceptron_tagger')"
