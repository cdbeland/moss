# -*- coding: utf-8 -*-

from collections import defaultdict
import gcld3
import re
import sys
from moss_dump_analyzer import read_en_article_text
from moss_entity_check import suppression_patterns
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext, ignore_tags_re


print("Loading dictionaries...", file=sys.stderr)

with open("/bulk-wikipedia/titles_all_wiktionaries_uniq.txt", "r") as title_list:
    ALL_WORDS = set(word.strip() for word in title_list)
with open("/bulk-wikipedia/english_words_only.txt", "r") as title_list:
    ENGLISH_WORDS = set(word.strip() for word in title_list)

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


WORD_RE = re.compile(r"[\w']+")
ROMAN_NUM_RE = re.compile(r"^[IVXLCM]+$")
GOOGLE_LANG_DETECTOR = gcld3.NNetLanguageIdentifier(min_num_bytes=0,
                                                    max_num_bytes=1000)


def find_non_english(article_title, article_text):
    if ignore_tags_re.search(article_text):
        # print("S\tSKIPPING due to known cleanup tag\t%s" % article_title, flush=True)
        return

    article_text = wikitext_to_plaintext(article_text)
    article_text = get_main_body_wikitext(article_text)
    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)
    article_text = article_text.replace("✂", " ")
    article_words_by_lang = defaultdict(list)

    word_list = [word.strip("'\n0123456789") for word in WORD_RE.findall(article_text)]
    word_list = [word for word in word_list if word]
    word_list = [word for word in word_list if not ROMAN_NUM_RE.match(word)]

    for word_mixedcase in word_list:
        if is_english_word(word_mixedcase):
            article_words_by_lang["en"].append(word_mixedcase)
        elif is_correct_word(word_mixedcase):
            if word_mixedcase == word_mixedcase.title():
                # Capitalized words are usually proper nouns; not
                # helpful for categorization
                continue
            lang_code = GOOGLE_LANG_DETECTOR.FindLanguage(word_mixedcase).language
            article_words_by_lang[lang_code].append(word_mixedcase)

    output_line = article_title
    recognized_word_count = 0
    for lang in article_words_by_lang:
        recognized_word_count += len(article_words_by_lang[lang])
    if recognized_word_count == 0:
        print(f"{article_title}\t0%\t0", flush=True)
        return

    # % non-English
    output_line += "\t" + str(100 * (recognized_word_count - len(article_words_by_lang["en"])) / recognized_word_count) + "%"
    # # non-English
    output_line += "\t" + str(recognized_word_count - len(article_words_by_lang["en"]))

    for lang in sorted(article_words_by_lang, key=lambda lang: len(article_words_by_lang[lang]), reverse=True):
        if lang == "en":
            continue
        output_line += "\t"
        # Stats for this language are too similar to overall
        # non-English stats, which are probably more accurate anyway
        # output_line += str(100 * len(article_words_by_lang[lang]) / recognized_word_count)
        # output_line += f"%\t{len(article_words_by_lang[lang])}"
        output_line += f"\t{lang}"
        output_line += "\t" + str(article_words_by_lang[lang][0:20])
        break  # Only report the most commonly detected non-English language
    print(output_line, flush=True)


if __name__ == '__main__':
    print("Starting search...", file=sys.stderr)
    read_en_article_text(find_non_english, parallel=True)
