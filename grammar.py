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
# * Produce reports for:
#   * Words to add to Wiktionary
#   * Wikipedia articles to fix
#     * Check e.g. that misspelled words are still present in live article
#   * Wikipedia common typos to fix
# * Report on theory of English grammar

# A quasi-representative sample of topics (for postive testing) from
# well-written articles listed at:
# https://en.wikipedia.org/wiki/Wikipedia:Featured_articles


import nltk
import wikipedia
# https://wikipedia.readthedocs.io/en/latest/code.html
from spell import is_word_spelled_correctly


def check_english(plain_text):
    print("SPP\tWPP\tmax WPS")
    paragraphs = plain_text.split("\n")
    for paragraph in paragraphs:
        words_in_paragraph = nltk.word_tokenize(paragraph)
        if len(words_in_paragraph) == 0:
            continue
        if len(words_in_paragraph) > 500:
            print("Overly long paragraph?\t%s" % paragraph)

        sentences = nltk.sent_tokenize(paragraph)

        max_words_per_sentence = 0
        for sentence in sentences:
            words = nltk.word_tokenize(sentence)
            if len(words) > max_words_per_sentence:
                max_words_per_sentence = len(words)

            if len(words) > 200:
                print("Overly long sentence?\t%s" % sentence)

            unknown_word = False
            for word in words:
                if not is_word_spelled_correctly(word):
                    # Suppression of foreign words with {{lang}} and
                    # {{not a typo}} doesn't work with the plain text,
                    # only with wikitext.  So just use this as a quick
                    # filter to skip sentences with words we can't
                    # identify or junk that isn't words.
                    print("Skipping sentence due to unknown word\t%s\t%s" % (word, sentence))
                    unknown_word = True
            if unknown_word:
                continue
            if not is_sentence_grammatical(sentence):
                print("Ungrammatical sentence?\t%s" % sentence)

        print("%s\t%s\t%s" % (len(sentences), len(words_in_paragraph), max_words_per_sentence))


def is_sentence_grammatical(sentence):
    # TODO!
    return True


def fetch_article_plaintext(title):
    page = wikipedia.page(title=title)
    return page.content


def check_article(title):
    plaintext = fetch_article_plaintext(title)
    check_english(plaintext)


# BOOTSTRAPPING

sample_featured_articles = [
    "Europa (moon)",
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
    "History of American football"
]


def check_samples_from_disk():
    for title in sample_featured_articles:
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "r") as text_file:
            plaintext = text_file.read()
            print("\n=%s=" % title)
            check_english(plaintext)


check_samples_from_disk()


def save_sample_articles():
    for title in sample_featured_articles:
        plaintext = fetch_article_plaintext(title)
        title_safe = title.replace(" ", "_")
        with open("samples/%s" % title_safe, "w") as text_file:
            text_file.write(plaintext)

# save_sample_articles()
