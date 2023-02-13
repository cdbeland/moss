# -*- coding: utf-8 -*-

# USAGE: run_not_english.sh
# Run time: About 60-70 minutes

from collections import defaultdict
import gcld3
import re
import sys
from moss_dump_analyzer import read_en_article_text
from moss_entity_check import suppression_patterns
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext, ignore_tags_re

# Set this to false if you want to find individual words that need {{lang}}
ONLY_LONG_SEGMENTS = True

# ---

WORD_RE = re.compile(r"[\w']+")
ACRONYM_RE = re.compile(r"^[A-Z]+$")
NUMBER_INSIDE_RE = re.compile(r"[0-9]")
ROMAN_NUM_RE = re.compile(r"^[IVXLCM]+$")
GOOGLE_LANG_DETECTOR = gcld3.NNetLanguageIdentifier(min_num_bytes=0,
                                                    max_num_bytes=1000)

print("Loading dictionaries...", file=sys.stderr)

with open("/bulk-wikipedia/titles_all_wiktionaries_uniq.txt", "r") as title_list:
    ALL_WORDS = set(word.strip() for word in title_list)
with open("/bulk-wikipedia/english_words_only.txt", "r") as title_list:
    ENGLISH_WORDS = set(word.strip() for word in title_list)

SPECIES_WORDS = list()
for filename in [
        "/bulk-wikipedia/specieswiki-latest-all-titles-in-ns0",
        "/bulk-wikipedia/Wikispecies:Requested_articles",
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.replace("_", " ").strip()
            SPECIES_WORDS.extend(list(WORD_RE.findall(line)))
SPECIES_WORDS = set(SPECIES_WORDS)
with open('/bulk-wikipedia/Wikispecies:Requested_articles', 'r') as requested_species_file:
    REQUESTED_SPECIES_HTML = requested_species_file.read()

print("Done loading.", file=sys.stderr)


def is_correct_word(word):
    if word in ALL_WORDS:
        return True
    # if word.lower() in ALL_WORDS:
    #     return True
    return False


def is_english_word(word):
    if word in ENGLISH_WORDS:
        return True
    word_lower = word.lower()
    if word_lower in ENGLISH_WORDS:
        return True
    if word.endswith("'s"):
        if word[0:-2] in ENGLISH_WORDS:
            return True
        if word_lower[0:-2] in ENGLISH_WORDS:
            return True
    return False


def find_non_english(article_title, article_text):
    if ignore_tags_re.search(article_text):
        return

    request_search_string_en = 'title="en:%s"' % article_title
    request_search_string_w = 'title="w:%s"' % article_title
    if request_search_string_en in REQUESTED_SPECIES_HTML or request_search_string_w in REQUESTED_SPECIES_HTML:
        return

    article_text = wikitext_to_plaintext(article_text)
    article_text = get_main_body_wikitext(article_text)
    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)
    article_text = article_text.replace("✂", " ")
    article_words_by_lang = defaultdict(list)

    paragraphs = article_text.split("\n")
    for paragraph_text in paragraphs:
        paragraph_words_by_lang = defaultdict(list)
        word_list = [word.strip("'\n0123456789") for word in WORD_RE.findall(paragraph_text)]
        word_list = [word for word in word_list if word]
        word_list = [word for word in word_list if not ROMAN_NUM_RE.match(word)]
        if len(word_list) < 20:
            if ONLY_LONG_SEGMENTS:
                continue

        non_english_count = 0
        for word_mixedcase in word_list:
            if len(word_mixedcase) <= 3:
                # Not long enough for the language classifier to
                # really work on. This also excludes the use of a lot
                # of Greek variables in STEM articles.
                continue

            if is_english_word(word_mixedcase) or word_mixedcase in SPECIES_WORDS:
                paragraph_words_by_lang["en"].append(word_mixedcase)
                continue

            if word_mixedcase[0].upper() == word_mixedcase[0]:
                # Capitalized words are usually proper nouns; not helpful
                # for categorization
                continue
            if ACRONYM_RE.match(word_mixedcase):
                continue
            if NUMBER_INSIDE_RE.search(word_mixedcase):
                # These are pretty much always science terms like genes
                continue

            lang_code = GOOGLE_LANG_DETECTOR.FindLanguage(word_mixedcase).language
            if not is_correct_word(word_mixedcase):
                lang_code = lang_code + "?"
            non_english_count += 1
            paragraph_words_by_lang[lang_code].append(word_mixedcase)

        if non_english_count == 0:
            continue
        if ONLY_LONG_SEGMENTS:
            english_word_count = len(paragraph_words_by_lang["en"])
            if english_word_count > len(word_list) / 3:
                continue
            if non_english_count < english_word_count / 2:
                continue

        for lang in paragraph_words_by_lang:
            article_words_by_lang[lang].extend(paragraph_words_by_lang[lang])

    output_line = article_title
    recognized_word_count = 0
    for lang in article_words_by_lang:
        recognized_word_count += len(article_words_by_lang[lang])
    if recognized_word_count == 0:
        return

    non_english_count = recognized_word_count - len(article_words_by_lang["en"])
    if non_english_count == 0:
        return
    output_line += f"\t{non_english_count}"

    article_word_count = len(article_text.split(" "))
    non_english_percent = round(100 * non_english_count / article_word_count, 2)
    output_line += f"\t{non_english_percent}%"

    for lang in sorted(article_words_by_lang, key=lambda lang: len(article_words_by_lang[lang]), reverse=True):
        if lang == "en":
            continue
        output_line += f"\t{lang}"
        output_line += "\t" + ", ".join(article_words_by_lang[lang][0:10])
        break  # Only report examples from the most commonly detected non-English language

    print(output_line, flush=True)


if __name__ == '__main__':
    print("Starting search...", file=sys.stderr)
    read_en_article_text(find_non_english, parallel=True)
