import re


# --- HELPER VARIABLES AND CONFIG ---

# Focus letters that were posted on the last run, and should take a
# rest this run to avoid duplicate work.
by_article_suppress = ["1", "2"]

# previously run: "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
# "Aa", "Ab", "Ba", "J", "Q", "X", "Y", "Z", "Á", "Å", "Ç", "É", "Ö",
# "Ø", "Ş"


# By-frequency lists swap which half of the alphabet they suppress
alpha_half_inactive = ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m"]
alpha_half_active = ["n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z"]
active_range_str = "%s-%s" % (alpha_half_active[0], alpha_half_active[-1])

find_word_re = re.compile(" - \[\[wikt:(.*?)\]\] - ")


# --- HELPER FUNCTIONS ---


def get_sections_from_file(filename, number_of_sections, suppression_list):
    output = ""
    sections_seen = 0
    skip_this_section = False
    with open(filename, "r") as lines:
        for line in lines:
            if line.startswith("="):
                skip_this_section = False
                result = re.match(r"==== ([^\-].*?)(\-.+)? ====", line)
                start = result.group(1)
                end = ""
                if result.group(2):
                    end = result.group(2)
                    end = end.strip("-")
                for prefix in suppression_list:
                    if start.startswith(prefix) or end.startswith(prefix):
                        skip_this_section = True
                        break

                if not skip_this_section:
                    sections_seen += 1

            if sections_seen > number_of_sections:
                return output
            if skip_this_section:
                continue
            else:
                output += line
        return output


def get_active_lines_from_file(filename, active_list, inactive_list):
    output = ""
    with open(filename, "r") as lines:
        for line in lines:
            word = find_word_re.search(line).group(1)
            first_letter = word[0]
            if first_letter in inactive_list:
                continue
            if first_letter not in active_list:
                raise Exception('Unexpected character "%s" in "%s"' % (first_letter, word))
            output += line
    return output


# --- MAIN PRINTOUT ---

print("=== Likely misspellings by article ===")
print("")
print("""The most efficient list to work on if all you want to do is fix
misspellings.  All typos from a given article are shown, but only
typos that are very close to known words are shown.  The algorithm is
not perfect, so some of these may still be words that need to be added
to Wiktionary. A different part of the alphabet is posted on each run
to avoid duplicate work, and because the whole list is too long to
post all at once.""")
print("")


print(get_sections_from_file("tmp-by-article-edit1.txt", 50, by_article_suppress))


print("=== Likely misspellings by frequency (%s) ===" % active_range_str)
print("")
print("""The best list to work on if you want to eliminate all instances of
a specific typo.  Only typos that are very close to known words are
shown. The algorithm is not perfect, so some of these may still be
words that need to be added to Wiktionary. For each run, only words
from half of the alphabet are shown, to avoid duplicate work from when
new dumps are being processed.""")
print("")
print(get_active_lines_from_file("tmp-most-common-edit1.txt", alpha_half_active, alpha_half_inactive))
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
print(get_active_lines_from_file("tmp-most-common-compound.txt", alpha_half_active, alpha_half_inactive))
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
