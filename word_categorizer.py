# R = Regular
# C = Chemistry
# N = Numbers or punctuation
# I = International (non-ASCII characters)

import fileinput
import re

az_re = re.compile("^[a-z]+$")
az_plus_re = re.compile("^[a-z|\d|\-]+$")

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
    # print("CHEM_SMALL\t%s" % small_word)
    if len(word) > 14:
        if len(small_word) < len(word) * .50:
            return True
    if len(small_word) < len(word) * .25:
        return True
    return False


for line in fileinput.input("-"):
    line = line.strip()

    (length, word) = line.split("\t")

    category = None
    if az_plus_re.match(word):
        if is_chemistry_word(word):
            category = "C"
        elif az_re.match(word):
            category = "R"
        else:
            category = "N"
    else:
        category = "I"
        
    print("%s\t* %s [https://en.wikipedia.org/w/index.php?search=%s %s]"
          % (category, length, word, word))
