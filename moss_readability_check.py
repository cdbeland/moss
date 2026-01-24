# -*- coding: utf-8 -*-

import datetime
import re
import textstat
import sys
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext, ignore_tags_re


list_cleanup_re = re.compile(r"(^|\n)[ :#\*].*")
year_in_re = re.compile(r"^(\d+s?$|\d+s? BC$|\d\d+s? in )")
article_skip_list = [
    "Alfonso de Borbón y Borbón",
]
ignore_tags_more_re = re.compile("|".join([
    r"{{[Ll]ike resume",
    r"{{[Aa]dvert",
    r"{{[Ll]ong plot",
    r"{{[Cc]reate list",
    ]))


def is_prose_paragraph(paragraph_text):
    if len(paragraph_text) < 100:
        return False
    if (paragraph_text.endswith(".")
            or paragraph_text.endswith("!")
            or paragraph_text.endswith("?")
            or paragraph_text.endswith("'")
            or paragraph_text.endswith('"')):
        return True
    return False


def check_reading_level(article_title, article_text):

    if "disambiguation)" in article_title:
        return
    if article_title.startswith("Index of"):
        return
    if article_title.startswith("List of"):
        return
    if article_title.startswith("Outline of"):
        return
    if article_title.startswith("Table of"):
        return
    if article_title.startswith("Glossary of"):
        return
    if article_title.startswith("Timeline of"):
        return
    if year_in_re.match(article_title):
        return
    if article_text.startswith("#REDIRECT") or article_text.startswith("#redirect"):
        return
    if ignore_tags_re.search(article_text):
        return
    if ignore_tags_more_re.search(article_text):
        return
    if article_title in article_skip_list:
        return

    article_text = wikitext_to_plaintext(article_text)
    article_text = get_main_body_wikitext(article_text, ignore_nonprose=True)
    article_text = article_text.replace("✂", "")

    # Non-prose is out of scope for readability metrics
    paragraphs = article_text.split("\n")
    paragraphs = [para for para in paragraphs if is_prose_paragraph(para)]
    article_text = "\n".join(paragraphs)

    if len(article_text.strip()) < 1000:
        # Ratings of very short articles are unreliable.
        return

    # TODO: Replace this with a sentence length metric, which is
    # faster to calculate and easier to set an absolute threshold for.
    # article_difficulty_level = textstat.dale_chall_readability_score(article_text)

    # https://en.wikipedia.org/wiki/Flesch%E2%80%93Kincaid_readability_tests
    article_difficulty_level = textstat.flesch_reading_ease(article_text)
    # 4m10s per 10,000 single-threaded
    # article_difficulty_level = textstat.coleman_liau_index(article_text)
    # 2m47s per 10,000 single-threaded

    # Available English metrics:
    # print(textstat.flesch_reading_ease(article_text))
    # print(textstat.smog_index(article_text))
    # print(textstat.flesch_kincaid_grade(article_text))
    # print(textstat.coleman_liau_index(article_text))
    # print(textstat.dale_chall_readability_score(article_text))  # SLOW
    # print(textstat.automated_readability_index(article_text))
    # print(textstat.difficult_words(article_text))  # SLOW
    # print(textstat.linsear_write_formula(article_text))
    # print(textstat.text_standard(article_text))  # NON-NUMERIC
    # print(textstat.gunning_fog(article_text))  # SLOW

    # After consideration by the Guild of Copy Editors, we decided not
    # to bother trying to make a systematic attempt to reduce the
    # reading level of articles.  So for now we only care about
    # articles that are excessively difficult to read, which probably
    # need to be marked for cleanup.
    # if article_difficulty_level < 17:  # For Coleman-Liau
    if article_difficulty_level > 5:  # For Flesch Reading Ease
        return

    return f"* {article_difficulty_level} - [[{article_title}]]"


if __name__ == '__main__':
    print(f"Started at {datetime.datetime.now().isoformat()}", file=sys.stderr)
    read_en_article_text(check_reading_level, parallel="incremental")
    print(f"Finished at {datetime.datetime.now().isoformat()}", file=sys.stderr)
