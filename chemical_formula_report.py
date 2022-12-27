from collections import defaultdict
import mysql.connector
import re
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext

mysql_connection = mysql.connector.connect(user='beland',
                                           host='127.0.0.1',
                                           database='enwiki')

cursor = mysql_connection.cursor()
formulas = []
for category in [
        "Redirects_from_chemical_formulas",
        "Inorganic_molecular_formula_set_index_pages",
        "Inorganic_molecular_formulas",
        "Molecular_formulas",
        "Molecular_formula_set_index_pages",
]:
    cursor.execute("SELECT title FROM page_categories WHERE category_name=%s", [category])
    formulas.extend([title.decode('utf8') for (title,) in cursor])
cursor.close()

formulas = [f for f in formulas if any(char for char in list(f) if char.isdigit())]
formulas = [f for f in formulas if "," not in f]
formulas = sorted(set(formulas), key=lambda f: len(f) * -1)
formulas_pattern = "|".join([rf"\b{formula}\b" for formula in formulas])
formulas_pattern = formulas_pattern.replace("(", r"\(")
formulas_pattern = formulas_pattern.replace(")", r"\)")
formulas_pattern = formulas_pattern.replace("+", r"\+")
formulas_re = re.compile(formulas_pattern)

articles_by_formula = defaultdict(list)


def chem_formula_check(article_title, article_text):
    article_text = wikitext_to_plaintext(article_text, flatten_sup_sub=False)
    article_text = get_main_body_wikitext(article_text)

    # Fast but over-matches
    matches = [f for f in formulas if f in article_text]
    if matches:
        # Slow but fewer false matches
        matches = formulas_re.findall(article_text)
    return(article_title, matches)


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
    # Run time: ~2h40m (8-core parallel)
    read_en_article_text(chem_formula_check, process_result_callback=add_tuples_to_results, parallel=True)
    dump_results()
