# Run time: About 97 minutes

from moss_dump_analyzer import read_en_article_text
import re
from unencode_entities import alert, keep, controversial, transform, greek_letters

entities_re = re.compile("&#?[a-zA-Z0-9]+;")
alerts_found = {}
controversial_found = {}
uncontroversial_found = {}
greek_letters_found = {}
unknown_found = {}
non_entity_transform = [string for string in transform.keys() if not string.startswith("&")]


def add_safely(value, key, dictionary):
    existing_list = dictionary.get(key, [])
    existing_list.append(value)
    dictionary[key] = existing_list
    return dictionary


def entity_check(article_title, article_text):

    for string in alert:
        if string in article_text:
            add_safely(article_title, string, alerts_found)

    for string in non_entity_transform:
        if string in article_text:
            add_safely(article_title, string, uncontroversial_found)

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


read_en_article_text(entity_check)
dump_results()


def html_tag_check():
    # TODO: search for HTML tags here
    # article_text_tmp = re.sub("<nowiki>.*?</nowiki>", "", article_text_tmp)
    pass
