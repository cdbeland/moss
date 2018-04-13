# -*- coding: utf-8 -*-

from time import sleep
import re
from moss_dump_analyzer import read_en_article_text
from wikitext_util import remove_structure_nested, wikitext_to_plaintext
from spell import is_word_spelled_correctly

# Run time for commit e317dabb: 3 hours

# SLOGAN: Dearth to typos!

# * Do a separate run for redirects matching
#   "{{[\w]+(misspelling|incorrect)[\w* ]+}}" pages on enwiki and
#   prepare batch edits for these
# * Is there an equivalent for misspellings on wiktionary?

# TODO: Use enwiktionary-20141129-pages-articles.xml and look for
# r"=\s*English" and part-of-speech headers or whatever.  This sorts
# out the non-English words for spellcheck purposes, and also produces
# dict values for part-of-speech tagging
# {'the': 'article'}
#
# ALTERNATIVELY, use category memberships??  Cross-check these two
# lists?

# TODOs:
# * Handle multi-word phrases properly, or slice up article titles?
# * Be case-sensitive (need to recover from article text due to first
#   word in article titles always being capitalized, and on the other
#   side need to detect first word in sentence or allow
#   over-capitalization but not under-capitalization)
# * Sort into dialects (American English, British English, Scottish English, etc.)
# * Support {{sic}}, reading and writing
# * Only allow 's on nouns
# * Handle final . properly for real, by detecting end-of-sentence

# * Monitor recent changes (see [[Wikipedia:Recent changes
#   patrol#Monitoring]]) and drop notes on editor talk pages notifying
#   them they may have made a spelling error.  The algorithm needs to
#   be pretty solid.

global article_count
global misspelled_words

misspelled_words = {}
# {'misspellling': (2, ['article1', 'article2'])}

article_count = 0


def dump_results():
    global misspelled_words
    misspelled_by_freq = [(value[0], key, value[1]) for (key, value) in misspelled_words.items()]
    misspelled_by_freq = sorted(misspelled_by_freq)
    for (freq, word, article_list) in misspelled_by_freq:
        uniq_list = list(set(article_list))
        uniq_list.sort()
        uniq_string = ""
        if uniq_list:
            uniq_string = u"[[" + u"]], [[".join(uniq_list) + u"]]"
        output_string = u"* %s - [[wikt:%s]] - %s" % (unicode(freq), word, uniq_string)
        print output_string.encode('utf8')


def spellcheck_all_langs(article_title, article_text):
    # article_text is Unicode (UTF-32) thanks to lxml

    global article_count

    # if article_title != "Anarchism":
    #     return

    article_text = wikitext_to_plaintext(article_text)
    ## Debug article_text processing:
    # print article_text.encode('utf8')
    # sleep(1)
    # return

    # TODO: Handle }} inside <nowiki>
    if "}}" in article_text:
        print "!\tABORTING PROCESSING\t%s" % article_title.encode('utf8')
        print "!\t%s" % article_text.encode('utf8')
        return

    article_count += 1
    article_oops_list = []
    for word in word_tokenize(article_text):
        if is_word_spelled_correctly(word):
            continue

        # Word is misspelled, so...

        # Index by misspelled word of article titles
        (freq, existing_list) = misspelled_words.get(word_lower, (0, []))
        existing_list.append(article_title)
        misspelled_words[word_lower] = (len(existing_list), existing_list)

        # Index by article of mispelled words
        article_oops_list.append(word_mixedcase)

    article_oops_string = u" ".join(article_oops_list)
    print "@\t%s\t%s\t%s" % (len(article_oops_list), article_title.encode('utf8'), article_oops_string.encode('utf8'))
    # if article_count % 100000 == 0:
    #     dump_results()


read_en_article_text(spellcheck_all_langs)
dump_results()


# TODO: Experiment with using NLTK and other grammar engines to parse
# wikitext

