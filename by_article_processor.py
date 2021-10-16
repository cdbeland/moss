import fileinput
from multiprocessing import Pool
import sys
from word_categorizer import get_word_category, load_data


def get_word_categories_uniq(word_list):
    # This is to speed up categorization for articles with multiple
    # typos that are actually just the same word (which happens a
    # lot)
    word_lookup = {
        word: get_word_category(word)
        for word in set(word_list)
    }
    category_list = [word_lookup[word] for word in word_list]
    return ",".join(category_list)


def escape(input_string):
    output = input_string.replace("&", "&amp;")
    output = output.replace("<", "&lt;")
    output = output.replace(">", "&gt;")
    return output


def process_line(line):
    columns = line.split("\t")
    num_typos = int(columns[1])
    article_title = columns[2]
    category = ""
    word_list_linked = ""
    if num_typos:
        word_list = columns[3].split("𝆃")
        category = get_word_categories_uniq(word_list)
        word_list_linked = ", ".join("[[wikt:%s]]" % escape(word) for word in word_list)

    article_link = "[[%s]]" % escape(article_title)
    return f"{category}\t* {num_typos} - {article_link} - {word_list_linked}"


if __name__ == '__main__':
    load_data()
    print("Loading input...", file=sys.stderr)
    lines = [line.strip() for line in fileinput.input("-")]
    print("Processing...", file=sys.stderr)
    with Pool(8) as pool:
        for result in pool.imap(process_line, lines, chunksize=100):
            print(result)
        pool.close()
        pool.join()
