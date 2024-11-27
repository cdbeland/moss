# -*- coding: utf-8 -*-

import os
import re
from string import punctuation
import sys
from lru import LRU
try:
    from wikitext_util import html_tag_re, contractions
    from unencode_entities import entities_re
except ImportError:
    from .wikitext_util import html_tag_re
    from .unencode_entities import entities_re

all_words = set()
punctuation_tmp = punctuation
punctuation_re = re.compile(r"[ " + punctuation + r"]")
compound_separators_re = re.compile(r"[—–/\-]")
#                                      emdash, endash, slash, hyphen


def add_tokens(line):
    line = line.replace("_", " ")
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


def load_data():
    print("Loading spellcheck dictionary...", file=sys.stderr)

    # TODO: Possibly move this to postgres or MySQL.  Load DB as part
    # of update_downloads.sh; startup time is very slow due to loading
    # this all into Python, even though accessing in-memory data is
    # very fast.

    with open("/var/local/moss/bulk-wikipedia/For_Wiktionary", "r") as moss_html_file:
        moss_html = moss_html_file.read()
        queued_matches = re.findall('"https://en.wiktionary.org/wiki/(.*?)"', moss_html)
        if not queued_matches:
            raise Exception("Empty Wiktionary queue; regex broken?")
        for queued_match in queued_matches:
            add_tokens(queued_match)

    for filename in [
            "/var/local/moss/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0",
            "/var/local/moss/bulk-wikipedia/enwiki-latest-all-titles-in-ns0",
            "/var/local/moss/bulk-wikipedia/specieswiki-latest-all-titles-in-ns0",
            "/var/local/moss/bulk-wikipedia/Wikispecies:Requested_articles",
            "/var/local/moss/bulk-wikipedia/Before_2019",
            "/var/local/moss/bulk-wikipedia/2020",
            "/var/local/moss/bulk-wikipedia/2021",
            "/var/local/moss/bulk-wikipedia/Old_case_notes",
    ]:
        with open(filename, "r") as title_list:
            for line in title_list:
                add_tokens(line)


if not os.environ.get("NO_LOAD"):
    load_data()


abbr_re = re.compile(r"\.\w\.$")
all_letters_re = re.compile(r"^[^\W\d_]+$", flags=re.UNICODE)
period_splice_re = re.compile(r"^[a-zA-Z]*[a-z]\.[A-Z][a-zA-Z]*$")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Delimiting_.28grouping_of_digits.29
base_number_format = r"(\d{1,4}|\d{1,3},\d\d\d|\d{1,3},\d\d\d,\d\d\d)(\.\d+)?"
# (possibly incomplete list)
# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Decimals
# says that "0.02" is generally favored over ".02" except for
# e.g. calibers and batting averages (which are filtered out elsewhere)

number_prefix_symbols = [
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currency_symbols
    r"±",
    r"−",  # U+2212 Minus sign; hyphen-minus is specifically not allowed
    r"\+",
    r"~",  # Not officially blessed:

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currency_symbols
    r"\$",
    r"US\$",
    r"€",
    r"£",  # Must be used for British pound (and others) rather than ₤
    r"₤",  # Must be used for Italian lira (and others) rather than £
    r"¥",
    r"₹",
    r"₴",
    r"₱",
]

prefixed_number_formats = [
    "%s%s" % (prefix, base_number_format) for prefix in number_prefix_symbols
]

number_formats_allowed_re = re.compile(
    r"(%s|%s%%|%s)" % (base_number_format,
                       base_number_format,
                       "|".join(prefixed_number_formats)))

# Word blocklist
bad_words = {
    # Per [[MOS:YOU]]
    "you",
    "your",

    "and/or",  # [[MOS:AND/OR]]

    # Bad syntax, requires argument
    "{{formatnum:}}",

    # Should be "God" when in regular prose, not necessarily in direct
    # quotes and titles
    "G-d",
}
# Per [[MOS:CONTRACTION]] and sourced from
bad_words.update(contractions)

bad_characters = {
    # Also works for multi-character substrings

    # See similar list in unencode_entities.py!
    # [[MOS:LIGATURE]], list adapted from:
    #  https://en.wikipedia.org/wiki/Ligature_(writing)
    # To be ignored for non-English languages if the spelling with the
    # ligature is considered standard, using {{lang}}.
    "Ꜳ",
    "ꜳ",
    "Ꜵ",
    "ꜵ",
    "Ꜷ",
    "ꜷ",
    "Ꜹ",
    "ꜹ",
    "🙰",
    "ﬀ",
    "ﬃ",
    "ﬄ",
    "ﬁ",
    "ﬂ",
    "Ƕ",
    "ƕ",
    "℔",
    "Ỻ",
    "ỻ",
    "Ꝏ",
    "ꝏ",
    "ﬆ",
    "Ꜩ",
    "ꜩ",
    "ᵫ",
    "ꭣ",
    "Ꝡ",
    "ꝡ",

    # These are extremely common in standard French and Scandanavian
    # languages, where they are allowed by [[MOS:LIGATURE]] because
    # they are considered standard spellings. De-listed here so that
    # any inappropriate uses in English are detected by dictionary
    # lookup failure (except for archaic/non-standard dictionary
    # entries, which are a TODO to suppress).
    # "æ",
    # "Æ",
    # "œ",
    # "Œ",

    # Per [[MOS:BLOCKQUOTE]]
    "{{cquote",
    # This type of string must be protected from template removal (see
    # early_substitutions and substitutions in wikitext_util)

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

    # Ordinal indicators allowed for non-English languages
    # [[MOS:ORDINAL]]
    # "ª",
    # "º",
}

# Treated as separate words by NLTK tokenizer
allow_list = {

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
    "<mapframe/>",
    "<templatestyles/>",
    "</templatestyles>",
    "<caption>",
    "</caption>",

    # Allowed HTML
    "<samp>",  # Replaces <tt>, {{samp}} can't do multi-line
    "</samp>",

    # Bidirectional text
    # For example when Latin and Hebrew characters are mixed.
    # Sometimes used spuriously. Might be replaced by using {{lro}},
    # {{rlo}}, etc.?
    "<bdi>",
    "</bdi>",

    # TODO: This discussion was somewhat inconclusive:
    # https://en.wikipedia.org/wiki/Wikipedia:Templates_for_discussion/Log/2019_March_17#Template:Dfn
    # These should probably be converted to {{dfn}} or markup removed.
    "<dfn>",
    "</dfn>",

    # TODO: Handle general mathematical notation in HTML here or in
    # regexes.  (<math>...</math> text will be removed.)  See:
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Mathematics#Using_HTML
}


print("Done.", file=sys.stderr)


cached_answers = LRU(10000)


# Returns True, False, or "uncertain"
def is_word_spelled_correctly(word_mixedcase):

    if not word_mixedcase:
        return True

    # For speed.  Should work well because in most articles the same
    # words are used several times, and English has a small number of
    # highly used words across all articles.
    if word_mixedcase in cached_answers:
        return cached_answers[word_mixedcase]
    answer = _is_word_spelled_correctly_impl(word_mixedcase)
    cached_answers[word_mixedcase] = answer
    return answer


def _is_word_spelled_correctly_impl(word_mixedcase):

    # word_lower = word_mixedcase.lower()

    # if word_lower in bad_words:
    if word_mixedcase in bad_words:
        # TODO: Ignoring capitalized words for now due to lots of
        # false positives; may want to detect and ignore italics
        # and/or multi-word proper nouns.
        return False

    if any(substring in word_mixedcase for substring in bad_characters):
        return False

    if word_mixedcase.lower() in all_words:
        return True

    if word_mixedcase in allow_list:
        return True

    if entities_re.match(word_mixedcase):
        # HTML entities show up in the entities report, and that looks
        # at sections ignored by spell check.
        return True

    if html_tag_re.match(word_mixedcase):
        # HTML tags should be whitelisted if allowed in wikitext, or
        # removed by a previous phase of processing.
        return False

    if number_formats_allowed_re.match(word_mixedcase):
        return True

    if is_science_expression(word_mixedcase):
        return True

    # Possessive: NLTK parses e.g. "'s" as a separate word, which
    # Wiktionary has listed.

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

    if word_mixedcase.endswith("(s)"):
        word_mixedcase = word_mixedcase[:-3] + "s"
        search_again = True

    if search_again:
        if not word_mixedcase:
            return True
        if word_mixedcase.lower() in all_words:
            return True

    word_parts_mixedcase = compound_separators_re.split(word_mixedcase)
    if len(word_parts_mixedcase) > 1:
        result_list = [is_word_spelled_correctly(word_part) for word_part in word_parts_mixedcase]

        # Results may be mixed (like "misspellledword-the-Captializedword"
        # would produce [False, True, "uncertain"]) so return the
        # "worst" value from the list.
        if False in result_list:
            return False
        if "uncertain" in result_list:
            return "uncertain"
        return True

    # Ignore all capitalized words (might be proper noun which we
    # legitimately don't have an entry for)
    # TODO: Detect beginning-of-sentence and optionally report
    # possibly misspelled words.  This might work well constraining to
    # edit-distance 1 from a known word, and grammatical constituent
    # parsing may also help.
    if word_mixedcase[0].upper() == word_mixedcase[0]:
        return "uncertain"

    if not all_letters_re.match(word_mixedcase):
        if period_splice_re.match(word_mixedcase):
            plus_period = "%s." % word_mixedcase.lower()
            if plus_period in all_words:
                # Because the word segmenter often doesn't keep the
                # trailing period with the word.  TODO: Catch situations
                # where the trailing period is actually missing.
                return True
            return False

        # Lots of things here are probably legitimate, but we need
        # better pattern-matching filters before it's worthwhile
        # posting these for editors to fix.
        return "uncertain"

    return False


numerator_words = {
    "m³",
    "km³",
    "ft³",
    "µg",
    "g",
    "mg",
    "l",
    "µmol",
    "people",  # Not persons
    "inhabitants",  # Not inhab, hab
    "kwh",
    "cells",
}

demoninator_words = {
    "m",
    "m²",
    "m³",
    "km²",
    "cm",
    "cm³",
    "mi²",
    "ft²",
    "µl",
    "ml",  # or mL?
    "dl",  # or dL?
    "g",
    "kg",
    "s",
    "second",
    "min",
    "h",
    "day",
    "year",
}


def is_science_expression(word):
    parts = word.split("/")
    if len(parts) == 2 and parts[0] in numerator_words and parts[1] in demoninator_words:
        return True
    return False
