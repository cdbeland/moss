# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import lxml.etree
from multiprocessing import Pool
import re


# Runtime: ~1.5 hours (with a simple callback, whata, single-threaded)


def print_result(result):
    if result:
        print(result)


def read_en_article_text(callback_function, filename="", parallel=False):
    working_string = ""

    if not filename:
        filename = "/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml"
    with open(filename, "r") as article_xml_file:
        with Pool(8) as pool:
            for line in article_xml_file:
                working_string += line
                if line == "  </page>\n":
                    working_string = re.sub(r"^.*(<page.*?</page>).*$", r"\1", working_string, flags=re.MULTILINE+re.DOTALL)
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
                    if parallel:
                        pool.apply_async(callback_function, args=[article_title, article_text], callback=print_result)
                    else:
                        callback_function(article_title, article_text)
