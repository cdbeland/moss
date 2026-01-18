# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import datetime
import multiprocessing
import re
import sys

# Runtime: ~1.5 hours (with a simple callback, single-threaded)

CPU_COUNT = multiprocessing.cpu_count()
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
    if parallel:
        # Shares parent data with children without copying
        multiprocessing.set_start_method("fork")
        if parallel is True:
            # Processes results all at once. May use a lot of memory
            # if there are a lot of results, and will NOT output
            # incrementally. Faster than parallel="incremental".
            #
            # callback_function will get only one argument: (article_title, article_text)

            # If more aggressive garbage collection is needed for
            # children, try e.g. maxtasksperchild=50000 for Pool()
            with multiprocessing.Pool(CPU_COUNT) as pool:
                results = pool.imap(callback_function,
                                    page_generator_fast(filename, which_articles),
                                    chunksize=10000)
                pool.close()
                pool.join()
                [process_result_callback(result) for result in results]
        elif parallel == "incremental":
            # Processes results incrementally, before processing too
            # many. Slower but uses less memory than parallel=True if
            # results are large.
            #
            # callback_function will get two arguments: article_title, article_text
            with multiprocessing.Pool(CPU_COUNT) as pool:
                count = 0
                for (article_title, article_text) in page_generator_fast(filename, which_articles):
                    result = pool.apply_async(callback_function,
                                              args=[article_title, article_text],
                                              callback=process_result_callback,
                                              error_callback=parallel_error)
                    count += 1
                    if count % 25000 == 0:
                        # Avoid using all available memory; article text
                        # isn't garbage collected until the callback is
                        # complete. (Not sure if it's queued requests
                        # waiting for child processes to start them, or
                        # results from child processes waiting for the
                        # parent to service them.)
                        result.wait()
    else:
        result = [callback_function(article_title, article_text)
                  for (article_title, article_text)
                  in page_generator_fast(filename)]
        process_result_callback(result)


def parallel_error(error):
    print(error, file=sys.stderr)
    raise Exception("ERROR IN CHILD PROCESS")


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
                print("Skipped {article_title}", file=sys.stderr)
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
