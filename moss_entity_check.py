# Run time: About 17 minutes

from moss_dump_analyzer import read_en_article_text
import re
import sys
from unencode_entities import (
    alert, keep, controversial, transform, greek_letters, find_char_num,
    entities_re, fix_text, should_keep_as_is)

strings_found_by_type = {}
non_entity_transform = [string for string
                        in list(transform.keys()) + list(controversial.keys())
                        if not string.startswith("&")]

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
    "Dania transcription",
    "Dash",
    "Devanagari transliteration",
    "DEC Hebrew",
    "DKOI",
    "DIN 66303",
    "Duplicate characters in Unicode",
    "Ellipsis",
    "ELOT 927",
    "En (typography)",
    "Extended Latin-8",
    "Extensions to the International Phonetic Alphabet",
    "Ezh",
    "FFL",
    "FOCAL character set",
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
    "List of Unicode characters",
    "Lotus Multi-Byte Character Set",
    "M",
    "Mac OS Celtic",
    "Mac OS Central European encoding",
    "Mac OS Devanagari encoding",
    "Mac OS Gaelic",
    "Mac OS Roman",
    "Mathematical Alphanumeric Symbols",
    "Mathematical operators and symbols in Unicode",
    "MIK (character set)",
    "Mojibake",
    "Multinational Character Set",
    "NEC APC character set",
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
    "Wade–Giles",
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

    # Chess with ½
    "World Chess960 Championship",
    "Algebraic notation (chess)",

    # !! in table (&#33; or &#x21;)
    "Cledus T. Judd",
    "Devin the Dude",
    "Frank Sinatra discography",
    "Kis-My-Ft2",
    "Kunio-kun",
    "Lattice tower",
    "List of Castlevania media",
    "List of Dragon Ball films",
    "List of Enix games",
    "List of Iwata Asks interviews",
    "List of Sega Saturn games",
    "List of songs recorded by Super Junior",
    "Rina Aiuchi discography",
    "Super Junior discography",
    "Super Junior-T",
    "The Aquabats",
    "The Chats",
    "V6 discography",

    # # in external link
    "WalangForever",

    # Special character in URL
    "Almah",
    "Cray XC50",
    "Rallying",
    "Pegeen Vail Guggenheim",
    "Power electronic substrate",

    # Roman numeral in image name (<gallery> or parameter)
    "Collection (publishing)",
    "Découvertes Gallimard",
    "Hillman Minx",
    "Grammaire égyptienne",

    # DISPLAYTITLE issues
    "Rosa Graham Thomas",

    # Blackboard bold characters used as anchors
    "Glossary of mathematical symbols",

    # Objection from Headbomb
    "Xi baryon",

    # Capital Alpha not in Greek word, exactly
    "Kamen Rider Agito",

    # &lowbar; needed to retain underscore in proper name
    "Double Fine",

    # Matching the actual unpronouncable album and song titles
    "Four Tet discography",

    # {{lang}} can't be used in {{cite}}
    "Everett, Washington",

    # Special character in file name
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

    # Special character in <timeline>
    "Chip (magazine)",
    "Cleo (group)",
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
#  lc_lig = "a-zøðþęáéóúýǫ́àèòùâêîôûëïöüÿçå"
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
    re.compile(r"<syntaxhighlight.*?</syntaxhighlight>", flags=re.I+re.S),
    re.compile(r"<source.*?</source>", flags=re.I+re.S),
    re.compile(r"<code.*?</code>", flags=re.I+re.S),
    re.compile(r"{{code\s*\|.*?}}", flags=re.I+re.S),

    re.compile(r"\[\[File:.*?(\||\])", flags=re.I+re.S),
    re.compile(r"\[\[Image:.*?(\||\])", flags=re.I+re.S),

    re.compile(r"{{[Ss]hort description.*?}}", flags=re.S),
    re.compile(r"{{proper name.*?}}", flags=re.S),
    re.compile(r"{{IPA.*?}}", flags=re.S),
    re.compile(r"{{UPA.*?}}", flags=re.S),
    re.compile(r"{{angle.*?}}", flags=re.I+re.S),
    re.compile(r"{{angbr.*?}}", flags=re.I+re.S),
    re.compile(r'{\|\s*class="wikitable IPA".*?\|}', flags=re.S),
    re.compile(r'{\|\s*class="IPA wikitable".*?\|}', flags=re.S),
    re.compile(r"{{transl.*?}}", flags=re.I+re.S),
    re.compile(r"{{angbr IPA.*?}}", flags=re.I+re.S),
    re.compile(r"{{Audio-IPA.*?}}", flags=re.I+re.S),
    re.compile(r"ipa symbol\d? *= *[^\n]+"),
    re.compile(r"poj *= *[^\n]+"),
    re.compile(r"{{PIE.*?}}", flags=re.S),
    re.compile(r"<blockquote lang=.*?</blockquote>", flags=re.I+re.S),
    re.compile(r"{{7seg.*?}}", flags=re.S),  # Uses superscript = as a parameter value
    re.compile(r"{{[Ii]nterlinear ?\| ?lang=.*?}}", flags=re.S),
    re.compile(r"{{[Nn]ot a typo.*?}}", flags=re.S),
    re.compile(r"{{([Ii]nfobox )?[Cc]hinese*?}}", flags=re.I+re.S),
    re.compile(r"{{char.*?}}", flags=re.S),

    # Used in various non-English orthographies and transliterations,
    # but must be tagged with the language.
    re.compile(r"{{(lang|Lang|transl|Transl)[^}]+[ʿʾʻʼ][^}]}}", flags=re.S),
    # ʿ U+02BF Modifier letter left half ring,
    # ʾ U+02BE Modifier letter right half ring
    # ʻ U+02BB 'Okina
    # ʼ U+02BC Modifier letter apostrophe

    # It's unclear if these should be using Unicode or HTML
    # superscripts/subscripts; ignoring for now.
    re.compile(r"{{[Ll]ang.*?}}", flags=re.S),
    re.compile(r"{{[Zz]h.*?}}", flags=re.S),

    re.compile(r".{0,100}{{[Nn]eeds IPA.*?}}", flags=re.S),

    # It's unclear if tones like <sup>H</sup> in IPA templates should
    # be converted to Unicode.
]


def entity_check(article_title, article_text):
    if article_title in article_blocklist:
        return

    if "{{cleanup lang" in article_text or "{{Cleanup lang" in article_text:
        return

    if "{{which lang" in article_text:
        return

    if "{{move to Wiki" in article_text or "{{Move to Wiki" in article_text:
        return

    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)

    article_text_lower = article_text.lower()

    result_tuples = []

    for string in alert:
        if string == "₤" and ("lira" in article_text_lower or "lire" in article_text_lower):
            # Per [[MOS:CURRENCY]]
            continue

        for instance in re.findall(string, article_text):
            result_tuples.append(("ALERT", article_title, string))
            # This intentionally adds the article title as many times
            # as the string appears

    for string in non_entity_transform:
        if string == "½" and ("chess" in article_text_lower):
            # Per [[MOS:FRAC]]
            continue

        if string in article_text:
            for instance in re.findall(re.escape(string), article_text):
                result_tuples.append(("UNCONTROVERSIAL", article_title, string))
                # This intentionally adds the article title as many
                # times as the string appears

    for entity in entities_re.findall(article_text):
        if entity in keep:
            continue
        if entity in alert:
            # Handled above
            continue

        if entity == "&ast;":
            if ("{{Infobox Chinese" in article_text
                    or "{{infobox Chinese" in article_text
                    or "{{Chinese" in article_text):
                # Legitimate use to prevent interpretation as wikitext list syntax
                continue

        if entity in controversial or entity in greek_letters:
            if "<math>" in article_text:
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
        articles.extend(sorted(article_list))

    articles = list(dict.fromkeys(articles))  # uniqify
    return articles


def dump_for_jwb(pulldown_name, bad_entities, file=sys.stdout):

    output_string = '{"%s":' % pulldown_name
    output_string += """{"string":{"articleList":"","summary":"convert special characters found by [[Wikipedia:Typo Team/moss]]","watchPage":"nochange","skipContains":"","skipNotContains":"","containFlags":"","moveTo":"","editProt":"all","moveProt":"all","protectExpiry":"","namespacelist":["0"],"cmtitle":"","linksto-title":"","pssearch":"","pltitles":""},"bool":{"preparse":false,"minorEdit":true,"viaJWB":true,"enableRETF":true,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":true,"exists-yes":false,"exists-no":true,"exists-neither":false,"skipAfterAction":true,"containRegex":false,"suppressRedir":false,"movetalk":false,"movesubpage":false,"categorymembers":false,"cmtype-page":true,"cmtype-subcg":true,"cmtype-file":true,"linksto":false,"backlinks":true,"embeddedin":false,"imageusage":false,"rfilter-redir":false,"rfilter-nonredir":false,"rfilter-all":true,"linksto-redir":true,"prefixsearch":false,"watchlistraw":false,"proplinks":false},"replaces":[\n"""  # noqa

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
    output_string = output_string.rstrip(",\n")
    output_string += "\n]}}"
    print(output_string, file=file)


def dump_results():
    sections = {
        "Unknown": strings_found_by_type.get("UNKNOWN", {}),
        "To avoid": strings_found_by_type.get("ALERT", {}),
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
        for dic_type in ["ALERT", "UNCONTROVERSIAL", "UNKNOWN", "NUMERIC", "CONTROVERSIAL", "GREEK"]:
            dictionary = strings_found_by_type.get(dic_type, {})
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=combof)

    with open("jwb-articles.txt", "w") as articlesf:
        # Sorted from least-frequent to most-frequent across all types
        mega_dict = {}
        for dic_type in ["CONTROVERSIAL", "GREEK", "NUMERIC", "UNCONTROVERSIAL"]:
            mega_dict.update(strings_found_by_type.get(dic_type, {}))
        articles = extract_articles(mega_dict)
        articles = list(dict.fromkeys(articles))  # uniqify across sublists
        print("\n".join(articles[0:1000]), file=articlesf)


if __name__ == '__main__':
    read_en_article_text(entity_check, process_result_callback=add_tuples_to_results, parallel=True)
    dump_results()
