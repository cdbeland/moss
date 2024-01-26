import re
# from xml.sax.saxutils import escape
from xml.sax.saxutils import unescape
from moss_dump_analyzer import read_en_article_text


regexes = []
with open("/var/local/moss/bulk-wikipedia/Typos", "r") as regex_file:

    for line in regex_file:
        if "Typo" not in line:
            continue
        line = unescape(line)
        line = line.replace("</span>", "")
        line = re.sub("<span.*?>", "", line)

        if "disabled" in line:
            continue
        if "find=" not in line:
            continue
        attribute = re.search('find="(.*?)"', line)
        if attribute:
            regexes.append(attribute[1])


def regex_callback(article_title, article_text):
    for regex in regexes:
        if re.search(regex, article_text):
            # print(escape(article_title))
            print(article_title)


read_en_article_text(regex_callback, parallel=True)
