# -*- coding: utf-8 -*-

import re


def remove_structure_nested(string, open_string, close_string):
    # string_clean and nesting_depth are for use during recursion only

    # Sample inputs and outputs:
    # "aaa {{bbb {{ccc}} ddd}} eee", "", 0
    # "bbb {{ccc}} ddd}} eee", "aaa ", 1
    # "ccc}} ddd}} eee", "aaa bbb", 2
    # " ddd}} eee", "aaa bbb ccc", 1
    # " eee", "aaa bbb ccc ddd", 0
    # "aaa bbb ccc ddd eee"

    string_clean = ""
    nesting_depth = 0

    # Use iteration instead of recursion to avoid exceeding maximum
    # recursion depth in articles with more than 500 template
    # instances
    while open_string in string:
        open_index = string.find(open_string)  # Always > -1 inside this loop
        close_index = string.find(close_string)

        # print("string_clean: %s" % string_clean)
        # print("nesting_depth: %s" % nesting_depth)
        # print("open_index: %s" % open_index)
        # print("close_index: %s" % close_index)
        # print("string: %s" % string)

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


whitespace_re = re.compile(r"\s+")
math_re = re.compile(r"<math.*?</math>")

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


def wikitext_to_plaintext(string):

    # TODO: Spell check visible contents of these special constructs

    string = whitespace_re.sub(" ", string)  # Sometimes contain "{{" etc.
    string = math_re.sub("", string)  # Sometimes contain "{{" etc.
    string = remove_structure_nested(string, "{{", "}}")
    string = remove_structure_nested(string, "{|", "|}")

    # We see some cases where the {| is in a template and the |} is in
    # the article.
    string = remove_structure_nested(string, "|-", "|}")

    for (regex, replacement) in substitutions:
        string = regex.sub(replacement, string)
        # print string
        # print "---"
    return string
