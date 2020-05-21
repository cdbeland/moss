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
non_entity_transform = [string for string in transform.keys() if not string.startswith("&")]
worst_articles = {}

article_blacklist = [
    # Characters themselves are discussed
    "' (disambiguation)",
    "Basic Latin (Unicode block)",
    "Bracket",
    "CEA-708",
    "Code page 259",
    "Devanagari transliteration",
    "German keyboard layout",
    "Grave accent",
    "ISO 5426",
    "ISO 5428",
    "KPS 9566",
    "Latin script in Unicode",
    "List of Japanese typographic symbols",
    "List of Unicode characters",
    "Mac OS Celtic",
    "Mac OS Devanagari encoding",
    "Mac OS Roman",
    "Mojibake",
    "Numero sign",
    "Phags-pa (Unicode block)",
    "Prime (symbol)",
    "Registered trademark symbol",
    "RISC OS character set",
    "Rough breathing",
    "Quotation mark",
    "Schwarzian derivative",
    "Tilde"
    "TRON (encoding)",
    "Windows-1252",
    "Windows-1258",
    "Windows Glyph List 4",

    "Arabic diacritics",
    "Arabic script in Unicode",  # objection from Mahmudmasri
    "Perso-Arabic Script Code for Information Interchange",
    # https://en.wikipedia.org/w/index.php?title=Perso-Arabic_Script_Code_for_Information_Interchange&oldid=prev&diff=900347984&diffmode=source]
    "Yiddish orthography",
    "Eastern Arabic numerals",
    "List of XML and HTML character entity references",

    # Correctly uses U+2011 Non-Breaking Hypens
    "Börje",

    # Correctly uses center dots
    "Additive category",

    # Variation issues, maybe need a variant selector?
    "Seong",
    "Sung-mi",
    "Yasukuni Shrine",
]


# Max number of articles a character can appear in before it's ignored
# for JWB purposes.
JWB_ARTICLE_CUTOFF = 1100


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
]


def entity_check(article_title, article_text):
    if article_title in article_blacklist:
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
            for instance in re.findall(string, article_text):
                add_safely(article_title, string, uncontroversial_found)
                add_safely(string, article_title, worst_articles)
                # This intentionally adds the article title as many
                # times as the string appears

    for entity in entities_re.findall(article_text):
        if entity in alert:
            # Handled above
            continue
        elif entity in controversial:
            add_safely(article_title, entity, controversial_found)
            add_safely(entity, article_title, worst_articles)
            continue
        elif entity in keep:
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
    print("\n=== %s ===" % section_title)

    if section_title == "To avoid":
        print(f"Fix automatically with jwb-articles-low.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")
    elif section_title == "Uncontroversial entities":
        print(f"Fix automatically with jwb-articles-low.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")
    elif section_title == "Greek letters":
        print(f"Fix automatically with jwb-articles-controversial.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")
    elif section_title == "Controversial entities":
        print(f"Fix automatically with jwb-articles-controversial.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")
    elif section_title == "Unknown numerical: Latin range":
        print(f"Fix automatically with jwb-articles-low.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")
    elif section_title == "Unknown high numerical":
        print(f"Fix automatically with jwb-articles-high.txt (cutoff at {JWB_ARTICLE_CUTOFF} articles)\n")

    sorted_items = sorted(dictionary.items(), key=lambda t: (len(t[1]), t[0]), reverse=True)
    for (key, article_list) in sorted_items[0:50]:
        article_set = set(article_list)
        print("* %s/%s - %s - %s" % (
            len(article_list),
            len(article_set),
            key,
            ", ".join(["[[%s]]" % article for article in sorted(article_set)][0:500])
            # Limit at 500 to avoid sorting 100,000+ titles, several
            # times.  Sampled articles aren't always the ones at the
            # beginning of the alphabet as a result, but this doesn't
            # really matter.
        ))


def extract_entities(dictionary):
    return {entity for entity in dictionary.keys()}


def extract_articles(dictionary):
    articles = set()
    for article_list in dictionary.values():
        # Skip articles that only have very common characters or
        # entities that will need to be dealt with by a real bot
        # someday.
        if len(article_list) < JWB_ARTICLE_CUTOFF:
            articles.update(article_list)
    return articles


def dump_for_jwb(pulldown_name, bad_entities, file=sys.stdout):

    output_string = '{"%s":' % pulldown_name
    output_string += """{"string":{"articleList":"","summary":"convert special characters","watchPage":"nochange","skipContains":"","skipNotContains":"","containFlags":"","moveTo":"","editProt":"all","moveProt":"all","protectExpiry":"","namespacelist":["0"],"cmtitle":"","linksto-title":"","pssearch":"","pltitles":""},"bool":{"preparse":false,"minorEdit":true,"viaJWB":true,"enableRETF":true,"redir-follow":false,"redir-skip":false,"redir-edit":true,"skipNoChange":false,"exists-yes":false,"exists-no":true,"exists-neither":false,"skipAfterAction":true,"containRegex":false,"suppressRedir":false,"movetalk":false,"movesubpage":false,"categorymembers":false,"cmtype-page":true,"cmtype-subcg":true,"cmtype-file":true,"linksto":false,"backlinks":true,"embeddedin":false,"imageusage":false,"rfilter-redir":false,"rfilter-nonredir":false,"rfilter-all":true,"linksto-redir":true,"prefixsearch":false,"watchlistraw":false,"proplinks":false},"replaces":[\n"""  # noqa

    for entity in sorted(bad_entities):
        fixed_entity = fix_text(entity, transform_greek=True)
        if fixed_entity == '"':
            fixed_entity = r'\"'
        if fixed_entity == "\\":
            fixed_entity = "\\\\"
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
        dump_dict(section_title, dictionary)

    with open("jwb-combo.json", "w") as comboj:
        bad_entities = set()
        for dictionary in [alerts_found, uncontroversial_found,
                           unknown_found, unknown_numerical_latin,
                           unknown_numerical_high]:
            bad_entities.update(extract_entities(dictionary))
        dump_for_jwb("combo", bad_entities, file=comboj)

    with open("jwb-articles-controversial.txt", "w") as contro:
        articles = set()
        for dictionary in [controversial_found, greek_letters_found]:
            articles.update(extract_articles(dictionary))
        print("\n".join(sorted(articles)), file=contro)

    with open("jwb-articles-low.txt", "w") as lowa:
        articles = set()
        for dictionary in [alerts_found, uncontroversial_found,
                           unknown_found, unknown_numerical_latin]:
            articles.update(extract_articles(dictionary))
        print("\n".join(sorted(articles)), file=lowa)

    with open("jwb-articles-high.txt", "w") as higha:
        print("\n".join(sorted(extract_articles(unknown_numerical_high))), file=higha)


read_en_article_text(entity_check)
dump_results()
