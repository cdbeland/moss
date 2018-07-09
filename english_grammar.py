# Following something like:
# https://en.wikipedia.org/wiki/Head-driven_phrase_structure_grammar

# https://en.wikipedia.org/wiki/Natural_Language_Toolkit
# TODO: Consider changing labels to academic-standard?
# Not quite right:
#  https://en.wikipedia.org/wiki/List_of_glossing_abbreviations

# As recognized by Wiktionary
# https://en.wiktionary.org/wiki/Category:English_lemmas
parts_of_speech = {
    "ADJ": "adjective",
    "ADV": "adverb",
    "CON": "conjunction",
    # https://en.wiktionary.org/wiki/Category:English_coordinating_conjunctions
    # Idiomaticish: https://en.wiktionary.org/wiki/Category:English_coordinates
    "DET": "determiner",
    "INJ": "interjection",
    "N": "noun",
    "NUM": "numeral",
    "PST": "postposition",
    "PRE": "preposition",
    "PAR": "particle",
    # TODO: May need to special-case or further classify
    # See also: https://en.wiktionary.org/wiki/Category:English_clitics
    "PRO": "pronoun",
    "V": "verb",

    # Yes, we handle punctuation!
    "TERM": "sentence-terminal punctuation",

    # Weird cases:
    "ABBR": "abbreviation",
    "CNT": "contraction",
    "NEG": "negation",
    "EMAIL": "email address",
    "WEB": "web address",
    "PHONE": "phone number"
}

phrase_categories = {
    "AJP": "adjective phrase",
    "AVP": "adverb phrase",
    "NP": "noun phrase",
    "NUMP": "numerical phrase",
    "PP": "prepositional phrase",
    "VP": "verb phrase",
    "IDIOM": "idiomatic phrase",  # Might not follow normal rules
    # https://en.wiktionary.org/wiki/Category:English_imperatives
    # https://en.wiktionary.org/wiki/Category:English_idioms
}

attributes = {
    "PL": "plural -singular",
    "UNC": "uncountable noun -countable",
    "PROP": "proper noun -common noun",
    "DR": "determiner required",
    "DNR": "determiner not required",
    "1P": "first person",
    "2P": "second person",
    "3P": "third person",
    "CO": "coordinating conjunction",
    "SU": "subordinating conjunction",
    "ART": "article",

    # https://en.wikipedia.org/wiki/Valency_(linguistics)
    "0V": "impersonal verb",                 # it rains
    "1V": "intransitive/monovalent verb",    # he sleeps
    "2V": "transitive/divalent verb",        # he kicks the ball
    "3V": "ditransitive/trivalent verb",     # he gave her a flower
    # "4V": "tritransitive/quadravalent verb",  # Not used in English
    # http://www.slate.com/blogs/quora/2014/04/09/does_english_have_any_tritransitive_verbs.html
}

closed_lexicon = {
    "CON+CO": ["and", "or", "not"],
    "DET+ART": ["a", "an", "the"],
    # https://en.wiktionary.org/wiki/Category:English_articles (ignoring archaic)
    "TERM": [".", "!", "?"],
}

attribute_expansion = {
    "DR": ["N-PROP-PL-UNC"],             # cup
    "NDR": ["N+PL", "N+UNC", "N+PROP"],  # puppies, money, Germany
}

# Agreement rules (TODO)
#
# * Impersonal verbs must have "it" as subject (?)
# * Subject and main verb must agree as to person and number
# * Determiner, and noun must agree as to definiteness
#   https://en.wikipedia.org/wiki/Article_(grammar)#Proper_article
#    some+uncountable, negative article "no", make zero article explicit?
#   https://en.wikipedia.org/wiki/Definiteness
#   (may need to rewrite NP rules below)
# * Some adjectives must agree with noun on countability
#   twelve money vs. twelve dollars

# American English
phrase_structures = {
    "NP": [
        ["N+NDR"],               # puppies, money, Germany
        ["AJP", "N+NDR"],        # brown puppies, dirty money, rich Germany
        ["DET", "N+DR"],         # the cup
        ["DET", "AJP", "N+DR"],  # the empty cup
        # NOT: cup, blue the ice
    ],

    "AJP": [
        ["ADJ"],  # green
        ["ADJ", ",", "ADJ"],   # wet, tired
        ["ADJ", "CON+CO", "ADJ"],  # wet and tired
        # TODO: More adjectives than this are possible, but some
        # configurations are disfavored.  Need to think about this
        # more.
        # Note that order matters in a complicated way:
        # https://en.wikipedia.org/wiki/Adjective#Order
    ],

    "PP": [
        ["PRE", "NP"],
        ["PP", "PP"]
        # TODO: More than two might be too many for an encyclopedia; need
        # to think about this more and maybe put in a limiter
    ],

    "VP": [
        ["V+0"],  # it rains
        ["V+1"],  # he runs
        ["V+2", "NP"],  # she runs Congress
        ["V+3", "NP", "NP"],  # you gave me the ball

        # ["VP", "AVP"] ?
        # TODO: NEED TO FIGURE OUT ADV vs. PP
        ["V+0", "PP"],  # it rains on the lawn
        ["V+1", "PP"],  # he runs on the grass
    ],

    "S": [
        ["NP", "VP", "TERM"],  # Joe runs.
        ["VP", "TERM"],  # (implied you) Run!
    ],

    # TODO: ?
    "AVP": [
        "ADV",
    ],

    # TODO - ? https://en.wikipedia.org/wiki/Complementizer
    # "CP": [
    #    ["C", "S"],
    # ]
}
