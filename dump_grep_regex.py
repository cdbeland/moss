from moss_dump_analyzer import read_en_article_text
import re
import sys
from xml.sax.saxutils import escape


if len(sys.argv) < 2:
    print("Please specify regex search term on the command line")
    exit(1)
if len(sys.argv) > 3:
    print("Too many arguments!")
    exit(1)


search_regex = re.compile(sys.argv[1])
filename = ""
if len(sys.argv) == 3:
    filename = sys.argv[2]


def grep_callback(article_title, article_text):
    if search_regex.search(article_title) or search_regex.search(article_text):
        article_title = escape(article_title)
        article_text = escape(article_text)
        print("<page>\n")
        print("<ns>0</ns>")
        print("<title>%s</title>" % article_title)
        print('<text xml:space="preserve">')
        print(article_text)
        print("</text>\n")
        print("  </page>\n")  # Whitespace is needed to fake real dump output exactly


read_en_article_text(grep_callback, filename=filename)
