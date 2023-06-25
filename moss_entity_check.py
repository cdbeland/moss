from moss_dump_analyzer import read_en_article_text
import re
import sys
from unencode_entities import (
    alert, keep, controversial, transform, greek_letters, find_char_num,
    entities_re, fix_text, should_keep_as_is)

low_priority = "０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ" \
    "¹²³⁴⁵⁶⁷⁸⁹⁰ⁱ⁺⁻⁼⁽⁾ᵃᵇᶜᵈᵉᶠᵍʰⁱʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻᴬᴮᴰᴱᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿᵀᵁⱽᵂ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₐₑₕᵢⱼₖₗₘₙₒₚᵣₛₜᵤᵥₓꟹᵝᵞᵟᵋᶿᶥᶹᵠᵡᵦᵧᵨᵩᵪᵅᶜ̧ᶞᵊᶪᶴᶵꭩˀₔᵑ"

strings_found_by_type = {}
non_entity_transform = [string for string
                        in list(transform.keys()) + list(controversial.keys())
                        if not string.startswith("&")]

# -- PERFORMANCE NOTES --

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
    "' (disambiguation)",
    "AA",
    "ANSEL",
    "ARIB STD B24 character set",
    "ALCOR",
    "ALGOL",
    "ALGOL 68",
    "ASCII",
    "ASMO 449",
    "AV",
    "AZERTY",
    "Adobe Glyph List",
    "Afrasianist phonetic notation",
    "AltGr key",
    "Americanist phonetic notation",
    "Ampersand",
    "Apostrophe",
    "Arabic alphabet",
    "Atari ST character set",
    "Ayin",
    "Baudot code",
    "Basic Latin (Unicode block)",
    "Big5",
    "Bitstream International Character Set",
    "Blackboard bold",
    "Bookshelf Symbol 7",
    "Bracket",
    ".ca",
    "C",
    "(C)",
    "C (disambiguation)",
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
    "Colon (punctuation)",
    "Compose key",
    "Computer Braille Code",
    "Cork encoding",
    "CTA-708",
    "Dania transcription",
    "Dash",
    "Devanagari transliteration",
    "DEC Hebrew",
    "Digital encoding of APL symbols",
    "DKOI",
    "DIN 66303",
    "Duplicate characters in Unicode",
    "Ellipsis",
    "ELOT 927",
    "Emoji",
    "En (typography)",
    "Enclosed Alphanumeric Supplement",
    "Extended Latin-8",
    "Extensions to the International Phonetic Alphabet",
    "Ezh",
    "FFL",
    "FOCAL character set",
    "FR",
    "G",
    "GB 2312",
    "German keyboard layout",
    "GOST 10859",
    "Grave accent",
    "Greek script in Unicode",
    "H",
    "Hashtag",
    "Hook (diacritic)",
    "HP Roman",
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
    "Jeremy Burge",
    "JIS X 0201",
    "JIS X 0208",
    "K",
    "KOI-8",
    "KOI8-B",
    "KOI8-F",
    "KOI8-R",
    "KOI8-RU",
    "KOI8-U",
    "KPS 9566",
    "KS X 1001",
    "L",
    "Latin Extended Additional",
    "Latin Extended-B",
    "Latin script in Unicode",
    "Letterlike Symbols",
    "Ligature (writing)",
    "List of Japanese typographic symbols",
    "List of Latin letters by shape",
    "List of Latin-script letters",
    "List of mathematical symbols by subject",
    "List of precomposed Latin characters in Unicode",
    "List of typographical symbols and punctuation marks",
    "List of Unicode characters",
    "Lotus Multi-Byte Character Set",
    "LY1 encoding",
    "M",
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
    "Mathematical Alphanumeric Symbols",
    "Mathematical operators and symbols in Unicode",
    "MIK (character set)",
    "Mojibake",
    "Multinational Character Set",
    "NEC APC character set",
    "NeXT character set",
    "Number Forms",
    "Numerals in Unicode",
    "Numero sign",
    "Numismatics",
    "OT1 encoding",
    "Palatal hook",
    "PETSCII",
    "Phags-pa (Unicode block)",
    "Phi",
    "Phonetic symbols in Unicode",
    "PostScript Standard Encoding",
    "Prime (symbol)",
    "Radical symbol",
    "Regional indicator symbol",
    "Registered trademark symbol",
    "RISC OS character set",
    "Roman numerals",
    "Romanization of Arabic",
    "Rough breathing",
    "RPL character set",
    "Quotation mark",
    "S",
    "Schwarzian derivative",
    "Secondary articulation",
    "Service mark",
    "Sharp pocket computer character sets",
    "Square sign",
    "SI 960",
    "Sinclair QL character set",
    "Six-bit character code",
    "Spacing Modifier Letters",
    "Specials (Unicode block)",
    "Slash (punctuation)",
    "Slashed zero",
    "Stokoe notation",
    "Summation",
    "Superior letter",
    "Symbol (typeface)",
    "T",
    "T.51/ISO/IEC 6937",
    "Tab key",
    "Tab-separated values",
    "Teletext character set",
    "Thai Industrial Standard 620-2533",
    "TI calculator character sets",
    "Tibetan (Unicode block)",
    "Tilde",
    "Trademark symbol",
    "TRON (encoding)",
    "Unicode compatibility characters",
    "Unicode equivalence",
    "Unicode input",
    "Unicode subscripts and superscripts",
    "UTF-8",
    "UTF-EBCDIC",
    "V",
    "Ventura International",
    "Videotex character set",
    "VISCII",
    "VSCII",
    "VT100 encoding",
    "VT52",
    "W",
    "Wang International Standard Code for Information Interchange",
    "Warmian-Masurian Voivodeship",
    "Welsh orthography",
    "Western Latin character sets (computing)",
    "Whitespace (programming language)",
    "Windows-1250",
    "Windows-1251",
    "Windows-1252",
    "Windows-1253",
    "Windows-1254",
    "Windows-1256",
    "Windows-1257",
    "Windows-1258",
    "Windows-1270",
    "Windows Cyrillic + Finnish",
    "Windows Cyrillic + French",
    "Windows Cyrillic + German",
    "Windows Glyph List 4",
    "Windows Polytonic Greek",
    "Wingdings",
    "World glyph set",
    "X",
    "Xerox Character Code Standard",
    "Yakut scripts",
    "YUSCII",
    "Zero-width space",
    "Z",
    "Œ",

    # Note: Characters like &Ohm; and &#x2F802; are changed by
    # Normalization Form Canonical Composition and appear as different
    # Unicode characters, like &Omega;.  Using the HTML entity instead
    # of the raw Unicode character prevents this.

    "Arabic diacritics",
    "Arabic script in Unicode",  # objection from Mahmudmasri
    "Perso-Arabic Script Code for Information Interchange",
    # https://en.wikipedia.org/w/index.php?title=Perso-Arabic_Script_Code_for_Information_Interchange&oldid=prev&diff=900347984&diffmode=source]
    "Yiddish orthography",
    "Eastern Arabic numerals",
    "List of XML and HTML character entity references",
    "Bengali–Assamese script",
    "Modern Arabic mathematical notation",  # LTR/RTL characters
    "List of jōyō kanji",  # Breaks display of certain characters

    # Ligatures correctly used
    "Massachusett dialects",
    "Massachusett language",
    "Massachusett writing systems",
    "Wampum",
    "Alchemical symbol",
    "Mayan languages",
    "Tezos",
    "Hubert Déquier",
    "Komi Nje",
    "Flow process chart",

    # Legitimate use of <h2> due to complex layout
    "Main Page",

    # &zwj; apparently needed
    "Rasm",
    "The Partisan",
    "44th Kerala State Film Awards",
    "Sumana Amarasinghe",
    "Gopi Sundar",
    "SASM/GNC romanization",
    "List of Malayalam films of 2021",
    "Memoirs of the Actor in a Supporting Role",
    "Muslim Youth League",
    "N. F. Varghese",

    # Correctly uses U+2011 Non-Breaking Hypens
    "Börje",

    # Correctly uses center dots
    "Additive category",

    # Legitimate uses of ©
    "Bobbsey Twins",

    # Variation issues, maybe need a variant selector?
    "Seong",
    "Sung-mi",
    "Yasukuni Shrine",

    # African language needs slash in link
    "2011 South African municipal elections",

    # Special character in URL
    "Almah",
    "Cray XC50",
    "Rallying",
    "Pegeen Vail Guggenheim",
    "Power electronic substrate",
    ".450 No 2 Nitro Express",
    "Armengol de Aspa",
    "Naoya Uchida",
    "Yoshito Yasuhara",

    # Special character in file name (<gallery> or parameter)
    "Collection (publishing)",
    "Découvertes Gallimard",
    "Hillman Minx",
    "Grammaire égyptienne",
    "Ōtaguro Park",
    "Cinder cloudy catshark",
    "Piano Concerto (Khachaturian)",
    "Charles Francis Adams III",
    "Daihatsu Boon",
    "Daihatsu Wake",
    "KARI KSR-3",
    "Nanzen-ji",
    "National Chung-Shan Institute of Science and Technology",
    "Sumida, Tokyo",
    "Tokyo",
    "Tokyo Skytree",
    "Patrice Bart-Williams",
    "Nomura Securities",
    "Rui En vol. 01",
    "Jan de Herdt",
    "H-IIB",
    "AGC Inc.",
    "Daihatsu Charade",
    "Daihatsu Move Canbus",
    "DeNA",
    "Doppelmayr/Garaventa Group",
    "Norinchukin Bank",
    "On the Road to Timbuktu: Explorers in Africa",
    "Palette Town",
    "Shibuya Hikarie",
    "Skyliner",
    "Halanaerobium praevalens",
    "Leonardo da Vinci: The Mind of the Renaissance",
    "Cirsium toyoshimae",
    "Cultural impact of Madonna",
    "Akita Northern Happinets",
    "Kyoto Hannaryz",
    "Isuzu 810",
    "'01 (Richard Müller album)",
    "'s Gravenmoer",
    ".հայ",
    ".577/500 No 2 Black Powder",
    "DNa inscription",

    # Blackboard bold characters used as anchors
    "Glossary of mathematical symbols",

    # Capital Alpha not in Greek word, exactly
    "Kamen Rider Agito",

    # &lowbar; needed to retain underscore in proper name
    "Double Fine",

    # Matching the actual unpronouncable album and song titles
    "Four Tet discography",

    # {{lang}} can't be used in {{cite}}
    "Everett, Washington",

    # {{lang}} and {{IPA}} interwoven with other templates
    "State Anthem of the Soviet Union",
    "National anthem of Bolivia",

    # {{not a typo}} not working well due to intersecting/nested templates
    "Beta",
    "Kappa",

    # Mixed thetas are intentional
    "Chebyshev function",
    "Eisenstein series",
    "J-invariant",
    "Kamassian language",
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
    re.compile(r"<(syntaxhighlight.*?</syntaxhighlight"
               r"|blockquote lang=.*?</blockquote"
               r"|<source.*?</source"
               r"|code.*?</code"
               r"|timeline.*?</timeline"
               ")>", flags=re.I+re.S),
    re.compile(r"\[\[(File|Image):.*?(\||\])", flags=re.I+re.S),

    re.compile(r"{{([Nn]ot a typo|[Ss]hort description|proper name|DISPLAYTITLE"
               # 7seg uses superscript = as a parameter value
               r"|7seg"

               # Unclear if these should be using Unicode or HTML
               # superscripts/subscripts (including tones like
               # <sup>H</sup> in IPA templates); ignoring for now.
               r"|IPA|UPA|PIE|[Aa]ngle|[Aa]ngbr|[Aa]ngbr IPA|[Aa]udio-IPA"
               r"|[Ll]ang\|"
               r"|[Tt]ransl\|"
               r"|[Zz]h\|"
               r"|[Ii]nterlinear ?\| ?lang="

               r"|([Ii]nfobox )?[Cc]hinese"
               r"|[Cc]har"
               r"|[Cc]ode\s*\|"
               r"|[Rr]ust\|"
               r").*?}}", flags=re.S),
    re.compile(r'{\|\s*class="(wikitable IPA|IPA wikitable)".*?\|}', flags=re.S),
    re.compile(r"(ipa symbol\d?|poj) *= *[^\n]+"),

    # Allow these characters:
    # ʿ U+02BF Modifier letter left half ring,
    # ʾ U+02BE Modifier letter right half ring
    # ʻ U+02BB 'Okina
    # ʼ U+02BC Modifier letter apostrophe
    # to be used in various non-English orthographies and transliterations,
    # if tagged with the language.
    #
    # re.compile(r"{{(lang|Lang|transl|Transl)[^}]+[ʿʾʻʼ][^}]+}}", flags=re.S),
    # Disabled for performance - redundant to above
]

needs_ipa_detect_re = re.compile(r"{{[Nn]eeds IPA", flags=re.S)
needs_ipa_remove_re = re.compile(r".{0,100}{{[Nn]eeds IPA.*?}}", flags=re.S)


def get_redacted_article_text(article_text):
    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)

    if needs_ipa_detect_re.match(article_text):
        article_text = needs_ipa_remove_re.sub("", article_text)

    return article_text


def entity_check(article_title, article_text):
    if article_title in article_blocklist:
        return

    if "{{cleanup lang" in article_text or "{{Cleanup lang" in article_text:
        return

    if "{{which lang" in article_text:
        return

    if "{{move to Wiki" in article_text or "{{Move to Wiki" in article_text:
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

        if check_string == "₤" and re.match("lira|lire", article_text, flags=re.I+re.S):
            # Per [[MOS:CURRENCY]]
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

        if check_string == "°K" and "°KMW" in article_text:
            continue
        if check_string == "° F" and not re.search(rf"° F(ahrenheit)?[^a-zA-Z{lc_lig}]", article_text):
            continue
        if check_string == "° C" and not re.search(rf"° C(elsius)?[^a-zA-Z{lc_lig}]", article_text):
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

        if entity in ["&ast;", "¹", "²", "³", "⁴", "⁵", "⁶", "⁷", "⁸", "⁹"]:
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
        output += "Fix automatically with jwb-articles.txt\n\n"
    elif section_title == "Low priority":
        output += "Fix automatically with jwb-articles.txt\n\n"
    elif section_title == "Greek letters":
        output += "Fix automatically with jwb-articles.txt (articles with {{tag|math}} markup excluded)\n\n"
    elif section_title == "Controversial entities":
        output += "Fix automatically with jwb-articles.txt (articles with {{tag|math}} markup excluded)\n\n"
    elif section_title == "Numeric":
        output += "Fix automatically with jwb-articles.txt\n\n"

    sorted_items = sorted(dictionary.items(), key=lambda t: (len(t[1]), t[0]), reverse=True)

    for (key, article_list) in sorted_items:

        if section_title == "To avoid":
            # Exclude overlapping entities
            if key in strings_found_by_type["UNCONTROVERSIAL"]:
                continue

        article_set = set(article_list)

        if len(article_set) > 100000:
            # These should probably be addressed by bot or policy
            # change or more targeted cleanup; leave them off this
            # todo list
            continue

        output += "* %s/%s - %s - %s\n" % (
            len(article_list),
            len(article_set),
            key,
            ", ".join(["[[%s]]" % article for article in sorted(article_set)][0:500])
            # Limit at 500 to avoid sorting 100,000+ titles, several
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
        articles.extend(sorted(article_list)[0:100])
        # Limit 100 to avoid getting stuck on one common entity and getting bored

    articles = list(dict.fromkeys(articles))  # uniqify
    return articles


def dump_for_jwb(pulldown_name, bad_entities, file=sys.stdout):

    output_string = '{"%s":' % pulldown_name
    output_string += """{"string":{"articleList":"","summary":"convert special characters found by [[Wikipedia:Typo Team/moss]]","watchPage":"nochange","skipContains":"","skipNotContains":"","containFlags":"","moveTo":"","editProt":"all","moveProt":"all","protectExpiry":"","namespacelist":["0"],"cmtitle":"","linksto-title":"","pssearch":"","pltitles":""},"bool":{"preparse":false,"minorEdit":true,"viaJWB":true,"enableRETF":true,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":true,"exists-yes":false,"exists-no":true,"exists-neither":false,"skipAfterAction":true,"containRegex":false,"suppressRedir":false,"movetalk":false,"movesubpage":false,"categorymembers":false,"cmtype-page":true,"cmtype-subcg":true,"cmtype-file":true,"linksto":false,"backlinks":true,"embeddedin":false,"imageusage":false,"rfilter-redir":false,"rfilter-nonredir":false,"rfilter-all":true,"linksto-redir":true,"prefixsearch":false,"watchlistraw":false,"proplinks":false},"replaces":[\n"""  # noqa

    # Must be before auto-generated replacements
    output_string += r"""{"replaceText":"(&#0?39;'|'&#0?39;)","replaceWith":"\"","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
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
        if fixed_entity in ["\r", "\t", "", ""]:  # \r is ^M
            fixed_entity == " "

        if entity != fixed_entity:
            output_string += '{"replaceText":"%s","replaceWith":"%s","useRegex":true,"regexFlags":"g","ignoreNowiki":true},\n' % (
                entity,
                fixed_entity)

    # {{frac}} repair
    output_string += r'{"replaceText":"([0-9,]+){{frac\\|([0-9]+)}}","replaceWith":"{{frac|$1|1|$2}}","useRegex":true,"regexFlags":"g","ignoreNowiki":true},'
    output_string += "\n"
    output_string += r'{"replaceText":"([0-9,]+){{frac\\|([0-9]+)\\|([0-9]+)}}","replaceWith":"{{frac|$1|$2|$3}}","useRegex":true,"regexFlags":"g","ignoreNowiki":true},'
    output_string += "\n"

    # MOS:LOGICAL
    output_string += r'{"replaceText":"\"([a-z ,:\\-;]+)([,\\.])\"","replaceWith":"\"$1\"$2","useRegex":true,"regexFlags":"g","ignoreNowiki":true},'
    output_string += "\n"

    # MOS:DOUBLE
    # output_string += r'{"replaceText":" ' + r"'" + r'([A-Za-z ,:\\-;]+)' + r"'" + r'([,\\. }\\)])", "replaceWith":" \"$1\"$2","useRegex":true,"regexFlags":"g","ignoreNowiki":true}'
    # TODO: This is disabled because it fails to respect:
    # * Single quotes properly nested inside double quotes, if there
    #   are words between all the quote marks
    # * {{cite web}} and other templates that put double quote marks
    #   around fields like "title" and "quote".

    prime_accepted_chars = "dijkrtvwxyzCDEFGHIJKMNUVWXYZγδζξϖπστΕΖΗΙΚΜΝΞΠΣΥϒΧΨcgsuBGOPQRSαβϑθκμνςυχψωΒΘΟΡΩab∂ehmnopqALεϵηιλοϱρφϕΑΔΛΦflTΓΤ"

    # {{prime}} takes preceding text as an argument to adjust whitespace
    output_string += """{"replaceText":"''(['""" + prime_accepted_chars + """]+)''{{prime}}","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
    output_string += "\n"
    output_string += """{"replaceText":"''(['""" + prime_accepted_chars + """]+){{prime}}''","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
    output_string += "\n"
    # {{prime}} does not adjust whitespace properly if italics are part of the argument
    output_string += """{"replaceText":"{{prime\\\\|''([""" + prime_accepted_chars + """]+)''}}","replaceWith":"''{{prime|$1}}''","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
    output_string += "\n"

    # CAUTION: Manually edit "north" to "N", etc.
    output_string += r"""{"replaceText":"([0-9]+)° ?([0-9]+)['′] ?([0-9]+)[\"″] ?(N|S|north|south),? ?([0-9]+)° ?([0-9]+)['′] ?([0-9]+)[\"″] ?(E|W|east|west)","""
    output_string += r""""replaceWith":"{{coord|$1|$2|$3|$4|$5|$6|$7|$8|display=inline}}","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
    output_string += "\n"
    output_string += r"""{"replaceText":"([0-9]+\\.[0-9]+)°? ?(N|S) ?([0-9]+\\.[0-9]+)°? ?(E|W)","""
    output_string += r""""replaceWith":"{{coord|$1|$2|$3|$4|display=inline}}","useRegex":true,"regexFlags":"g","ignoreNowiki":true},"""
    output_string += "\n"

    # This must come after the {{coord}} transformations
    # CAUTION: Use {{sky}} for celestial coordinates
    output_string += r"""{"replaceText":"([0-9]+)° ?([0-9]+)['′] ?([0-9]+)[\"″]","replaceWith":"$1°$2{{prime}}$3{{pprime}}","useRegex":true,"regexFlags":"g","ignoreNowiki":true}"""
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

    with open("jwb-combo.json", "w") as combof:
        bad_entities = set()
        for dic_type in ["ALERT", "LOW_PRIORITY", "UNCONTROVERSIAL", "UNKNOWN", "NUMERIC", "CONTROVERSIAL", "GREEK"]:
            dictionary = strings_found_by_type.get(dic_type, {})
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=combof)

    with open("jwb-articles.txt", "w") as articlesf:
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
        print("\n".join(articles), file=articlesf)


if __name__ == '__main__':
    read_en_article_text(entity_check, process_result_callback=add_tuples_to_results, parallel=True)
    dump_results()
