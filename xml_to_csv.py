# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import lxml.etree
import re
import sys


# Runtime: ~1.5 hours (with a simple callback, whata, single-threaded)

DEFAULT_XML_FILE = "/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml"
PAGE_RE = re.compile(r"^.*(<page.*?</page>).*$", flags=re.MULTILINE+re.DOTALL)
NEWLINE_RE = re.compile(r"\n")

if __name__ == '__main__':
    working_string = ""
    with open(DEFAULT_XML_FILE, "r") as article_xml_file:
        for line in article_xml_file:
            working_string += line
            if line == "  </page>\n":
                working_string = PAGE_RE.sub(r"\1", working_string)
                root_element = lxml.etree.fromstring(working_string)
                working_string = ""

                namespace = root_element.findtext('ns')
                if namespace != '0':
                    # Page is not an article
                    continue

                redirect_target = root_element.find('redirect')
                if redirect_target is not None:
                    # Article is redirect; skip it for now
                    continue

                article_title = root_element.findtext('title')
                article_text = root_element.findtext('.//text')
                sys.stdout.write(f"{article_title}\t{article_text}\r")
                # Using linefeed as line separator to avoid
                # conflicting with newlines in article_text
