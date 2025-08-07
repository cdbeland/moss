import fileinput
import re

match_re = re.compile(r"([\w\+/\-\?]+)\t\* \d+ - \[\[wikt:(.*?)\]\] - (.*)$")

for line in fileinput.input("-"):
    line = line.strip()
    match = match_re.match(line)

    category = match.group(1)
    word = match.group(2)
    article_list_str = match.group(3)

    print("%s\t* %s - [[wikt:%s]] - %s" %
          (category, len(word), word, article_list_str))
