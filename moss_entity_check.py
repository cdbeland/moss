# Run time: About 2 hours

from moss_dump_analyzer import read_en_article_text
import re
from unencode_entities import alert, keep, controversial, transform, greek_letters, find_char_num, entities_re, fix_text

alerts_found = {}
controversial_found = {}
uncontroversial_found = {}
greek_letters_found = {}
unknown_found = {}
unknown_numerical_latin = {}
unknown_numerical_low = {}
unknown_numerical_high = {}
non_entity_transform = [string for string in transform.keys() if not string.startswith("&")]
worst_articles = {}


def add_safely(value, key, dictionary):
    existing_list = dictionary.get(key, [])
    existing_list.append(value)
    dictionary[key] = existing_list
    return dictionary


def entity_check(article_title, article_text):

    for string in alert:
        for instance in re.findall(string, article_text):
            add_safely(article_title, string, alerts_found)
            add_safely(string, article_title, worst_articles)
            # This intentionally adds the article title as many times
            # as the string appears

    for string in non_entity_transform:
        if string in article_text:
            for instance in re.findall(string, article_text):
                add_safely(article_title, string, uncontroversial_found)
                add_safely(string, article_title, worst_articles)
                # This intentionally adds the article title as many
                # times as the string appears

    for entity in entities_re.findall(article_text):
        if entity in alert:
            continue
        elif entity in controversial:
            add_safely(article_title, entity, controversial_found)
            continue
        elif entity in keep:
            continue
        elif entity in greek_letters:
            add_safely(article_title, entity, greek_letters_found)
            continue

        add_safely(entity, article_title, worst_articles)  # Only counting auto-fixable things

        if entity in transform:
            add_safely(article_title, entity, uncontroversial_found)
        else:
            value = find_char_num(entity)
            if value:
                if int(value) < 592:      # x0250
                    add_safely(article_title, entity, unknown_numerical_latin)
                elif int(value) < 12288:  # x3000
                    add_safely(article_title, entity, unknown_numerical_low)
                else:
                    add_safely(article_title, entity, unknown_numerical_high)
            else:
                if entity == entity.upper() and re.search("[A-Z]+%s" % entity, article_text):
                    # Ignore things like "R&B;" and "PB&J;" which is common in railroad names.
                    continue
                add_safely(article_title, entity, unknown_found)


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


def extract_entities(dictionary):
    return {entity for entity in dictionary.keys()}


def dump_results():
    sections = {
        "Worst articles": worst_articles,
        "Controversial entities": controversial_found,
        "Greek letters": greek_letters_found,
        "To avoid": alerts_found,
        "Uncontroversial entities": uncontroversial_found,
        "Unknown": unknown_found,
        "Unknown numerical: Latin range": unknown_numerical_latin,
        "Unknown low numerical": unknown_numerical_low,
        "Unknown high numerical": unknown_numerical_high,
    }
    for (section_title, dictionary) in sections.items():
        dump_dict(section_title, dictionary)

    print("= REGEXES FOR JWB =")
    bad_entities = set()
    for dictionary in [alerts_found, uncontroversial_found,
                       unknown_found, unknown_numerical_latin, unknown_numerical_low,
                       unknown_numerical_high]:
        bad_entities.update(extract_entities(dictionary))

    for entity in sorted(bad_entities):
        # Skip tens of thousands of CJK and other characters, just to
        # keep the size of the config file reasonable (use
        # auto_correct.py to fix these en masse until the number is
        # reasonable again)
        if re.match("&#x?[1-9a-fA-F][0-9a-fA-F]{3,5}", entity):
            continue

        fixed_entity = fix_text(entity)
        if '"' == fixed_entity:
            fixed_entity = '\"'
        if fixed_entity == "\\":
            fixed_entity = "\\\\"
        if fixed_entity in ["\r", "\t", "", ""]:
            continue

        if entity != fixed_entity:
            print('{"replaceText":"%s","replaceWith":"%s","useRegex":true,"regexFlags":"g","ignoreNowiki":true},' % (
                entity,
                fixed_entity,
            ))


read_en_article_text(entity_check)
dump_results()
