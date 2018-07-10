# -*- coding: utf-8 -*-

import nltk
import re
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext
from spell import is_word_spelled_correctly

# TO CHECK:
# * transpress, literaturii dropped from common misspellings
# TODO:
# * \xXX in article titles in tmp-output.txt
# ', -, * in words in post-longest-shortest-misspelled-words.txt
# * Contractions in tmp-output.txt being truncated
# * ''xxx in words in post-articles-with-single-typo2.txt
# * ''whatido''—hosted by Robert Melnichuck, based on a ''100 Huntley Street'' segment. This program is no longer in production.
# * Suppress broken table parses and HTML words
# * &fnof; showing up as "fnof" commonly misspelled word, and CSS colors
# * "... find all" not necessary in post-least-common-misspellings.txt
# * Auto-suppress words in links from https://species.wikimedia.org/wiki/Wikispecies:Requested_articles#From_Wikipedia
# * Put Suppress direct quotations on a different channel?
#   (verifying them takes more effort)
# * {{spaced endash}} and friends (subst: all instances?)
#   https://en.wikipedia.org/wiki/Category:Wikipedia_character-substitution_templates
# * tmp-output.txt:* 24 - [[wikt:ation]] - [[1772 in poetry]] ([[attest]]ation)

# TODO LONG TERM:
# * Suppress items on
#   https://en.wiktionary.org/wiki/Category:English_misspellings from
#   the whitelist (maybe conditionally, if that is also a correct
#   spelling of some other word)
#   (suggested by User:-sche)
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
        output_string = u"* %s - [[wikt:%s]] - %s" % (freq, word, uniq_string)
        print(output_string)


move_re = re.compile(r"{{\s*(copy|move) to \w+\s*}}", flags=re.I)
ignore_sections_re = re.compile(r"(==\s*External links\s*==|==\s*References\s*==|==\s*Bibliography\s*==|==\s*Further reading\s*==|==\s*Sources\s*==).*?$", flags=re.M & re.I)

def spellcheck_all_langs(article_title, article_text):
    global article_count

    if move_re.search(article_text):
        print("!\tSKIPPING (copy/move to other project)\t%s" % article_title)

    article_text = wikitext_to_plaintext(article_text)

    # TODO: Get smarter about these sections.  But for now, ignore
    # them, since they are full of proper nouns and URL words.
    article_text = ignore_sections_re.sub("", article_text)

    # TODO: Handle }} inside <nowiki>
    if "}}" in article_text:
        print("!\tABORTING PROCESSING\t%s" % article_title)
        print("!\t%s" % article_text)
        return

    article_count += 1
    article_oops_list = []
    for word_mixedcase in nltk.word_tokenize(article_text):
        if is_word_spelled_correctly(word_mixedcase):
            continue

        # Word is misspelled, so...
        word_lower = word_mixedcase.lower()

        # Index by misspelled word of article titles
        (freq, existing_list) = misspelled_words.get(word_lower, (0, []))
        existing_list.append(article_title)
        misspelled_words[word_lower] = (len(existing_list), existing_list)

        # Index by article of mispelled words
        article_oops_list.append(word_mixedcase)

    article_oops_string = u" ".join(article_oops_list)
    print("@\t%s\t%s\t%s" % (len(article_oops_list), article_title, article_oops_string))
    # if article_count % 100000 == 0:
    #     dump_results()


read_en_article_text(spellcheck_all_langs)
dump_results()
