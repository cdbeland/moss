# -*- coding: utf-8 -*-

import re
from moss_dump_analyzer import read_en_article_text

# SLOGAN: Dearth to typos!

# TODO: Use enwiktionary-20141129-pages-articles.xml and look for
# r"=\s*English" and part-of-speech headers or whatever.  This sorts
# out the non-English words for spellcheck purposes, and also produces
# dict values for part-of-speech tagging
# {'the': 'article'}
#
# ALTERNATIVELY, use category memberships??  Cross-check these two
# lists?

# TODOs:
# * Exclude {{R from misspelling}} pages on enwiki and equivalent on wiktionary
# * Handle multi-word phrases properly, or slice up article titles?
# * Be case-sensitive (need to recover from article text due to first
#   word in article titles always being capitalized, and on the other
#   side need to detect first word in sentence or allow
#   over-capitalization but not under-capitalization)
# * Sort into dialects (American English, British English, Scottish English, etc.)
# * Support {{sic}}, reading and writing
# * Only allow 's on nouns
# * Handle final . properly for real, by detecting end-of-sentence

all_words = set()
all_titles = set()


with open("/bulk-wikipedia/enwiktionary-20141129-all-titles-in-ns0", "r") as title_list:
    for line in title_list:
        all_words.add(line.strip().lower().decode('utf8'))

with open("/bulk-wikipedia/enwiki-20141208-all-titles-in-ns0", "r") as title_list:
    for line in title_list:
        all_titles.add(line.strip().lower().decode('utf8'))


global count
global misspelled_words

misspelled_words = {}
count = 0


def dump_results():
    global misspelled_words
    misspelled_by_freq = [(value, key) for (key, value) in misspelled_words.items()]
    misspelled_by_freq = sorted(misspelled_by_freq)
    for (freq, word) in misspelled_by_freq:
        print "%s\t%s" % (freq, word.encode('utf8'))
    print "***"

possessive_re = re.compile(r"'s$")
abbr_re = re.compile(r"\.\w\.$")


def spellcheck_all_langs(article_title, article_text):
    global count
    count += 1
    for word in article_text.split(" "):
        word_orig = word.strip(" ,?!-()[]'\":;")
        word_tmp = word_orig.lower()
        if (word_tmp in all_words) or (word_tmp in all_titles):
            continue

        # Bob's
        word_tmp = possessive_re.sub("", word_tmp)

        # F.C. vs. lastwordinsentence.
        if not abbr_re.search(word_tmp):
            word_tmp = word_tmp.strip(".")

        if (word_tmp in all_words) or (word_tmp in all_titles):
            continue

        word_parts = re.split(u"–-/", word_tmp)
        if len(word_parts) > 1:
            any_bad = False
            for part in word_parts:
                if (part in all_words) or (part in all_titles):
                    pass
                else:
                    any_bad = True
            if not any_bad:
                continue

        misspelled_words[word_orig] = misspelled_words.get(word_orig, 0) + 1
        # print "MISSPELLED: %s" % word_orig.encode('utf8')
    if count % 10000 == 0:
        dump_results()


read_en_article_text(spellcheck_all_langs)
dump_results
