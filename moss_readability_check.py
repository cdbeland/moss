# -*- coding: utf-8 -*-

import datetime
import re
import textstat
import sys
from moss_dump_analyzer import read_en_article_text
from moss_spell_check import ignore_tags_re
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext


list_cleanup_re = re.compile(r"(^|\n)[ :#\*].*")
year_in_re = re.compile(r"^(\d+s?$|\d+s? BC$|\d\d+s? in )")


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
    if year_in_re.match(article_title):
        return
    if article_text.startswith("#REDIRECT") or article_text.startswith("# REDIRECT"):
        return
    if ignore_tags_re.search(article_text):
        return

    article_text = wikitext_to_plaintext(article_text)
    article_text = get_main_body_wikitext(article_text, strong=True)
    article_text = article_text.replace("✂", "")

    # Non-prose is out of scope for readability metrics
    paragraphs = article_text.split("\n")
    paragraphs = [para for para in paragraphs if is_prose_paragraph(para)]
    article_text = "\n".join(paragraphs)

    if not article_text.strip():
        return
    if len(article_text) < 1000:
        # Ratings of very short articles are unreliable.
        return

    # TODO: Replace this with a sentence length metric, which is
    # faster to calculate and easier to set an absolute threshold for.
    article_difficulty_level = textstat.dale_chall_readability_score(article_text)

    # After consideration by the Guild of Copy Editors, we decided not
    # to bother trying to make a systematic attempt to reduce the
    # reading level of articles.  So for now we only care about
    # articles that are excessively high on the scale, which probably
    # need to be marked for cleanup.
    if article_difficulty_level < 12:
        return

    print(f"* {article_difficulty_level} - [[{article_title}]]")


if __name__ == '__main__':
    print(f"Started at {datetime.datetime.now().isoformat()}", file=sys.stderr)
    read_en_article_text(check_reading_level)
    print(f"Finished at {datetime.datetime.now().isoformat()}", file=sys.stderr)
