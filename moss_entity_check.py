from moss_dump_analyzer import read_en_article_text
import re
import sys
from unencode_entities import (
    alert, keep, controversial, transform, greek_letters, find_char_num,
    entities_re, fix_text, should_keep_as_is)

# Characters with over 100,000 MOS:STRAIGHT violations deprioritized
# in favor of jwb-straight-quotes-unbalanced.txt
low_priority = """‘’“”"""

strings_found_by_type = {}
non_entity_transform = [string for string
                        in list(transform.keys()) + list(controversial.keys())
                        if not string.startswith("&")]

# -- PERFORMANCE NOTES --

# Run time: About 2.5 hours on 8 cores for 6.6M articles, nothing else running
# (big-bucks), about 30 min on big-board

# Trie-based regex is a little faster than a regular regex, but both
# are a lot slower than string.count() method
# non_entity_transform_re = re.compile("(" + "|".join([re.escape(s) for s in non_entity_transform]) + ")")
# ../venv/bin/pip install trieregex
# from trieregex import TrieRegEx as TRE
# non_entity_transform_words = [re.escape(s) for s in non_entity_transform]
# non_entity_transform_tre = TRE(*non_entity_transform_words)
# non_entity_transform_re = re.compile(non_entity_transform_tre.regex())

# alert_re = re.compile("(" + "|".join([re.escape(s) for s in alert]) + ")")
# Sadly, trie-regex here is slower than a regular regex
# from trieregex import TrieRegEx as TRE
# alert_tre = TRE(*alert)
# alert_re = re.compile(alert_tre.regex())

# No faster than a regular expression
# ../venv/bin/pip install pyahocorasick
# import ahocorasick
# alert_automaton = ahocorasick.Automaton()
# for needle in alert:
#     alert_automaton.add_word(needle, needle)
#
# alert_automaton.make_automaton()
#
# In code:
# for (_end_index, instance) in alert_automaton.iter(article_text):

# --

article_blocklist = [

    # Characters themselves are discussed or listed as part of a mapping
    "CEA-708",
    "CER-GS",
    "Casio calculator character sets",
    "Chinese Character Code for Information Interchange",
    "Code page 259",
    "Code page 293",
    "Code page 310",
    "Code page 351",
    "Code page 361",
    "Code page 437",
    "Code page 897",
    "Code page 899",
    "Code page 903",
    "Code page 904",
    "Code page 921",
    "Code page 950",
    "Code page 1006",
    "Code page 1008",
    "Code page 1040",
    "Code page 1042",
    "Code page 1043",
    "Code page 1046",
    "Code page 1115",
    "Code page 1127",
    "Code page 1169",
    "Code page 1287",
    "Code page 1288",
    "Cork encoding",
    "CTA-708",
    "DEC Hebrew",
    "Digital encoding of APL symbols",
    "DKOI",
    "DIN 66303",
    "Duplicate characters in Unicode",
    "ELOT 927",
    "Emoji",
    "Enclosed Alphanumeric Supplement",
    "Extended Latin-8",
    "Extensions to the International Phonetic Alphabet",
    "FOCAL character set",
    "GB 2312",
    "GOST 10859",
    "Grave accent",
    "IBM 2741",
    "IBM 3270",
    "INIS-8",
    "ISO/IEC 646",
    "ISO/IEC 10367",
    "ISO 5426",
    "ISO 5428",
    "ISO 6862",
    "ISO-IR-111",
    "ISO-IR-200",
    "ISO/IEC 8859-1",
    "ISO/IEC 8859-10",
    "ISO/IEC 8859-11",
    "ISO/IEC 8859-13",
    "ISO/IEC 8859-14",
    "ISO/IEC 8859-15",
    "ISO/IEC 8859-16",
    "ISO/IEC 8859-2",
    "ISO/IEC 8859-3",
    "ISO/IEC 8859-4",
    "ISO/IEC 8859-5",
    "ISO/IEC 8859-6",
    "ISO/IEC 8859-7",
    "ISO/IEC 8859-8",
    "ISO/IEC 8859-9",
    "ISO basic Latin alphabet",
    "ITU T.61",
    "JIS X 0201",
    "JIS X 0208",
    "KOI-8",
    "KOI8-B",
    "KOI8-F",
    "KOI8-R",
    "KOI8-RU",
    "KOI8-U",
    "KPS 9566",
    "KS X 1001",
    "Latin Extended Additional",
    "Latin Extended-B",
    "Latin script in Unicode",
    "List of Japanese typographic symbols",
    "List of Latin letters by shape",
    "List of Latin-script letters",
    "List of mathematical symbols by subject",
    "List of precomposed Latin characters in Unicode",
    "List of typographical symbols and punctuation marks",
    "List of Unicode characters",
    "Lotus Multi-Byte Character Set",
    "LY1 encoding",
    "Mac OS Armenian",
    "Mac OS Celtic",
    "Mac OS Central European encoding",
    "Mac OS Croatian encoding",
    "Mac OS Devanagari encoding",
    "Mac OS Gaelic",
    "Mac OS Georgian",
    "Mac OS Icelandic encoding",
    "Mac OS Roman",
    "Mac OS Romanian encoding",
    "Mac OS Turkish encoding",
    "MIK (character set)",
    "Multinational Character Set",
    "NEC APC character set",
    "NeXT character set",
    "OT1 encoding",
    "Phags-pa (Unicode block)",
    "Phonetic symbols in Unicode",
    "PostScript Standard Encoding",
    "RISC OS character set",
    "Romanization of Arabic",
    "Rough breathing",
    "RPL character set",
    "Schwarzian derivative",
    "Secondary articulation",
    "Sharp pocket computer character sets",
    "SI 960",
    "Sinclair QL character set",
    "Six-bit character code",
    "Spacing Modifier Letters",
    "Specials (Unicode block)",
    "Stokoe notation",
    "Superior letter",
    "T.51/ISO/IEC 6937",
    "Teletext character set",
    "Thai Industrial Standard 620-2533",
    "TI calculator character sets",
    "Tibetan (Unicode block)",
    "TRON (encoding)",
    "Unicode compatibility characters",
    "Unicode equivalence",
    "Unicode input",
    "Unicode subscripts and superscripts",
    "UTF-8",
    "UTF-EBCDIC",
    "Ventura International",
    "Videotex character set",
    "VISCII",
    "VSCII",
    "VT100 encoding",
    "VT52",

    # Note: Characters like &Ohm; and &#x2F802; are changed by
    # Normalization Form Canonical Composition and appear as different
    # Unicode characters, like &Omega;.  Using the HTML entity instead
    # of the raw Unicode character prevents this.

    "Arabic diacritics",
    "Arabic script in Unicode",  # objection from Mahmudmasri
    "Perso-Arabic Script Code for Information Interchange",
    # https://en.wikipedia.org/w/index.php?title=Perso-Arabic_Script_Code_for_Information_Interchange&oldid=prev&diff=900347984&diffmode=source]
    "Eastern Arabic numerals",
    "List of XML and HTML character entity references",
    "Bengali–Assamese script",
    "Modern Arabic mathematical notation",  # LTR/RTL characters
    "List of jōyō kanji",  # Breaks display of certain characters

    # Variation issues, maybe need a variant selector?
    "Seong",
    "Sung-mi",
    "Yasukuni Shrine",

    # Legitimate use of <h2> due to complex layout
    "Main Page",
]


def jwb_escape(text):
    text = text.replace("\\", "\\\\")  # e.g. for <math> markup
    text = text.replace('"', '\\"')
    return text


def add_tuples_to_results(tuple_list):
    if not tuple_list:
        return
    for (result_type, article_title, string) in tuple_list:
        if result_type not in strings_found_by_type:
            strings_found_by_type[result_type] = {}
        if string not in strings_found_by_type[result_type]:
            strings_found_by_type[result_type][string] = []
        articles_with_string = strings_found_by_type[result_type][string]
        articles_with_string.append(article_title)
        strings_found_by_type[result_type][string] = articles_with_string


# Lowercase letters for French and Scandanavian languages that use
# ligatures as standard characters
lc_lig = "a-zøðþęáéóúýǫ́àèòùâêîôûëïöüÿçå"
# Proper nouns with ligatures, which are an exception to the general
# no-ligatures-in-English rule at [[MOS:LIGATURE]].
#  ligature_suppression_pattern = rf"\W[[:upper:]]{lg_lig}*[æœ]{lg_lig}*\W|\W[ÆŒ]{lg_lig}+\W"
#
# The below is omitted from suppression_patterns because æ and œ are
# disabled in unencode_entities.transform_unsafe; detection of
# inappropriate uses of these is now handled by spell check, because
# they are very common standard spelling in French and Scandanavian
# languages.
#  import regex
#  regex.compile(ligature_suppression_pattern),


suppression_patterns = [
    # TODO: Some substitutions should be made anyway in certain
    # contexts. For example, "&#39;" -> "'" is safe inside filenames.

    re.compile(r'{\|\s*class="(wikitable IPA|IPA wikitable|wikitable notatypo|notatypo)".*?\|}', flags=re.S),

    re.compile(r"<(syntaxhighlight.*?</syntaxhighlight"
               r"|blockquote lang=.*?</blockquote"
               r"|<source.*?</source"
               r"|code.*?</code"
               r"|timeline.*?</timeline"
               ")>", flags=re.I+re.S),
    re.compile(r"\[\[(File|Image):.*?(\||\])"),
    re.compile(r"(File:|Image:|link=):[^ ]\.(jpg|JPG|gif|png)"),
    re.compile(r"[^ ]+\.(jpg|JPG|gif|png)\|"),

    # For <gallery> blocks. Must use non-matching lookahead to avoid
    # consuming the beginning of the next line, which is needed to
    # exclude the next filename.
    re.compile(r"(^|\n)\|? *(File|Image):.*?(?=\||\n)"),

    re.compile(r"\| *image[0-9]? *=.*"),
    re.compile(r"\| *img_?[0-9]? *=.*"),
    re.compile(r"\| *ImageFile *=.*"),
    re.compile(r"\| *image_skyline *=.*"),
    re.compile(r"\| *cover *=.*jpg"),

    # TODO: These can be URL-escaped
    re.compile(r"https?://[^ \n\|&]+"),

    re.compile(r"{{[Nn]ot a typo start}}.*?{{[Nn]ot a typo end}}", flags=re.S),

    re.compile(r"{{lang.*?translit=.*?}}|{{([Nn]ot a typo|[Ss]hort description|proper name|DISPLAYTITLE"
               # 7seg uses superscript = as a parameter value
               r"|7seg"

               # Unclear if these should be using Unicode or HTML
               # superscripts/subscripts (including tones like
               # <sup>H</sup> in IPA templates); ignoring for now.
               r"|IPA|UPA|PIE|[Aa]ngle|[Aa]ngbr|[Aa]ngbr IPA|[Aa]udio-IPA"
               r"|[Ll]ang(-\w\w+)?\|"
               r"|[Tt]ransl(iteration)?\|"
               r"|[Zz]h\|"
               r"|[Ss]cript/|"
               r"|[Nn]astaliq"
               r"|[Ii]nterlinear ?\| ?lang="
               r"|([Ii]nfobox )?[Cc]hinese"
               r"|[Cc]har"
               r"|[Ii]ll"  # Interlanguage link
               r"|[Cc]ode\s*\|"
               r"|[Rr]ust\|"
               r"|{{[Cc]ite[^}]+lang(uage)?="
               r").*?}}", flags=re.S),

    re.compile(r"(ipa symbol\d?|poj) *= *[^\n]+"),

    # Allow these characters:
    # ʿ U+02BF Modifier letter left half ring,
    # ʾ U+02BE Modifier letter right half ring
    # ʻ U+02BB 'Okina
    # ʼ U+02BC Modifier letter apostrophe
    # to be used in various non-English orthographies and transliterations,
    # if tagged with the language.
    #
    # re.compile(r"{{(lang|Lang|transliteration|Transliteration)[^}]+[ʿʾʻʼ][^}]+}}", flags=re.S),
    # Disabled for performance - redundant to above
]

needs_ipa_detect_re = re.compile(r"{{[Nn]eeds IPA", flags=re.S)
needs_ipa_remove_re = re.compile(r".{0,100}{{[Nn]eeds IPA.*?}}", flags=re.S)


def get_redacted_article_text(article_text):
    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)

    if needs_ipa_detect_re.search(article_text):
        article_text = needs_ipa_remove_re.sub("", article_text)

    return article_text


skip_article_strings = [
    "{{cleanup lang",
    "{{Cleanup lang",
    "{{cleanup-lang",
    "{{Cleanup-lang",
    "{{which lang",
    "{{move to Wiki",
    "{{Move to Wiki",
    "{{MOS",
]


def entity_check(article_title, article_text):
    if article_title in article_blocklist:
        return

    for skip_string in skip_article_strings:
        if skip_string in article_text:
            return

    # Entities that need to be reported are rare, and text redaction
    # is expensive, so check unredacted text first.
    result_tuples = []
    article_text_redacted = None

    # This is the fastest check
    results_tmp = subcheck_html_entity(article_text, article_title)
    if results_tmp:
        article_text_redacted = get_redacted_article_text(article_text)
        result_tuples.extend(subcheck_html_entity(article_text_redacted, article_title))

    # This check hits most often but is somewhat slow, so it's better to run it on redacted text
    if article_text_redacted:
        result_tuples.extend(subcheck_non_entity(article_text_redacted, article_title))
    else:
        results_tmp = subcheck_non_entity(article_text, article_title)
        if results_tmp:
            # Hint avoids redoing a lot of work
            article_text_redacted = get_redacted_article_text(article_text)
            found_check_strings = set([tup[2] for tup in results_tmp])
            result_tuples.extend(subcheck_non_entity(article_text_redacted, article_title, hint=found_check_strings))

    # This check is the least likely to hit, and is somewhat slow so it's better to run on redacted text
    if article_text_redacted:
        result_tuples.extend(subcheck_alert(article_text_redacted, article_title))
    else:
        results_tmp = subcheck_alert(article_text, article_title)
        if results_tmp:
            # Hint avoids redoing a lot of work
            article_text_redacted = get_redacted_article_text(article_text)
            found_check_strings = set([tup[2] for tup in results_tmp])
            result_tuples.extend(subcheck_alert(article_text_redacted, article_title, hint=found_check_strings))

    return result_tuples


# hint is a list of the only characters that can possibly be in article_text
def subcheck_alert(article_text, article_title, hint=None):
    result_tuples = []

    # Weirdly, this is a lot faster than a pre-compiled regular
    # expression or Aho-Corasick automaton.
    # if not any(alert_word in article_text for alert_word in alert):
    #     return
    # for instance in alert_re.findall(article_text):

    for check_string in hint or alert:
        found_count = article_text.count(check_string)
        if not found_count:
            continue

        # Add the article title for each instance
        for i in range(0, found_count):
            result_tuples.append(("ALERT", article_title, check_string))
    return result_tuples


def subcheck_non_entity(article_text, article_title, hint=None):
    result_tuples = []

    article_text_lower = None
    # Not constructing here because it's rarely needed and uses a lot
    # of CPU (.5 sec per 10,000 articles)

    for check_string in hint or non_entity_transform:
        found_count = article_text.count(check_string)
        if not found_count:
            continue

        if check_string == "₤" and re.search("lira|lire", article_text, flags=re.I+re.S):
            # Per [[MOS:CURRENCY]]
            continue

        if check_string in ["¼", "½", "¾"]:
            if check_string in article_title:
                # e.g. Ranma ½, Bentley 4½ Litre,
                # Category:4 ft 6½ in gauge railways,
                # 1980 Massachusetts Proposition 2½
                continue
            article_text_lower = article_text.lower()
            # Per [[MOS:FRAC]]
            if check_string == "½" and ("chess" in article_text_lower):
                continue
            if "{{frac" not in article_text_lower and "{{sfrac" not in article_text_lower and r"\frac" not in article_text_lower:
                # If no other fractions are present, these three are
                # allowed (they are compatible with screen readers)
                continue

        if check_string == "`" and "{{`}}" in article_text:
            continue
        if check_string == "°K" and "°KMW" in article_text:
            continue
        if check_string == "° F" and not re.search(rf"° F(ahrenheit)?[^a-zA-Z{lc_lig}]", article_text):
            continue
        if check_string == "° C" and not re.search(rf"° C(elsius)?[^a-zA-Z{lc_lig}]", article_text):
            continue
        if check_string == "C°" and article_title == "Complementizer":
            continue

        if check_string in controversial and "<math" in article_text:
            continue

        if check_string == "ϑ" and "θ" not in article_text:
            # Probably not appropriate for basic geometry articles,
            # but some branches of mathematics may prefer it
            # (e.g. [[Chebyshev function]] and [[Lovász number]] - see
            # ([[Wikipedia talk:Manual of Style/Mathematics#‎Can
            # cursive theta be substituted?]], Mar 2022). So this
            # check makes it so the only articles that are flagged are
            # those that use both, which might be accidental
            # inconsistency.
            #
            # This will miss some articles that use cursive theta in
            # Greek words and for simple high school geometry angles.
            continue
        elif check_string == "ϑ":
            # Mixed thetas are intentional
            if article_title in [
                    "Chebyshev function",
                    "Eisenstein series",
                    "J-invariant",
                    "Kamassian language",
                    "Scythian languages",
                    "Scythian religion",
            ]:
                continue

        if check_string in ["¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]:
            if ("{{Infobox Chinese" in article_text
                    or "{{infobox Chinese" in article_text
                    or "{{Chinese" in article_text):
                # For tones in some transcription systems
                continue

        # This intentionally adds the article title as many
        # times as the string appears
        if len(check_string) == 1 and check_string in low_priority:
            for i in range(0, found_count):
                result_tuples.append(("LOW_PRIORITY", article_title, check_string))
        else:
            for i in range(0, found_count):
                result_tuples.append(("UNCONTROVERSIAL", article_title, check_string))
    return result_tuples


def subcheck_html_entity(article_text, article_title):
    result_tuples = []

    # This is super fast, probably because "&" is an uncommon character
    for entity in entities_re.findall(article_text):
        if entity in keep:
            continue
        if entity in alert:
            # Handled above
            continue

        if entity in ["&#91;", "&#93;"]:
            result_tuples.append(("LOW_PRIORITY", article_title, entity))
            continue

        if entity == "&ast;":
            if ("{{Infobox Chinese" in article_text
                    or "{{infobox Chinese" in article_text
                    or "{{Chinese" in article_text):
                # Legitimate use to prevent interpretation as wikitext list syntax
                continue

        if entity in controversial or entity in greek_letters:
            if "<math" in article_text:
                # Editors in these types of articles prefer the HTML
                # entity so that special characters can be found by
                # name in both TeX and HTML markup.
                continue

            if entity in controversial:
                result_tuples.append(("CONTROVERSIAL", article_title, entity))
                continue
            if entity in greek_letters:

                # eta, pi, phi, rho, omega, upsilon
                if any(meson in article_text for meson in ["ta meson", "i meson", "ho meson", "mega meson", "psilon meson", "scalar meson"]):
                    # Per User:Headbomb
                    continue

                result_tuples.append(("GREEK", article_title, entity))
                continue

        if (entity == "&semi;") and "lim=" in article_text:
            # Needed for {{linktext |lim=&semi;{{sp}} |...}}
            # Use {{sp}} instead of &ensp;
            continue
        if should_keep_as_is(entity):
            # Excludes numeric ranges that must remain untouched
            continue
        if find_char_num(entity):
            # Intentionally mixing both known and unknown, all of
            # which can usually be handled seamlessly, though not
            # including numeric entities in the "alert" section,
            # which by definition can't be handled automatically.
            result_tuples.append(("NUMERIC", article_title, entity))
            continue
        if entity in transform:
            result_tuples.append(("UNCONTROVERSIAL", article_title, entity))
            continue
        elif entity == entity.upper() and re.search("[A-Z]+%s" % entity, article_text):
            # Ignore things like "R&B;" and "PB&J;" which is common in railroad names.
            continue
        result_tuples.append(("UNKNOWN", article_title, entity))
    return result_tuples


def dump_dict(section_title, dictionary):
    output = f"=== {section_title} ===\n"

    if section_title == "To avoid":
        output += "Not included in JWB scripts; fix manually or update moss code.\n\n"
    elif section_title == "Unknown":
        output += "Not included in JWB scripts; fix manually or update moss code.\n\n"
    elif section_title == "Uncontroversial entities":
        output += "Fix automatically with jwb-combo.json\n\n"
    elif section_title == "Low priority":
        output += "Consider using jwb-straight-quotes-unbalanced.txt instead.\n\n"
    elif section_title == "Greek letters":
        output += "Fix automatically with jwb-combo.json (articles with {{tag|math}} markup excluded)\n\n"
    elif section_title == "Controversial entities":
        output += "Fix automatically with jwb-combo.json (articles with {{tag|math}} markup excluded)\n\n"
    elif section_title == "Numeric":
        output += "Fix automatically with jwb-combo.json\n\n"

    sorted_items = sorted(dictionary.items(), key=lambda t: (len(t[1]), t[0]), reverse=True)

    for (key, article_list) in sorted_items:

        if section_title == "To avoid":
            # Exclude overlapping entities
            if key in strings_found_by_type["UNCONTROVERSIAL"]:
                continue

        article_set = set(article_list)

        """
        # Actually, can do these with help from more volunteers, if we remember "skip" outcomes
        if len(article_set) > 100000:
            # These should probably be addressed by bot or policy
            # change or more targeted cleanup; leave them off this
            # todo list
            continue
        """

        output += "* %s/%s - %s - %s\n" % (
            len(article_list),
            len(article_set),
            key,
            ", ".join(["[[%s]]" % article for article in sorted(article_set)][0:5000])
            # Limit at 5000 to avoid sorting 100,000+ titles, several
            # times.  Sampled articles aren't always the ones at the
            # beginning of the alphabet as a result, but this doesn't
            # really matter.
        )
    return output


def extract_entities(dictionary):
    return {entity for entity in dictionary.keys()}


def extract_articles(dictionary):
    # Returns a list sorted by:
    # 1.) Frequency of least-frequent entity occurrence, low to high
    # 2.) Alphabetically by entity
    # 3.) Alphabetically by article title
    #
    # Ignores entities with 100,000+ articles because these should be
    # addressed by bot (or policy change)

    articles = list()
    for (entity, article_list) in sorted(sorted(dictionary.items()),
                                         key=lambda tup: len(tup[1])):
        if len(article_list) >= 100000:
            continue
        articles.extend(sorted(article_list)[0:1000])
        # Limit 1000 to avoid excessive report file size

    articles = list(dict.fromkeys(articles))  # uniqify
    return articles


def dump_for_jwb(pulldown_name, bad_entities, file=sys.stdout, articles=[]):
    articles_string = r"\n".join(articles)
    articles_string = articles_string.replace('"', r'\"')
    output_string = '{"%s":' % pulldown_name
    output_string += '{"string":{"articleList":"'
    output_string += articles_string
    output_string += '","summary":"convert special characters found by [[Wikipedia:Typo Team/moss]]"},"bool":{"minorEdit":true,"viaJWB":true,"enableRETF":false,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":true,"containRegex":false,"suppressRedir":false},"replaces":[\n'  # noqa
    # output_string += '","summary":"convert special characters found by [[Wikipedia:Typo Team/moss]]","watchPage":"nochange","skipContains":"","skipNotContains":"","containFlags":"","moveTo":"","editProt":"all","moveProt":"all","protectExpiry":"","namespacelist":["0"],"cmtitle":"","linksto-title":"","pssearch":"","pltitles":""},"bool":{"preparse":false,"minorEdit":true,"viaJWB":true,"enableRETF":true,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":true,"exists-yes":false,"exists-no":true,"exists-neither":false,"skipAfterAction":true,"containRegex":false,"suppressRedir":false,"movetalk":false,"movesubpage":false,"categorymembers":false,"cmtype-page":true,"cmtype-subcg":true,"cmtype-file":true,"linksto":false,"backlinks":true,"embeddedin":false,"imageusage":false,"rfilter-redir":false,"rfilter-nonredir":false,"rfilter-all":true,"linksto-redir":true,"prefixsearch":false,"watchlistraw":false,"proplinks":false},"replaces":[\n'  # noqa

    # Must be before auto-generated replacements
    output_string += r"""{"replaceText":"(&#0?39;'|'&#0?39;)","replaceWith":"\"","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += r"""{"replaceText":"&apos;''","replaceWith":"{{'}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += r"""{"replaceText":"''&apos;","replaceWith":"''{{'}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    # These were useful when there were a lot of badly formatted
    # lists, but now they just make a lot of bad changes.
    # output_string += r"""{"replaceText":"<br ?/?> *&bull;","replaceWith":"\n*","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    # output_string += r"""{"replaceText":"\\* *(.*?)<br ?/?>\n?","replaceWith":"* $1\n","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    # output_string += r"""{"replaceText":"\n&bull; *(.*?)(<br ?/?>)?\n","replaceWith":"\n* $1\n","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""

    output_string += "\n"

    bad_entities_sorted = []
    bad_entities_last = []
    for entity in sorted(bad_entities):
        if entity[0] == "<":
            # </sup><sup> etc. operate on the output of previous regexes
            bad_entities_last.append(entity)
        else:
            bad_entities_sorted.append(entity)
    bad_entities_sorted.extend(bad_entities_last)

    for entity in bad_entities_sorted:
        fixed_entity = fix_text(entity, transform_greek=True)
        fixed_entity = jwb_escape(fixed_entity)
        if fixed_entity in ["\n"]:
            fixed_entity = r"\n"
        if fixed_entity in ["\r", "\t", "", "", "", ""]:  # \r is ^M
            fixed_entity == " "

        if entity != fixed_entity:
            output_string += '{"replaceText":"%s","replaceWith":"%s","useRegex":true,"regexFlags":"g","ignoreNowiki":false},\n' % (
                entity,
                fixed_entity)

    # {{frac}} repair
    output_string += r'{"replaceText":"([0-9]+) ?{{frac\\|([0-9]+)}}","replaceWith":"{{frac|$1|1|$2}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},'
    output_string += "\n"
    output_string += r'{"replaceText":"([0-9]+) ?{{frac\\|([0-9]+)\\|([0-9]+)}}","replaceWith":"{{frac|$1|$2|$3}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},'
    output_string += "\n"

    # MOS:LOGICAL
    output_string += r'{"replaceText":"\"([a-z ,:\\-;]+)([,\\.])\"","replaceWith":"\"$1\"$2","useRegex":true,"regexFlags":"g","ignoreNowiki":false},'
    output_string += "\n"

    # MOS:DOUBLE
    # output_string += r'{"replaceText":" ' + r"'" + r'([A-Za-z ,:\\-;]+)' + r"'" + r'([,\\. }\\)])", "replaceWith":" \"$1\"$2","useRegex":true,"regexFlags":"g","ignoreNowiki":false}'
    # TODO: This is disabled because it fails to respect:
    # * Single quotes properly nested inside double quotes, if there
    #   are words between all the quote marks
    # * {{cite web}} and other templates that put double quote marks
    #   around fields like "title" and "quote".

    prime_accepted_chars = "dijkrtvwxyzCDEFGHIJKMNUVWXYZγδζξϖπστΕΖΗΙΚΜΝΞΠΣΥϒΧΨcgsuBGOPQRSαβϑθκμνςυχψωΒΘΟΡΩab∂ehmnopqALεϵηιλοϱρφϕΑΔΛΦflTΓΤ"

    # Common error
    output_string += """{"replaceText":"{{prime}}\\\\.([0-9]+)","replaceWith":".$1{{prime}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""

    # {{prime}} takes preceding text as an argument to adjust whitespace
    output_string += """{"replaceText":"''(['""" + prime_accepted_chars + """]+)''{{prime}}","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    output_string += """{"replaceText":"''(['""" + prime_accepted_chars + """]+){{prime}}''","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    output_string += """{"replaceText":"([""" + prime_accepted_chars + """]){{prime}}","replaceWith":"{{prime|$1}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    # {{prime}} does not adjust whitespace properly if italics are part of the argument
    output_string += """{"replaceText":"{{prime\\\\|''([""" + prime_accepted_chars + """]+)''}}","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    output_string += """{"replaceText":"([0-9])°([CF])","replaceWith":"$1&nbsp;°$2","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    output_string += """{"replaceText":"&nbsp; ","replaceWith":" ","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    output_string += """{"replaceText":" &nbsp;","replaceWith":" ","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    # CAUTION: Manually edit "north" to "N", etc.
    output_string += r"""{"replaceText":"([0-9]+)° *([0-9]+)('|′|{{prime}}) *([0-9]+)(\"|″|{{pprime}}) *(N|S|north|south),? """
    output_string += r"""*([0-9]+)° *([0-9]+)('|′|{{prime}}) *([0-9]+)(\"|″|{{pprime}}) ?(E|W|east|west)","""
    output_string += r""""replaceWith":"{{coord|$1|$2|$4|$6|$7|$8|$10|$12}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    output_string += r"""{"replaceText":"([0-9]+\\.[0-9]+)°? ?(N|S) ?([0-9]+\\.[0-9]+)°? ?(E|W)","""
    output_string += r""""replaceWith":"{{coord|$1|$2|$3|$4}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"
    output_string += r"""{"replaceText":"([0-9]+)° *([0-9]+)('|′|{{prime}}) *(N|S|north|south),? *([0-9]+)° *([0-9]+)('|′|{{prime}}) *(E|W|east|west)","""
    output_string += r""""replaceWith":"{{coord|$1|$2|$4|$5|$6|$8}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    output_string += r"""{"replaceText":"No\\.([0-9])","replaceWith":"No. $1","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    output_string += r"""{"replaceText":"'Abd","replaceWith":"{{ayin}}Abd","useRegex":true,"regexFlags":"g","ignoreNowiki":false},"""
    output_string += "\n"

    # This must come after the {{coord}} transformations
    # CAUTION: Use {{sky}} for celestial coordinates
    output_string += r"""{"replaceText":"([0-9]+)° ?([0-9]+)['′] ?([0-9]+)[\"″]","replaceWith":"$1° $2{{prime}} $3{{pprime}}","useRegex":true,"regexFlags":"g","ignoreNowiki":false}"""
    output_string += "\n"

    output_string += "]}}"
    print(output_string, file=file)


def dump_results():
    sections = {
        "Unknown": strings_found_by_type.get("UNKNOWN", {}),
        "To avoid": strings_found_by_type.get("ALERT", {}),
        "Low priority": strings_found_by_type.get("LOW_PRIORITY", {}),
        "Uncontroversial entities": strings_found_by_type.get("UNCONTROVERSIAL", {}),
        "Numeric": strings_found_by_type.get("NUMERIC", {}),
        "Greek letters": strings_found_by_type.get("GREEK", {}),
        "Controversial entities": strings_found_by_type.get("CONTROVERSIAL", {})
    }
    for (section_title, dictionary) in sections.items():
        output = dump_dict(section_title, dictionary)
        print(output)

    # Make list of articles to fix in JWB
    """
    # Sorted from least-frequent to most-frequent across all types
    mega_dict = {}
    for dic_type in ["CONTROVERSIAL", "GREEK", "NUMERIC", "UNCONTROVERSIAL", "LOW_PRIORITY"]:
        mega_dict.update(strings_found_by_type.get(dic_type, {}))
    articles = extract_articles(mega_dict)
    articles = list(dict.fromkeys(articles))  # uniqify across sublists
    print("\n".join(articles[0:1000]), file=articlesf)
    """

    # By section, from least-frequent to most-frequent with each section
    articles = []
    for dic_type in ["CONTROVERSIAL", "GREEK", "NUMERIC", "UNCONTROVERSIAL", "LOW_PRIORITY"]:
        articles += extract_articles(strings_found_by_type.get(dic_type, {}))
    articles = list(dict.fromkeys(articles))  # uniqify across sublists

    # If the list is too long, it starts to slow down JWB JavaScript
    articles = articles[0:2500]

    # with open("jwb-articles.txt", "w") as articlesf:
    #     print("\n".join(articles), file=articlesf)

    with open("jwb-combo.json", "w") as combof:
        bad_entities = set()
        for dic_type in ["ALERT", "LOW_PRIORITY", "UNCONTROVERSIAL", "UNKNOWN", "NUMERIC", "CONTROVERSIAL", "GREEK"]:
            dictionary = strings_found_by_type.get(dic_type, {})
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=combof, articles=articles)


if __name__ == '__main__':
    read_en_article_text(entity_check, process_result_callback=add_tuples_to_results, parallel=True)
    dump_results()
