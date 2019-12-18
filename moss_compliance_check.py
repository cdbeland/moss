from moss_dump_analyzer import read_en_article_text
import re


REGEX_SUBSTITUTIONS = [
    # ORDER MATTERS
    # Tuple format (all regexes): From, To, skip page if wikitext contains

    (re.compile(r'(title="([^"]+)\s*"\s*|)'), r"title=\1 |", None),
    (re.compile(r"(title='([^']+)\s*'\s*|)"), r"title=\1 |", None),

    (re.compile(r"N°\s+(\d)"), r"Number \1", re.compile("Image:Cal12 N°8.jpg")),
    (re.compile(r"n°\s+(\d)"), r"number \1", None),
    (re.compile(r"№\s+(\d)"), r"Number \1", re.compile("Numero sign")),
    (re.compile(r"№"), r"Number", re.compile("Numero sign")),

    # Not always safe to do; need to exclude legitimate wikitext and
    # manually inspect to see if this is HTML that needs to be cleaned
    # up.
    (re.compile(r"<([a-zA-Z]+)>"), "{{angbr|\1}}", None),
    (re.compile(r"&lt;([a-zA-Z]+)&gt;"), "{{angbr|\1}}", None),

    (re.compile(r"cosθ"), r"cos θ", None),
    (re.compile(r"sinθ"), r"sin θ", None),
    (re.compile(r"tanθ"), r"tan θ", None),

    # TODO ITEMS

    # ("([0-9]+)(° |°)([CF][ .,])", {{convert}} or \1&nbsp;°\3
    # For manual review, degrees without C or F:
    # insource:/°[^FC]/

    # {{convert}} for inches, meters, feet.  Example of
    # multi-dimensional converts:
    # https://en.wikipedia.org/wiki/Terris_Nguyen_Temple

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Ligatures
    # æ -> ae unless word is capitalized or not English or in IPA
    # https://en.wikipedia.org/w/index.php?search=insource%3A%2F%C3%A6%2F&title=Special%3ASearch&profile=advanced&fulltext=1&advancedSearch-current=%7B%7D&ns0=1
    #
    # insource:/coöperative/ -> cooperative, archaic?
    # (or should English have accents to help pronunciation?)

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Section_headings
    # Remove markup from section titles

    # insource:/\[\[:fr/
    # etc.
    # -> Shouldn't interwiki link in this way? (lots of these)
    #
    # insource:/\[\[fr:[^\]]+\|.+\]/
    # -> Definitely shouldn't pipe normal interwiki links (33 of these)

    # <big> should be quite rare, maybe also <small>
    # <u> should usually be replaced with '', <s> should be rare

    # insource:/ layman/ or just blacklist "layman"
    # -> sometimes a last name, sometimes accurate because it refers
    # -> to a male individual.

    # https://en.wikipedia.org/wiki/Wikipedia:Use_modern_language
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Words_to_watch

    # https://en.wikipedia.org/wiki/User:Tony1/How_to_improve_your_writing
]


def make_change_map_for_article(article_title, article_text):
    from_to_this_article = {}
    for (from_re, to_string, must_not_contain_re) in REGEX_SUBSTITUTIONS:
        if must_not_contain_re:
            if must_not_contain_re.search(article_text):
                continue
        matches = from_re.findall(article_text)
        if matches:
            for match in matches:
                result = from_re.sub(to_string, match[0])
                if result != match[0]:
                    from_to_this_article[match[0]] = from_re.sub(to_string, match[0])
    return from_to_this_article


def dump_dict(section_title, dictionary):
    print("=== %s ===" % section_title)
    sorted_items = sorted(dictionary.items(), key=lambda t: len(t[1]), reverse=True)
    for (key, article_list) in sorted_items[0:50]:
        article_set = set(article_list)
        print("* %s/%s - %s - %s" % (
            len(article_list),
            len(article_set),
            key,
            ", ".join(["[[%s]]" % article for article in sorted(article_set)])
            ))


def jwb_escape(text):
    text = text.replace('"', '\"')
    text = text.replace("\\", "\\\\")
    return text


def dump_results(change_tuples, loop_number):
    print(f"= MANUAL FIXES {loop_number} =")
    for (article_title, from_to_map) in change_tuples:
        print("* [[{article_title}]]:")
        for (from_text, to_text) in from_to_map:
            print("** <nowiki>{from_text} -> {to_text}</nowiki>")

    print(f"= REGEXES FOR JWB {loop_number} =")
    for (article_title, from_to_map) in change_tuples:
        for (from_text, to_text) in from_to_map:
            from_text = jwb_escape(from_text)
            to_text = jwb_escape(to_text)
            print('{"replaceText":"%s","replaceWith":"%s","useRegex":true,"regexFlags":"g","ignoreNowiki":true},' % (
                from_text,
                to_text,
            ))


accumulated_changes = []
loop_number = 1


def process_article(article_title, article_text):
    global accumulated_changes, loop_number
    accumulated_changes.append((article_title,
                                make_change_map_for_article(article_title, article_text)))

    if len(accumulated_changes) > 1:
        dump_results(accumulated_changes, loop_number)
    accumulated_changes = []
    loop_number += 1


read_en_article_text(process_article)
