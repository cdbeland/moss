import fileinput
from word_categorizer import get_word_category


for line in fileinput.input("-"):
    line = line.strip()
    columns = line.split("\t")

    num_typos = int(columns[1])
    article_title = columns[2]
    category = ""
    word_list_linked = ""
    if num_typos:
        word_list = columns[3].split(" ")
        category = ",".join([get_word_category(word) for word in word_list])
        word_list_linked = ", ".join("[[wikt:%s]]" % word for word in word_list)

    article_link = article_title
    article_link = article_link.replace("&", "&amp;")
    article_link = article_link.replace("<", "&lt;")
    article_link = article_link.replace(">", "&gt;")
    article_link = "[[%s]]" % article_link

    print("%s\t* %s - %s - %s" % (category, num_typos, article_link, word_list_linked))
