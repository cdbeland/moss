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
import wikipedia  # https://wikipedia.readthedocs.io/en/latest/code.html
from english_grammar import (enwiktionary_cat_to_pos,
                             phrase_structures,
                             closed_lexicon,
                             vocab_overrides)

prose_quote_re = re.compile(r'"\S[^"]{0,1000}?\S"|"\S"')
parenthetical_re = re.compile(r'\(\S[^\)]{0,1000}?\S\)|\(\S\)')

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


# Seems to happen with <math>
# TODO: Report as bug to either Mediawiki (check for existing bug) or
# Python Wikipedia module.
# POSSIBLE WORKAROUND: Use wikitext instead of plain text
# ACTUALLY TODO - run through wiki_utils.py
broken_re = re.compile(r"displaystyle|colspan|rowspan|cellspacing|{|}")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Numbers
number_pattern = "(\d+|\d+.\d+|\d+:\d)"
conforming_number_re = re.compile(r"^%s$" % number_pattern)
ordinal_re = re.compile(r"^\d*(1st|2nd|3rd|4th|5th|6th|7th|8th|9th|0th)$")

# https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Currencies_and_monetary_values
currency_pattern = "|".join(closed_lexicon["CUR"])
currency_pattern = currency_pattern.replace("$", "\$")
conforming_currency_re = re.compile("^(%s)%s$" % (currency_pattern, number_pattern))


def check_english(plaintext, title):
    # Output is to stdout with tab-separated fields:
    # * Type of message
    #   S = spelling problem
    #   G = grammar problem
    #   L = length issues
    #   ! = parse failure
    # * Article title
    # * Message
    # * Details

    if broken_re.search(plaintext):
        print("!\tArticle parse broken?\t%s" % title)
        return

    paragraphs = plaintext.split("\n")
    for paragraph in paragraphs:
        words_in_paragraph = nltk.word_tokenize(paragraph)
        if len(words_in_paragraph) > 500:
            print("L\t%s\tOverly long paragraph?\t%s words\t%s" % (title, len(words_in_paragraph), paragraph))

    # Quotations and parentheticals are not inspected for grammar
    plaintext = prose_quote_re.sub("✂", plaintext)
    plaintext = parenthetical_re.sub("", plaintext)

    sentences = nltk.sent_tokenize(plaintext)

    # Parse the short sentences first since they should be
    # easiest.
    sentences.sort(key=lambda s: len(s))

    for sentence in sentences:
        (grammar_string, word_to_pos) = load_grammar_for_text(sentence)

        words = nltk.word_tokenize(sentence)
        if len(words) > 200:
            print("L\t%s\tOverly long sentence?\t%s words\t%s" % (title, len(words), sentence))

        # TODO: Skip this inside <poem>...</poem>
        if not is_sentence_grammatical_beland(words, word_to_pos, title, sentence, grammar_string):
            print("G\t%s\tUngrammatical sentence?\t%s" % (title, sentence))


def is_sentence_grammatical_beland(word_list, word_to_pos, title, sentence, grammar_string):
    if "==" in word_list or "===" in word_list:
        return True

    word_train = []

    first_word = True
    for word in word_list:
        expand_grammar = False
        pos_list = word_to_pos.get(word)
        if pos_list:
            print("Found %s: %s" % (word, pos_list))
        if first_word and not pos_list and word == word.title():
            pos_list = word_to_pos.get(word.lower())
            if pos_list:
                print("Lowercase version found for %s: %s" % (word, pos_list))
                # For CFG library
                word_list[0] = word.lower()
        if not pos_list and word.isalpha() and (word == word.title() or word == word.upper()):
            # Assume all capitalized words and acronyms are proper nouns
            pos_list = ["N"]
            expand_grammar = True
            print("Assuming proper noun for %s" % word)
        if not pos_list and conforming_number_re.match(word):
            pos_list = ["NUM"]
            expand_grammar = True
            print("Assuming cardinal number for %s" % word)
        if not pos_list and ordinal_re.match(word):
            pos_list = ["ORD"]
            expand_grammar = True
            print("Assuming ordinal number for %s" % word)
        if not pos_list and conforming_currency_re.match(word):
            pos_list = ["CURNUM"]
            expand_grammar = True
            print("Assuming ordinal number for %s" % word)
        if not pos_list:
            # print("S\t%s\tSkipping sentence due to unknown word\t%s\t%s" % (title, word, word_list))
            print("S\t%s\tNo POS for word\t%s" % (word, word_list))
            return True

        if expand_grammar:
            print("expanding %s %s" % (word, pos_list))
            word_to_pos[word] = pos_list
            for pos in pos_list:
                grammar_string += '%s -> "%s"\n' % (pos, word)

        word_train.append((word, pos_list))
        first_word = False

    grammar = nltk.CFG.fromstring(grammar_string)

    # parser = nltk.parse.RecursiveDescentParser(grammar)  # Cannot handle X -> X Y (infinite loop)
    # parser.trace(5)
    # parser = nltk.parse.LeftCornerChartParser(grammar)
    parser = nltk.parse.BottomUpLeftCornerChartParser(grammar)

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
            print("DROPPED DUP!")
            continue
        else:
            possible_parses_dedup.append(parse)
            seen.append(serialized)
    parse_dummies = [parse.pretty_print() for parse in possible_parses_dedup]
    if len(parse_dummies) == 0:
        return False
    return True


def is_sentence_grammatical_nltk(word_list):
    # "word_list" instead of sentence avoids re-tokenizing

    tagged = nltk.pos_tag(word_list)
    print(tagged)
    return True


def fetch_article_plaintext(title):
    page = wikipedia.page(title=title)
    return page.content


# TODO: For later command-line use
def check_article(title):
    plaintext = fetch_article_plaintext(title)
    check_english(plaintext, title)


# BOOTSTRAPPING

# A quasi-representative sample of topics (for positive testing) from
# well-written articles listed at:
# https://en.wikipedia.org/wiki/Wikipedia:Featured_articles

sample_featured_articles = [
    # "0test",
    "BAE Systems",
    # "Evolution",
    # "Chicago Board of Trade Building",
    # "ROT13",
    # "Periodic table",
    # "Everything Tastes Better with Bacon",
    # "Renewable energy in Scotland",
    # "Pigeon photography",
    # "University of California, Riverside",
    # "Same-sex marriage in Spain",
    # "Irish phonology",
    # "Sentence spacing",
    # https://en.wikipedia.org/wiki/X%C3%A1_L%E1%BB%A3i_Pagoda_raids
    # "Xá Lợi Pagoda raids",
    # "Flag of Japan",
    # "Cerebellum",
    # https://en.wikipedia.org/wiki/L%C5%8D%CA%BBihi_Seamount
    # "Lōʻihi Seamount",
    # "India",
    # "To Kill a Mockingbird",
    # "Edward VIII abdication crisis",
    # https://en.wikipedia.org/wiki/W%C5%82adys%C5%82aw_II_Jagie%C5%82%C5%82o
    # "Władysław II Jagiełło",
    # "Atheism",
    # "Liberal Movement (Australia)",
    # "Europa (moon)",
    # "Philosophy of mind",
    # "R.E.M.",
    # "Tornado",
    # "The Hitchhiker's Guide to the Galaxy (radio series)",
    # "Pi",
    # "Byzantine navy",
    # "Wii",
    # "Mass Rapid Transit (Singapore)",
    # "History of American football"
]


def check_samples_from_disk():
    for title in sample_featured_articles:
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "r") as text_file:
            plaintext = text_file.read()
            check_english(plaintext, title)
            # generate_stats(plaintext)


def save_sample_articles():
    for title in sample_featured_articles:
        plaintext = fetch_article_plaintext(title)
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "w") as text_file:
            text_file.write(plaintext)


# --- GRAMMAR-MAKING HACK ---


def fetch_categories(word):
    if not word:
        return []
    cursor = mysql_connection.cursor()
    cursor.execute("SELECT title, category_name FROM page_categories WHERE title=%s", (word, ))

    # Account for SQL being case-insensitive
    result = [cat.decode('utf-8') for (title, cat) in cursor if title.decode('utf-8') == word]
    cursor.close()
    return result


def load_grammar_for_text(text):
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

    word_set = set(nltk.word_tokenize(text))

    # Deal with the possibility that some words are only capitalized
    # because they begin a sentence.  No harm here in loading a few
    # lowercase variants we won't actually use later.
    more_words = set()
    for word in word_set:
        if word == word.title():
            more_words.add(word.lower())
    word_set = word_set.union(more_words)

    word_to_pos = {}
    for word in word_set:
        word_pos_set = set()

        if word in vocab_overrides:
            word_pos_set = vocab_overrides[word]
        else:
            word_categories = fetch_categories(word)
            for category_name in word_categories:
                new_pos = enwiktionary_cat_to_pos.get(category_name)
                if new_pos:
                    word_pos_set.add(new_pos)

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

# save_sample_articles()

check_samples_from_disk()
mysql_connection.close()
