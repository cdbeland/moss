# -*- coding: utf-8 -*-

import re
import sys
from moss_dump_analyzer import read_en_article_text

# Faster alternative to dump_grep.py + dump_grep_inline.py, which
# greps the CSV version of the database dump directly.

# This script is for manual use; other scripts should use
# moss_check_style_by_line.py instead, to reduce overhead of loading
# article text for lots of different checks.

# For example:
# venv/bin/python3 dump_grep_csv.py ₤ | grep -v lira | perl -pe "s/:.*//" | sort | uniq

FIND_RE = re.compile(sys.argv[1])


def grep_page(article_title, article_text):
    for article_line in article_text.splitlines():
        if FIND_RE.search(article_line):
            # Avoid print() due to possible race condition with newlines
            sys.stdout.write(f"{article_title}: {article_line}\n")


if __name__ == "__main__":
    read_en_article_text(grep_page, parallel="incremental")
