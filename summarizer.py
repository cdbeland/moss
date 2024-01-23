import fileinput
import re
import sys
import urllib.parse


for line in fileinput.input("-"):
    line = line.strip()

    match_result = re.match(r"^\* (\d+) - \[\[wikt:(.*?)\]\] - (.+)$",
                            line)
    if not match_result:
        match_result = re.match(r"^\* (\d+/\d+) - (.*?) - (\[\[.+\]\])$", line)

    if not match_result:
        print(line)
        continue

    article_count = match_result.group(1)
    word = match_result.group(2)
    article_list_str = match_result.group(3)

    article_list = article_list_str.split("]], [[")
    article_list = article_list[:5]
    article_list_str = "]], [[".join(article_list).strip("[]")

    special_word = False

    if word == "₤":
        special_word = True
        better_line = line
    elif word.startswith("<"):
        special_word = True
        better_line = "* %s - <nowiki>%s</nowiki> - [[%s]]" % (article_count, word, article_list_str)
    elif word.startswith("&"):
        special_word = True
        word_no_amp = word.lstrip("&")
        better_line = "* %s - &amp;%s (%s) - [[%s]]" % (article_count, word_no_amp, word, article_list_str)
    else:
        better_line = "* %s - [[wikt:%s]] - [[%s]]" % (article_count, word, article_list_str)

    if len(sys.argv) > 1 and sys.argv[1] == "--find-all":
        if special_word:
            # Strip ">" instead of encoding it so we find instances
            # with HTML attributes
            # word_safe = re.sub(">", "%3E", word_safe)
            word_safe = re.sub(">", "", word)

            word_safe = word_safe.replace("/", r"\/")
            word_safe = word_safe.replace("<", r"\<\/?")  # This also merges start and end tags
            word_safe = urllib.parse.quote_plus(word_safe)
            better_line += f" ... [https://en.wikipedia.org/w/index.php?search=insource%3A%2F{word_safe}%2Fi&ns0=1 find all]"

        else:
            better_line += f" ... [https://en.wikipedia.org/w/index.php?search=%22{word}%22&ns0=1 find all]"
    print(better_line)
