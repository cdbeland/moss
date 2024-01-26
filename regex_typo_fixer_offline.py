from collections import defaultdict
import datetime
from pprint import pformat, pprint
import regex as re
import sys
import time
from xml.sax.saxutils import unescape

from moss_dump_analyzer import read_en_article_text
from moss_entity_check import skip_article_strings
from wikitext_util import get_main_body_wikitext

# Run time: 1h40m per 100,000 articles (before performance improvements)

regex_tuples = []
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
        attribute = re.search('word="(.*?)" find="(.*?)" replace="(.*?)"', line, re.MULTILINE)
        if attribute:
            if attribute[1] == "Regex code to detect the error":
                continue

            regex_name = attribute[1]
            regex_string = attribute[2]
            replacement = re.sub(r"\$([0-9])", r"\\\1", attribute[3])
            regex_compiled = re.compile(regex_string)
            regex_tuples.append((regex_name, regex_string, regex_compiled, replacement))

regex_frequencies = {
}

regex_tuples = sorted(regex_tuples, key=lambda r: (len(r[1]), r[1]))

please_load = "all"
if please_load == "high_freq_only":
    regex_tuples = [r for r in regex_tuples if r[0] in regex_frequencies]
    regex_tuples = sorted(regex_tuples, key=lambda r: regex_frequencies[r[0]])
elif please_load == "low_freq_only":
    regex_tuples = [r for r in regex_tuples if r[0] not in regex_frequencies]
elif please_load == "all":
    pass
else:
    print(f"Unknown please_load {please_load}")
    exit(1)

print(f"Loaded {len(regex_tuples)} regular expressions", file=sys.stderr)


def skip_article(article_text):
    """
    # Weeded out upstream by xml_to_csv.py
    if article_text.startswith("#REDIRECT") or article_text.startswith("#redirect"):
        return True
    """

    for skip_string in skip_article_strings:
        if skip_string in article_text:
            return True

    return False


attr_suppressor = re.compile('<(ref|span) .*?>')
general_suppressor_patterns = [
    r"https?://[^ \n\|&]+",
    r"[0-9a-zA-Z\-\.]+\.(com|edu|org|gov)",
    r"<!--.*?-->",
    r"{{not a typo.*?}}",
]
general_suppressor_regexes = [re.compile(p, flags=re.S) for p in general_suppressor_patterns]

# Reduce false positives at the expense of missing some things
aggressive_suppressor_patterns = [
    r'<ref( .*?>|>).*?</ref>',
    r'<ref .*?/>',
    r"<gallery[^>]*>.*?</gallery>",  # Must happen before table removal due to possibility of "|-"
    r"<code[^>]*>.*?</code>",
    r"<syntaxhighlight[^>]*>.*?</syntaxhighlight>",
    r"<math[^>]*>.*?</math>",
    r"<score[^>]*>.*?</score>",
    r'{\|.*?\|}',
    r'{{[Ii]nfobox([^}]+{{.*?}})+.*?}}',
    r'{{[Ii]nfobox.*?}}',
    r'\[\[(File|Image):.*\]\]',
    r'{{[Ll]ang.*?}}',
    r'{{IPA.*?}}',
]
aggressive_suppressor_regexes = [re.compile(p, flags=re.S) for p in aggressive_suppressor_patterns]


def clean_article(article_text, aggressive=False):
    article_text = attr_suppressor.sub(r"<\1>", article_text)
    for suppress_re in general_suppressor_regexes:
        article_text = suppress_re.sub("✂", article_text)
    if aggressive:
        article_text = get_main_body_wikitext(article_text)
        for suppress_re in aggressive_suppressor_regexes:
            article_text = suppress_re.sub("✂", article_text)
    return article_text


def regex_callback(article_title, article_text):
    if skip_article(article_text):
        return
    article_text = clean_article(article_text, aggressive=True)

    for regex_tuple in regex_tuples:
        result = regex_tuple[2].search(article_text)
        if result:
            print(article_title)
            # For performance reasons, stop after the first detected problem
            return


checked = 0
skipped = 0
regex_runtimes = defaultdict(int)
regex_hits = defaultdict(int)
debug_contents = False
print_stats = False  # Probably need to set parallel=False


def show_replacement(result, regex_tuple, article_text):
    replacement = regex_tuple[3]
    snippet_start = max(result.start() - 10, 0)
    snippet_end = min(result.end() + 10, len(article_text))
    snippet = article_text[snippet_start:snippet_end]
    changed_to = regex_tuple[2].sub(replacement, snippet)
    if snippet == changed_to:
        return None
    else:
        snippet = snippet.replace("\n", "\\n")
        changed_to = changed_to.replace("\n", "\\n")
        return (f'"{snippet}" -> "{changed_to}"')


def calibration_callback(article_title, article_text):
    global checked
    global skipped

    if skip_article(article_text):
        skipped += 1
        return
    article_text = clean_article(article_text, aggressive=True)

    checked += 1
    article_matched = False
    for regex_tuple in regex_tuples:
        if print_stats:
            start_time = time.time()

        result = regex_tuple[2].search(article_text)

        if print_stats:
            elapsed = time.time() - start_time
            regex_runtimes[regex_tuple[0]] += elapsed

        if result:
            replacement_str = show_replacement(result, regex_tuple, article_text)
            if replacement_str:
                article_matched = True
                if print_stats:
                    regex_hits[regex_tuple[0]] += 1
                print(f"{article_title}\t{pformat(result[0])}\t{replacement_str}\t{regex_tuple[0]}")
            else:
                # print(f"{article_title}\tNO CHANGES MADE")
                pass

    if article_matched and debug_contents:
        print(">>>>>>>>>>>>>>>>>>>>")
        print(article_text)
        print("<<<<<<<<<<<<<<<<<<<<")

    # if not article_matched:
    #     print(f"{article_title}\tNO HITS")

    if print_stats:
        if checked % 1000 == 0:
            print(f"{checked} articles checked so far", file=sys.stderr)
            print(f"{skipped} articles skipped so far", file=sys.stderr)
        if checked % 1000 == 0:
            runtimes_sorted = sorted(regex_runtimes.items(), key=lambda pair: (pair[1], pair[0]))
            pprint(runtimes_sorted)

            hits_sorted = sorted(regex_hits.items(), key=lambda pair: (pair[1], pair[0]))
            for (r, hits) in hits_sorted:
                print(f"    {pformat(r)}: {hits},  # noqa", file=sys.stderr)
            # pprint(hits_sorted)


print(f"{datetime.datetime.now().isoformat()}", file=sys.stderr)
# read_en_article_text(regex_callback, parallel=True)
read_en_article_text(calibration_callback, parallel=True)
print(f"{datetime.datetime.now().isoformat()} ", file=sys.stderr)
