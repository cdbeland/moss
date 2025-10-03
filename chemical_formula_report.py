from collections import defaultdict
import os
import re
import requests
import sys
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext

# This script finds all instances of known chemical formulas which do
# not use subscripts as required by [[MOS:SUPERSCRIPT]]. These should
# be enclosed in {{chem}} or {{chem2}} for spell-checking purposes.


MANUAL_FORMULAS = ["MtCO2", "MtCO2e", "MtCO2eq", "GtCO2"]
MOSS_USER_AGENT = os.environ["MOSS_USER_AGENT"]


# Always returns a list, even if there are no articles in the category
def get_articles_in_category(category_name, continue_params=None):
    article_list = []
    api_params = {
        "action": "query",
        "cmtitle": "Category:" + category_name,
        "cmlimit": 500,
        "list": "categorymembers",
        "format": "json"
    }
    if continue_params:
        api_params.update(continue_params)
    result = session.get(url=api_url, params=api_params)

    try:
        data = result.json()
    except Exception as e:
        print("Bad response to category membership fetch!")
        print(result)
        print(e)
        exit(1)
    pages = data.get('query', {}).get('categorymembers', [])

    for page in pages:
        article_list.extend([page['title']])

    if "continue" in data:
        return article_list + get_articles_in_category(category_name, continue_params=data["continue"])
    return article_list


# --- Live interrogation of Wikipedia categories ---

formulas = []
session = requests.Session()
session.headers.update({"User-Agent": MOSS_USER_AGENT})
api_url = "https://en.wikipedia.org/w/api.php"
print("Getting live category member lists...", file=sys.stderr)
for category_name in [
        "Redirects_from_chemical_formulas",  # About 8763 pages
        "Inorganic_molecular_formulas",
        "Molecular_formulas",
        "Set index articles on molecular formulas",
]:
    article_list = get_articles_in_category(category_name)
    print(f"{category_name} - {len(article_list)}", file=sys.stderr)
    formulas.extend(article_list)

formulas.extend(MANUAL_FORMULAS)
formulas = [f for f in formulas if any(char for char in list(f) if char.isdigit())]
formulas = [f for f in formulas if "," not in f]
formulas = [f for f in formulas if not f[0].isdigit()]
formulas = sorted(set(formulas), key=lambda f: len(f) * -1)

formulas_by_first_letter = defaultdict(list)
for formula in formulas:
    first_letter = formula.strip("()")[0]
    formulas_by_first_letter[first_letter].append(formula)
first_letters = list(formulas_by_first_letter.keys())

formulas_pattern = "|".join([rf"\b{formula}\b" for formula in formulas])
formulas_pattern = formulas_pattern.replace("(", r"\(")
formulas_pattern = formulas_pattern.replace(")", r"\)")
formulas_pattern = formulas_pattern.replace("+", r"\+")
formulas_re = re.compile(formulas_pattern)

articles_by_formula = defaultdict(list)


def chem_formula_check(article_title, article_text):
    article_text = wikitext_to_plaintext(article_text, flatten_sup_sub=False)
    article_text = get_main_body_wikitext(article_text)

    # If we ever start looking inside templates, we will need
    # something like this to avoid false alarms for [[Template:Infobox
    # geologic timespan]]:
    # parameter_exclude_re = re.compile(r"\| c?o2 *=")
    # article_text = parameter_exclude_re.sub("", article_text)

    # Quickly ignore any words without digits
    article_words = article_text.split(" ")
    article_words = [word for word in article_words if any(char.isdigit() for char in word)]
    article_words = [word for word in article_words if not word[0].isdigit()]

    # Quickly ignore any words that won't match any formula
    article_words = [word for word in article_words
                     if any(letter for letter in first_letters if letter in word)]

    # Fast but over-matches
    matching_formulas = []
    for word in article_words:
        for letter in first_letter:
            if letter not in word:
                continue
            for formula in formulas_by_first_letter:
                if formula in word:
                    matching_formulas.append(formula)
                    break
        if matching_formulas:
            break

    if matching_formulas:
        article_text_short = " ".join(article_words)
        # Slow but fewer false matches
        matches = formulas_re.findall(article_text_short)
        return (article_title, matches)


def add_tuples_to_results(tuple_list):
    if not tuple_list:
        return
    (article_title, matches) = tuple_list
    for match in matches:
        articles_by_formula[match].append(article_title)


def dump_results():
    for (formula, article_list) in articles_by_formula.items():
        articles_by_formula[formula] = sorted(set(article_list))
    tuples = list(articles_by_formula.items())
    tuples.sort(key=lambda t: (len(t[1]) * -1, t[0]))
    for (formula, article_list) in tuples:
        short_list = sorted(article_list)
        length = len(article_list)
        line = f"* {length} - {formula} - [["
        line += "]], [[".join(short_list)
        line += "]]"
        print(line)


if __name__ == '__main__':
    print("Running chem_formula_check...", file=sys.stderr)
    # Run time: ~1h 15 m (8-core parallel)
    read_en_article_text(chem_formula_check, process_result_callback=add_tuples_to_results, parallel=True)
    dump_results()
    print("Done", file=sys.stderr)
