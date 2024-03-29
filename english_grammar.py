# Following something like:
# https://en.wikipedia.org/wiki/Head-driven_phrase_structure_grammar

# https://en.wikipedia.org/wiki/Natural_Language_Toolkit
# TODO: Consider changing labels to academic-standard?
# Not quite right:
#  https://en.wikipedia.org/wiki/List_of_glossing_abbreviations
# NLTK set:
# Tag	Meaning	English Examples
# ADJ	adjective	new, good, high, special, big, local
# ADP	adposition	on, of, at, with, by, into, under
# ADV	adverb	really, already, still, early, now
# CONJ	conjunction	and, or, but, if, while, although
# DET	determiner, article	the, a, some, most, every, no, which
# NOUN	noun	year, home, costs, time, Africa
# NUM	numeral	twenty-four, fourth, 1991, 14:24
# PRT	particle	at, on, out, over per, that, up, with
# PRON	pronoun	he, their, her, its, my, I, us
# VERB	verb	is, say, told, given, playing, would
# .	punctuation marks	. , ; !
# X	other	ersatz, esprit, dunno, gr8, univeristy
# http://www.nltk.org/book/ch05.html

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
    "CON+CO": ["and", "or", "not", "&"],
    "DET+ART": ["a", "an", "the"],
    # https://en.wiktionary.org/wiki/Category:English_articles (ignoring archaic)
    "TERM": [".", "!", "?"],
    "COMMA": [","],
    "SEMCOL": [";"],
    "COLON": [":"],
    "PERC": ["%"],
    "CUR": ["$", "€", "£", "¥", "₹", "US$", "A$", "Can$"],
    "POSS": ["'s", "'"],  # "'" is for words that end in "s"

    "QUOTE": ["✂"],
    # Quotations are not inspected for grammar, but must be retained
    # to keep the surrounding syntax structure intact.


    "SAID": ["said", "says", "wrote", "writes", "stated", "states",
             "opined", "opines"],
    "MONTH": ["January", "February", "March", "April", "May", "June",
              "July", "August", "September", "October", "November", "December"],
    "DOM": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12",
            "13", "14", "15", "16", "17", "18", "19", "20", "21", "22",
            "23", "24", "25", "26", "27", "28", "29", "30", "31"]
}

# Wiktionary includes a lot of archaic and obscure definitions.  For
# high-frequency words, this can cause a lot of spurious parses.  This
# lmits the part-of-speech possibilities for a given word to only
# those possibilities listed here.
vocab_overrides = {
    "a": ["DET"],
    "to": ["INF", "PRE"],

    # TODO: Mark these as "+PROP" (can't handle attributes at this
    #  late stage yet)
    # Final nouns for company names:
    "plc": ["N"],  # Wiktionary just marks this as an English intialism

    # Contractions are not allowed outside of direct quotes and proper nouns: https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Abbreviations#Contractions
    # If parsing informal speech, these will need to be added...
    # "'s": ["POSS", "V", "AUXV"],  # Dave's, it's, it's been completed
    # "'t": ["ADV"]     # not, as in "isn't"
    # "'ve": ["AUXV"],  # have, as in "you've"  (not seen as V, like "you've the ball")
    # ...and more: https://en.wikipedia.org/wiki/English_auxiliaries_and_contractions#Contractions
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
        ["NP2"],  # the doctor

        # https://en.wikipedia.org/wiki/Apposition
        ["NP2", "COMMA", "NP2", "COMMA"],  # the doctor, a consummate professional,
        ["NP2", "COMMA", "NP2"],           # the ball, a toy.  (TERM omitted)
    ],
    "NP2": [
        ["N+NDR"],               # puppies, money, Germany
        ["AJP", "N+NDR"],        # brown puppies, dirty money, rich Germany
        ["DET", "N+DR"],         # the cup
        ["DET", "AJP", "N+DR"],  # the empty cup
        # NOT: cup, blue the ice
        # Same as above but with modifiers
        ["N+NDR", "PP"],
        ["AJP", "N+NDR", "PP"],
        ["DET", "N+DR", "PP"],
        ["DET", "AJP", "N+DR", "PP"],

        ["N", "V+PAST", "PP"],                # boards composed of wood
        ["DET", "N", "V+PAST", "PP"],         # the board composed of wood
        ["AJP", "N", "V+PAST", "PP"],         # long boards composed of wood
        ["DET", "AJP", "N", "V+PAST", "PP"],  # the long board composed of wood

        # Putting ["N", "POSS"] in AJP makes more sense, but that
        # creates an infinite loop that resultes in a stack overflow.
        ["N", "POSS", "N"],  # David's car
        ["DET", "N", "POSS", "N"],  # the owner's money
        ["DET", "AJP", "N", "POSS", "N"],  # the blue puppy's eyes

        # Infinitives as post-positional adjectives
        ["DET", "N", "INF", "V", "V"],   # the task to be completed
        ["DET", "AJP", "N", "INF", "V", "V"],   # the ugly task to be completed

        # Multi-word proper nouns (not checked for agreement)
        ["N", "N"],
        ["N", "N", "N"],
        ["N", "N", "N", "N"],
        ["N", "N", "N", "CON+CO", "N"],  # BAE Systems Land & Armaments
        ["N", "N", "N", "N", "N"],

        # Lists, Oxford comma required
        ["N", "CON+CO" "N"],
        ["N", "COMMA", "N", "COMMA", "CON+CO", "N"],
        ["N", "COMMA", "N", "COMMA", "N", "COMMA", "CON+CO", "N"],

        ["NUM", "PERC"],
        ["DET", "NUM", "PERC", "N"],  # A 5% solution
        ["CUR", "NUM"],     # $5 when nltk parses the parts separately

        ["CURNUM"],         # £7
        ["CURNUM", "NUM"],  # £2.3 billion
        ["CURNUM", "N"],         # £7 items
        ["CURNUM", "NUM", "N"],  # £2.3 billion mistakes
        ["DET", "CURNUM", "N"],         # the £7 disc
        ["DET", "CURNUM", "NUM", "N"],  # the £2.3 billion project

        ["NUM"],  # works for dates, numbers as numbers

        ["QUOTE+NP"],

        ["DATE"],
    ],

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Dates,_months_and_years
    "DATE": [
        ["MDY_DATE"],
        ["DMY_DATE"],
        ["MONTH", "YEAR"],
    ],
    "MDY_DATE": [
        ["MONTH", "DOM"],
        ["MONTH", "DOM", "COMMA", "YEAR"],
        ["MONTH", "DOM", "COMMA", "YEAR", "COMMA"],
    ],
    "DMY_DATE": [
        ["DOM", "MONTH"],
        ["DOM", "CON", "DOM", "MONTH"],
        ["DOM", "MONTH", "YEAR"],
        ["DOM", "CON", "DOM", "MONTH", "YEAR"],
    ],
    "YEAR": [
        ["NUM"],
    ],

    # Hacky workaround for the numbers 1-30 only have one category due to override
    "NUM": [
        ["DOM"],
    ],

    "AJP": [
        ["ADJ2"],  # green
        ["ADJ2", "COMMA", "ADJ2"],         # wet, tired
        ["ADJ2", "ADJ2"],                  # big brown
        ["ADJ2", "ADJ2", "ADJ2"],          # ugly big brown
        ["ADJ2", "ADJ2", "ADJ2", "ADJ2"],  # Hawk advanced jet trainer [aircraft]
        ["ADJ2", "ADJ2"],                  # big brown
        ["ADJ2", "CON+CO", "ADJ2"],        # wet and tired

        ["ADJ2", "COMMA", "ADJ2", "COMMA", "CON+CO", "ADJ2"],
        ["ADJ2", "COMMA", "ADJ2", "COMMA", "ADJ2", "COMMA", "CON+CO", "ADJ2"],

        ["ADJ2", "ADJ2", "COMMA", "ADJ2", "COMMA", "CON+CO", "ADJ2"],
        ["ADJ2", "ADJ2", "ADJ2", "COMMA", "ADJ2", "COMMA", "CON+CO", "ADJ2"],  # British multinational defence, security, and aerospace [company]

        # TODO: More adjectives than this are possible, but some
        # configurations are disfavored.  Need to think about this
        # more.
        # Note that order matters in a complicated way:
        # https://en.wikipedia.org/wiki/Adjective#Order
        ["NUM"],          # five
        ["NUM", "ADJ2"],  # two red
        ["ORD"],          # 3rd

        ["ADV", "ADJ"],   # generally red
    ],

    "ADJ2": [
        ["ADJ"],
        ["N"],  # Any noun can work as an adjective, like "security company"
    ],

    "PP": [
        # TODO: More than two might be too many for an encyclopedia; need
        # to think about this more and maybe put in a limiter
        ["PP2"],
        ["PP2", "PP2"]
    ],
    # Using "2" to avoid an infinite loop
    "PP2": [
        ["PRE", "NP"],
    ],

    "VP": [
        ["CORE_V"],            # it rains, he runs
        ["CORE_V", "POST_V"],  # she runs Congress

        ["AVP", "CORE_V"],     # Silently, he hid.  In 2006, they ruled.
        ["AVP", "CORE_V", "POST_V"],     # Quickly, he hid the papers.

        ["SAID", "PP", "QUOTE"],  # Donna said in 2016 "xxx"
        ["SAID", "QUOTE"],  # Donna said "xxx"
        ["SAID", "CON+SUB", "0S"],  # Alice said that Bob is broke
        ["SAID", "0S"],  # Alice said Bob is broke
    ],

    "CORE_V": [
        ["CORE_V2"],

        # Passive voice, which might be disfavored
        ["AUXV", "CORE_V2"],          # was illuminated
        ["AUXV", "AUXV", "CORE_V2"],  # has been deleted
        ["AUXV", "AUXV", "AVP", "CORE_V2"],  # has been widely praised

        ["INF", "CORE_V2"],           # to wonder
        ["INF", "ADV", "CORE_V2"],    # to boldly go  (yes, split infinitives are allowed)
    ],

    "POST_V": [
        ["AVP"],

        # TODO: These should only be used with to-be verbs, I think
        ["AJP"],  # are generally fast

        ["NP"],  # Direct object
        ["NP", "AVP"],

        ["NP", "NP"],  # Direct and indirect objects
        ["NP", "NP", "AVP"],
    ],

    "CORE_V2": [
        ["V"],          # glow
        ["V", "PRE"],    # burn up
    ],

    # TODO: Including valence tracking multiplies out the
    # possibilities too much.  Analyze this as another phase after
    # syntactic parse, possibly to help disambiguate.
    #
    # "VP": [
    #     ["V+0"],  # it rains
    #     ["V+1"],  # he runs
    #     ["V+2", "NP"],  # she runs Congress
    #     ["V+3", "NP", "NP"],  # you gave me the ball
    #
    #     ["V+0", "PP"],   # it rains on the lawn
    #     ["V+0", "ADV"],  # it rains often
    #     ["V+1", "PP"],   # Sunlight shines on the grass
    #     ["V+1", "ADV"],  # Alice runs often
    #     ["ADV", "V+1", "ADV"],  # he often runs quickly
    #     ["ADV", "V+1", "PP"],  # he often runs in circles
    #     ["V+2", "NP", "PP"],  # Don drove the car on the sidewalk
    #     ["V+2", "NP", "AVP"],  # he ran the race well
    #     ["AVP", "V+2", "NP", "PP"],  # she quickly tossed the ball over the fence
    #     ["V+3", "NP", "NP", "PP"],   # you gave me the ball on Tuesday
    #     ["V+3", "NP", "NP", "ADV"],  # you gave me the ball too fast
    #     ["V+3", "NP", "NP", "PP", "ADV"],  # Kelly sold him the house on the corner expeditiously
    #
    #     ["SAID", "PP", "QUOTE"],  # Donna said in 2016 "xxx"
    #     ["SAID", "QUOTE"],  # Donna said "xxx"
    #     ["SAID", "CON+SUB", "0S"],  # Alice said that Bob is broke
    #     ["SAID", "0S"],  # Alice said Bob is broke
    #        "English_auxiliary_verb_forms": "AUXV",
    # ],

    # "0" added to force this to sort to the top, since the grammar
    # definition requires the start state to be the first thing
    # defined.
    "0S": [

        # Simple sentences
        ["NP", "VP", "TERM"],

        # However, he is dead.   Slowly, the ship was raised.
        ["AVP", "COMMA", "NP", "VP", "TERM"],

        ["PP", "NP", "VP", "TERM"],
        # Allows "On 7 March 2005 something happened" without commas,
        # which Beland does not like but which
        # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Commas
        # doesn't say is wrong.

        # Compound sentences and subordinate clauses
        ["NP", "VP", "CON", "NP", "VP", "TERM"],
        ["NP", "VP", "COMMA", "CON", "NP", "VP", "TERM"],
        ["NP", "VP", "SEMCOL", "NP", "VP", "TERM"],

        # Implied "you"
        ["VP", "TERM"],

        # Introducing a list, e.g. "The districts of the province are:"
        ["NP", "CORE_V", "COLON"],
    ],

    "AVP": [
        ["ADV"],         # well
        ["ADV", "ADV"],  # very well, too fast

        ["PP"],
        ["ADV", "PP"],   # recklessly on the sidewalk
        ["PP", "ADV"],   # on the sidewalk recklessly
    ],
}


enwiktionary_cat_to_pos = {
    # Canonical form (lemmas in the dictionary)
    "English_adjectives": "ADJ",
    "English_adverbs": "ADV",
    "English_conjunctions": "CON",
    "English_determiners": "DET",
    "English_interjections": "INJ",
    "English_nouns": "N",
    "English_proper_nouns": "N",
    "English_numerals": "NUM",
    # "English_particles": "PAR",  # Not a useful category, syntactically speaking
    "English_postpositions": "PST",
    "English_prepositions": "PRE",
    "English_pronouns": "PRO",
    "English_verbs": "V",
    "English_irregular_verbs": "V",
    "English_intransitive_verbs": "V",
    "English_auxiliary_verbs": "AUXV",

    # Inflected
    "English_adjectives": "ADJ",
    "English_adjective_forms": "ADJ",
    "English_comparative_adjectives": "ADJ",
    "English_superlative_adjectives": "ADJ",
    "English_adverb_forms": "ADV",
    "English_adverb_comparative_forms": "ADJ",
    "English_adverb_superlative_forms": "ADJ",
    "English_noun_forms": "N",
    "English_noun_plural_forms": "N",
    "English_irregular_plurals": "N",
    'English_irregular_plurals_ending_in_"-e"': "N",
    'English_invariant_nouns': "N",
    'English_irregular_plurals_ending_in_"-ae"': "N",
    'English_irregular_plurals_ending_in_"-ces"': "N",
    'English_irregular_plurals_ending_in_"-des"': "N",
    'English_irregular_plurals_ending_in_"-es"': "N",
    'English_irregular_plurals_ending_in_"-ges"': "N",
    'English_irregular_plurals_ending_in_"-i"': "N",
    'English_irregular_plurals_ending_in_"-ves"': "N",
    'English_plurals_ending_in_"-a"': "N",
    'English_plurals_ending_in_"-en"': "N",
    'English_plurals_ending_in_"-es"': "N",
    'English_plurals_ending_in_"-ies"': "N",
    "English_proper_noun_forms": "N",
    "English_proper_noun_plural_forms": "N",
    "English_verb_forms": "V",
    "English_verb_irregular_forms": "V",
    "English_verb_simple_past_forms": "V",
    "English_past_participles": "V",
    "English_present_participles": "V",
    "English_auxiliary_verb_forms": "AUXV",
    "English_irregular_first-person_singular_forms": "V",
    "English_irregular_past_participles": "V",
    "English_irregular_second-person_singular_forms": "V",
    "English_irregular_simple_past_forms": "V",
    "English_irregular_third-person_singular_forms": "V",
    "English_gerunds": "V",
    "English_verb_simple_past_forms": "V",
    "English_verb_singular_forms": "V",
    "English_first-person_singular_forms": "V",
    "English_second-person_singular_forms": "V",
    "English_second-person_singular_past_tense_forms": "V",
    "English_third-person_singular_forms": "V",
}

# PARTIALLY DIGESTED DUMP OF CATEGORIES
#
# English_English
# English_Latin
# English_Pig_Latin_terms
# English_abbreviations
# English_abstract_nouns
# English_acronyms
# English_act-related_adverbs
# English_adjective-forming_suffixes
# English_adjective-noun_compound_nouns
# English_adjective_comparative_forms
# English_adjective_forms
# English_adjective_superlative_forms
# English_adjectives
# English_adjectives_commonly_used_as_postmodifiers
# English_adjectives_ending_in_-en
# English_adjectives_ending_in_-en_formed_from_a_noun
# English_adjectives_suffixed_with_-en
# English_adverb-adjective_phrases
# English_adverb-forming_suffixes
# English_adverb-preposition_compound_prepositions
# English_adverb_comparative_forms
# English_adverb_superlative_forms
# English_adverbs
# English_affixes
# English_agent_nouns
# English_alliterative_compounds
# English_allusions
# English_animal_commands
# English_aphetic_forms
# English_apocopic_forms
# English_archaic_forms
# English_archaic_terms
# English_archaic_third-person_singular_forms
# English_articles
# English_aspect_adverbs
# English_autological_terms
# English_back-formations
# English_bahuvrihi_compounds
# English_basic_words
# English_blends
# English_borrowed_terms
# English_braille_logograms
# English_buzzwords
# English_calques
# English_cant
# English_cardinal_numbers
# English_case_citation_abbreviations
# English_catachreses
# English_catchphrases
# English_catenative_verbs
# English_causative_verbs
# English_childish_terms
# English_circumfixes
# English_class_1_strong_verbs
# English_class_2_strong_verbs
# English_class_3_strong_verbs
# English_class_4_strong_verbs
# English_class_5_strong_verbs
# English_class_6_strong_verbs
# English_class_7_strong_verbs
# English_clausal_phrases
# English_clippings
# English_clitics
# English_cognate_expressions
# English_collateral_adjectives
# English_collective_nouns
# English_colloquialisms
# English_combining_forms
# English_comparative-only_adjectives
# English_compound_adjectives
# English_compound_determinatives
# English_compound_words
# English_conjunctions
# English_conjunctive_adverbs
# English_contractions
# English_contranyms
# English_control_verbs
# English_coordinated_pairs
# English_coordinated_triples
# English_coordinates
# English_coordinating_conjunctions
# English_copulative_verbs
# English_countable_nouns
# English_countable_proper_nouns
# English_dated_forms
# English_dated_terms
# English_defective_verbs
# English_degree_adverbs
# English_deixes
# English_demonstrative_adverbs
# English_derogatory_terms
# English_determiners
# English_dialectal_terms
# English_diminutive_nouns
# English_diminutive_proper_nouns
# English_diminutives_of_female_given_names
# English_diminutives_of_male_given_names
# English_discourse_markers
# English_dismissals
# English_disputed_terms
# English_ditransitive_verbs
# English_domain_adverbs
# English_double_contractions
# English_doublets
# English_duration_adverbs
# English_dvandva_compounds
# English_ellipses
# English_elongated_forms
# English_eponyms
# English_ergative_verbs
# English_ethnic_slurs
# English_euphemisms
# English_evaluative_adverbs
# English_familiar_terms
# English_female_given_names
# English_filled_pauses
# English_first-person_singular_forms
# English_first_person_pronouns
# English_focus_adverbs
# English_formal_terms
# English_four-letter_abbreviations
# English_fractional_numbers
# English_frequency_adverbs
# English_frequentative_verbs
# English_gender-neutral_terms
# English_genericized_trademarks
# English_gerunds
# English_given_names
# English_hapax_legomena
# English_haplological_forms
# English_hedges
# English_heteronyms
# English_historical_terms
# English_homographic_denominal_verbs
# English_homophonic_translations
# English_honorific_forms
# English_hyperboles
# English_hypercorrections
# English_hyperforeign_terms
# English_idiomatic_construction_prototypes
# English_idioms
# English_imperative_sentences
# English_imperatives
# English_impersonal_verbs
# English_indefinite_pronouns
# English_infixes
# English_inflectional_suffixes
# English_informal_demonyms
# English_informal_forms
# English_informal_terms
# English_initialisms
# English_intensifiers
# English_interfixes
# English_interjections
# English_interjs
# English_interrogative_adverbs
# English_interrogative_pro-forms
# English_interrogative_pronouns
# English_jocular_terms
# English_karmadharaya_compounds
# English_letters
# English_light_verb_constructions
# English_literary_terms
# English_location_adverbs
# English_locatives
# English_male_given_names
# English_manner_adverbs
# English_matched_pairs
# English_medical_slang
# English_merisms
# English_metonyms
# English_military_slang
# English_minced_oaths
# English_misconstructions
# English_misspellings
# English_mnemonics
# English_modal_adverbs
# English_modal_verbs
# English_negative_polarity_items
# English_non-constituents
# English_non-idiomatic_translation_targets
# English_non-lemma_forms
# English_nonce_terms
# English_nonstandard_forms
# English_nonstandard_terms
# English_noun-forming_suffixes
# English_noun-noun_compound_nouns
# English_nouns_with_common_ending_formations
# English_nouns_with_irregular_plurals
# English_nouns_with_unattested_plurals
# English_nouns_with_unknown_or_uncertain_plurals
# English_numbers
# English_numeral_symbols
# English_numerical_contractions
# English_oaths
# English_obsolete_forms
# English_obsolete_terms
# English_one-letter_words
# English_onomatopoeias
# English_ordinal_numbers
# English_orthographically_borrowed_terms
# English_parasynthetic_adjectives
# English_pejoratives
# English_personal_pronouns
# English_phrasal_prepositions
# English_phrasal_verbs
# English_phrasal_verbs_with_particle_(aback)
# English_phrasal_verbs_with_particle_(about)
# English_phrasal_verbs_with_particle_(above)
# English_phrasal_verbs_with_particle_(across)
# English_phrasal_verbs_with_particle_(adrift)
# English_phrasal_verbs_with_particle_(after)
# English_phrasal_verbs_with_particle_(against)
# English_phrasal_verbs_with_particle_(aground)
# English_phrasal_verbs_with_particle_(ahead)
# English_phrasal_verbs_with_particle_(aloft)
# English_phrasal_verbs_with_particle_(along)
# English_phrasal_verbs_with_particle_(apart)
# English_phrasal_verbs_with_particle_(around)
# English_phrasal_verbs_with_particle_(as)
# English_phrasal_verbs_with_particle_(aside)
# English_phrasal_verbs_with_particle_(astray)
# English_phrasal_verbs_with_particle_(asunder)
# English_phrasal_verbs_with_particle_(at)
# English_phrasal_verbs_with_particle_(away)
# English_phrasal_verbs_with_particle_(back)
# English_phrasal_verbs_with_particle_(before)
# English_phrasal_verbs_with_particle_(behind)
# English_phrasal_verbs_with_particle_(below)
# English_phrasal_verbs_with_particle_(between)
# English_phrasal_verbs_with_particle_(beyond)
# English_phrasal_verbs_with_particle_(by)
# English_phrasal_verbs_with_particle_(down)
# English_phrasal_verbs_with_particle_(even)
# English_phrasal_verbs_with_particle_(for)
# English_phrasal_verbs_with_particle_(forth)
# English_phrasal_verbs_with_particle_(forward)
# English_phrasal_verbs_with_particle_(from)
# English_phrasal_verbs_with_particle_(in)
# English_phrasal_verbs_with_particle_(into)
# English_phrasal_verbs_with_particle_(low)
# English_phrasal_verbs_with_particle_(of)
# English_phrasal_verbs_with_particle_(off)
# English_phrasal_verbs_with_particle_(on)
# English_phrasal_verbs_with_particle_(onto)
# English_phrasal_verbs_with_particle_(out)
# English_phrasal_verbs_with_particle_(over)
# English_phrasal_verbs_with_particle_(past)
# English_phrasal_verbs_with_particle_(round)
# English_phrasal_verbs_with_particle_(through)
# English_phrasal_verbs_with_particle_(to)
# English_phrasal_verbs_with_particle_(together)
# English_phrasal_verbs_with_particle_(towards)
# English_phrasal_verbs_with_particle_(under)
# English_phrasal_verbs_with_particle_(up)
# English_phrasal_verbs_with_particle_(upon)
# English_phrasal_verbs_with_particle_(with)
# English_phrasal_verbs_with_particle_(without)
# English_phrasebook
# English_phrasebook/Communication
# English_phrasebook/Emergencies
# English_phrasebook/Ethnicity
# English_phrasebook/Family
# English_phrasebook/Food_and_drink
# English_phrasebook/Health
# English_phrasebook/Love
# English_phrasebook/Religion
# English_phrasebook/Sex
# English_phrasebook/Travel
# English_phrases
# English_placeholder_terms
# English_pleonastic_compound_adjectives
# English_pleonastic_compound_nouns
# English_plural_pronouns
# English_pluralia_tantum
# English_plurals
# English_plurals_ending_in_"-a"
# English_plurals_ending_in_"-en"
# English_plurals_ending_in_"-es"
# English_plurals_ending_in_"-ies"
# English_poetic_terms
# English_polite_terms
# English_possessive_determiners
# English_possessive_pronouns
# English_post-nominal_letters
# English_postpositions
# English_predicates
# English_prefixes
# English_prepositional_phrases
# English_pro-forms
# English_pro-sentences
# English_productive_suffixes
# English_pronominal_adverbs
# English_pronunciation_spellings
# English_proper_adjectives
# English_proper_names
# English_proper_noun_plural_forms
# English_proper_nouns
# English_proper_nouns_with_unattested_plurals
# English_proper_nouns_with_unknown_or_uncertain_plurals
# English_pseudo-acronyms
# English_punctuation_marks
# English_quantizers
# English_questions
# English_radio_slang
# English_rare_forms
# English_rare_terms
# English_rebracketings
# English_reciprocal_pronouns
# English_reciprocal_verbs
# English_reduplicated_coordinated_pairs
# English_reduplicated_coordinated_quadruples
# English_reduplicated_coordinated_triples
# English_reduplications
# English_reflexive_pronouns
# English_reflexive_verbs
# English_refractory_feminine_rhymes
# English_relative_pronouns
# English_religious_slurs
# English_reporting_verbs
# English_responses
# English_retronyms
# English_rhetorical_questions
# English_rhyming_compounds
# English_rhyming_slang
# English_sarcastic_terms
# English_school_slang
# English_second-person_singular_forms
# English_second-person_singular_past_tense_forms
# English_second_person_pronouns
# English_senses_used_only_in_hyphenated_compounds
# English_sentence_adverbs
# English_sentences
# English_sequence_adverbs
# English_set_phrases
# English_short_forms
# English_similes
# English_singularia_tantum
# English_slang
# English_speech-act_adverbs
# English_spoonerisms
# English_stative_verbs
# English_student_slang
# English_subordinate_clauses
# English_subordinating_conjunctions
# English_suffix_forming_adjectives_suffixed_with_-al
# English_suffix_forms
# English_suffixes
# English_suffixes_suffixed_with_-ic
# English_suffixes_that_form_adjectives_from_nouns
# English_suffixes_that_form_nouns_from_adjectives
# English_suppletive_adjectives
# English_suppletive_adverbs
# English_suppletive_nouns
# English_suppletive_verbs
# English_surnames
# English_swear_words
# English_syllabic_abbreviations
# English_symbols
# English_synchronized_entries
# English_syncopic_forms
# English_temporal_location_adverbs
# English_third-person_singular_forms
# English_third_person_pronouns
# English_three-letter_abbreviations
# English_three-letter_words
# English_time_adverbs
# English_trademarks
# English_transitive_verbs
# English_translation_hubs
# English_triple_contractions
# English_twice-borrowed_terms
# English_two-letter_words
# English_uncommon_forms
# English_uncomparable_adjectives
# English_uncomparable_adverbs
# English_uncountable_nouns
# English_unisex_given_names
# English_univerbations
# English_unproductive_prefixes
# English_unproductive_suffixes
# English_verb-forming_suffixes
# English_verbal_nouns
# English_verbs_suffixed_with_-en
# English_verbs_with_base_form_identical_to_past_participle
# English_verbs_with_placeholder_it
# English_verbs_with_weak_preterite_but_strong_past_participle

"""
BOOK: https://www.amazon.com/Cambridge-Grammar-English-Language/dp/0521431468

** TRY GENERATING ALL VALID POS SEQUENCES
* Instead of parsing every sentence, just POS tag and see if ANY
  possible POS sequence for the sentence is grammatically valid


** TRY PARSING EVERYTHING WITH ONLY THE MOST COMMON POS FOR THAT WORD!
-> for speed on correct sentences!
https://en.wikipedia.org/wiki/Part-of-speech_tagging#Use_of_hidden_Markov_models
-> says this is 90%+ accurate
-> Can fall back to an all-possibilities parse

Systems:
* What moss uses from Wiktionary
* http://universaldependencies.org/u/feat/index.html
  separate from features: http://universaldependencies.org/u/feat/index.html
  (used by spaCy's dependency parser)
* https://www.ling.upenn.edu/courses/Fall_2003/ling001/penn_treebank_pos.html
* https://en.wikipedia.org/wiki/Brown_Corpus#Part-of-speech_tags_used
* More: https://en.wikipedia.org/wiki/Template:Corpus_linguistics

https://en.wikipedia.org/wiki/Part-of-speech_tagging#Tag_sets
-> 50 to 150 POSes are typical, over 1000 possible

"""
