# -*- coding: utf-8 -*-

from time import sleep
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

for filename in [
        "/bulk-wikipedia/enwiktionary-20141129-all-titles-in-ns0",
        "/bulk-wikipedia/enwiki-20141208-all-titles-in-ns0"
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.strip().lower().decode('utf8')
            for word in line.split(" "):
                all_words.add(word)


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
    # Order in the below is very important!  Templates must be removed
    # before these are applied.
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


def remove_templates(string):
    # string_clean and nesting_depth are for use during recursion only

    string_clean = ""
    nesting_depth = 0

    # Use iteration instead of recursion to avoid exceeding maximum
    # recursion depth in articles with more than 500 template
    # instances
    while "{{" in string:
        open_index = string.find("{{")  # Always > -1 inside this loop
        close_index = string.find("}}")

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
            # Unbalanced {{}}s (too many {{)
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

    while nesting_depth > 0 and "}}" in string:
        # Remove this template and close
        close_index = string.find("}}")
        string = string[close_index+2:]
        nesting_depth -= 1

    # Note: if "}}" is in string and nesting_depth == 0, "}}" gets included
    # in the output string due to unbalanced {{}} (too many }})
    return string_clean + string


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

    # print "PROCESSING ARTICLE: " + article_title

    # if article_title != "Anarchism":
    #     return

    article_text = wikitext_to_plaintext(article_text)
    ## Debug article_text processing:
    # print article_text.encode('utf8')
    # sleep(1)
    # return

    # TODO: Handle }} inside <nowiki>
    if "}}" in article_text:
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

test_result = remove_templates("{{xxx yyy}} zzz")
if test_result != " zzz":
    raise Exception("Broken remove_templates returned: '%s'" % test_result)

read_en_article_text(spellcheck_all_langs)
dump_results
