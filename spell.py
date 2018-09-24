# -*- coding: utf-8 -*-

import re
from string import punctuation
import sys

print("Loading spellcheck dictionary...", file=sys.stderr)

# TODO: Possibly move this to postgres or MySQL.  Load DB as part of
# update_downloads.sh; startup time is very slow due to loading this
# all into Python, even though accessing in-memory data is very fast.

all_words = set()
punctuation_tmp = punctuation
punctuation_re = re.compile(r"[ " + punctuation + r"]")

for filename in [
        "/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0",
        "/bulk-wikipedia/enwiki-latest-all-titles-in-ns0",
        "/bulk-wikipedia/specieswiki-latest-all-titles-in-ns0",
        "/bulk-wikipedia/Wikispecies:Requested_articles",
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            line = line.strip().lower()

            # Mostly splitting on " ", but also ":", etc.
            [all_words.add(title_word)
             for title_word
             in punctuation_re.split(line)
             if title_word]

            # Re-parse splitting only on " " to make sure forms like
            # "'s" get added (for compatibility with the NLTK
            # tokenizer)
            [all_words.add(title_word)
             for title_word
             in line.split(" ")
             if title_word]

abbr_re = re.compile(r"\.\w\.$")
all_letters_re = re.compile(r"^[^\W\d_]+$", flags=re.UNICODE)
html_entity_re = re.compile(r"&#?[a-zA-Z]+;")
html_tag_re = re.compile(r"<\??/?\s*[a-zA-Z]+\s*/?\s*>")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Delimiting_.28grouping_of_digits.29
base_number_format = "(\d{1,4}|\d{1,3},\d\d\d|\d{1,3},\d\d\d,\d\d\d)(\.\d+)?"
# (possibly incomplete list)
# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Decimals
# says that "0.02" is generally favored over ".02" except for
# e.g. calibers and batting averages (which can be marked with {{not a typo}})

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currency_symbols
number_prefix_symbols = [
    "±",
    r"\$",
    r"US\$",
    "€",
    "£",
    "¥",
    "₹",
    "₴",
]

prefixed_number_formats = [
    "%s%s" % (prefix, base_number_format) for prefix in number_prefix_symbols
]

number_formats_allowed_re = re.compile(
    r"(%s|%s%%|%s)" % (base_number_format,
                       base_number_format,
                       "|".join(prefixed_number_formats)))


prohibited_list = [
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Text_formatting#HTML_character_entity_references
    # Use "..." instead
    "…",
    # micro -> mu
    "µ",
    # No Unicode fractions
    "¼",
    "½",
    "¾",
    "⅐",
    "⅑",
    "⅒",
    "⅓",
    "⅔",
    "⅕",
    "⅖",
    "⅗",
    "⅘",
    "⅙",
    "⅚",
    "⅛",
    "⅜",
    "⅝",
    "⅞",
    "⅟",
    "&frasl;",
    "⁄",  # U+2044
    # Use <sup> and <sub> instead of Unicode subscripts and superscripts
    "²",
    "³",
    "¹",
    "⁰",
    "ⁱ",
    "⁴",
    "⁵",
    "⁶",
    "⁷",
    "⁸",
    "⁹",
    "⁺",
    "⁻",
    "⁼",
    "⁽",
    "⁾",
    "ⁿ",
    "₀",
    "₁",
    "₂",
    "₃",
    "₄",
    "₅",
    "₆",
    "₇",
    "₈",
    "₉",
    "₊",
    "₋",
    "₌",
    "₍",
    "₎",
    "ₐ",
    "ₑ",
    "ₒ",
    "ₓ",
    "ₔ",
    "ₕ",
    "ₖ",
    "ₗ",
    "ₘ",
    "ₙ",
    "ₚ",
    "ₛ",
    "ₜ",
    "ª",
    "º",
    "ⱽ",
    "ⱼ",
    "ꝰ",
    "ꟸ",
    "ꟹ",
    "ꭜ",
    "ꭝ",
    "ꭞ",
    "ꭟ",
    "ͣ",
    "ͤ",
    "ͥ",
    "ͦ",
    "ͧ",
    "ͨ",
    "ͩ",
    "ͪ",
    "ͫ",
    "ͬ",
    "ͭ",
    "ͮ",
    "ͯ",
    "ᷓ",
    "ᷔ",
    "ᷕ",
    "ᷖ",
    "ᷗ",
    "ᷘ",
    "ᷙ",
    "ᷚ",
    "ᷛ",
    "ᷜ",
    "ᷝ",
    "ᷞ",
    "ᷟ",
    "ᷠ",
    "ᷡ",
    "ᷢ",
    "ᷣ",
    "ᷤ",
    "ᷥ",
    "ᷦ",
    "ᷧ",
    "ᷨ",
    "ᷩ",
    "ᷪ",
    "ᷫ",
    "ᷬ",
    "ᷭ",
    "ᷮ",
    "ᷯ",
    "ᷰ",
    "ᷱ",
    "ᷲ",
    "ᷳ",
    "ᷴ",
    "᷊",
    "ʰ",
    "ʱ",
    "ʲ",
    "ʳ",
    "ʴ",
    "ʵ",
    "ʶ",
    "ʷ",
    "ʸ",
    "ˀ",
    "ˁ",
    "ˠ",
    "ˡ",
    "ˢ",
    "ˣ",
    "ˤ",
    "ᴬ",
    "ᴭ",
    "ᴮ",
    "ᴯ",
    "ᴰ",
    "ᴱ",
    "ᴲ",
    "ᴳ",
    "ᴴ",
    "ᴵ",
    "ᴶ",
    "ᴷ",
    "ᴸ",
    "ᴹ",
    "ᴺ",
    "ᴻ",
    "ᴼ",
    "ᴽ",
    "ᴾ",
    "ᴿ",
    "ᵀ",
    "ᵁ",
    "ᵂ",
    "ᵃ",
    "ᵄ",
    "ᵅ",
    "ᵆ",
    "ᵇ",
    "ᵈ",
    "ᵉ",
    "ᵊ",
    "ᵋ",
    "ᵌ",
    "ᵍ",
    "ᵏ",
    "ᵐ",
    "ᵑ",
    "ᵒ",
    "ᵓ",
    "ᵖ",
    "ᵗ",
    "ᵘ",
    "ᵚ",
    "ᵛ",
    "ᵢ",
    "ᵣ",
    "ᵤ",
    "ᵥ",
    "ᵝ",
    "ᵞ",
    "ᵟ",
    "ᵠ",
    "ᵡ",
    "ᵦ",
    "ᵧ",
    "ᵨ",
    "ᵩ",
    "ᵪ",
    "ᵸ",
    "ᵎ",
    "ᵔ",
    "ᵕ",
    "ᵙ",
    "ᵜ",
    "ᶛ",
    "ᶜ",
    "ᶝ",
    "ᶞ",
    "ᶟ",
    "ᶠ",
    "ᶡ",
    "ᶢ",
    "ᶣ",
    "ᶤ",
    "ᶥ",
    "ᶦ",
    "ᶧ",
    "ᶨ",
    "ᶩ",
    "ᶪ",
    "ᶫ",
    "ᶬ",
    "ᶭ",
    "ᶮ",
    "ᶯ",
    "ᶰ",
    "ᶱ",
    "ᶲ",
    "ᶳ",
    "ᶴ",
    "ᶵ",
    "ᶶ",
    "ᶷ",
    "ᶸ",
    "ᶹ",
    "ᶺ",
    "ᶻ",
    "ᶼ",
    "ᶽ",
    "ᶾ",
    "ᶿ",
    "ꚜ",
    "ꚝ",
    "ⷠ",
    "ⷡ",
    "ⷢ",
    "ⷣ",
    "ⷤ",
    "ⷥ",
    "ⷦ",
    "ⷧ",
    "ⷨ",
    "ⷩ",
    "ⷪ",
    "ⷫ",
    "ⷬ",
    "ⷭ",
    "ⷮ",
    "ⷯ",
    "ⷰ",
    "ⷱ",
    "ⷲ",
    "ⷳ",
    "ⷴ",
    "ⷵ",
    "ⷶ",
    "ⷷ",
    "ⷸ",
    "ⷹ",
    "ⷺ",
    "ⷻ",
    "ⷼ",
    "ⷽ",
    "ⷾ",
    "ⷿ",
    "ꙴ",
    "ꙵ",
    "ꙶ",
    "ꙷ",
    "ꙸ",
    "ꙹ",
    "ꙺ",
    "ꙻ",
    "ꚞ",
    "ꚟ",
    "ჼ",
    "㆒",
    "㆓",
    "㆔",
    "㆕",
    "㆖",
    "㆗",
    "㆘",
    "㆙",
    "㆚",
    "㆛",
    "㆜",
    "㆝",
    "㆞",
    "㆟",
    "ⵯ",

    # sum -> sigma
    "∑",
    # prod -> Pi
    "∏",
    # horbar
    "―",

    # Unnecessary whitespace
    "&ensp;",
    "&emsp;",
    "&zwj;",
]

# Treated as separate words by NLTK tokenizer
allowed_list = [

    # Legitimate English prose punctuation
    ",",
    "?",
    "!",
    "-",
    "(",
    ")",
    "[",
    "]",
    "'",
    '"',
    ":",
    ".",

    # Wiki markup
    "*",
    "#",
    "<poem>",
    "</poem>",
    "<abbr>",
    "</abbr>",

    # Allowed HTML entities per
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Text_formatting#HTML_character_entity_references
    # (May want to comment these out occasionaly and make sure the
    # uses are legitimate, or convert some or all to <nowiki>?)
    "&amp;",
    "&lt;",
    "&gt;",
    "&#91;",
    "&#93;",
    "&apos;",
    "&zwnj;",

    # TODO: Handle general mathematical notation in HTML here or in
    # regexes.  (<math>...</math> text will be removed.)  See:
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Mathematics#Using_HTML
]


print("Done.", file=sys.stderr)


# Returns True, False, or "uncertain"
def is_word_spelled_correctly(word_mixedcase):

    if not word_mixedcase:
        return True

    if word_mixedcase.lower() in all_words:
        return True

    if word_mixedcase in allowed_list:
        return True

    if html_entity_re.match(word_mixedcase):
        # Allowed HTML-escaped characters should have been converted
        # to a real UTF-8 character in a previous phase of processing.
        # If they have not, this is a sign that the rule for this
        # particular character either isn't coded into moss or that it
        # was violated by the wikitext.  Either way, it's an error
        # that needs to be fixed.
        return False

    if html_tag_re.match(word_mixedcase):
        # HTML tags should be whitelisted if allowed in wikitext, or
        # removed by a previous phase of processing.
        return False

    if number_formats_allowed_re.match(word_mixedcase):
        return True

    for substring in prohibited_list:
        if substring in word_mixedcase:
            return False

    # Possessive: NLTK parses e.g. "'s" as a separate word, which
    # Wikitionary has listed.

    # https://en.wiktionary.org/wiki/Wiktionary:Criteria_for_inclusion#Inflections
    # says that plural forms SHOULD be in the dictionary, so we do
    # NOT exclude them systematically.  Any plurals that show up
    # as misspelled words should be added to Wiktionary following
    # the example at: https://en.wiktionary.org/wiki/cameras

    search_again = False

    # F.C. vs. lastwordinsentence.
    if not abbr_re.search(word_mixedcase):
        word_mixedcase = word_mixedcase.rstrip(".")
        search_again = True

    if word_mixedcase.startswith("†"):
        # Used to indicate extinct species
        word_mixedcase = word_mixedcase.lstrip("†")
        search_again = True

    if search_again:
        if not word_mixedcase:
            return True
        if word_mixedcase.lower() in all_words:
            return True

    # Ignore all capitalized words (might be proper noun which we
    # legitimately don't have an entry for)
    # TODO: Detect beginning-of-sentence and optionally report
    # possibly misspelled words.  This might work well constraining to
    # edit-distance 1 from a known word, and grammatical constituent
    # parsing may also help.
    if word_mixedcase[0].upper() == word_mixedcase[0]:
        return "uncertain"

    word_parts_mixedcase = re.split(u"[––/-]", word_mixedcase)
    # emdash, endash, slash, hyphen
    if len(word_parts_mixedcase) > 1:
        any_bad = False
        for part in word_parts_mixedcase:
            if not (part.lower() in all_words):
                any_bad = True
        if not any_bad:
            return True

    # Lots of things here are probably legitimate, but we need better
    # pattern-matching filters before it's worthwhile posting these
    # for editors to fix.
    if not all_letters_re.match(word_mixedcase):
        return "uncertain"

    return False
