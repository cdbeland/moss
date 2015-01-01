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

"""
for filename in [
        "/bulk-wikipedia/enwiktionary-20141129-all-titles-in-ns0",
        "/bulk-wikipedia/enwiki-20141208-all-titles-in-ns0"
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.strip().lower().decode('utf8')
            for word in line.split(" "):
                all_words.add(word)
"""

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
number_formats_allowed_re = re.compile(r"(\d{1,4}|\d{1,3},\d\d\d|\d{1,3},\d\d\d,\d\d\d)(\.\d+)?%?")
# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Delimiting_.28grouping_of_digits.29

substitutions = [
    # Order in the below is very important!
    (re.compile(r"\{\{\S+\}\}"), ""),  # Templates, inner (hopefully)
    (re.compile(r"\{\{.+?\}\}"), ""),  # Templates, inner (hopefully, no \n)
    (re.compile(r"\s+"), " "),
    (re.compile(r"(&nbsp;|<br.*?>)"), " "),
    (re.compile(r"&ndash;"), "-"),  # To regular hypen
    (re.compile(r"<ref.*?</ref>"), ""),
    (re.compile(r"<ref.*?/\s*>"), ""),
    (re.compile(r"<source.*?</source>"), ""),
    (re.compile(r"<blockquote.*?</blockquote>"), ""),
    (re.compile(r"<syntaxhighlight.*?</syntaxhighlight>"), ""),
    # (re.compile(r"<X.*?</X>"), ""),
    # (re.compile(r"<X.*?</X>"), ""),
    # (re.compile(r"<X.*?</X>"), ""),
    (re.compile(r"<math.*?</math>"), ""),
    (re.compile(r"<gallery.*?</gallery>"), ""),
    (re.compile(r"<small>"), ""),
    (re.compile(r"</small>"), ""),
    (re.compile(r"<!--.*?-->"), ""),
    (re.compile(r"<references.*?>"), ""),
    (re.compile(r"__notoc__"), ""),

    # Causes major malfunction, overmatching 8(
    # {{.*?{{.*?}}.*?}}
    # (re.compile(r"\{\{.*?\{\{.*?\}\}.*?\}\}"), ""),  # Templates, nested

    (re.compile(r"\{\{.*?\}\}"), ""),  # Templates, possibly outer
    (re.compile(r"\{\|.*?\|\}"), ""),  # Tables
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


def remove_templates(string, string_clean="", nesting_depth=0):
    # string_clean and nesting_depth are for use during recursion only

    # print "remove_templates string >>>%s<<<" % string
    # print "remove_templates string_clean >>>%s<<<" % string_clean
    print "remove_templates nesting_depth >>>%s<<<" % nesting_depth

    open_index = string.find("{{")
    close_index = string.find("}}")

    if open_index == -1 and nesting_depth == 0:
        # Base case
        # if close_index > 1, "}}" gets included in the output string.
        return string_clean + string

    if open_index > -1 and nesting_depth == 0:
        # Save text to the beginning of the template and open a new one
        string_clean += string[:open_index]
        return remove_templates(string[open_index+2:], string_clean, nesting_depth+1)

    # nesting_depth > 0 from here on...

    if close_index == -1:
        # Unbalanced {{}}s
        return string_clean

    # nesting_depth > 0 and close_index > -1 from here on...

    if open_index == -1:
        # Remove this template and close, but check for further templates
        return remove_templates(string[close_index+2:], string_clean, nesting_depth-1)

    if open_index > -1:
        if close_index < open_index:
            # Remove this template and close, but check for further templates
            return remove_templates(string[close_index+2:], string_clean, nesting_depth-1)
        else:
            # Discard text to the beginning of the template and open a new one
            return remove_templates(string[open_index+2:], string_clean, nesting_depth+1)


def wikitext_to_plaintext(string):

    # TODO: Spell check visible contents of these special constructs

    string = remove_templates(string)

    for (regex, replacement) in substitutions:
        string = regex.sub(replacement, string)
        # print string
        # print "---"
    return string


def spellcheck_all_langs(article_title, article_text):
    # article_text is Unicode (UTF-32) thanks to lxml

    global count

    print "PROCESSING ARTICLE: " + article_title

    # if article_title != "Anarchism":
    #     return

    article_text = wikitext_to_plaintext(article_text)
    # print "*** %s ***" % article_title.encode('utf8')
    # print article_text.encode('utf8')
    # sleep(2)
    # return

    if "}" in article_text:
        print "ABORTING PROCESSING OF %s" % article_title
        print article_text
        return

    count += 1
    for word in article_text.split(" "):
        word_orig = word.strip(r",?!-()[]'\":;=*|")

        if not word_orig:
            continue

        word_tmp = word_orig.lower()

        if (word_tmp in all_words):
            continue

        # Bob's
        word_tmp = possessive_re.sub("", word_tmp)

        # F.C. vs. lastwordinsentence.
        if not abbr_re.search(word_tmp):
            word_tmp = word_tmp.strip(".")

        if word_tmp in all_words:
            continue

        if number_formats_allowed_re.match(word_tmp):
            continue

        word_parts = re.split(u"[––/-]", word_tmp)
        # emdash, endash, slash, hyphen
        if len(word_parts) > 1:
            any_bad = False
            for part in word_parts:
                if (part in all_words):
                    pass
                else:
                    any_bad = True
            if not any_bad:
                continue

        misspelled_words[word_tmp] = misspelled_words.get(word_tmp, 0) + 1
        # print "MISSPELLED: %s" % word_tmp.encode('utf8')

    if count % 1000 == 0:
        dump_results()

test_result = remove_templates("aaa {{bbb {{ccc}} ddd}} eee")
if test_result != "aaa  eee":
    raise Exception("Broken remove_templates returned: '%s'" % test_result)

read_en_article_text(spellcheck_all_langs)
dump_results
