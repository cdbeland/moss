import fileinput
import re
import sys
import urllib.parse


for line in fileinput.input("-"):
    line = line.strip()

    match_result = re.match(r"^\* (\d+) - \[\[wikt:(.*?)\]\] - (.+)$",
                            line)
    if not match_result:
        # Some sort of garbled output?
        continue

    article_count = match_result.group(1)
    word = match_result.group(2)
    article_list_str = match_result.group(3)

    article_list = article_list_str.split("]], [[")
    article_list = article_list[:5]
    article_list_str = "]], [[".join(article_list).strip("[]")

    special_word = False
    if word.startswith("<") or word.startswith("&"):
        special_word = True

    if special_word:
        better_line = "* %s - <nowiki>%s</nowiki> - [[%s]]" % (article_count, word, article_list_str)
    else:
        better_line = "* %s - [[wikt:%s]] - [[%s]]" % (article_count, word, article_list_str)

    if len(sys.argv) > 1 and sys.argv[1] == "--find-all":
        if special_word:
            # Strip ">" instead of encoding it so we find instances
            # with HTML attributes
            # word_safe = re.sub(">", "%3E", word_safe)
            word_safe = re.sub(">", "", word)

            word_safe = urllib.parse.quote_plus(word_safe)
            better_line += " ... [https://en.wikipedia.org/w/index.php?search=insource%%3A%%2F\%s%%2F&ns0=1 find all]" % word_safe

        else:
            better_line += " ... [https://en.wikipedia.org/w/index.php?search=%s find all]" % word
    print(better_line)
