# -*- coding: utf-8 -*-

import re


def remove_structure_nested(string, open_string, close_string):
    # TODO: Write tests
    # Sample inputs and outputs:
    # ("aaa {{bbb {{ccc}} ddd}} eee", "{{, "}}") -> "aaa  eee"
    # ("bbb {{ccc}} ddd}} eee", "{{, "}}") -> "bbb  ddd}} eee"

    string_clean = ""
    nesting_depth = 0

    # Use iteration instead of recursion to avoid exceeding maximum
    # recursion depth in articles with more than 500 template
    # instances
    while open_string in string:
        open_index = string.find(open_string)  # Always > -1 inside this loop
        close_index = string.find(close_string)

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


# These have to happen before templates are stripped out.
early_substitutions = [
    (re.compile(r"\s+"), " "),
    (re.compile(r"{{[·|bold middot|dot|middot]}}"), " · "),
    (re.compile(r"{{[•|bull]}}"), " • "),
    (re.compile(r"<math>.*?</math>", flags=re.I), ""),  # Sometimes contain {{ / }}, which can look like template start/end
    (re.compile(r"{{[spaced en dash|dash|nbspndash|snd|sndash|spacedendash|spacedndash|spnd|spndash]}}", flags=re.I), " - "),
]

substitutions = [
    # Order in the below is very important!  Templates must be removed
    # before these are applied.

    # TODO: Implement results of discussion at
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Manual_of_Style#HTML_entities

    # Whitespace
    (re.compile(r"&nbsp;|<br.*?>|&thinsp;", flags=re.I), " "),

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Dashes
    # says these are allowed
    (re.compile(r"&ndash;", flags=re.I), "-"),  # To regular hypen
    (re.compile(r"&mdash;", flags=re.I), "—"),  # U+2013
    (re.compile(r"&minus;", flags=re.I), "−"),  # U+2212

    # Confusingly similar to quotation marks
    (re.compile(r"&prime;", flags=re.I), "′"),  # U+2032
    (re.compile(r"&Prime;", flags=re.I), "″"),  # U+2033

    (re.compile(r"<!--.*?-->"), ""),
    (re.compile(r"<(\??[a-zA-Z]+)[^>]{0,1000}?(/?)\s*>"), r"<\1\2>"),  # Drop HTML attributes for easier parsing

    (re.compile(r"<ref/>", flags=re.I), ""),  # Must come before <ref>...</ref>
    (re.compile(r"<ref>.*?</ref>", flags=re.I), ""),
    (re.compile(r"<source>.*?</source>", flags=re.I), ""),
    (re.compile(r"<syntaxhighlight>.*?</syntaxhighlight>", flags=re.I), ""),
    (re.compile(r"<gallery>.*?</gallery>", flags=re.I), ""),
    (re.compile(r"<timeline>.*?</timeline>", flags=re.I), ""),
    (re.compile(r"<code>.*?</code>", flags=re.I), ""),
    (re.compile(r"<chem>.*?</chem>", flags=re.I), ""),
    (re.compile(r"<score>.*?</score>", flags=re.I), ""),
    (re.compile(r"<span>", flags=re.I), ""),
    (re.compile(r"</span>", flags=re.I), ""),
    (re.compile(r"<div>", flags=re.I), ""),
    (re.compile(r"</div>", flags=re.I), ""),
    (re.compile(r"<small>", flags=re.I), ""),
    (re.compile(r"</small>", flags=re.I), ""),
    (re.compile(r"<big>", flags=re.I), ""),
    (re.compile(r"</big>", flags=re.I), ""),
    (re.compile(r"<center>", flags=re.I), ""),
    (re.compile(r"</center>", flags=re.I), ""),
    (re.compile(r"<sub>", flags=re.I), " "),
    (re.compile(r"</sub>", flags=re.I), " "),
    (re.compile(r"<sup>", flags=re.I), " "),
    (re.compile(r"</sup>", flags=re.I), " "),
    (re.compile(r"<s>", flags=re.I), ""),
    (re.compile(r"</s>", flags=re.I), ""),
    (re.compile(r"<u>", flags=re.I), ""),
    (re.compile(r"</u>", flags=re.I), ""),
    (re.compile(r"<references[^>]*?>", flags=re.I), ""),
    (re.compile(r"__notoc__", flags=re.I), ""),
    (re.compile(r"\[\s*(http|https|ftp):.*?\]", flags=re.I), ""),  # External links
    (re.compile(r"(http|https|ftp):.*?[ $]", flags=re.I), ""),  # Bare URLs

    # TODO: These could really use test cases
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)([^\|]+?)\]\]"), r"\1"),
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)(.*?)\|\s*(.*?)\s*\]\]"), r"\2"),

    (re.compile(r"\[\[[a-zA-Z\s]+:.*?\]\]"), ""),  # Category, interwiki
    (re.compile(r"'''''"), ""),
    (re.compile(r"''''"), ""),  # For when ''xxx'' has xxx removed
    (re.compile(r"'''"), ""),
    (re.compile(r"''"), ""),
    (re.compile(r"\{.{1,200}?\{.{1,200}?\}\}"), ""),  # Happens in mathematical expressions

    # TODO: Might need to actually respect this and protect segments
    # inside these tags from substitutions.
    (re.compile(r"<nowiki>", flags=re.I), ""),
    (re.compile(r"</nowiki>", flags=re.I), ""),

    (re.compile(r"<nowiki/>", flags=re.I), ""),
    # Used to prevent auto-linking inflections, for example [[truck]]<nowiki/>s

    # Used inside links per https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Brackets_and_linking
    (re.compile(r"&#91;", flags=re.I), "["),
    (re.compile(r"&#93;", flags=re.I), "]"),
]


# This function does not preserve all elements in the wikitext where
# non-linear rendering or template substitution would be required, so
# some information on the page is lost.  It is intended for use with
# verification algorithms that are mostly expecting prose, and will
# leave complicated markup (including math-in-prose) unverified.  Some
# wikitext features, like section headers, are left intact.
def wikitext_to_plaintext(string):
    for (regex, replacement) in early_substitutions:
        string = regex.sub(replacement, string)

    # TODO: Spell check visible contents of these special constructs
    string = remove_structure_nested(string, "{{", "}}")
    string = remove_structure_nested(string, "{|", "|}")

    # We see some cases where the {| is in a template and the |} is in
    # the article.
    string = remove_structure_nested(string, "|-", "|}")

    for (regex, replacement) in substitutions:
        string = regex.sub(replacement, string)

    return string
