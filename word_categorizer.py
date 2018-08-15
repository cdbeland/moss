# R = Regular
# C = Chemistry
# P = Pattern of some kind (rhyme scheme, reduplication)
# D = DNA sequence
# N = Numbers or punctuation
# I = International (non-ASCII characters)

from collections import defaultdict
import fileinput
import re

az_re = re.compile("^[a-z]+$", flags=re.I)
az_plus_re = re.compile("^[a-z|\d|\-]+$", flags=re.I)
ag_re = re.compile("^[a-g]+$")
mz_re = re.compile("[m-z]")
dna_re = re.compile("^[acgt]+$")

chem_re = re.compile(
    "(\d+\-|"
    "mono|di|bi|tri|tetr|pent|hex|hept|oct|nona|deca|"
    "methyl|phenyl|acetate|ene|ine|ane|ide|hydro|nyl|ate$|ium$|acetyl|"
    "gluco|aminyl|galacto|pyro|benz|brom|amino|fluor|glycer|cholester|ase$|"
    "chlor|oxy|nitr|silic|phosph|nickel|copper|iron|carb|sulf|alumin|arsen|magnesium|mercury|lead|calcium|"
    "propyl|itol|ethyl|oglio|stearyl|alkyl|ethan|amine|ether|keton|oxo|pyri|ine$|"
    "cyclo|poly|iso)")


# Note: This may malfunction slightly if there are commas inside the
# chemical name.
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_inorganic_chemistry
# https://en.wikipedia.org/wiki/IUPAC_nomenclature_of_organic_chemistry
# https://en.wikipedia.org/wiki/Chemical_nomenclature
def is_chemistry_word(word):
    small_word = chem_re.sub("", word)
    if len(word) > 14:
        if len(small_word) < len(word) * .50:
            return True
    if len(small_word) < len(word) * .25:
        return True
    return False


def is_rhyme_scheme(word):
    word = word.lower()
    points = 0
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


for line in fileinput.input("-"):
    line = line.strip()

    (length, word) = line.split("\t")

    category = None
    if az_plus_re.match(word):
        if dna_re.match(word):
            category = "D"
        elif is_chemistry_word(word):
            category = "C"
        elif is_rhyme_scheme(word):
            category = "P"
        elif az_re.match(word):
            category = "R"
        else:
            category = "N"
    else:
        category = "I"

    print("%s\t* %s [https://en.wikipedia.org/w/index.php?search=%s %s]"
          % (category, length, word, word))
