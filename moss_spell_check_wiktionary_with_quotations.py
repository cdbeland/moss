# -*- coding: utf-8 -*-

from moss_dump_analyzer import read_en_article_text
from moss_spell_check import dump_results, tally_misspelled_words, spellcheck_all_langs_wikt

if __name__ == '__main__':
    read_en_article_text(spellcheck_all_langs_wikt(include_quotations=True),
                         filename="/var/local/moss/bulk-wikipedia/enwiktionary-articles-no-redir.csv",
                         process_result_callback=tally_misspelled_words,
                         parallel=True)
    dump_results()
