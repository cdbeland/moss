# Probably a typo:
#
# H = HTML/XML/SGML tag
# HB = Known bad HTML tag, like <font>
# HL = Bad HTML-like linking, like <http://...>
# T1, T2, etc. = Typo likely in regular word; number gives edit
#                distance to nearest common dictionary word
# TE = Typo likely English based on language recognition
# TF = Typo likely Foreign (non-English) based on language recognition
#      (followed by "+" then ISO 639 language code and possible ISO
#      15924 script code)
# TS = Typo likely in regular word; probably two words that need to be
#      split by space or dash
# T/ = Possible violation of [[MOS:SLASH]]
# BW = Bad word
# BC = Bad character
# Z = Decimal fraction missing leading zero (includes calibers and
#     batting averages that need a link in the article)
# CF = Chemical formula (if not using subscripts)
#
# Probably OK:
#
# CN = Chemical name
# CH = Chess notation
# D = DNA sequence
# P = Pattern of some kind (rhyme scheme, reduplication)
# L = Probable Romanization (transLiteration)
# ME = Probable coMpound, English in English Wiktionary
# U = URL or computer file name
# A = mAth
# N = Numbers or punctuation

from collections import defaultdict
import datetime
import fileinput
import gcld3
from multiprocessing import Pool
from nltk.metrics import distance
import os
import re
import sys
import unicodedata

os.environ["NO_LOAD"] = "1"

try:
    from sectionalizer import get_word
    from spell import bad_characters
    from spell import bad_words
    from wikitext_util import html_tag_re
except ImportError:
    from .sectionalizer import get_word
    from .spell import bad_characters
    from .spell import bad_words
    from .wikitext_util import html_tag_re

az_re = re.compile(r"^[a-z']+$", flags=re.I)
az_plus_re = re.compile(r"^[a-z|\d|\-|\.']+$", flags=re.I)
az_dot_re = re.compile(r"^[a-z]+(\-[a-z]+)?\.[a-z]+(\-[a-z]+)?$", flags=re.I)
ag_re = re.compile(r"^[a-g]+$")
mz_re = re.compile(r"[m-z]")
dna_re = re.compile(r"^[acgt]+$")
missing_leading_zero_re = re.compile(r"[ ^]\.\d")

known_html_bad = {"<tt>", "<li>", "<ol>", "<ul>", "<table>", "<th>",
                  "<tr>", "<td>", "<i>", "<em>", "<dd>", "<dt>",
                  "<dl>", "<cite>", "<p>", "<strong>", "<b>", "<hr>",
                  "<hr/>", "<font>", "</br>", "<center>", "<strike>",
                  "<ins>", "<q>", "<wbr>", "<ruby>", "<rt>",
                  "<rp>", "<var>"}
known_bad_link = {"<http>", "<https>", "<http/>", "<https/>", "<www>"}
not_html = {"<a>", "<name>", "<r>", "<h>"}
# <a> is not turned into a link by Mediawiki, so it's almost always
# intentional like linguistics markup.

# -- INITIALIZATION HELPERS AND GLOBAL VARIABLES --

# Edit distance 4 and greater gives a negligible true positive rate
# Though even 2 and 3 are more non-typos than typos, especially if
# using a full dictionary.  Need to use other methods to classify
# those.
MAX_EDIT_DISTANCE = 1


# From http://norvig.com/spell-correct.html
# All edits that are one edit away from "word".
def edits1(word):
    letters = "abcdefghijklmnopqrstuvwxyz"
    splits = [(word[:i], word[i:]) for i in range(len(word) + 1)]
    deletes = [left + right[1:] for left, right in splits if right]
    transposes = [left + right[1] + right[0] + right[2:] for left, right in splits if len(right) > 1]
    replaces = [left + center + right[1:] for left, right in splits if right for center in letters]
    inserts = [left + center + right for left, right in splits for center in letters]
    return set(deletes + transposes + replaces + inserts)


"""
def check_dictionary(word_list, edit_distance_target, this_edit_distance=1, english_words):
    if not english_words:
        print("MISSING english_words in check_dictionary()", file=sys.stderr)
        exit(1)

    edited_string_sets = [edits1(word) for word in word_list]
    edited_strings = set()
    edited_strings.update(*edited_string_sets)
    found_strings = [s for s in edited_strings if s in english_words]
    if found_strings:
        return (this_edit_distance, found_strings)
    if this_edit_distance == edit_distance_target:
        return None
    return check_dictionary(edited_strings, edit_distance_target, this_edit_distance + 1, english_words)
"""


# Based on code from http://norvig.com/spell-correct.html
def make_edits_lowfi(lowfi_strings, edit_distance_target, this_edit_distance=1, seen=None):
    # Takes a "lowfi" string and produces a dictionary where the keys
    # are the edit distance and the values are sets of lowfi strings.

    # Edited strings are produced with a low-fi matching
    # representation. Instead of ordered strings, words are stored as
    # a string of letters in alphabetical order (rather than the order
    # present in the word), and the number of occurrances of each
    # letter doesn't matter (each letter present is listed only
    # once). "*" means "any letter". This means transposes are
    # ignored; actual edit distance between two words must be
    # calculated after generating match candidates. But it is
    # guaranteed a given candidate may have a lower (closer) reported
    # edit distance than actual, but never higher (more distant).
    #
    # Matches at higher distances are suppressed to save space, since
    # it's assumed lower distances will be searched first.

    deletes = []
    replaces = []
    inserts = []

    if not seen:
        seen = set(lowfi_strings)
    else:
        seen.update(lowfi_strings)

    for lfs in lowfi_strings:
        splits = [(lfs[:i], lfs[i:]) for i in range(len(lfs) + 1)]
        deletes += [left + right[1:] for left, right in splits if right]

        if lfs.startswith("*"):
            # No need to do inserts; this would just add a second "*"
            # which is invisible in the lowfi representation

            # No need to do replaces; this would duplicate a delete
            # that has already been calculated.
            pass
        else:
            inserts.append("*" + lfs)
            replaces += ["*" + left + right[1:] for left, right in splits if right]

    edited_strings_lowfi = set(deletes + replaces + inserts)  # De-dup
    edited_strings_lowfi -= seen

    if edit_distance_target == this_edit_distance:
        return {this_edit_distance: edited_strings_lowfi}
    else:
        results = make_edits_lowfi(edited_strings_lowfi, edit_distance_target, this_edit_distance + 1, seen=seen)
        results[this_edit_distance] = edited_strings_lowfi
        return results


def make_lowfi_string(string_in):
    # Low-fi by ignoring case, order, and number of instances of the
    # same letter
    return "".join(sorted(set(string_in.lower())))


def make_suggestion_helper(word):
    sets_for_word = make_edits_lowfi([make_lowfi_string(word)], MAX_EDIT_DISTANCE)
    return (word, sets_for_word)


def make_suggestion_dict(input_list):

    # Takes about 4.5 min in parallel, 10 min serial at MAX_EDIT_DISTANCE 3
    suggestion_dict = dict()
    for d in range(1, MAX_EDIT_DISTANCE + 1):
        suggestion_dict[d] = defaultdict(set)

    with Pool(8) as pool:
        for (word, sets_for_word) in pool.imap(make_suggestion_helper, input_list, 100000):
            for (ed, sets_for_word_this_ed) in sets_for_word.items():
                for set_for_word_this_ed in sets_for_word_this_ed:
                    suggestion_dict[ed][set_for_word_this_ed].add(word)
        pool.close()
        pool.join()

    # Keys are length, values are low-fi match sets
    return suggestion_dict


# -- Chemistry and math and chess ---

chem_re = re.compile(
    r"(\d+\-|(D\-|\-)?\d+,\d\-?|N\d+,N\d+\-?|,\d+|"
    r"mono|di|bi|tri|tetr|pent|hex|hept|oct|nona|deca|"
    r"hydrogen|hydroxy|"
    r"methyl|phenyl|acetate|ene|ine|ane|ide|hydro|nyl|ate$|ium$|acetyl|"
    r"gluco|aminyl|galacto|pyro|benz|brom|amino|fluor|glyc|cholester|ase$|"
    r"chlor|oxy|nitr|silic|phosph|nickel|copper|iron|carb|sulf|alumin|arsen|magnesium|mercury|lead|calcium|"
    r"propyl|itol|ethyl|oglio|stearyl|alkyl|ethan|amine|ether|keton|oxo|pyri|ine$|"
    r"cyclo|poly|iso|^Bis|methan|ase|delta\d+|late$|meth|ate$|dione|butan)+",
    flags=re.I)

element_symbols = [
    "H", "He", "Li", "Be", "B", "C", "N", "O", "F", "Ne", "Na", "Mg", "Al", "Si", "P", "S",
    "Cl", "Ar", "K", "Ca", "Sc", "Ti", "V", "Cr", "Mn", "Fe", "Co", "Ni", "Cu", "Zn", "Ga",
    "Ge", "As", "Se", "Br", "Kr", "Rb", "Sr", "Y", "Zr", "Nb", "Mo", "Tc", "Ru", "Rh", "Pd",
    "Ag", "Cd", "In", "Sn", "Sb", "Te", "I", "Xe", "Cs", "Ba", "La", "Ce", "Pr", "Nd", "Pm",
    "Sm", "Eu", "Gd", "Tb", "Dy", "Ho", "Er", "Tm", "Yb", "Lu", "Hf", "Ta", "W", "Re", "Os",
    "Ir", "Pt", "Au", "Hg", "Tl", "Pb", "Bi", "Po", "At", "Rn", "Fr", "Ra", "Ac", "Th", "Pa",
    "U", "Np", "Pu", "Am", "Cm", "Bk", "Cf", "Es", "Fm", "Md", "No", "Lr", "Rf", "Db", "Sg",
    "Bh", "Hs", "Mt", "Ds", "Rg", "Cn", "Nh", "Fl", "Mc", "Lv", "Ts", "Og",
    "R"  # Not an element; for [[substiuent]]s ("R groups")
]
upper_only_symbols = "".join([e for e in element_symbols if len(e) == 1])

chem_roman_numerals = ["II", "III", "IV", "VI", "VII", "VIII", "IX"]

element_alternation = "(" + "|".join(element_symbols) + ")"
roman_alternation = "(" + "|".join(chem_roman_numerals) + ")"
num_pat = "([2-9]|[1-9][0-9])?"
elem_plus_num = f"({element_alternation}{num_pat})"


chem_formula_re = re.compile(
    rf"^{elem_plus_num}+" + "(" +
    r"$|" +                                # NaCl, O2, H2O (numbers violate [[MOS:SUB]])
    rf"\({elem_plus_num}+\)$|" +           # Ca(OH)
    rf"([·∙][0-9]*{elem_plus_num}+)+$|" +  # MgCl2·6H2O
    rf"\({roman_alternation}\)$" +         # Mn(II)
    ")")

chem_exclude_re = re.compile(r"^("

                             # Implausible chemical, probable model number
                             + rf"[{upper_only_symbols}]+[1-9][0-9]|"

                             # Probably an acronym, possibly pluralized
                             + r"[" + upper_only_symbols + r"]{3,}s?|"

                             # Catalog numbers, acryonyms, proteins, DNA markers, etc.
                             + r"[" + upper_only_symbols + r"]{3,}[0-9]+|"

                             + r")$|"

                             # Unusually large numbers
                             + r"[^CHNO][4-9][0-9]"
                             )

math_re = re.compile(r"^([A-Za-z]{1,2}\([A-Za-z]{1,2}\)|log\([a-z0-9]\)|[A-Za-zΑ-Ωα-ω0-9]{2,3})$")
greek_letter_present_re = re.compile(r"[Α-Ωα-ω]")

chess_re = re.compile(r"^[KQRBNP][a-h][1-8]$")


def is_math(word):
    if math_re.search(word):
        return True
    if greek_letter_present_re.search(word):
        if "-" in word:
            return True
        if "/" in word:
            return True
    return False


# [[Algebraic notation (chess)]]
def is_chess_notation(word):
    if chess_re.match(word):
        return True
    return False


# Note: This may malfunction slightly if there are commas inside the
# chemical name.
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_inorganic_chemistry
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_organic_chemistry
# https://en.wikipedia.org/wiki/Chemical_nomenclature
def is_chemical_name(word):
    small_word = None
    small_word_last = word
    while True:
        small_word = chem_re.sub("", small_word_last)
        if small_word == small_word_last:
            break
        small_word_last = small_word
    if len(word) > 14:
        if len(small_word) < len(word) * .50:
            return True
    if len(small_word) < len(word) * .25:
        return True
    if word.lower() in ["cis,cis", "trans,cis", "alpha,beta", "trans,trans", "alpha,alpha", "gamma,delta"]:
        return True
    if re.match(r"\d(alpha|beta)", word):
        return True
    if ",NAD" in word or "methyl" in word:
        return True
    if "phenoxy)" in word or "propyl)" in word or "phenyl)" in word or "oxyimino)" in word or "ethyl)" in word:
        return True
    if "dinyl)" in word or "(propylene" in word or "bis(" in word:
        return True


# Overlaps with is_chess_notation()
def is_chemical_formula(word):
    if chem_formula_re.match(word):
        if chem_exclude_re.match(word):
            return False
        return True
    return False


# --


def is_url_or_filename(word):
    if "/" in word and "." in word:
        return True
    if word.endswith(".pdf"):
        return True
    if word.endswith(".html"):
        return True
    if word.startswith("www."):
        return True
    if word.endswith(".org"):
        return True
    if word.endswith(".net"):
        return True
    if word.endswith(".int"):
        return True
    if word.endswith(".edu"):
        return True
    if word.endswith(".gov"):
        return True
    if word.endswith(".mil"):
        return True
    if word.endswith(".arpa"):
        return True
    if word.endswith(".co.uk"):
        return True
    if word.endswith(".de"):
        return True
    if word.endswith(".jp"):
        return True
    if word.endswith(".ru"):
        return True
    if word.endswith(".txt"):
        return True
    if word.endswith(".jar"):
        return True


def letters_introduced_alphabetically(word):
    # One of the distinctive characteristics of a rhyme scheme, at
    # least for the first stanza, is that letters are used in
    # alphabetical order, left to right, with each letter appearing
    # for the first time for a line that doesn't rhyme with any
    # previous lines.

    letters_seen = []
    for letter in word.lower():
        if len(letters_seen) == 0:
            if letter != "a":
                return False
        elif letter in letters_seen:
            continue
        elif letter != chr(ord(letters_seen[-1]) + 1):
            return False
        letters_seen.append(letter)
    return True


def is_rhyme_scheme(word):
    word = word.lower()
    points = 0

    if word == "cdcd" or word == "efef":
        return True
    if letters_introduced_alphabetically(word):
        return True

    if ag_re.match(word):
        points += 50
    if mz_re.search(word):
        points -= 30
    substring_counts = defaultdict(int)
    for i in range(0, len(word)):
        if i < len(word) - 1:
            substring2 = word[i:i + 2]
            substring_counts[substring2] += 1
        if i < len(word) - 2:
            substring3 = word[i:i + 3]
            substring_counts[substring3] += 1

    repeated_substrings = 0
    for (sequence, instances) in substring_counts.items():
        if sequence[0] == sequence[1]:
            points += 10
        if instances > 1:
            repeated_substrings += 1
            points += 10
    if repeated_substrings / len(substring_counts) > .5:
        points += 50

    if points > 100:
        return True
    return False


def is_english_compound(word, english_words):
    if not english_words:
        print("PARALLEL GARBAGE COLLECT RECOVERY - english_words in is_english_compound()", file=sys.stderr)
        exit(1)
        # load_data()

    if "." in word:
        return False

    parts = word.split("-")
    if len(parts) > 1:
        if all(part in english_words for part in parts):
            return True
        return False

    pairs = [(word[0:i], word[i:]) for i in range(1, len(word))]
    for pair in pairs:
        if pair[0] in english_words and pair[1] in english_words:
            return True
    return False


# -- Spelling suggestions and T_ code --

# Process the input word into low-fi match strings
def get_anychar_permutations(word):
    word = word.lower()
    permus = [word]
    working_list = [word]
    for num_any in range(1, MAX_EDIT_DISTANCE + 1):
        new_permus = []
        for wrd in working_list:
            new_permus.extend([wrd[0:c] + "*" + wrd[c + 1:] for c in range(0, len(wrd))])
        permus.extend(new_permus)
        working_list = new_permus
    return permus


# Returns (False) if not near a known English word, or (integer edit
# distance, spelling suggestion) to closest word up to
# MAX_EDIT_DISTANCE
def near_common_word(word, english_words, suggestion_dict):
    if not english_words or not suggestion_dict:
        print("PARALLEL GARBAGE COLLECT RECOVERY - near_common_words()", file=sys.stderr)
        exit(1)
        # load_data()

    word = word.lower()
    if word in english_words:
        return 0

    lowfi_strings = {make_lowfi_string(permu) for permu in get_anychar_permutations(word)}
    # PERFORMANCE NOTE: Can be made more efficient by doing equivalent
    # of get_anychar_permutations() knowing we only care about lowfi
    # strings

    matches_by_distance = defaultdict(set)
    for edit_distance in range(1, MAX_EDIT_DISTANCE + 1):
        matches = []  # List to avoid excessive de-dup comparisons
        for lowfi_string in lowfi_strings:
            if lowfi_string in suggestion_dict[edit_distance]:
                matches.extend(list(suggestion_dict[edit_distance][lowfi_string]))
        matches = {match for match in matches if abs(len(match) - len(word)) <= MAX_EDIT_DISTANCE}
        if edit_distance > 1:
            # A little lossy, but greatly improves performance
            matches = {match for match in matches if match[0] == word[0]}

        for match in matches:
            matches_by_distance[distance.edit_distance(word, match, transpositions=True)].add(match)
        if matches_by_distance[edit_distance]:
            return (edit_distance, list(matches_by_distance[edit_distance])[0])
        # Intentionally leaving matches_by_distance of higher edit
        # distance (if any) for the next loop, so all suggestions of
        # equal distance will show up
    return (False, False)


google_lang_detector = gcld3.NNetLanguageIdentifier(min_num_bytes=0,
                                                    max_num_bytes=1000)


def tag_by_lang(word):
    # TODO: Very unreliable for Korean. Try using script detection?
    # -> https://en.wikipedia.org/wiki/Wikipedia:Language_recognition_chart

    lang_code = google_lang_detector.FindLanguage(word).language
    if lang_code == "en":
        if az_plus_re.match(word):
            return "TE"
        else:
            # English does not have diacritics, MIT Technology Review
            # and The New Yorker notwithstanding.
            return "TF+?"
    else:
        if lang_code == "iw":
            lang_code = "he"
            # ISO 639 code change for Hebrew
        return f"TF+{lang_code}"


# -- Main loop functions --


def get_word_category(word, english_words, titles_all_wiktionaries, transliterations, suggestion_dict):
    category = None
    suggestion = None

    if word.lower() in bad_words or word in bad_words:
        # "you", etc.
        return "BW"
    if word in bad_words:
        # "I'm"
        return "BW"
    if any([bad_char in word for bad_char in bad_characters]):
        # (bad character or substring)
        return "BC"

    if missing_leading_zero_re.search(word):
        return "Z"
    elif is_chess_notation(word):
        return "CH"  # Should be before "CF"
    elif is_chemical_name(word):
        return "CN"  # Should be before "ME"
    elif is_chemical_formula(word):
        return "CF"
    elif is_english_compound(word, english_words):
        return "ME"

    if is_math(word):
        return "A"

    # Parallel garbage collection problems?
    if not titles_all_wiktionaries or not transliterations:
        print("PARALLEL GARBAGE COLLECT RECOVERY - get_word_catgegory", file=sys.stderr)
        exit(1)
        # load_data()

    # Words in English Wiktionary (presumably including all known
    # English words) are ignored by the spell checker, so no need to
    # categorize words in english_words and english_wiktionary.
    #
    # TODO: Find the language of the word by Wikitionary lookup
    # instead of fuzzy language identification.
    if word in titles_all_wiktionaries:
        return tag_by_lang(word)

    if is_url_or_filename(word):
        return "U"

    if any(char in word for char in [",", "(", ")", "[", "]", " "]):
        # Extra or missing whitespace
        category = "TS"
    elif az_plus_re.match(word):
        if az_re.match(word):
            (edit_distance, suggestion) = near_common_word(word, english_words, suggestion_dict)
            if word in transliterations:
                category = "L"
            elif is_rhyme_scheme(word):
                category = "P"
            elif edit_distance:
                category = "T" + str(edit_distance)
            elif dna_re.match(word):
                category = "D"
            else:
                category = tag_by_lang(word)
        elif az_dot_re.match(word):
            # Usually missing whitespace after a period at the end of
            # a sentence
            category = "TS"

    if not category and html_tag_re.match(word):
        category = "H"
        if word in known_bad_link:
            category = "HL"
        elif word in not_html:
            category = "N"
        elif word in known_html_bad:
            category = "HB"
        else:
            word = word.replace("/", "")
            if word in known_html_bad:
                category = "HB"

    if not category:
        # Unicode category code meanings:
        # https://www.unicode.org/reports/tr44/#Property_Values
        unicode_classes = [unicodedata.category(char) for char in word]
        odd_classes = [c for c in unicode_classes if not c.startswith("L")]
        odd_classes = [c for c in odd_classes if c != "Pd"]
        if odd_classes:
            if odd_classes == ["Po"] and "/" in word:
                category = "T/"
            else:
                category = "N"
        else:
            category = tag_by_lang(word)

    # Dropping suggestion for now. TODO: Put suggestions in a JWB
    # substitution file for speedy fixups.
    return category


def process_line(param_list):
    # Share data made by parent
    english_words = param_list[0]
    titles_all_wiktionaries = param_list[1]
    transliterations = param_list[2]
    suggestion_dict = param_list[3]
    line = param_list[4]

    length = None
    word = None

    if "\t" in line:
        (length, word) = line.split("\t")
    else:
        word = get_word(line)

    category = get_word_category(word, english_words, titles_all_wiktionaries, transliterations, suggestion_dict)

    if length:
        return f"{category}\t* {length} [https://en.wikipedia.org/w/index.php?search={word} {word}]"
    else:
        return f"{category}\t{line}"


def process_input_parallel(english_words, titles_all_wiktionaries, transliterations, suggestion_dict):

    # TODO: Would probably be more efficient if this used shared
    # memory; right now, data is copied.
    # https://docs.python.org/3/library/multiprocessing.shared_memory.html

    lines = [line.strip() for line in fileinput.input("-")]
    with Pool(8) as pool:
        param_list = [(english_words, titles_all_wiktionaries, transliterations, suggestion_dict, line) for line in lines]
        # Chunk size 100000 is a LOT faster than the default of 1
        for result in pool.imap(process_line, param_list, 100000):
            print(result)
        pool.close()
        pool.join()


# Separate function so these don't have to be loaded for unit tests,
# but can be loaded when importing functions that need all the data.
def load_data():
    # Any words in multi-word phrases should also be listed as individual
    # words, so don't bother tokenizing.  TODO: Drop multi-word phrases
    # (at list creation time?) since these won't be matched anyway.
    print(datetime.datetime.now(), file=sys.stderr)
    print("Loading all languages...", file=sys.stderr)
    with open("/var/local/moss/bulk-wikipedia/titles_all_wiktionaries_uniq.txt", "r") as title_list:
        titles_all_wiktionaries = set([line.strip() for line in title_list])

    print("Loading transliterations...", file=sys.stderr)
    with open("/var/local/moss/bulk-wikipedia/transliterations.txt", "r") as title_list:
        transliterations = set([line.strip().split("\t")[1] for line in title_list
                                if "\t" in line.strip() and "_" not in line])

    print("Loading English words only...", file=sys.stderr)
    with open("/var/local/moss/bulk-wikipedia/english_words_only.txt", "r") as title_list:
        english_words = set([line.strip() for line in title_list])

    """
    global english_words_by_length_and_letter
    print("Indexing English words by length...", file=sys.stderr)
    english_words_by_length_and_letter = defaultdict(dict)
    for word in [w.lower() for w in english_words if az_re.match(w)]:
        existing_dict = english_words_by_length_and_letter[len(word)]
        first_letter = word[0]
        if first_letter not in existing_dict:
            existing_dict[first_letter] = {word}
        else:
            existing_dict[first_letter].add(word)
    """

    print(datetime.datetime.now(), file=sys.stderr)
    print("Indexing English spelling suggestions...", file=sys.stderr)
    suggestion_dict = make_suggestion_dict([w for w in english_words if az_re.match(w)])

    print("Done loading.", file=sys.stderr)
    print(datetime.datetime.now(), file=sys.stderr)
    return (english_words, titles_all_wiktionaries, transliterations, suggestion_dict)


if __name__ == '__main__':
    print("NORMAL load_data", file=sys.stderr)
    (english_words, titles_all_wiktionaries, transliterations, suggestion_dict) = load_data()

    process_input_parallel(english_words, titles_all_wiktionaries, transliterations, suggestion_dict)
    print("Done categorizing.", file=sys.stderr)
    print(datetime.datetime.now(), file=sys.stderr)
