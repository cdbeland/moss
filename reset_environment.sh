rm -rf venv/
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
venv/bin/python3 -c "import nltk; nltk.download('punkt')"
venv/bin/python3 -c "import nltk; nltk.download('averaged_perceptron_tagger')"
