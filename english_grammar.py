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
    "COMMA": [","],
    "SEMCOL": [";"],
    "PERC": ["%"],
    "POSS": ["'s"],
    "CUR": ["$", "€", "£", "¥", "₹", "US$", "A\$", "Can$"],

    "QUOTE": ["✂"],
    # Quotations are not inspected for grammar, but must be retained
    # to keep the surrounding syntax structure intact.

}

# Wiktionary includes a lot of archaic and obscure definitions.  For
# high-frequency words, this can cause a lot of spurious parses.  This
# lmits the part-of-speech possibilities for a given word to only
# those possibilities listed here.
vocab_overrides = {
    "a": ["DET"],
    "plc": ["N"],  # Not found in Wiktionary; part of multi-word proper nouns (company names)
    # "plc": ["N+PROP"],
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

        # Putting ["N", "POSS"] in AJP makes more sense, but that
        # creates an infinite loop that resultes in a stack overflow.
        ["N", "POSS", "N"],  # David's car
        ["DET", "N", "POSS", "N"],  # the owner's money
        ["DET", "AJP", "N", "POSS", "N"],  # the blue puppy's eyes

        # Multi-word proper nouns (not checked for agreement)
        ["N", "N"],
        ["N", "N", "N"],
        ["N", "N", "N", "N"],

        # Lists, Oxford comma required
        ["N", "CON+CO" "N"],
        ["N", "COMMA", "N", "COMMA", "CON+CO", "N"],
        ["N", "COMMA", "N", "COMMA", "N", "COMMA", "CON+CO", "N"],

        ["NUM", "PERC"],
        ["CUR", "NUM"],
        ["CURNUM"],

        ["NUM"],  # works for dates, numbers as numbers
    ],

    "AJP": [
        ["ADJ2"],  # green
        ["ADJ2", "COMMA", "ADJ2"],   # wet, tired
        ["ADJ2", "ADJ2"],            # big brown
        ["ADJ2", "ADJ2", "ADJ2"],     # ugly big brown
        ["ADJ2", "ADJ2"],            # big brown
        ["ADJ2", "CON+CO", "ADJ2"],  # wet and tired

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
        ["V+0"],  # it rains
        ["V+1"],  # he runs
        ["V+2", "NP"],  # she runs Congress
        ["V+3", "NP", "NP"],  # you gave me the ball

        ["V+0", "PP"],   # it rains on the lawn
        ["V+0", "ADV"],  # it rains often
        ["V+1", "PP"],   # Sunlight shines on the grass
        ["V+1", "ADV"],  # Alice runs often
        ["ADV", "V+1", "ADV"],  # he often runs quickly
        ["ADV", "V+1", "PP"],  # he often runs in circles
        ["V+2", "NP", "PP"],  # Don drove the car on the sidewalk
        ["V+2", "NP", "AVP"],  # he ran the race well
        ["AVP", "V+2", "NP", "PP"],  # she quickly tossed the ball over the fence
        ["V+3", "NP", "NP", "PP"],   # you gave me the ball on Tuesday
        ["V+3", "NP", "NP", "ADV"],  # you gave me the ball too fast
        ["V+3", "NP", "NP", "PP", "ADV"],  # Kelly sold him the house on the corner expeditiously

        ["V+SAID", "PP", "QUOTE"],  # Donna said in 2016 "xxx"
        ["V+SAID", "QUOTE"],  # Donna said "xxx"

    ],

    # "0" added to force this to sort to the top, since the grammar
    # definition requires the start state to be the first thing
    # defined.
    "0S": [

        # Simple sentences
        ["NP", "VP", "TERM"],

        # Compound sentences and subordinate clauses
        ["NP", "VP", "CON", "NP", "VP", "TERM"],
        ["NP", "VP", "COMMA", "CON", "NP", "VP", "TERM"],
        ["NP", "VP", "SEMCOL", "NP", "VP", "TERM"],

        # Implied "you"
        ["VP", "TERM"],
    ],

    # TODO: ?
    "AVP": [
        ["ADV"],         # well
        ["ADV", "ADV"],  # very well, too fast
    ],

    # TODO - ? https://en.wikipedia.org/wiki/Complementizer
    # "CP": [
    #    ["C", "S"],
    # ]
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
    "English_particles": "PAR",
    "English_postpositions": "PST",
    "English_prepositions": "PRE",
    "English_pronouns": "PRO",
    "English_verbs": "V",

    # Inflected
    "English_adjective_forms": "ADJ",
    "English_adjective_comparative_forms": "ADJ",
    "English_adjective_superlative_forms": "ADJ",
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
# English_auxiliary_verb_forms
# English_auxiliary_verbs
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
# English_intransitive_verbs
# English_invariant_nouns
# English_irregular_first-person_singular_forms
# English_irregular_past_participles
# English_irregular_plurals
# English_irregular_second-person_singular_forms
# English_irregular_simple_past_forms
# English_irregular_third-person_singular_forms
# English_irregular_verbs
# English_jocular_terms
# English_karmadharaya_compounds
# English_learnedly_borrowed_terms
# English_lemmas
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
# English_neologisms
# English_non-constituents
# English_non-idiomatic_translation_targets
# English_non-lemma_forms
# English_nonce_terms
# English_nonstandard_forms
# English_nonstandard_terms
# English_noun-forming_suffixes
# English_noun-noun_compound_nouns
# English_noun_forms
# English_noun_plural_forms
# English_nouns
# English_nouns_with_common_ending_formations
# English_nouns_with_irregular_plurals
# English_nouns_with_unattested_plurals
# English_nouns_with_unknown_or_uncertain_plurals
# English_numbers
# English_numeral_symbols
# English_numerals
# English_numerical_contractions
# English_oaths
# English_obsolete_forms
# English_obsolete_terms
# English_offensive_terms
# English_officialese_terms
# English_one-letter_words
# English_onomatopoeias
# English_ordinal_numbers
# English_orthographically_borrowed_terms
# English_oxymorons
# English_palindromes
# English_parasynthetic_adjectives
# English_particles
# English_past_participles
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
# English_prepositions
# English_present_participles
# English_pro-forms
# English_pro-sentences
# English_productive_suffixes
# English_pronominal_adverbs
# English_pronouns
# English_pronunciation_spellings
# English_proper_adjectives
# English_proper_names
# English_proper_noun_plural_forms
# English_proper_nouns
# English_proper_nouns_with_unattested_plurals
# English_proper_nouns_with_unknown_or_uncertain_plurals
# English_proverbs
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
# English_verb_forms
# English_verb_forms_using_redundant_wikisyntax
# English_verb_froms
# English_verb_irregular_forms
# English_verb_simple_past_forms
# English_verbal_nouns
# English_verbs
# English_verbs_suffixed_with_-en
# English_verbs_with_base_form_identical_to_past_participle
# English_verbs_with_placeholder_it
# English_verbs_with_weak_preterite_but_strong_past_participle
