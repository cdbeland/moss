# -*- coding: utf-8 -*-

import re


html_tag_re = re.compile(r"<\??/?\s*[a-zA-Z]+\s*/?\s*>")
blockquote_re = re.compile(r"(<blockquote.*?</blockquote>|<poem.*?</poem>)", flags=re.I+re.S)
ignore_tags_re = re.compile(r"{{\s*(([Cc]opy|[Mm]ove|[Cc]opy section) to \w+"
                            r"|[Nn]ot English"
                            r"|[Cc]leanup HTML"
                            r"|[Cc]leanup"
                            r"|[Ww]hich lang(uage)?"
                            r"|[Tt]ypo help inline"
                            r"|[Yy]ou"
                            r"|[Tt]one"
                            r"|[Cc]opy ?edit"
                            r"|[Gg]rammar"
                            r"|[Mm]anual"
                            r"|[Tt]ravel guide"
                            r"|[Ll]like resume"
                            r"|[Hh]ow\-?to).*?}}")


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
                string_clean += "✂"
                string = string[close_index+2:]
                nesting_depth -= 1
                continue
            else:
                # Discard text to the beginning of the template and
                # open a new one
                string_clean += "✂"
                string = string[open_index+2:]
                nesting_depth += 1
                continue

    while nesting_depth > 0 and close_string in string:
        # Remove this template and close
        string_clean += "✂"
        close_index = string.find(close_string)
        string = string[close_index+2:]
        nesting_depth -= 1

    # Note: if close_string is in string and nesting_depth == 0,
    # close_string gets included in the output string due to
    # imbalance (too many close_string)
    return string_clean + string


# These have to happen before templates are stripped out.
early_substitutions = [

    # Normalize whitespace a bit
    (re.compile(r"  +"), " "),
    (re.compile(r"\n\n\n+"), r"\n\n"),

    (re.compile(r"{{(·|bold middot|dot|middot)}}"), " · "),
    (re.compile(r"{{(•|bull)}}"), " • "),

    (re.compile(r"<syntaxhighlight[^>]*>.*?</syntaxhighlight>", flags=re.I+re.S), "\n\n"),
    # include <math.h> will mess up <math>...</math>

    (re.compile(r"<math[^>]*>.*?</math>", flags=re.I+re.S), ""),  # Sometimes contain {{ / }}, which can look like template start/end

    (re.compile(r"{{ISBN\|(.*?)}}"), r"\1"),

    # Mostly from:
    # https://en.wikipedia.org/wiki/Category:Character_templates
    (re.compile(r"{{(spaced en dash|spaced en dash space|dash|nbspndash|snd|sndash|spacedendash|spacedndash|spnd|spndash)}}", flags=re.I), " - "),
    (re.compile(r"{{(mdash|—|em dash|emdash|em-dash|--|em dash)}}", flags=re.I), "-"),
    (re.compile(r"{{(endash|en dash|–|ndash|nsndns|subdash)}}", flags=re.I), "-"),
    (re.compile(r"{{(\\)}}", flags=re.I), " / "),
    (re.compile(r"{{tm}}", flags=re.I), "™"),
    (re.compile(r"{{theta}}", flags=re.I), "&theta;"),
    (re.compile(r"{{SH}}"), "ś"),
    (re.compile(r"{{seggol}}", flags=re.I), "ֶ"),
    (re.compile(r"{{schwahook}}", flags=re.I), "ɚ"),
    (re.compile(r"{{schwa}}", flags=re.I), "ə"),
    (re.compile(r"{{rturn}}", flags=re.I), "ɹ"),
    (re.compile(r"{{rfishhook}}", flags=re.I), "ɾ"),
    (re.compile(r"{{pipedbl}}", flags=re.I), "ǁ"),
    (re.compile(r"{{okina}}", flags=re.I), "ʻ"),
    (re.compile(r"{{mu}}", flags=re.I), "μ"),
    (re.compile(r"{{mappiq}}", flags=re.I), "ּ"),
    (re.compile(r"{{linevertsub}}", flags=re.I), "ˌ"),
    (re.compile(r"{{linevert}}", flags=re.I), "ˈ"),
    (re.compile(r"{{lengthmark}}", flags=re.I), "ː"),
    (re.compile(r"{{lambda}}", flags=re.I), "λ"),
    (re.compile(r"{{hicaron}}", flags=re.I), "̌"),
    (re.compile(r"{{hbrrafe}}", flags=re.I), "ֿ"),
    (re.compile(r"{{thinsp}}", flags=re.I), "&thinsp;"),
    (re.compile(r"{{gamma}}", flags=re.I), "γ"),
    (re.compile(r"{{epsilon1revhook}}", flags=re.I), "ɝ"),
    (re.compile(r"{{epsilon1rev}}", flags=re.I), "ɜ"),
    (re.compile(r"{{epsilon1}}", flags=re.I), "Ɛ"),
    (re.compile(r"{{dirprod}}", flags=re.I), "⊗"),
    (re.compile(r"{{DELTA}}"), "Δ"),
    (re.compile(r"{{circle}}", flags=re.I), "￼"),
    (re.compile(r"{{angle bracket\|(.*?)}}", flags=re.I), "⟨\1⟩"),
    (re.compile(r"{{beta letter}}", flags=re.I), "β"),

    (re.compile(r"{{em\|(.*?)}}", flags=re.I), "$1"),
    (re.compile(r"{{strong\|(.*?)}}", flags=re.I), "$1"),

    # Templates that should survive template removal because they are
    # on the prohibited_list
    (re.compile(r"{{(cquote\|.*?)}}", flags=re.I), "⁅⁅$1⁆⁆"),

    # ---

    # Must happen before table removal to prevent [[aa|{{bb}}-cc]] being changed to "aacc"

    # [[Regular page]]
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)([^\|]+?)\]\]"), r"\1"),

    # [[Target page|Display text]]
    (re.compile(r"\[\[(?![a-zA-Z\s]+:)(.*?)\|\s*(.*?)\s*\]\]", flags=re.S), r"\2"),

    # [[Namespace:Target page]]
    # Deletes links for category, interwiki, images, etc.
    (re.compile(r"\[\[[a-zA-Z\s]+:.*?\]\]", flags=re.S), ""),

    # ---

    # Must happen before table removal due to possibility of "|-"
    (re.compile(r"<gallery[^>]*>.*?</gallery>", flags=re.I+re.S), "\n\n"),

    # May contain mismatched }}
    (re.compile(r"<score[^>]*>.*?</score>", flags=re.I+re.S), ""),
]

substitutions = [
    # Order in the below is very important!  Templates must be removed
    # before these are applied.

    # Whitespace
    (re.compile(r"&nbsp;|&thinsp;|&hairsp;"), " "),
    (re.compile(r"<br.*?>", flags=re.I), " "),

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Text_formatting#HTML_character_entity_references
    # says these are allowed to avoid confusion.  Should be treated
    # the same as the Unicode characters by downstream code, so
    # normalize them to that.
    (re.compile(r"&ndash;"), "-"),  # To regular hypen
    (re.compile(r"&shy;"), ""),  # Optional hyphen
    (re.compile(r"&mdash;"), "—"),  # U+2013
    (re.compile(r"&minus;"), "−"),  # U+2212
    (re.compile(r"&prime;"), "′"),  # U+2032
    (re.compile(r"&Prime;"), "″"),  # U+2033
    (re.compile(r"&Prime;"), "″"),  # U+2033
    (re.compile(r"&Alpha;"), "Α"),
    (re.compile(r"&Beta;"), "Β"),
    (re.compile(r"&Epsilon;"), "Ε"),
    (re.compile(r"&Zeta;"), "Ζ"),
    (re.compile(r"&Eta;"), "Η"),
    (re.compile(r"&Iota;"), "Ι"),
    (re.compile(r"&Kappa;"), "Κ"),
    (re.compile(r"&Mu;"), "Μ"),
    (re.compile(r"&Nu;"), "Ν"),
    (re.compile(r"&Omicron;"), "Ο"),
    (re.compile(r"&Rho;"), "Ρ"),
    (re.compile(r"&Tau;"), "Τ"),
    (re.compile(r"&Upsilon;"), "Υ"),
    (re.compile(r"&Chi;"), "Χ"),
    (re.compile(r"&kappa;"), "κ"),
    (re.compile(r"&omicron;"), "ο"),
    (re.compile(r"&rho;"), "ρ"),
    (re.compile(r"&lsquo;"), "‘"),
    (re.compile(r"&rsquo;"), "’"),
    (re.compile(r"&sbquo;"), "‚"),
    (re.compile(r"&ldquo;"), "“"),
    (re.compile(r"&rdquo;"), "”"),
    (re.compile(r"&bdquo;"), "„"),
    (re.compile(r"&acute;"), "´"),
    (re.compile(r"&#96;"), "`"),
    (re.compile(r"&lrm;"), ""),
    (re.compile(r"&rlm;"), ""),
    (re.compile(r"&times;"), "×"),
    (re.compile(r"&and;"), "∧"),
    (re.compile(r"&or;"), "∨"),
    (re.compile(r"&lang;"), "〈"),
    (re.compile(r"&rang;"), "〉"),
    (re.compile(r"&lsaquo;"), "‹"),
    (re.compile(r"&rsaquo;"), "›"),
    (re.compile(r"&sdot;"), "⋅"),
    (re.compile(r"&middot;"), "·"),
    (re.compile(r"&bull;"), "•"),

    (re.compile(r"<!--.*?-->", flags=re.S), ""),

    # Drop HTML attributes for easier parsing
    (re.compile(r"<(\??[a-zA-Z]+)[^>]{0,1000}?(/?)\s*>"), r"<\1\2>"),

    # ----

    # https://en.wikipedia.org/wiki/Help:HTML_in_wikitext has a big
    # list of allowed elements, some of which are custom tags
    # interpreted by the Mediawiki engine.

    # Unlikely to have parseable prose
    (re.compile(r"<ref/>", flags=re.I), ""),
    (re.compile(r"<ref>.*?</ref>", flags=re.I+re.S), ""),
    (re.compile(r"<references/>", flags=re.I), "\n\n"),
    (re.compile(r"<references>.*?</\s*references>", flags=re.I+re.S), "\n\n"),
    (re.compile(r"<source[^>]*>.*?</source>", flags=re.I+re.S), "\n\n"),
    (re.compile(r"<timeline>.*?</timeline>", flags=re.I+re.S), "\n\n"),
    (re.compile(r"<code>.*?</code>", flags=re.I+re.S), "\n\n"),
    (re.compile(r"<chem>.*?</chem>", flags=re.I+re.S), ""),
    (re.compile(r"<graph>.*?</graph>", flags=re.I+re.S), ""),
    (re.compile(r"<pre>.*?</pre>", flags=re.I+re.S), "\n\n"),
    (re.compile(r"<var>.*?</var>", flags=re.I+re.S), ""),
    (re.compile(r"<hiero>.*?</hiero>", flags=re.I+re.S), ""),
    (re.compile(r"<imagemap>.*?</imagemap>", flags=re.I+re.S), ""),
    (re.compile(r"<mapframe>.*?</mapframe>", flags=re.I+re.S), ""),
    (re.compile(r"<kbd>.*?</kbd>", flags=re.I+re.S), ""),

    # Make the contained text bubble up to become part of the
    # surrounding text
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
    (re.compile(r"<sub>", flags=re.I), ""),  # e.g. PreQ<sub>1</sub>, H<sub>2</sub>O
    (re.compile(r"</sub>", flags=re.I), ""),
    (re.compile(r"<sup>", flags=re.I), ""),
    (re.compile(r"</sup>", flags=re.I), ""),
    (re.compile(r"<s>", flags=re.I), ""),
    (re.compile(r"</s>", flags=re.I), ""),
    (re.compile(r"<u>", flags=re.I), ""),
    (re.compile(r"</u>", flags=re.I), ""),
    (re.compile(r"<del>", flags=re.I), ""),
    (re.compile(r"</del>", flags=re.I), ""),
    (re.compile(r"<time>", flags=re.I), ""),
    (re.compile(r"</time>", flags=re.I), ""),
    (re.compile(r"<onlyinclude>", flags=re.I), ""),
    (re.compile(r"</onlyinclude>", flags=re.I), ""),
    (re.compile(r"<includeonly>", flags=re.I), ""),
    (re.compile(r"</includeonly>", flags=re.I), ""),
    (re.compile(r"<section[^>]*/>", flags=re.I), ""),
    (re.compile(r"<noinclude>", flags=re.I), ""),
    (re.compile(r"</noinclude>", flags=re.I), ""),

    (re.compile(r"__notoc__", flags=re.I), ""),
    (re.compile(r"\[\s*(http|https|ftp):.*?\]", flags=re.I), ""),  # External links
    (re.compile(r"(http|https|ftp):.*?[ $]", flags=re.I), ""),  # Bare URLs

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

    # Some parts of tables can end up outside of {| |} due to templates
    (re.compile(r"! colspan=.*?\n"), ""),
    (re.compile(r"\| colspan=.*?\n"), ""),
    (re.compile(r"\|\|? rowspan=.*?\n"), ""),

    # Make one line per paragraph, being careful to keep headers and
    # list and table items on their own lines
    (re.compile(r"\n\s*\n+"), r"\n\n"),
    (re.compile(r"^\s*\n+"), r"\n"),
    (re.compile(r"(?<!^)(?<![=\n✂\}\]\|])\n(?![\n=\*#:;✂ \|])"), r" "),
    (re.compile(r"\n\n+"), r"\n"),
    (re.compile(r"  +"), " "),

    # Unprotect items that moss protected internally
    (re.compile(r"⁅⁅"), "{{"),
    (re.compile(r"⁆⁆"), "}}"),
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


prose_quote_re = re.compile(r'"\S[^"]{0,1000}?\S"|"\S"|""')
# "" because the contents may have been removed by a previous replacement
parenthetical_re = re.compile(r'\(\S[^\)]{0,1000}?\S\)|\(\S\)|\[\S[^\]]{0,1000}?\S\]|\[\S\]')
ignore_sections_re = re.compile(
    r"(==\s*See also\s*==|"
    r"==\s*External links\s*==|"
    r"==\s*References\s*==|"
    r"==\s*Bibliography\s*==|"
    r"==\s*Further reading\s*==|"
    r"==\s*Sources\s*==|"
    r"==\s*Publications\s*==|"
    r"==\s*Selected publications\s*==|"
    r"==\s*Filmography\s*==|"
    r"==\s*Discography\s*==|"
    r"==\s*Works\s*==|"
    r"==\s*Selected works\s*==|"
    r"==\s*Books\s*==|"
    r"==\s*Compositions\s*==|"
    r"==\s*Recordings\s*=="
    r").*$",
    flags=re.I + re.S)
ignore_headers_re = re.compile("=[^\n]+=\n")
ignore_lists_re = re.compile(r"\n[\*\#;][^\n]*")
line_starts_with_re = re.compile(r"\n[ :†][^\n]*")
# Starts with space - often computer programming code snippets
# Starts with colon - generally quotes or technical content
# † - footnotes


def get_main_body_wikitext(wikitext_input, strong=False):
    # Ignore non-prose and segments not parsed for grammar, spelling, etc.

    # TODO: Get smarter about these sections.  But for now, ignore
    # them, since they are full of proper nouns and URL words.
    wikitext_working = ignore_sections_re.sub("", wikitext_input)

    wikitext_working = prose_quote_re.sub("✂", wikitext_working)
    wikitext_working = ignore_headers_re.sub("", wikitext_working)
    wikitext_working = line_starts_with_re.sub("", wikitext_working)

    if strong:
        wikitext_working = parenthetical_re.sub("", wikitext_working)
        wikitext_working = ignore_lists_re.sub("", wikitext_working)

    """
    quotation_list = blockquote_re.findall(article_text)
    quotation_list.extend(prose_quote_re.findall(article_text))
    if quotation_list:
        article_text = blockquote_re.sub(" ", article_text)
        article_text = prose_quote_re.sub("✂", article_text)

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
    """

    return wikitext_working
