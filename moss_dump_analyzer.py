# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import datetime
import multiprocessing
import re
import sys

# Runtime: ~1.5 hours (with a simple callback, single-threaded)

DEFAULT_CSV_FILE = "/var/local/moss/bulk-wikipedia/enwiki-articles-no-redir.csv"
PAGE_RE = re.compile(r"^.*(<page.*?</page>).*$", flags=re.MULTILINE+re.DOTALL)


def print_result(result):
    # Print from parent process to avoid race conditions
    if result:
        print(result)


# which_articles selects articles by first character in the title. It
# can be "ALL", "BEFORE_A", a capital letter A through Z, or "AFTER_Z"
# (or any leading character you wish to select on)
def read_en_article_text(callback_function,
                         filename=DEFAULT_CSV_FILE,
                         parallel=False,
                         process_result_callback=print_result,
                         which_articles="ALL"):
    if not filename:
        # Necessary backstop for dump_grep_regex.py
        filename = DEFAULT_CSV_FILE
    count = 0
    if parallel:
        # Shares parent data with children without copying
        multiprocessing.set_start_method("fork")

        # If this needs more aggressive garbage collection, add
        # maxtasksperchild=10000 or something
        with multiprocessing.Pool(16) as pool:
            for (article_title, article_text) in page_generator_fast(filename, which_articles):
                result = pool.apply_async(callback_function, args=[article_title, article_text], callback=process_result_callback)
                count += 1
                if count % 25000 == 0:
                    # Avoid using all available memory; article text
                    # isn't garbage collected until the callback is
                    # complete. (Not sure if it's queued requests
                    # waiting for child processes to start them, or
                    # results from child processes waiting for the
                    # parent to service them.)
                    result.wait()
            pool.close()
            pool.join()
    else:
        for (article_title, article_text) in page_generator_fast(filename):
            """
            # For debugging performance issues
            count += 1
            if count % 100 == 0:
                print(f"Processed {count} articles - " + str(datetime.datetime.now().isoformat()),
                      file=sys.stderr)
            if count % 1001 == 0:
                exit(0)
            """
            callback_function(article_title, article_text)


def page_generator_fast(filename=DEFAULT_CSV_FILE, which_articles="ALL"):
    count = 0
    # Using formfeed as line separator so article text can have newlines.
    with open(filename, "r", newline="\r") as article_csv_file:
        for line in article_csv_file:
            count += 1
            if count % 100000 == 0:
                print(f"Queued {count} articles - " + str(datetime.datetime.now().isoformat()),
                      file=sys.stderr)
            (article_title, article_text) = line.split("\t", 1)
            if skip_article(article_title, which_articles):
                print ("Skipped {article_title}", file=sys.stderr)
                continue
            yield (article_title, article_text)


def skip_article(article_title, which_articles):
    if which_articles == "ALL":
        return False
    if which_articles == "BEFORE_A":
        if article_title[0] < "A":
            return False
        return True
    if which_articles == "AFTER_Z":
        if article_title[0] > "Z":
            return False
        return True
    if article_title[0] == which_articles:
        return False
    return True
