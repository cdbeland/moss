# Run time: About 2 hours

from moss_dump_analyzer import read_en_article_text
import re
import sys
from unencode_entities import (
    alert, keep, controversial, transform, greek_letters, find_char_num,
    entities_re, fix_text, should_keep_as_is)

alerts_found = {}
controversial_found = {}
uncontroversial_found = {}
greek_letters_found = {}
unknown_found = {}
unknown_numerical_latin = {}
unknown_numerical_high = {}
non_entity_transform = [string for string
                        in list(transform.keys()) + list(controversial.keys())
                        if not string.startswith("&")]
worst_articles = {}

article_blocklist = [
    # Characters themselves are discussed or listed as part of a mapping
    "' (disambiguation)",
    "ANSEL",
    "ARIB STD B24 character set",
    "ALCOR",
    "ALGOL",
    "ALGOL 68",
    "ASMO 449",
    "AZERTY",
    "AltGr key",
    "Apostrophe",
    "Ayin",
    "Basic Latin (Unicode block)",
    "Big5",
    "Bitstream International Character Set",
    "Blackboard bold",
    "Bookshelf Symbol 7",
    "Bracket",
    "CEA-708",
    "CER-GS",
    "Casio calculator character sets",
    "Chinese Character Code for Information Interchange",
    "Code page 259",
    "Code page 293",
    "Code page 310",
    "Code page 351",
    "Code page 361",
    "Code page 897",
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
    "Computer Braille Code",
    "Dash",
    "Devanagari transliteration",
    "DEC Hebrew",
    "DKOI",
    "Duplicate characters in Unicode",
    "Ellipsis",
    "ELOT 927",
    "En (typography)",
    "Extended Latin-8",
    "Extensions to the International Phonetic Alphabet",
    "G",
    "GB 2312",
    "German keyboard layout",
    "GOST 10859",
    "Grave accent",
    "Greek script in Unicode",
    "Hashtag",
    "HP Roman",
    "IBM 2741",
    "IBM 3270",
    "INIS-8",
    "ISO/IEC 646",
    "ISO/IEC 10367",
    "ISO 5426",
    "ISO 5428",
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
    "ITU T.61",
    "Jeremy Burge",
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
    "Latin script in Unicode",
    "List of Japanese typographic symbols",
    "List of Latin letters by shape",
    "List of Latin-script letters",
    "List of precomposed Latin characters in Unicode",
    "List of Unicode characters",
    "Lotus Multi-Byte Character Set",
    "M",
    "Mac OS Celtic",
    "Mac OS Devanagari encoding",
    "Mac OS Gaelic",
    "Mac OS Roman",
    "Mathematical Alphanumeric Symbols",
    "Mathematical operators and symbols in Unicode",
    "Mojibake",
    "Multinational Character Set",
    "Number Forms",
    "Numerals in Unicode",
    "Numero sign",
    "Palatal hook",
    "PETSCII",
    "Phags-pa (Unicode block)",
    "Prime (symbol)",
    "Regional indicator symbol",
    "Registered trademark symbol",
    "RISC OS character set",
    "Roman numerals",
    "Rough breathing",
    "Quotation mark",
    "Schwarzian derivative",
    "Secondary articulation",
    "Service mark",
    "Sharp pocket computer character sets",
    "SI 960",
    "Sinclair QL character set",
    "Six-bit character code",
    "Specials (Unicode block)",
    "Slash (punctuation)",
    "Slashed zero",
    "Superior letter",
    "Symbol (typeface)",
    "T.51/ISO/IEC 6937",
    "Tab key",
    "Teletext character set",
    "Thai Industrial Standard 620-2533",
    "TI calculator character sets",
    "Tibetan (Unicode block)",
    "Tilde",
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
    "Wade–Giles",
    "Wang International Standard Code for Information Interchange",
    "Warmian-Masurian Voivodeship",
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
    "World glyph set",
    "Xerox Character Code Standard",
    "YUSCII",
    "Zero-width space",

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

    "List of jōyō kanji",  # Breaks display of certain characters

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

    # Unwanted character in file name (which could theoretically be fixed)
    "2019 in India",
    "Charles Francis Adams III",
    "Graham Sutton (musician)",
    "Ichikawa Danjūrō IX",
    "Kamakura Gongorō Kagemasa",
    "OptiX",
    "Aragoto",
    "Collection (publishing)",
    "Group A",
    "Kobee",
    "Luanping County",
    "Radio masts and towers",
    "Baden VI c",
    "Découvertes Gallimard",
    "Tokyo International Conference on African Development",
    "Swallow-tailed Hems and Flying Ribbons clothing",
    "China Railway DF5",
    "H-IIB",
    "Housing in Japan",
    "KARI KSR-3",
    "Keisei Narita Airport Line",
    "List of Daihatsu vehicles",
    "List of National Treasures of Japan (temples)",
    "List of Places of Scenic Beauty of Japan (Kyōto)",
    "Nanzen-ji",
    "National Central University",
    "National Chung-Shan Institute of Science and Technology",
    "Nomura Securities",
    "Norinchukin Bank",
    "Palette Town",
    "Piano Concerto (Khachaturian)",
    "Sanxingdui",
    "Shibuya Hikarie",
    "Skyliner",
    "Tokyo Skytree",
    "Tree of life",
    "Tricable gondola lift",

    # Chess with ½
    "World Chess960 Championship",
    "Algebraic notation (chess)",

    # !! in table (&#33; or &#x21;)
    "Cledus T. Judd",
    "Frank Sinatra discography",
    "Kis-My-Ft2",
    "Kunio-kun",
    "Lattice tower",
    "List of Castlevania media",
    "List of Dragon Ball films",
    "List of Enix games",
    "List of Iwata Asks interviews",
    "List of Sega Saturn games",
    "Rina Aiuchi discography",
    "Super Junior discography",
    "Super Junior-T",
    "The Aquabats",
    "The Chats",
    "V6 discography",

    # # in external link
    "WalangForever",

    # Unicode superscript in URL in bidirectional text
    "Almah",

    # DISPLAYTITLE issues
    "Rosa Graham Thomas",
]


# Max number of articles a character can appear in before it's ignored
# for JWB article-list-generation purposes.
JWB_ARTICLE_CUTOFF = 15


def jwb_escape(text):
    text = text.replace("\\", "\\\\")  # e.g. for <math> markup
    text = text.replace('"', '\\"')
    return text


def add_safely(value, key, dictionary):
    existing_list = dictionary.get(key, [])
    existing_list.append(value)
    dictionary[key] = existing_list
    return dictionary


suppression_patterns = [
    re.compile(r"<syntaxhighlight.*?</syntaxhighlight>", flags=re.I+re.S),
    re.compile(r"<source.*?</source>", flags=re.I+re.S),
    re.compile(r"<code.*?</code>", flags=re.I+re.S),
    re.compile(r"{{code\s*\|.*?}}", flags=re.I+re.S),

    re.compile(r"[[File:.*?]]", flags=re.I+re.S),
    re.compile(r"[[Image:.*?]]", flags=re.I+re.S),

    re.compile(r"{{IPA.*?}}", flags=re.I+re.S),
    re.compile(r"{{angbr IPA.*?}}", flags=re.I+re.S),
    re.compile(r"{{PIE.*?}}", flags=re.I+re.S),

    # It's unclear if these and if text outside of templates should be
    # converted to Unicode or HTML superscripts/subscripts.  Produce a
    # report after IPA revert is complete.
    # re.compile(r"{{lang.*?}}", flags=re.I+re.S),
    #
    # It's unclear if tones like <sup>H</sup> in IPA templates should
    # be converted to Unicode.
]


def entity_check(article_title, article_text):
    if article_title in article_blocklist:
        return

    for pattern in suppression_patterns:
        article_text = pattern.sub("", article_text)

    article_text_lower = article_text.lower()

    for string in alert:
        if string == "₤" and ("lira" in article_text_lower):
            # Per [[MOS:CURRENCY]]
            continue

        for instance in re.findall(string, article_text):
            add_safely(article_title, string, alerts_found)
            add_safely(string, article_title, worst_articles)
            # This intentionally adds the article title as many times
            # as the string appears

    for string in non_entity_transform:
        if string == "½" and ("chess" in article_text_lower):
            # Per [[MOS:FRAC]]
            continue

        if string in article_text:
            for instance in re.findall(re.escape(string), article_text):
                add_safely(article_title, string, uncontroversial_found)
                add_safely(string, article_title, worst_articles)
                # This intentionally adds the article title as many
                # times as the string appears

    for entity in entities_re.findall(article_text):
        if entity in keep:
            continue
        elif entity in alert:
            # Handled above
            continue
        elif entity in controversial:
            add_safely(article_title, entity, controversial_found)
            add_safely(entity, article_title, worst_articles)
            continue
        elif entity in greek_letters:
            add_safely(article_title, entity, greek_letters_found)
            add_safely(entity, article_title, worst_articles)
            continue

        add_safely(entity, article_title, worst_articles)

        if entity in transform:
            add_safely(article_title, entity, uncontroversial_found)
        else:
            if should_keep_as_is(entity):
                continue
            value = find_char_num(entity)
            if value:
                if int(value) < 0x0250:
                    add_safely(article_title, entity, unknown_numerical_latin)
                else:
                    add_safely(article_title, entity, unknown_numerical_high)
            else:
                if entity == entity.upper() and re.search("[A-Z]+%s" % entity, article_text):
                    # Ignore things like "R&B;" and "PB&J;" which is common in railroad names.
                    continue
                add_safely(article_title, entity, unknown_found)


def dump_dict(section_title, dictionary):
    output = f"=== {section_title} ===\n"

    if section_title == "To avoid":
        output += f"Not included in JWB scripts; may need to isolate instances in main body text, add automatic substitutions, or fix manually.\n\n"
    elif section_title == "Uncontroversial entities":
        output += f"Fix automatically with jwb-articles-low.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n\n"
    elif section_title == "Greek letters":
        output += f"Fix automatically with jwb-articles-greek.txt (avoiding STEM articles)\n\n"
    elif section_title == "Controversial entities":
        output += f"Fix automatically with jwb-articles-controversial.txt (avoiding STEM articles)\n\n"
    elif section_title == "Unknown numerical: Latin range":
        output += f"Fix automatically with jwb-articles-low.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n\n"
    elif section_title == "Unknown high numerical":
        output += f"Fix automatically with jwb-articles-high.txt\n\n"

    sorted_items = sorted(dictionary.items(), key=lambda t: (len(t[1]), t[0]), reverse=True)

    if section_title == "Worst articles":
        # Disabled - mostly low-priority MOS:STRAIGHT violations
        return
    """
        output += "Fix automatically with jwb-articles-worst.txt\n"
        for (article_title, entities) in sorted_items[0:50]:
            distinct_entities = set(entities)
            output += f"* {len(entities)}/{len(distinct_entities)} - [[{article_title}]] - "
            output += ", ".join([entity for entity in sorted(distinct_entities)])
            output += "\n"
        with open("jwb-articles-worst.txt", "w") as worsta:
            print("\n".join([article_title
                             for (article_title, entities)
                             in sorted_items[0:50]]),
                  file=worsta)
        return output
    """

    for (key, article_list) in sorted_items[0:100]:
        if section_title == "To avoid":
            # Exclude overlapping entities
            if key in uncontroversial_found:
                continue

        article_set = set(article_list)
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


def extract_articles(dictionary, limit=True):
    articles = set()
    for (entity, article_list) in dictionary.items():

        # Above-cutoff characters to work on next
        if entity in [
                "&Xi;"
                # "Ⅰ", "Ⅱ", "Ⅲ", "Ⅳ", "Ⅴ", "Ⅵ", "Ⅶ", "Ⅷ", "Ⅸ", "Ⅹ", "Ⅺ", "Ⅻ", "Ⅼ", "Ⅽ", "Ⅾ", "Ⅿ", "ⅰ", "ⅱ", "ⅲ", "ⅳ", "ⅴ", "ⅵ", "ⅶ", "ⅷ", "ⅸ", "ⅹ", "ⅺ", "ⅻ", "ⅼ", "ⅽ", "ⅾ", "ⅿ",
                # TODO next with JWB_ARTICLE_CUTOFF set at 25:
                # "&larr;", "&uarr;", "&darr;", "&sup;", "&rfloor;", "&lfloor;", "&subseteq;"
                # Numerous but satisfying:
                # "&rarr;", "&copy;", "&#8212;", "&apos;", "&hellip;", "&alpha;"
        ]:
            articles.update(article_list)
            continue

        # Skip articles that only have very common characters or
        # entities that will need to be dealt with by a real bot
        # someday.
        if limit and len(set(article_list)) > JWB_ARTICLE_CUTOFF:
            continue

        if entity in [
                # Too many STEM articles; temporarily skipping
                "&plusmn;",
        ]:
            continue

        articles.update(article_list)

    return articles


def dump_for_jwb(pulldown_name, bad_entities, file=sys.stdout):

    output_string = '{"%s":' % pulldown_name
    output_string += """{"string":{"articleList":"","summary":"convert special characters","watchPage":"nochange","skipContains":"","skipNotContains":"","containFlags":"","moveTo":"","editProt":"all","moveProt":"all","protectExpiry":"","namespacelist":["0"],"cmtitle":"","linksto-title":"","pssearch":"","pltitles":""},"bool":{"preparse":false,"minorEdit":true,"viaJWB":true,"enableRETF":true,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":true,"exists-yes":false,"exists-no":true,"exists-neither":false,"skipAfterAction":true,"containRegex":false,"suppressRedir":false,"movetalk":false,"movesubpage":false,"categorymembers":false,"cmtype-page":true,"cmtype-subcg":true,"cmtype-file":true,"linksto":false,"backlinks":true,"embeddedin":false,"imageusage":false,"rfilter-redir":false,"rfilter-nonredir":false,"rfilter-all":true,"linksto-redir":true,"prefixsearch":false,"watchlistraw":false,"proplinks":false},"replaces":[\n"""  # noqa

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
        "Worst articles": worst_articles,
        "Controversial entities": controversial_found,
        "Greek letters": greek_letters_found,
        "To avoid": alerts_found,
        "Uncontroversial entities": uncontroversial_found,
        "Unknown": unknown_found,
        "Unknown numerical: Latin range": unknown_numerical_latin,
        "Unknown high numerical": unknown_numerical_high,
    }
    for (section_title, dictionary) in sections.items():
        output = dump_dict(section_title, dictionary)
        print(output)
        """
        # Disabled - mostly low-priority MOS:STRAIGHT violations
        if section_title == "Worst articles":
            with open("tmp-worst.txt", "w") as worst:
                print(output, file=worst)
        else:
            print(output)
        """

    with open("jwb-combo-no-greek-no-controversial.json", "w") as combojng:
        bad_entities = set()
        for dictionary in [alerts_found, uncontroversial_found,
                           unknown_found, unknown_numerical_latin,
                           unknown_numerical_high]:
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=combojng)

    with open("jwb-combo-full.json", "w") as combof:
        bad_entities = set()
        for dictionary in [alerts_found, uncontroversial_found,
                           unknown_found, unknown_numerical_latin,
                           unknown_numerical_high,
                           controversial_found, greek_letters_found]:
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=combof)

    with open("jwb-articles-controversial.txt", "w") as contro:
        articles = extract_articles(controversial_found, limit=False)
        print("\n".join(sorted(articles)), file=contro)

    with open("jwb-articles-greek.txt", "w") as greek:
        articles = extract_articles(greek_letters_found, limit=False)
        print("\n".join(sorted(articles)), file=greek)

    with open("jwb-articles-low.txt", "w") as lowa:
        articles = set()
        for dictionary in [uncontroversial_found, unknown_found, unknown_numerical_latin]:
            articles.update(extract_articles(dictionary))
        print("\n".join(sorted(articles)), file=lowa)

    with open("jwb-articles-high.txt", "w") as higha:
        print("\n".join(sorted(extract_articles(unknown_numerical_high, limit=False))), file=higha)


read_en_article_text(entity_check)
dump_results()
