# Probably a typo:
#
# H = HTML/XML/SGML tag
# HB = Known bad HTML tag, like <font>
# HL = Bad HTML-like linking, like <http://...>
# T1, T2, etc. = Typo likely in regular word; number gives edit
#                distance to nearest common dictionary word
# TS = Typo likely in regular word; probably two words that need to be
#      split by space or dash
# BW = Bad word
# BC = Bad character
# Z = Decimal fraction missing leading zero (includes calibers and
#     batting averages that need a link in the article)
#
# Probably OK:
#
# C = Chemistry
# D = DNA sequence
# P = Pattern of some kind (rhyme scheme, reduplication)
# W = Found in a non-English Wikitionary
# L = Probable Romanization (transLiteration)
# ME = Probable coMpound, English in English Wiktionary
# MI = Probable coMpound, non-English (International) in English Wiktionary
# MW = Probable coMpound, found in non-English Wiktionary
# ML = Probable coMpound, transLiteration
# U = URL or computer file name
#
# Relatively unsorted:
#
# R = Regular word (a-z only)
# I = International (non-ASCII characters)
# N = Numbers or punctuation

from collections import defaultdict
import difflib
import enchant
import fileinput
from nltk.metrics import distance
import re
import sys
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

enchant_en = enchant.Dict("en_US")  # en_GB seems to give US dictionary
az_re = re.compile(r"^[a-z]+$", flags=re.I)
az_plus_re = re.compile(r"^[a-z|\d|\-|\.]+$", flags=re.I)
az_dot_re = re.compile(r"^[a-z]+(\-[a-z]+)?\.[a-z]+(\-[a-z]+)?$", flags=re.I)
ag_re = re.compile(r"^[a-g]+$")
mz_re = re.compile(r"[m-z]")
dna_re = re.compile(r"^[acgt]+$")
missing_leading_zero_re = re.compile(r"[ ^]\.\d")
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

known_html_bad = {"<tt>", "<li>", "<ol>", "<ul>", "<table>", "<th>",
                  "<tr>", "<td>", "<i>", "<em>", "<dd>", "<dt>",
                  "<dl>", "<cite>", "<p>", "<strong>", "<b>", "<hr>",
                  "<hr/>", "<font>", "</br>", "<center>", "<strike>",
                  "<ins>", "<q>", "<wbr>", "<ruby>", "<rt>",
                  "<rp>"}
known_bad_link = {"<http>", "<https>", "<http/>", "<https/>", "<www>"}
not_html = {"<a>", "<name>", "<r>", "<h>"}
# <a> is not turned into a link by Mediawiki, so it's almost always
# intentional like linguistics markup.

# Any words in multi-word phrases should also be listed as individual
# words, so don't bother tokenizing.  TODO: Drop multi-word phrases
# (at list creation time?) since these won't be matched anyway.
print("Loading all languages...", file=sys.stderr)
with open("/bulk-wikipedia/titles_all_wiktionaries_uniq.txt", "r") as title_list:
    titles_all_wiktionaries = set([line.strip() for line in title_list])

print("Loading transliterations...", file=sys.stderr)
with open("/bulk-wikipedia/transliterations.txt", "r") as title_list:
    transliterations = set([line.strip().split("\t")[1] for line in title_list
                            if "\t" in line.strip() and "_" not in line])

print("Loading English Wiktionary...", file=sys.stderr)
with open("/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0", "r") as title_list:
    english_wiktionary = set([line.strip() for line in title_list if "_" not in line])

print("Loading English words only...", file=sys.stderr)
with open("/bulk-wikipedia/english_words_only.txt", "r") as title_list:
    english_words = set([line.strip() for line in title_list])

print("Done loading.", file=sys.stderr)

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

chem_roman_numerals = ["II", "III", "IV", "VI", "VII", "VIII", "IX"]

element_alternation = "(" + "|".join(element_symbols) + ")"
roman_alternation = "(" + "|".join(chem_roman_numerals) + ")"

chem_formula_regexes = [
    rf"^{element_alternation}+$",                            # NaCl
    rf"^{element_alternation}+\({element_alternation}+\)$",  # Ca(OH)
    rf"^{element_alternation}+\({roman_alternation}\)$",     # Mn(II)
]
chem_formula_re = re.compile("(" + "|".join(chem_formula_regexes) + ")")


# Note: This may malfunction slightly if there are commas inside the
# chemical name.
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_inorganic_chemistry
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_organic_chemistry
# https://en.wikipedia.org/wiki/Chemical_nomenclature
def is_chemistry_word(word):
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
    if chem_formula_re.match(word):
        return True
    return False


def is_url(word):
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


# Returns False if not near a common word, or integer edit distance to
# closest word, or "S" for word split
def near_common_word(word):
    close_matches = difflib.get_close_matches(word, enchant_en.suggest(word))
    if close_matches:
        if " " in close_matches[0] or "-" in close_matches[0]:
            return "S"
        this_distance = distance.edit_distance(word, close_matches[0], transpositions=True)
        if this_distance <= 3:
            # 4 and greater is fairly useless
            return this_distance
    return False
# Other spell check and spelling suggestion libraries:
# https://textblob.readthedocs.io/en/dev/quickstart.html#spelling-correction
#  -> based on NLTK and http://norvig.com/spell-correct.html
# https://pypi.org/project/autocorrect/
#  from autocorrect import spell
#  print(spell('caaaar'))
# https://github.com/wolfgarbe/SymSpell


def is_compound(word):
    parts = word.split("-")
    if len(parts) > 1:
        if all(part in english_words for part in parts):
            return "ME"
        if all(part in english_wiktionary for part in parts):
            return "MI"
        if all(part in titles_all_wiktionaries for part in parts):
            return "MW"
        if all(part in transliterations for part in parts):
            return "ML"
        return False

    pairs = [(word[0:i], word[i:]) for i in range(1, len(word))]
    for (cat_letter, dictionary) in [("E", english_words),
                                     ("I", english_wiktionary),
                                     ("W", titles_all_wiktionaries),
                                     ("L", transliterations)]:
        for pair in pairs:
            if pair[0] in dictionary and pair[1] in dictionary:
                return "M" + cat_letter

    return False


def get_word_category(word):
    category = None

    if word.lower() in bad_words or word in bad_words:
        # "you", "I'm"
        return "BW"
    if any([bad_char in word for bad_char in bad_characters]):
        # (bad character or substring)
        return "BC"

    # Words in English Wiktionary (presumably including all known
    # English words) are ignored by the spell checker, so no need to
    # categorize words in english_words and english_wiktionary.
    if word in titles_all_wiktionaries:
        return "W"

    if is_url(word):
        return "U"

    compound_cat = is_compound(word)

    if missing_leading_zero_re.search(word):
        category = "Z"
    elif is_chemistry_word(word):
        category = "C"
    elif any(char in word for char in [",", "(", ")", "[", "]", " "]):
        # Extra or missing whitespace
        category = "TS"
    elif az_plus_re.match(word):
        if az_re.match(word):
            edit_distance = near_common_word(word)
            if edit_distance:
                # Possibly TS
                category = "T" + str(edit_distance)
            elif word in transliterations:
                category = "L"
            elif compound_cat:
                category = compound_cat
            elif dna_re.match(word):
                category = "D"
            elif is_rhyme_scheme(word):
                category = "P"
            else:
                category = "R"
        elif az_dot_re.match(word):
            # Usually missing whitespace after a period at the end of
            # a sentence
            category = "TS"
        else:
            category = "N"
    elif html_tag_re.match(word):
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
    else:
        category = compound_cat or "I"

    return category


if __name__ == '__main__':
    for line in fileinput.input("-"):
        line = line.strip()

        length = None
        word = None

        if "\t" in line:
            (length, word) = line.split("\t")
        else:
            word = get_word(line)

        category = get_word_category(word)

        if length:
            print("%s\t* %s [https://en.wikipedia.org/w/index.php?search=%s %s]"
                  % (category, length, word, word))
        else:
            print("%s\t%s" % (category, line))
