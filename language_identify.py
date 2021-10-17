# grep -P '^[IRW]' tmp-words-with-articles.txt | ../venv/bin/python3 ../language_identify.py

# W can be handled by lookup to find which Wiktionary it appears in,
# to provide a link for translators

from collections import defaultdict
import fileinput
import gcld3
from pycountry import languages
from sectionalizer import get_word


# Alternative language detection libraries
# nltk.detect
# spacy_langdetect, TextBlob, googletrans
#  https://towardsdatascience.com/4-python-libraries-to-detect-english-and-non-english-language-c82ad3efd430
# fasttext (Facebook)
#  https://amitness.com/2019/07/identify-text-language-python/
# langdetect, langid (not recommended)

lines = [line.strip() for line in fileinput.input("-")]

# https://github.com/google/cld3
google_lang_detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0,
                                                    max_num_bytes=1000)

lang_table = defaultdict(list)

for line in lines:
    word = get_word(line)
    prediction = google_lang_detector.FindLanguage(word)
    # Possibly useful: prediction.is_reliable, prediction.proportion
    lang_table[prediction.language].append((prediction.probability, word, line))


def lang_code_to_name(code):
    if code == "iw":
        code = "he"
        # ISO 639 code change for Hebrew

    script = ""
    if code.endswith("-Latn"):
        code = code[:-5]
        script = " (Latin script)"

    if len(code) == 2:
        return languages.get(alpha_2=code).name + script
    if len(code) == 3:
        return languages.get(alpha_3=code).name + script
    raise(Exception(f"Unknown code {code}"))


for (lang_code, word_tuples) in sorted(lang_table.items(),
                                       key=lambda t: len(t[1]),
                                       reverse=True):
    sorted_tuples = sorted(word_tuples, reverse=True)
    lang_name = lang_code_to_name(lang_code)
    print(f"== {lang_name} ({len(sorted_tuples)}) ==")
    for (probability, word, line) in sorted_tuples:
        print(line + f" - confidence {probability}")
