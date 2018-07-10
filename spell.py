# -*- coding: utf-8 -*-

import re
from string import punctuation
import sys

print("Loading spellcheck dictionary...", file=sys.stderr)

# TODO: Possibly move this to postgres or MySQL.  Load DB as part of
# update_downloads.sh; startup time is very slow due to loading this
# all into Python, even though accessing in-memory data is very fast.

all_words = set()
punctuation_re = re.compile(r"[" + punctuation + r"]")

for filename in [
        "/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0",
        "/bulk-wikipedia/enwiki-latest-all-titles-in-ns0",
        "/bulk-wikipedia/specieswiki-latest-all-titles-in-ns0",
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.strip().lower()

            # Mostly splitting on "_", but also ":", etc.
            [all_words.add(title_word)
             for title_word
             in punctuation_re.split(line)
             if title_word]


# Words that aren't article titles, for technical reasons
all_words.add("#")
all_words.add("km<sup>2</sup>")
all_words.add("co<sub>2</sub>")
all_words.add("h<sub>2</sub>o")
all_words.add("h<sub>2</sub>")
all_words.add("o<sub>2</sub>")
# NOTE: These cases and many others are now handled by excluding anything that isn't ^[a-z]+$


abbr_re = re.compile(r"\.\w\.$")
all_letters_re = re.compile(r"^[a-zA-Z]+$")
upper_alpha_re = re.compile(r"[A-Z]")


# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Delimiting_.28grouping_of_digits.29
base_number_format = "(\d{1,4}|\d{1,3},\d\d\d|\d{1,3},\d\d\d,\d\d\d)(\.\d+)?"
# (possibly incomplete list)

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currency_symbols
number_formats_allowed_re = re.compile(
    r"(%s|%s%%|\$%s|US\$%s)" % (base_number_format, base_number_format, base_number_format, base_number_format))

print("Done.", file=sys.stderr)


def is_word_spelled_correctly(word_mixedcase):
    if not word_mixedcase:
        return True

    if word_mixedcase.lower() in all_words:
        return True

    # Possessive: NLTK parses e.g. "'s" as a separate word, which
    # Wikitionary has listed.

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
        return True

    if number_formats_allowed_re.match(word_mixedcase):
        return True

    # Ignore all capitalized words (might be proper noun which we
    # legitimately don't have an entry for)
    # TODO: Detect beginning-of-sentence and optionally report
    # possibly misspelled words (or wait for sentence grammar
    # parsing)
    if upper_alpha_re.match(word_mixedcase):
        return True

    # TODO: This is a massive loophole; need better wikitext
    # processing.
    if not all_letters_re.match(word_mixedcase):
        return True

    word_parts_mixedcase = re.split(u"[––/-]", word_mixedcase)
    # emdash, endash, slash, hyphen
    if len(word_parts_mixedcase) > 1:
        any_bad = False
        for part in word_parts_mixedcase:
            if not (part.lower() in all_words):
                any_bad = True
        if not any_bad:
            return True

    return False
