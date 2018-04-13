# -*- coding: utf-8 -*-

from time import sleep
import re
from moss_dump_analyzer import read_en_article_text

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

all_words = set()

for filename in [
        "/bulk-wikipedia/enwiktionary-20150102-all-titles-in-ns0",
        "/bulk-wikipedia/enwiki-20141208-all-titles-in-ns0",
        "/bulk-wikipedia/specieswiki-20141218-all-titles-in-ns0",
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.strip().lower().decode('utf8')
            for word in line.split("_"):
                all_words.add(word)

# Words that aren't article titles, for technical reasons
all_words.add("#")
all_words.add("km<sup>2</sup>")
all_words.add("co<sub>2</sub>")
all_words.add("h<sub>2</sub>o")
all_words.add("h<sub>2</sub>")
all_words.add("o<sub>2</sub>")
# NOTE: These cases and many others are now handled by excluding anything that isn't ^[a-z]+$

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

possessive_re = re.compile(r"'s$")
abbr_re = re.compile(r"\.\w\.$")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Delimiting_.28grouping_of_digits.29
base_number_format = "(\d{1,4}|\d{1,3},\d\d\d|\d{1,3},\d\d\d,\d\d\d)(\.\d+)?"
# (possibly incomplete list)

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currency_symbols
number_formats_allowed_re = re.compile(
    r"(%s|%s%%|\$%s|US\$%s)" % (base_number_format, base_number_format, base_number_format, base_number_format))

whitespace_re = re.compile(r"\s+")
math_re = re.compile(r"<math.*?</math>")
all_letters_re = re.compile(r"^[a-zA-Z]+$")
upper_alpha_re = re.compile(r"[A-Z]")

substitutions = [
    # Order in the below is very important!  Templates must be removed
    # before these are applied.
    (re.compile(r"(&nbsp;|<br.*?>)"), " "),
    (re.compile(r"&ndash;"), "-"),  # To regular hypen
    (re.compile(r"<!--.*?-->"), ""),
    (re.compile(r"<ref.*?</ref>"), ""),
    (re.compile(r"<ref.*?/\s*>"), ""),
    (re.compile(r"<source.*?</source>"), ""),
    (re.compile(r"<blockquote.*?</blockquote>"), ""),
    (re.compile(r"<syntaxhighlight.*?</syntaxhighlight>"), ""),
    (re.compile(r"<gallery.*?</gallery>"), ""),
    (re.compile(r"<code.*?</code>"), ""),
    (re.compile(r"<timeline.*?</timeline>"), ""),
    # (re.compile(r"<X.*?</X>"), ""),
    (re.compile(r"<small>"), ""),
    (re.compile(r"</small>"), ""),
    (re.compile(r"<references.*?>"), ""),
    (re.compile(r"__notoc__"), ""),
    (re.compile(r"\[\s*(http|https|ftp):.*?\]"), ""),  # External links
    (re.compile(r"(http|https|ftp):.*?[ $]"), ""),  # Bare URLs
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)([^\|]+?)\]\]"), r"\1"),
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)(.*?)\|\s*(.*?)\s*\]\]"), r"\2"),
    (re.compile(r"\[\[[a-zA-Z\s]+:.*?\]\]"), ""),  # Category, interwiki
]


# "aaa {{bbb {{ccc}} ddd}} eee", "", 0
# "bbb {{ccc}} ddd}} eee", "aaa ", 1
# "ccc}} ddd}} eee", "aaa bbb", 2
# " ddd}} eee", "aaa bbb ccc", 1
# " eee", "aaa bbb ccc ddd", 0
# "aaa bbb ccc ddd eee"


def remove_structure_nested(string, open_string, close_string):
    # string_clean and nesting_depth are for use during recursion only

    string_clean = ""
    nesting_depth = 0

    # Use iteration instead of recursion to avoid exceeding maximum
    # recursion depth in articles with more than 500 template
    # instances
    while open_string in string:
        open_index = string.find(open_string)  # Always > -1 inside this loop
        close_index = string.find(close_string)

        #print "string_clean: %s" % string_clean
        #print "nesting_depth: %s" % nesting_depth
        #print "open_index: %s" % open_index
        #print "close_index: %s" % close_index
        #print "string: %s" % string

        if nesting_depth == 0:
            # Save text to the beginning of the template and open a new one
            string_clean += string[:open_index]
            string = string[open_index+2:]
            nesting_depth += 1
            continue

        # nesting_depth > 0 from here on...

        if close_index == -1 and nesting_depth > 0:
            # Unbalanced (too many open_string)
            # Drop string
            return string_clean

        if close_index > -1 and nesting_depth > 0:
            if close_index < open_index:
                # Discard text to the end of the template, close it,
                # and check for further templates
                string = string[close_index+2:]
                nesting_depth -= 1
                continue
            else:
                # Discard text to the beginning of the template and
                # open a new one
                string = string[open_index+2:]
                nesting_depth += 1
                continue

    while nesting_depth > 0 and close_string in string:
        # Remove this template and close
        close_index = string.find(close_string)
        string = string[close_index+2:]
        nesting_depth -= 1

    # Note: if close_string is in string and nesting_depth == 0,
    # close_string gets included in the output string due to
    # imbalance (too many close_string)
    return string_clean + string


def wikitext_to_plaintext(string):

    # TODO: Spell check visible contents of these special constructs

    string = whitespace_re.sub(" ", string)  # Sometimes contain "{{" etc.
    string = math_re.sub("", string)  # Sometimes contain "{{" etc.
    string = remove_structure_nested(string, "{{", "}}")
    string = remove_structure_nested(string, "{|", "|}")

    for (regex, replacement) in substitutions:
        string = regex.sub(replacement, string)
        # print string
        # print "---"
    return string


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
    for word in article_text.split(" "):
        word_mixedcase = word.strip(r",?!-()[]'\":;=*|")

        if not word_mixedcase:
            continue

        if (word_mixedcase.lower() in all_words):
            continue

        # Bob's
        word_mixedcase = possessive_re.sub("", word_mixedcase)
        # http://en.wiktionary.org/wiki/Wiktionary:About_English#Criteria_for_inclusion
        # says that possessives should not be in the dictionary, so we
        # exclude them systematically.

        # https://en.wiktionary.org/wiki/Wiktionary:Criteria_for_inclusion#Inflections
        # says that plural forms SHOULD be in the dictionary, so we do
        # NOT exclude them systematically.  Any plurals that show up
        # as misspelled words should be added to Wiktionary following
        # the example at [[cameras]].

        # F.C. vs. lastwordinsentence.
        if not abbr_re.search(word_mixedcase):
            word_mixedcase = word_mixedcase.strip(".")

        # Do it again in case . or 's was outside one of these
        word_mixedcase = word_mixedcase.strip(r",?!-()[]'\":;=*|")

        word_lower = word_mixedcase.lower()

        if word_lower in all_words:
            continue

        if number_formats_allowed_re.match(word_mixedcase):
            continue

        # Ignore all capitalized words (might be proper noun which we
        # legitimately don't have an entry for)
        # TODO: Detect beginning-of-sentence and optionally report
        # possibly misspelled words (or wait for sentence grammar
        # parsing)
        if upper_alpha_re.match(word_mixedcase):
            continue

        # TODO: This is a massive loophole; need better wikitext
        # processing.
        if not all_letters_re.match(word_mixedcase):
            continue

        word_parts_mixedcase = re.split(u"[––/-]", word_mixedcase)
        # emdash, endash, slash, hyphen
        if len(word_parts_mixedcase) > 1:
            any_bad = False
            for part in word_parts_mixedcase:
                if (part.lower() in all_words):
                    pass
                else:
                    any_bad = True
            if not any_bad:
                continue

        # Index by misspelled word of article titles
        (freq, existing_list) = misspelled_words.get(word_lower, (0, []))
        existing_list.append(article_title)
        misspelled_words[word_lower] = (len(existing_list), existing_list)

        # Index by article of mispelled words
        article_oops_list.append(word_mixedcase)

        # print "ARTICLE %s MISSPELLED: %s\t\t\t\t%s" % (article_title.encode('utf8'), word_tmp.encode('utf8'), word_mixedcase.encode('utf8'))

    article_oops_string = u" ".join(article_oops_list)
    print "@\t%s\t%s\t%s" % (len(article_oops_list), article_title.encode('utf8'), article_oops_string.encode('utf8'))
    # if article_count % 100000 == 0:
    #     dump_results()


test_result = remove_structure_nested("aaa {{bbb {{ccc}} ddd}} eee", "{{", "}}")
if test_result != "aaa  eee":
    raise Exception("Broken remove_structure_nested returned: '%s'" % test_result)

test_result = remove_structure_nested("{{xxx yyy}} zzz", "{{", "}}")
if test_result != " zzz":
    raise Exception("Broken remove_structure_nested returned: '%s'" % test_result)

read_en_article_text(spellcheck_all_langs)
dump_results()


# Analysis:
# python moss_spell_check.py > run-1234567.txt
# grep ^@ run-1234567.txt | sort -nr -k2 > articles-with-words.txt
# cat articles-with-words.txt | grep -vP '^@\t0' | perl -pe 's/.*\t//' >! misspelled-lists.txt
# cat misspelled-lists.txt | perl -ne 'foreach $word (split(" ")) {print $word . "\n"}' >! misspelled-words.txt
# cat misspelled-words.txt | perl -pe 'print length($_) - 1; print "\t"' | sort -n >! misspelled-words-charlen.txt
# grep '^*' run-1234567.txt | tac > words-with-articles.txt

# cat articles-with-words.txt | perl -pe 's/^@\t(\d+)\t(.*?)\t/* \1 - [[\2]] - /' > articles-with-words-linked.txt
# tac articles-with-words-linked.txt | grep -P "\* 1 -" | perl -pe 's/ - (\w+)$/ - [[wikt:\1]]/' >! articles-with-words-linked-2.txt

# tac run-e026b41/words-by-article.txt | head -1000 | python summarizer.py
# tac misspelled-words-charlen.txt | uniq | perl -pe 's%(\d+)\t(.*)$%* \1 [https://en.wikipedia.org/w/index.php?search=\2 \2]%' > ! misspelled-words-charlen-linked.txt

# TODO: Experiment with using NLTK and other grammar engines to parse
# wikitext

# TODO: Post lists of the shortest and longest misspelled words,
# articles with most and least number of misspelled words, random
# assortment of typos in dump order.
# * 2 - [[wikt:X]] - [[article1]], [[article2]]

