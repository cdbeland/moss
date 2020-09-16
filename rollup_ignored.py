from collections import defaultdict
import fileinput
import re

unsupported_titles = ["{", "}", "|", "#", ".", ":", "<", ">", "__TOC__", "||"]


if __name__ == '__main__':

    articles_by_word = defaultdict(list)
    
    for line in fileinput.input("-"):
        line = line.strip()

        (_, word, article) = line.split("\t")
        if word in unsupported_titles:
            continue
        articles_by_word[word].append(article)

    for (word, article_list) in articles_by_word.items():
        article_set = set(article_list)

        category = "*"
        if word.endswith("’s"):
            category = "S"  # MOS:STRAIGHT

        # article_links = ", ".join(["[[%s]]" % article_name for article_name in sorted(article_set)][0:500])
        # Limit at 500 to avoid expensive sorting.  Sampled articles
        # aren't always the ones at the beginning of the alphabet as a
        # result, but this doesn't really matter.

        print(f"{category} {len(article_list)}/{len(article_set)} - {word}")
        # " - {article_links}"
