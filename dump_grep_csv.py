# -*- coding: utf-8 -*-

import re
import sys
from moss_dump_analyzer import read_en_article_text

# Used to turn the XML output of dump_grep.py (which takes a long time
# to run) into output more typical of Unix grep (one line per
# instance, with the article name instead of file name)

# For example:
# venv/bin/python3 dump_grep.py ₤ > /tmp/pound-grep.xml
# cat /tmp/pound-grep.xml | venv/bin/python3 dump_grep_inline.py ₤ | grep -v lira | perl -pe "s/:.*//" | sort | uniq

FIND_RE = re.compile(sys.argv[1])


def grep_page(article_title, article_text):
    for article_line in article_text.splitlines():
        if FIND_RE.search(article_line):
            # Avoid print() due to possible race condition with newlines
            sys.stdout.write(f"{article_title}: {article_line}\n")


if __name__ == "__main__":
    read_en_article_text(grep_page, parallel=True)
