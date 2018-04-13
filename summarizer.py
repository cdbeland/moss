import fileinput
import re


for line in fileinput.input():
    line = line.strip()

    match_result = re.match(r"^\* (\d+) - \[\[wikt:(\w+)\]\] - (.+)$",
                            line)

    article_count = match_result.group(1)
    word = match_result.group(2)
    article_list_str = match_result.group(3)

    article_list = article_list_str.split("]], [[")
    article_list = article_list[:5]
    article_list_str = "]], [[".join(article_list).strip("[]")
    better_line = "* %s - [[wikt:%s]] - [[%s]] ... [https://en.wikipedia.org/w/index.php?search=%s find all]" \
                  % (article_count, word, article_list_str, word)
    print better_line
