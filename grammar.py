# Encyclopedia style rules:
# * Implied you not allowed?
# * Abbreviation rules
# * Punctuation rules
#    " not '
#    terminal punctuation and quotes
#    comma style (Oxford comma mandatory!)


# Use cases:
# * Suggest edits for a specific article
#   * Command line from file
#   * Command line from Wikipedia API
#   * JavaScript
# * Report on theory of English grammar


import mysql.connector
import nltk
import re
import stopit
import sys
import time
from english_grammar import (enwiktionary_cat_to_pos,
                             phrase_structures,
                             closed_lexicon,
                             vocab_overrides)
from pywikibot import Page, Site
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext, blockquote_re


mysql_connection = mysql.connector.connect(user='beland',
                                           host='127.0.0.1',
                                           database='enwiktionary')


# TODO: Use this for visualization.  Would be interesting to see
# curves for articles rated Featured, A, B, Good, C, Start, Stub, etc.
def generate_stats(plaintext):
    print("sentences per paragraph\twords per paragraph\tmax words per paragraph")
    paragraphs = plaintext.split("\n")
    for paragraph in paragraphs:
        words_in_paragraph = nltk.word_tokenize(paragraph)
        if len(words_in_paragraph) == 0:
            continue

        sentences = nltk.sent_tokenize(paragraph)
        max_words_per_sentence = 0
        for sentence in sentences:
            words = nltk.word_tokenize(sentence)
            if len(words) > max_words_per_sentence:
                max_words_per_sentence = len(words)

        print("%s\t%s\t%s" % (len(sentences), len(words_in_paragraph), max_words_per_sentence))


# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Numbers
# Includes integers, decimal fractions, ratios
number_pattern = r"(\d+|\d+.\d+|\d+:\d)"
conforming_number_re = re.compile(r"^%s$" % number_pattern)
ordinal_re = re.compile(r"^\d*(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|0th)$")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currencies_and_monetary_values
currency_pattern = "|".join(closed_lexicon["CUR"])
currency_pattern = currency_pattern.replace("$", "\\$")
conforming_currency_re = re.compile("^(%s)%s(M|bn)?$" % (currency_pattern, number_pattern))
# M for million, bn for billion per
# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currencies_and_monetary_values

# Must be an integer
SENTENCE_TIMEOUT_SEC = 1


repair_dot_re = re.compile(r"([A-Z]\.[A-Z]$)|(^[A-Z]$)")


def repair_tokenization(words_in):
    # Fix "i.e.", "R.E.M.", etc.
    words_out = []
    for word in words_in:
        # No word to append to
        if not words_out:
            words_out.append(word)
            continue

        if word == "." and repair_dot_re.search(words_out[-1]):
            words_out[-1] += word
            continue

        words_out.append(word)

    return words_out


def check_english(wikitext, title):
    # Output is to stdout with tab-separated fields:
    # * Type of message
    #   S = spelling problem
    #   G = grammar problem
    #   L = length issues
    #   U = Unsupported construct
    #   ! = parse failure
    # * Article title
    # * Message
    # * Details

    # if (TODO: CONSOLIDATE WITH moss_spell_check.py):
    #    print("!\tArticle parse broken?\t%s" % title)
    #    return

    # TODO: Block equations can be introduced with lines like "Then"
    # or "Maxwell's laws are" and lots of different variations.
    if "<math>" in wikitext:
        print(f"U\t{title}\t<math> detected, skipping article")
        return

    if "#REDIRECT" in wikitext:
        print(f"U\t{title}\tRedirect detected, skipping article")
        return

    # Ignore bad grammar in quotations and poems
    wikitext = blockquote_re.sub("✂", wikitext)

    plaintext = get_main_body_wikitext(wikitext_to_plaintext(wikitext), strong=True)
    sentences = []

    # Tokenizing paragraphs individually helps prevent NLTK from
    # getting confused by some situations, like list items.
    paragraphs = plaintext.split("\n")
    for paragraph in paragraphs:
        words_in_paragraph = nltk.word_tokenize(paragraph)
        if len(words_in_paragraph) > 500:
            print("L\t%s\tOverly long paragraph?\t%s words\t%s" % (title, len(words_in_paragraph), paragraph))

        sentences.extend(nltk.sent_tokenize(paragraph))

    # Parse the short sentences first since they should be
    # easiest.
    sentences.sort(key=lambda s: len(s))

    for sentence in sentences:
        start_time = time.time()

        if "✂" in sentence:
            # These represent suppressions (hiding things from spell
            # check and grammar check) during the transformation from
            # wikitext, such as templates and quotations.

            # TODO: Handle quote marks
            # * They can replace any part of speech, if they parse as that
            #   part of speech themselves.
            # * They can contain novel words and errors.
            # * They can be a literal quotation with a "said"
            #   construction, in which case they don't need to be any
            #   particular part of speech.  (Though maybe they are usually
            #   full sentences, unless it's someone blurting out a partial
            #   utterance?)
            print("U\t%s\tSuppression detected, skipping sentence\t%s" % (title, sentence))
            continue

        words = nltk.word_tokenize(sentence)
        words = repair_tokenization(words)
        if len(words) > 200:
            print("L\t%s\tOverly long sentence?\t%s words\t%s" % (title, len(words), sentence))
            continue

        if len(words) > 15:
            print("U\t%s\t%s words, skipping sentence\t%s" % (title, len(words), sentence))
            continue

        (grammar_string, word_to_pos) = load_grammar_for_word_list(words)
        is_grammatical = None
        with stopit.SignalTimeout(SENTENCE_TIMEOUT_SEC, swallow_exc=True) as timeout_result:
            is_grammatical = is_sentence_grammatical_beland(words, word_to_pos, title, sentence, grammar_string)

        elapsed = time.time() - start_time

        if timeout_result.state == timeout_result.TIMED_OUT:
            print("T\t%s\t%s\tTIMEOUT\t%s" % (elapsed, title, sentence))
            continue

        elapsed = time.time() - start_time
        if is_grammatical:
            print("Y\t%s\t%s\tYay, parsed sentence successfully!\t%s" % (elapsed, title, sentence))
        else:
            print("G\t%s\t%s\tUngrammatical sentence?\t%s" % (elapsed, title, sentence))


def is_sentence_grammatical_beland(word_list, word_to_pos, title, sentence, grammar_string):

    word_train = []

    previous_word = None
    for word in word_list:
        expand_grammar = False
        pos_list = word_to_pos.get(word, [])

        # Not requiring pos_list be empty because "Such" is a proper
        # noun but we need to look up "such"
        if previous_word is None and word == word.title():
            tmp_pos_list = word_to_pos.get(word.lower())
            if tmp_pos_list:
                # So that CFG parser can do the POS lookup
                word_list[0] = word.lower()
                pos_list.extend(tmp_pos_list)
        if not pos_list and conforming_number_re.match(word):
            pos_list = ["NUM"]
            expand_grammar = True
        if not pos_list and ordinal_re.match(word):
            pos_list = ["ORD"]
            expand_grammar = True
        if not pos_list and conforming_currency_re.match(word):
            pos_list = ["CURNUM"]
            expand_grammar = True
        if not pos_list and word.isalnum() and word[0].isalpha() and (word[0] == word[0].upper()):
            # Assume all capitalized words and acronyms (allowing some numbers sprinkled in) are proper nouns
            # Including Chris, NASA, GmbH, A380
            pos_list = ["N"]
            expand_grammar = True
        if not pos_list and (word == "'" and previous_word[-1].lower() == "s") or word == "'s":
            pos_list = ["POSS"]
            expand_grammar = True
        if "-" in word:
            word_parts = word.split("-")
            pos_patterns = []
            for part in word_parts:
                tmp_pos_list = word_to_pos.get(part)
                if not tmp_pos_list:
                    tmp_pos_list = word_to_pos.get(part.lower())
                if tmp_pos_list:
                    pos_patterns.append(tmp_pos_list)
                else:
                    break
            if len(pos_patterns) == len(word_parts) and len(word_parts) == 2:
                if "ADJ" in pos_patterns[0] and "N" in pos_patterns[1]:
                    # e.g. "blue-hull"
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif "NUM" in pos_patterns[0] and "N" in pos_patterns[1]:
                    # e.g. "two-hull"
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif "ADJ" in pos_patterns[0] and "ADJ" in pos_patterns[1]:
                    # e.g. "blue-grey"
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif word_parts[0].isnumeric() and "N" in pos_patterns[1]:
                    # e.g. 15-year
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif "ADJ" in pos_patterns[0] and "V" in pos_patterns[1] and word_parts[1][-1] == "d":
                    # e.g. Saudi-led
                    # -d is a cheesy way to look for past tense verbs only
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif "N" in pos_patterns[0] and "V" in pos_patterns[1] and word_parts[1][-1] == "d":
                    # e.g. hickory-smoked
                    # -d is a cheesy way to look for past tense verbs only
                    pos_list = ["ADJ"]
                    expand_grammar = True
                elif word_parts[0].lower() == "sub":
                    # e.g. sub-contract
                    pos_list = pos_patterns[1]
                    expand_grammar = True
                elif word_parts[0].lower() == "co":
                    # e.g. co-founders, co-founded
                    pos_list = pos_patterns[1]
                    expand_grammar = True
                elif word_parts[0].lower() == "non":
                    # e.g. non-aggression, non-blue
                    pos_list = pos_patterns[1]
                    expand_grammar = True
                elif word_parts[1].lower() == "class":
                    # e.g. Washington-class
                    pos_list = "ADJ"
                    expand_grammar = True

        if not pos_list:
            print("S\t%s\t%s\tNo POS for word\t%s" % (word, title, word_list))
            return True

        if expand_grammar:
            word_to_pos[word] = pos_list
            for pos in pos_list:
                grammar_string += '%s -> "%s"\n' % (pos, word)

        word_train.append((word, pos_list))
        previous_word = word

    print("DEBUG\t%s" % word_train)

    grammar = nltk.CFG.fromstring(grammar_string)

    # parser = nltk.parse.RecursiveDescentParser(grammar)  # Cannot handle X -> X Y (infinite loop)
    # parser.trace(5)
    # parser = nltk.parse.LeftCornerChartParser(grammar)
    parser = nltk.parse.BottomUpLeftCornerChartParser(grammar)
    # Parsers background: http://www.nltk.org/book/ch08.html
    # Other parsers are available in nltk.parse

    # print(grammar)

    try:
        possible_parses = parser.parse(word_list)
    except Exception as e:
        print(e)
        return False

    seen = []
    possible_parses_dedup = []
    for parse in possible_parses:
        serialized = parse.pformat()
        if serialized in seen:
            print("!\tDROPPED DUP!")
            continue
        else:
            possible_parses_dedup.append(parse)
            seen.append(serialized)
    # parse_dummies = [parse.pretty_print() for parse in possible_parses_dedup]
    parse_dummies = [parse for parse in possible_parses_dedup]
    if len(parse_dummies) == 0:
        print("DEBUG\t%s" % word_train)
        return False
    return True


def is_sentence_grammatical_nltk(word_list):
    # "word_list" instead of sentence avoids re-tokenizing

    tagged = nltk.pos_tag(word_list)
    print(tagged)
    return True


def fetch_article_wikitext(title):
    site = Site()
    page = Page(site, title=title)
    return page.text


def fetch_article_plaintext(title):
    site = Site()
    page = Page(site, title=title)
    plaintext = wikitext_to_plaintext(page.text)
    return get_main_body_wikitext(plaintext, strong=True)


# TODO: For later command-line use
def check_article(title):
    wikitext = fetch_article_wikitext(title)
    check_english(wikitext, title)


# BOOTSTRAPPING

# A quasi-representative sample of topics (for positive testing) from
# well-written articles listed at:
# https://en.wikipedia.org/wiki/Wikipedia:Featured_articles

sample_featured_articles = [

    # DEBUGGING FILES

    # "0test",

    # FEATURED ARTICLES

    "BAE Systems",
    "Evolution",
    "Chicago Board of Trade Building",
    "ROT13",
    "Periodic table",
    "Everything Tastes Better with Bacon",
    "Renewable energy in Scotland",
    "Pigeon photography",
    "University of California, Riverside",
    "Same-sex marriage in Spain",
    "Irish phonology",
    "Sentence spacing",
    # https://en.wikipedia.org/wiki/X%C3%A1_L%E1%BB%A3i_Pagoda_raids
    "Xá Lợi Pagoda raids",
    "Flag of Japan",
    "Cerebellum",
    # https://en.wikipedia.org/wiki/L%C5%8D%CA%BBihi_Seamount
    "Lōʻihi Seamount",
    "India",
    "To Kill a Mockingbird",
    "Edward VIII abdication crisis",
    # https://en.wikipedia.org/wiki/W%C5%82adys%C5%82aw_II_Jagie%C5%82%C5%82o
    "Władysław II Jagiełło",
    "Atheism",
    "Liberal Movement (Australia)",
    "Europa (moon)",
    "Philosophy of mind",
    "R.E.M.",
    "Tornado",
    "The Hitchhiker's Guide to the Galaxy (radio series)",
    "Pi",
    "Byzantine navy",
    "Wii",
    "Mass Rapid Transit (Singapore)",
    "History of American football",

    # ARTICLES NEEDING COPYEDIT
    "Gender inequality in China"
]


def check_samples_from_disk():
    for title in sample_featured_articles:
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "r") as text_file:
            wikitext = text_file.read()
            check_english(wikitext, title)
            # generate_stats(plaintext)


def save_sample_articles():
    for title in sample_featured_articles:
        wikitext = fetch_article_wikitext(title)
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "w") as text_file:
            text_file.write(wikitext)


# --- GRAMMAR-MAKING HACK ---


def fetch_parts_of_speech(word):
    # Returns a LIST of parts of speech
    word_categories = fetch_categories(word)
    pos_list = [enwiktionary_cat_to_pos.get(category_name) for category_name in word_categories]
    return [pos for pos in pos_list if pos]


def fetch_categories(word):
    if not word:
        return []
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT title, category_name FROM page_categories WHERE title=%s", (word, ))

    # Account for SQL being case-insensitive
    # result = [cat.decode('utf-8') for (title, cat) in cursor if title.decode('utf-8') == word]
    result = [cat for (title, cat) in cursor if title == word]
    cursor.close()
    return result


def load_grammar_for_word_list(word_list):
    grammar_string = ""

    # ---

    # Load relationships between parts of speech

    for (parent_pos, child_structures) in sorted(phrase_structures.items()):
        alternatives = []
        for child_list in child_structures:
            # Strip attributes for now
            child_list = [child.split("+")[0] for child in child_list]
            alternatives.append(" ".join(child_list))
        grammar_string += "%s -> %s\n" % (parent_pos, " | ".join(alternatives))

    # ---

    # Load limited vocabulary (only for words in this text, to
    # minimize the size of the grammar).

    word_set = set(word_list)

    # Deal with the possibility that some words are only capitalized
    # because they begin a sentence.  No harm here in loading a few
    # lowercase variants we won't actually use later.
    more_words = set()
    for word in word_set:
        if word == word.title():
            more_words.add(word.lower())
        if "-" in word:
            [more_words.add(part) for part in word.split("-")]
            [more_words.add(part.lower()) for part in word.split("-")]
    word_set = word_set.union(more_words)

    word_to_pos = {}
    for word in word_set:
        word_pos_set = set()

        if word in vocab_overrides:
            word_pos_set = vocab_overrides[word]
        else:
            [word_pos_set.add(pos) for pos in fetch_parts_of_speech(word)]

        if word_pos_set:
            word_to_pos[word] = list(word_pos_set)

        for pos in word_pos_set:
            grammar_string += '%s -> "%s"\n' % (pos, word)

    # ---

    # Load closed-class vocabulary explicity set by
    # english_grammar.py.

    # TODO: This is probably unnecessary; Wiktionary almost certainly
    # has these listed. These are currently adding to the grammar, not
    # overriding Wiktionary, so it's unclear if the attributes are
    # going to come through at the other end.  (They're currently
    # unused anyway, but that could change.)

    for (pos, word_list) in closed_lexicon.items():
        pos = pos.split("+")[0]
        for word in word_list:
            grammar_string += '%s -> "%s"\n' % (pos, word)

            pos_list = word_to_pos.get(word, [])
            pos_list.append(pos)
            word_to_pos[word] = pos_list

    return (grammar_string, word_to_pos)


# --- RUNTIME ---

def run_grammar_check():
    if len(sys.argv) > 1 and sys.argv[1] == "--download":
        save_sample_articles()
        exit(0)

    check_samples_from_disk()
    mysql_connection.close()


if __name__ == '__main__':
    run_grammar_check()
