# -*- coding: utf-8 -*-

# Usage:
#  cat enwiki-latest-pages-articles-multistream.xml | venv/bin/python3 xml_to_csv.py enwiki
#
# This script will create 2 CSV files (one with articles and one with
# redirects) named starting with the specified base name.

# Files come from:
#  http://dumps.wikimedia.org/backup-index.html
# XML format info:
#  http://meta.wikimedia.org/wiki/Data_dumps

import lxml.etree
import re
import sys

PAGE_RE = re.compile(r"^.*(<page.*?</page>).*$", flags=re.MULTILINE+re.DOTALL)
NEWLINE_RE = re.compile(r"\n")

if __name__ == '__main__':
    base_name = sys.argv[1]
    if not base_name:
        print("NO BASE NAME SPECIFIED")
        exit(1)

    working_string = ""
    article_file = open(f"{base_name}-articles-no-redir.csv", "w")
    redirect_file = open(f"{base_name}-redirects.csv", "w")

    for line in sys.stdin:
        working_string += line
        if line == "  </page>\n":
            working_string = PAGE_RE.sub(r"\1", working_string)
            root_element = lxml.etree.fromstring(working_string)
            working_string = ""

            namespace = root_element.findtext('ns')
            if namespace != '0':
                # Page is not an article
                continue

            article_title = root_element.findtext('title')
            redirect_element = root_element.find('redirect')
            if redirect_element is not None:
                redirect_target = redirect_element.get("title")
                if not redirect_target:
                    raise Exception(f"{article_title}: missing redirect target")
                print(f"{article_title}\t{redirect_target}", file=redirect_file)
            else:
                article_text = root_element.findtext('.//text')
                article_file.write(f"{article_title}\t{article_text}\r")
                # Using linefeed as line separator to avoid
                # conflicting with newlines in article_text
