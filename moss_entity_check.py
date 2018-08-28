# Run time: About 2 hours

from moss_dump_analyzer import read_en_article_text
import re
from unencode_entities import alert, keep, controversial, transform, greek_letters, find_char_num


entities_re = re.compile("&#?[a-zA-Z0-9]+;")
alerts_found = {}
controversial_found = {}
uncontroversial_found = {}
greek_letters_found = {}
unknown_found = {}
unknown_numerical_latin = {}
unknown_numerical_low = {}
unknown_numerical_high = {}
non_entity_transform = [string for string in transform.keys() if not string.startswith("&")]


def add_safely(value, key, dictionary):
    existing_list = dictionary.get(key, [])
    existing_list.append(value)
    dictionary[key] = existing_list
    return dictionary


def entity_check(article_title, article_text):

    for string in alert:
        for instance in re.findall(string, article_text):
            add_safely(article_title, string, alerts_found)
            # This intentionally adds the article title as many times
            # as the string appears

    for string in non_entity_transform:
        if string in article_text:
            for instance in re.findall(string, article_text):
                add_safely(article_title, string, uncontroversial_found)
                # This intentionally adds the article title as many
                # times as the string appears

    for entity in entities_re.findall(article_text):
        if entity in alert:
            continue
        elif entity in controversial:
            add_safely(article_title, entity, controversial_found)
        elif entity in keep:
            continue
        elif entity in greek_letters:
            add_safely(article_title, entity, greek_letters_found)
        elif entity in transform:
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
    for (key, article_list) in sorted_items:
        article_set = set(article_list)
        print("* %s/%s - %s - %s" % (
            len(article_list),
            len(article_set),
            key,
            ", ".join(["[[%s]]" % article for article in sorted(article_set)])
            ))


def dump_results():
    dump_dict("Controversial entities", controversial_found)
    dump_dict("Greek letters", greek_letters_found)
    dump_dict("To avoid", alerts_found)
    dump_dict("Uncontroversial entities", uncontroversial_found)
    dump_dict("Unknown", unknown_found)
    dump_dict("Unknown numerical, Latin range", unknown_numerical_latin)
    dump_dict("Unknown low numerical", unknown_numerical_low)
    dump_dict("Unknown high numerical", unknown_numerical_high)


read_en_article_text(entity_check)
dump_results()


def html_tag_check():
    # TODO: search for HTML tags here
    # article_text_tmp = re.sub("<nowiki>.*?</nowiki>", "", article_text_tmp)
    pass
