# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import lxml.etree
from multiprocessing import Pool
import re


# Runtime: ~1.5 hours (with a simple callback, whata, single-threaded)

DEFAULT_XML_FILE = "/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml"
DEFAULT_CSV_FILE = "/bulk-wikipedia/enwiki-articles-no-redir.csv"
PAGE_RE = re.compile(r"^.*(<page.*?</page>).*$", flags=re.MULTILINE+re.DOTALL)


def print_result(result):
    # Print from parent process to avoid race conditions
    if result:
        print(result)


def read_en_article_text(callback_function, filename=DEFAULT_XML_FILE, parallel=False):
    if not filename:
        # Necessary backstop for dump_grep_regex.py
        filename = DEFAULT_XML_FILE
    if parallel:
        with Pool(8) as pool:
            for (article_title, article_text) in page_generator(filename):
                pool.apply_async(callback_function, args=[article_title, article_text], callback=print_result)
            pool.close()
            pool.join()
    else:
        for (article_title, article_text) in page_generator(filename):
            callback_function(article_title, article_text)


def page_generator_fast(filename=DEFAULT_CSV_FILE):
    # Using formfeed as line separator so article text can have newlines.
    with open(filename, "r", newline="\r") as article_xml_file:
        for line in article_xml_file:
            (article_title, article_text) = line.split("\t", 1)
            yield (article_title, article_text)


def page_generator(filename=DEFAULT_XML_FILE):
    working_string = ""
    with open(filename, "r") as article_xml_file:
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
                yield (article_title, article_text)
