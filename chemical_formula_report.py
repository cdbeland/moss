from collections import defaultdict
import mysql.connector
import re
from moss_dump_analyzer import read_en_article_text


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

formulas = sorted(set([f for f in formulas if any(char for char in list(f) if char.isdigit())]))
supression_re = re.compile(r"{{chem\|.*?}}|{{chem2\|.*?}}")
articles_by_formula = defaultdict(list)


def chem_formula_check(article_title, article_text):
    article_text = supression_re.sub("", article_text)
    matches = [f for f in formulas if f in article_text]
    # if matches:
    #     print(f"* [[{article_title}]] - {' '.join(matches)}")
    return(article_title, matches)


def add_tuples_to_results(tuple_list):
    if not tuple_list:
        return
    (article_title, matches) = tuple_list
    for match in matches:
        articles_by_formula[match].append(article_title)


if __name__ == '__main__':
    # Run time: About 6h15m (8 core parallel)
    read_en_article_text(chem_formula_check, process_result_callback=add_tuples_to_results, parallel=True)
    for (formula, article_list) in articles_by_formula.items():
        print(f"* {len(article_list)} - {formula} - [[{']], [['.join(article_list)}]]")
