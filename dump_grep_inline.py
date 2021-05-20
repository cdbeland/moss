# -*- coding: utf-8 -*-

import lxml.etree
from multiprocessing import Pool
import re
import sys

# Used to turn the XML output of dump_grep.py (which takes a long time
# to run) into output more typical of Unix grep (one line per
# instance, with the article name instead of file name)

# For example:
# venv/bin/python3 dump_grep.py ₤ > /tmp/pound-grep.xml
# cat /tmp/pound-grep.xml | venv/bin/python3 dump_grep_inline.py ₤ | grep -v lira | perl -pe "s/:.*//" | sort | uniq

FIND_RE = re.compile(sys.argv[1])


def process_article(article_title, article_text):
    for article_line in article_text.splitlines():
        if FIND_RE.search(article_line):
            sys.stdout.write(f"{article_title}: {article_line}\n")


def grep_dump_inline():
    working_string = ""

    with Pool(8) as pool:
        for line in sys.stdin:
            working_string += line
            if line == "  </page>\n":
                working_string = re.sub(r"^.*(<page.*?</page>).*$", r"\1", working_string, flags=re.MULTILINE+re.DOTALL)
                root_element = lxml.etree.fromstring(working_string)
                working_string = ""
    
                article_title = root_element.findtext('title')
                article_text = root_element.findtext('.//text')
                pool.apply_async(process_article,
                                 [article_title, article_text])
        pool.close()
        pool.join()


if __name__ == "__main__":
    grep_dump_inline()
