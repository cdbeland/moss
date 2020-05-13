import re


# --- HELPER VARIABLES AND CONFIG ---

# By-frequency lists swap which half of the alphabet they suppress
alpha_half_active = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]
alpha_half_inactive = ["n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
other_active = True
active_range_str = "%s-%s" % (alpha_half_active[0], alpha_half_active[-1])

find_word_re = re.compile(r" - \[\[wikt:(.*?)\]\] - ")
find_word_html_re = re.compile(r" - <nowiki><(.*?)></nowiki> - ")


# --- HELPER FUNCTIONS ---


def get_active_lines_from_file(filename, active_list, inactive_list, exclude_dot=False):
    output = ""
    with open(filename, "r") as lines:
        for line in lines:
            match = find_word_re.search(line)
            if not match:
                match = find_word_html_re.search(line)
            if not match:
                print(line)
                raise Exception("Could not extract word from line '%s'" % line)
            word = match.group(1)
            first_letter = word[0]
            if first_letter in inactive_list:
                continue
            if first_letter not in active_list:
                if not other_active:
                    continue
            if exclude_dot and "." in word:
                continue
            output += line
    return output


def restrict_misspellings(input_lines_str):
    output_str = ""
    for line in input_lines_str.split("\n"):
        if not line:
            continue

        match = re.match(r"\* (\d+) - ", line)
        if not match:
            raise Exception(f"Could not find number of instances from '{line}'")
        number = int(match.group(1))

        # There will always be a low level of typos; below 5 probably
        # not frequent enough to put on lists of frequent typos, and
        # at that point this report will probably be obsolete.
        if number <= 5:
            continue

        # Skip words that only appear in one article
        if not re.search(r"\]\],", line):
            continue

        output_str += f"{line}\n"
    return output_str


# --- MAIN PRINTOUT ---

print("=== Likely misspellings by frequency (%s) ===" % active_range_str)
print("")
print("""The best list to work on if you want to eliminate all instances of
a specific typo.  Only typos that are very close to known words are
shown. The algorithm is not perfect, so some of these may still be
words that need to be added to Wiktionary. For each run, only words
from half of the alphabet are shown, to avoid duplicate work from when
new dumps are being processed.

Legitimate misspellings are candidates for [[Wikipedia:Lists of common misspellings]].
If there is an obvious correction, adding that to
[[Wikipedia:Lists of common misspellings/For machines]] will help
editors who use automated tools to fix cases faster.""")
print("")
print(restrict_misspellings(get_active_lines_from_file("tmp-most-common-edit1.txt", alpha_half_active, alpha_half_inactive)))
print("")


print("=== Likely new compounds by frequency (%s) ===" % active_range_str)
print("")
print("""The best list to work on if you want to add variations of known
words to Wiktionary, mostly compound words.  The algorithm is not
perfect, so some of these might be common mistakes that need to
corrected. For each run, only words from half of the alphabet are
shown, to avoid duplicate work from when new dumps are being
processed.""")
print("")
print(get_active_lines_from_file("tmp-most-common-compound.txt", alpha_half_active, alpha_half_inactive, exclude_dot=True))
print("")

print("=== Likely new words by frequency (%s) ===" % active_range_str)
print("")
print("""The best list to work on if you want to add completely new words to
Wiktionary. The algorithm is not perfect, so some of these might be
common mistakes that need to corrected. For each run, only words from
half of the alphabet are shown, to avoid duplicate work from when new
dumps are being processed.

Some of the words might not be from English.  To get these words off
this list, you can either add an entry to the English Wiktionary
(which provides English definitions for words in all languages) or tag
all instances of the word on the English Wikipedia with {{tl|lang}}.
Wiktionary does not accept Romanizations for some languages, so those
cases must be tagged as {{tl|transl}} or {{tl|lang}}.""")
print("")
print(get_active_lines_from_file("tmp-most-common-new-words.txt", alpha_half_active, alpha_half_inactive))
print("")
