# head /backup/whata/home/beland/moss/run-c600526+2019-08-26T20\:46\:38-dump-2019-08-20/done/tmp-articles-linked-words.txt | python3 t1-extractor.py

import fileinput
import re
import string
from urllib.parse import unquote
from sectionalizer import sectionalize_lines

unsorted = [
    "BW",
    # TODO: BW needs to ignore italics and capital letters for "You"
    # in titles etc.  See [[1947]], [[1972 in film]]

    "Z",
    # TODO: Special report for batting averages and calibers, possibly
    # geared for JWB

    "BC",
    # Processing these with JWB via moss_entity_check.py; there are
    # too many to do manually, and the benefit is usually small.

    "TS+BRACKET",
    # TODO: Fix quality issues discriminating whitespace oops vs. STEM
    # notation

    "TF",
    # TODO: QA on language detection for more languages; code below
    # truncates any unlisted languages to this.

    "N", "P", "H", "U", "TS", "A"]
probably_wrong = ["T1", "TS+DOT", "TS+COMMA", "TS+EXTRA", "HB", "HL", "T/", "TE", "ME",

                  # These need {{lang}} and also to be added to the
                  # English Wiktionary; might be misspelled.
                  "TF+el", "TF+de"]
probably_right = ["L", "C", "D"]


line_parser_re = re.compile(r"^(.*?)\t\* \d+ - \[\[(.*?)\]\] - (.*$)")
first_letters = ["BEFORE A"] + [letter for letter in string.ascii_uppercase] + ["AFTER Z"]
typos_by_letter = {
    letter: {type_: [] for type_ in probably_wrong}
    for letter in first_letters
}
before_a = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9"}
comma_missing_ws_re = re.compile(r"\w,\w")
extra_ws_re = re.compile(r"\w ,\w|\w .\w|\w \)\w|\w\( \w|\w\[ \w|\w ]\w")

# Simpler than bracket_missing_whitespace_re for performance reasons
bracket_missing_ws_re = re.compile(r"(\w\[|\w\(|\)\w|\]\w)")


def get_first_letter(input_string):
    if input_string[0] in first_letters:
        return input_string[0]
    if input_string[0] in before_a:
        return "BEFORE A"
    return "AFTER Z"


for line in fileinput.input("-"):
    line = line.strip()
    if line.startswith("* 0 -"):
        continue
    groups = line_parser_re.match(line)
    if not groups:
        print(f"FAILED TO PARSE: '{line}'")
    types = groups[1].split(",")
    article_title = groups[2]
    typo_links = groups[3].split(", ")

    for (index, typo_link) in enumerate(typo_links):
        if types[index] == "TS" and "." in typo_link and " " not in typo_link:
            types[index] = "TS+DOT"
        elif types[index] == "TS" and comma_missing_ws_re.search(typo_link):
            types[index] = "TS+COMMA"
        elif types[index] == "TS" and extra_ws_re.search(typo_link):
            types[index] = "TS+EXTRA"
        elif types[index] == "TS" and bracket_missing_ws_re.search(typo_link):
            types[index] = "TS+BRACKET"
        elif types[index].startswith("TF") and types[index] not in probably_wrong:
            types[index] = "TF"

    best_type = None
    for type_ in probably_wrong:
        if type_ in types:
            best_type = type_
            break

    if not best_type:
        # Ignore any article that does have at least one probably wrong typo
        continue

    if any(type_ in unsorted for type_ in types):
        filtered_tuples = [tuple_ for tuple_ in zip(types, typo_links) if tuple_[0] in probably_wrong]
        if not filtered_tuples:
            continue
        typo_links = [tuple_[1] for tuple_ in filtered_tuples]
        types = [tuple_[0] for tuple_ in filtered_tuples]

    typos_by_letter[get_first_letter(article_title)][best_type].append((article_title, types, typo_links))


def clean_typo_link(typo_link):
    core = typo_link.replace("[[wikt:", "")
    core = core.replace("]]", "")
    if any(substring in core for substring in ["&lt;", "[", "]"]):
        typo_link = core
    return typo_link


def extract_linked_articles():
    linked_articles = set()
    for letter in ["before_A"] + list(string.ascii_uppercase) + ["after_Z"]:
        with open(f"/bulk-wikipedia/moss-subpages/{letter}", "r") as subpage_file:
            subpage_html = subpage_file.read()
            linked_articles_this_page = re.findall('<a href="/wiki/([^"]+)"', subpage_html)
            linked_articles_this_page = linked_articles.update(linked_articles_this_page)

    linked_articles = [unquote(title).replace("_", " ")
                       for title in linked_articles
                       if not (title.startswith("Wikipedia:")
                               or title.startswith("Wikipedia_talk:")
                               or title.startswith("User:")
                               or title.startswith("User_talk:")
                               or title.startswith("MOS:")
                               or title.startswith("Talk:")
                               or title.startswith("Help:")
                               or title.startswith("Special:")
                               or "#" in title)]
    return linked_articles


articles_to_ignore = extract_linked_articles()

for (letter, typos_by_best_type) in typos_by_letter.items():
    print(f"= {letter} =")
    for (best_type, tuple_list) in typos_by_best_type.items():
        print(f"=== {best_type}+ ===")
        output_lines = []
        for (article_title, types, typo_links) in sorted(tuple_list):
            if article_title in articles_to_ignore:
                continue
            bad_typo_links = []
            not_typo_links = []
            chem_links = []
            transliteration_links = []
            dna_links = []
            for (index, type_) in enumerate(types):
                if type_ in probably_wrong:
                    bad_typo_links.append(clean_typo_link(typo_links[index]))
                elif type_ == "C":
                    chem_links.append(clean_typo_link(typo_links[index]))
                elif type_ == "L":
                    transliteration_links.append(clean_typo_link(typo_links[index]))
                elif type_ == "D":
                    dna_links.append(clean_typo_link(typo_links[index]))
                else:
                    not_typo_links.append(clean_typo_link(typo_links[index]))
            output_line = f'* {len(typo_links)} - [[{article_title}]] - {", ".join(bad_typo_links)}'
            if chem_links:
                output_line += f'  (probably needs {{tl|chem name}}: {", ".join(chem_links)})'
            if transliteration_links:
                output_line += f'  (probably needs {{tl|transl}}: {", ".join(transliteration_links)})'
            if dna_links:
                output_line += f'  (probably needs {{tl|DNA sequence}}: {", ".join(dna_links)})'
            if not_typo_links:
                output_line += f'  (possibly OK: {", ".join(not_typo_links)})'
            output_lines.append(output_line)
        print(sectionalize_lines(output_lines))
