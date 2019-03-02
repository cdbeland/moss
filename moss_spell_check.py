# -*- coding: utf-8 -*-

import nltk
import re
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext
from spell import is_word_spelled_correctly
from grammar import prose_quote_re, ignore_sections_re, line_starts_with_space_re


# TODO:
# * Detect strings of three or more Greek letters ONLY for
#   spell-checking purposes.
# * tmp-output.txt:* 24 - [[wikt:ation]] - [[1772 in poetry]] ([[attest]]ation)
# * Report these:
#    :"..."
#    :''"..."''
#    <blockquote>"..."</blockquote>
#    {{quote|"..."}}
#   as possible violations of [[MOS:BLOCKQUOTE]]; exclude these from
#   "parse failed" output

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


ignore_tags_re = re.compile(r"{{\s*(([Cc]opy|[Mm]ove) to \w+|[Nn]ot English|[Cc]leanup HTML|[Cc]leanup).*?}}")
blockquote_re = re.compile(r"<blockquote.*?</blockquote>", flags=re.I+re.S)
start_template_re = re.compile(r"{{")
end_template_re = re.compile(r"}}")
unicode_letters_plus_dashes_re = re.compile(r"^([^\W\d_]|-)+$")
spaced_emdash_re = re.compile(r".{0,10}—\s.{0,10}|.{0,10}\s—.{0,10}")
newline_re = re.compile(r"\n")

requested_species_html = ""
with open('/bulk-wikipedia/Wikispecies:Requested_articles', 'r') as requested_species_file:
    requested_species_html = requested_species_file.read()


def spellcheck_all_langs(article_title, article_text):
    global article_count

    if ignore_tags_re.search(article_text):
        print("S\tSKIPPING due to known cleanup tag\t%s" % article_title)
        return

    request_search_string = 'title="en:%s"' % article_title
    if request_search_string in requested_species_html:
        print("S\tSKIPPING - list with requested species\t%s" % article_title)
        return

    # This can break wikitext_to_plaintext() in ways that cause wiki
    # syntax to be mistaken for prose.
    starters = start_template_re.findall(article_text)
    enders = end_template_re.findall(article_text)
    if len(starters) != len(enders):
        print("!\t* [[%s]] - Mismatched {{ }}; try [https://tools.wmflabs.org/bracketbot/cgi-bin/find.py bracketbot]" % article_title)
        return

    article_text_orig = article_text
    article_text = wikitext_to_plaintext(article_text)

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Dashes
    # requires that emdashes be unspaced.
    article_text_safe = newline_re.sub(" ", article_text)
    bad_emdash_context_list = spaced_emdash_re.findall(article_text_safe)
    if bad_emdash_context_list:
        print("D\t* %s - [[%s]]: %s" % (
            len(bad_emdash_context_list),
            article_title,
            " ... ".join(bad_emdash_context_list)))

    # TODO: Get smarter about these sections.  But for now, ignore
    # them, since they are full of proper nouns and URL words.
    article_text = ignore_sections_re.sub("", article_text)
    # Many of these are computer programming code snippets
    article_text = line_starts_with_space_re.sub("\n", article_text)

    quotation_list = blockquote_re.findall(article_text)
    quotation_list.extend(prose_quote_re.findall(article_text))
    if quotation_list:
        article_text = blockquote_re.sub(" ", article_text)
        article_text = prose_quote_re.sub("", article_text)

        # (Works, but disabled to save space because output is not being used.)
        # print("Q\t%s\t%s" % (article_title, u"\t".join(quotation_list)))
        # TODO: Spell-check quotations, but publish typos in them in a
        #  separate list, since they need to be verified against the
        #  original source, or at least corrected more carefully.
        #  Archaic spelling should be retained and added to Wiktionary.
        #  Spelling errors should be corrected, or if important to
        #  keep, tagged with {{typo|}} and {{sic}}.  For now, we have
        #  plenty of typos to fix without bothering with quotations.
        #  See: https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Quotations
        # TODO: Handle notation for fixes to quotes like:
        #  [[340B Drug Pricing Program]] - [s]tretch
        #  [[Zachery Kouwe]] - appropriat[ing]

    for unmatched_item in ["<ref", "</ref>", "<blockquote", "</blockquote>", "}}", "{{", '"', "colspan", "rowspan", "cellspacing"]:
        if unmatched_item in article_text:
            matches = re.findall(r".{0,20}%s.{0,20}" % unmatched_item, article_text)
            excerpt = " ... ".join(matches)
            print("!\t* [[%s]] - Unmatched %s near: %s" % (article_title, unmatched_item, excerpt))
            # Often due to typo in wiki markup or mismatched English
            # punctuation, but might be due to moss misinterpreting
            # the markup.  (Either way, should be fixed because this
            # blocks spell-checking the entire article.)
            return

    # These are now in a report; this is only needed for debugging.
    # unknown_html_tag_re = re.compile(r"<[/!?a-zA-Z].*?>")
    # html_tag_matches = unknown_html_tag_re.findall(article_text)
    # if html_tag_matches:
    #     print("W\tWARNING: Unknown HTML tag(s) present: %s \t%s" % ("  ".join(html_tag_matches), article_title))
    #     print("W\t%s" % article_text)

    article_count += 1
    article_oops_list = []

    article_text = article_text.replace("✂", " ")
    word_list = nltk.word_tokenize(article_text)

    # Old-fashioned loop to allow lookahead and cope with the fact
    # that the length of word_list may change as it is edited in
    # place.
    i = 0
    while i < len(word_list):
        # TODO: Make test cases, especially for beginning and
        # end-of-document HTML entities.

        # Reassemble HTML markup the tokenizer has split into multiple
        # words.  Must double-check because the tokenizer ignores
        # whitespace, and we don't want to accidentally match
        # e.g. where an ampersand in prose is followed shortly by a
        # semicolon.

        # TODO: Parameterize to avoid code duplication

        # Three-token sequences
        if i < len(word_list) - 2:
            if word_list[i] == "&" and word_list[i + 2] == ";":

                # Protect against & in acronyms, common for railroads
                # and companies like AT&T, PG&E.
                if i == 0 or not (re.match("^[A-Z]+s?$", word_list[i + 1])
                                  and re.match("^[A-Z]+$", word_list[i - 1])):
                    consolidated = "&%s;" % word_list[i + 1]
                    if consolidated in article_text:
                        word_list[i] = consolidated
                        del word_list[i + 2]
                        del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 2] == ">":
                consolidated = "<%s>" % word_list[i + 1]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 2]
                    del word_list[i + 1]

            # In transliterations from Arabic script (which includes
            # Persian), NLTK correctly parses U+0027 (apostrophe) and
            # U+02BE/U+02BF (preferred by the Unicode Consortium and
            # United Nations).
            # https://en.wikipedia.org/wiki/Romanization_of_Persian
            # https://en.wikipedia.org/wiki/Romanization_of_Arabic
            #
            # However, Wikipedia allows the use of U+2019 (right
            # single quote mark) which NLTK will (arguably
            # justifiably) misparse if used as something other than a
            # quotation mark.
            # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Persian
            # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Arabic
            elif word_list[i + 1] == "’":
                # For example "Āb Anbār-e Pā’īn" must be parsed as three words.
                if unicode_letters_plus_dashes_re.search(word_list[i]) and unicode_letters_plus_dashes_re.search(word_list[i + 2]):
                    word_list[i] = word_list[i] + word_list[i + 1] + word_list[i + 2]
                    del word_list[i + 2]
                    del word_list[i + 1]

        # Four-token sequences
        if i < len(word_list) - 3:
            if word_list[i] == "&" and word_list[i + 1] == "#" and word_list[i + 3] == ";":
                consolidated = "&#%s;" % word_list[i + 2]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 1] == "/" and word_list[i + 3] == ">":
                consolidated = "</%s>" % word_list[i + 2]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 2] == "/" and word_list[i + 3] == ">":
                consolidated = "<%s/>" % word_list[i + 1]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

        i += 1

    for word_mixedcase in word_list:

        # "." is specifically excluded from the below list, due to
        # abbreviations which are handled correctly by spell.py with
        # periods in place.
        word_mixedcase = word_mixedcase.strip(
            # Deal with symmetrical wiki markup
            "=" +
            # Deal with, NLTK treatment of hyphenated and slashed words
            "––/-" +

            # TODO: NLTK tokenizer breaks on British quoting style
            # (which is allowed in places): 'xxx'
            "'"

            # https://en.wikipedia.org/wiki/%CA%BBOkina#Names
            # TODO: NLTK tokenizer breaks on Polynesian words using
            # apostrophes and quote marks to represent 'eta and other
            # glottal stops.  Hawaiian words should use ʻokina which
            # are tokenized correctly, as a letter.
        )

        # Deal with asymmetrical wiki markup
        word_mixedcase = word_mixedcase.lstrip(":")
        word_mixedcase = word_mixedcase.lstrip("*")

        if not word_mixedcase.startswith("&"):
            # Let &xxx; pass through un-stripped so it's easy to identify later
            word_mixedcase = word_mixedcase.strip(";")

        is_spelling_correct = is_word_spelled_correctly(word_mixedcase)
        if is_spelling_correct is True:
            continue
        if is_spelling_correct == "uncertain":
            print("G\t%s\t%s" % (word_mixedcase, article_title))
            # "G" for "iGnored but maybe shouldn't be"
            continue

        # Hack to avoid having to do even more complicated token
        # re-assembly, though this may cause some unnecessary HTML
        # markup on the same page to be ignored.
        if word_mixedcase == "<li>" and "<li value=" in article_text_orig:
            continue
        if word_mixedcase == "<li>" and "<ol start=" in article_text_orig:
            continue
        if word_mixedcase == "<ol>" and "<ol start=" in article_text_orig:
            continue

        # TODO: In some situations this might actually be replaced
        # with a streamlined wiki-style list, or footnote syntax.
        if word_mixedcase == "<ol>" and "<ol type=" in article_text_orig:
            continue
        if word_mixedcase == "<li>" and "<ol type=" in article_text_orig:
            continue

        # Word is misspelled, so...

        # Normalize for report rollup purposes, even if this is incorrect capitalization
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


if __name__ == '__main__':
    read_en_article_text(spellcheck_all_langs)
    dump_results()
