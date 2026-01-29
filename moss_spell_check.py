# -*- coding: utf-8 -*-

from collections import defaultdict
import nltk
import re
import sys
from moss_dump_analyzer import read_en_article_text
from wikitext_util import wikitext_to_plaintext, get_main_body_wikitext, ignore_tags_re
from spell import is_word_spelled_correctly, bad_words
from word_categorizer import is_chemical_name, is_chemical_formula, is_chess_notation

# TODO:
# * Flag articles for topic (e.g. species, genus) and language hints
#   (country name, language name, {{lang}} and {{transl}})
# * Detect strings of three or more Greek letters ONLY for
#   spell-checking purposes.
# * tmp-output.txt:* 24 - [[wikt:ation]] - [[1772 in poetry]] ([[attest]]ation)
# * Report these:
#    :"..."
#    :''"..."''
#    <blockquote>"..."</blockquote>
#    {{quote|"..."}}
#   as possible violations of [[MOS:BLOCKQUOTE]]; exclude these from
#   "parse failed" output

# TODO LONG TERM:
# * Suppress items on
#   https://en.wiktionary.org/wiki/Category:English_misspellings from
#   the allow list (maybe conditionally, if that is also a correct
#   spelling of some other word)
#   (suggested by User:-sche)
# * Do a separate run for redirects matching
#   "{{[\w]+(misspelling|incorrect)[\w* ]+}}" pages on enwiki and
#   prepare batch edits for these
# * Is there an equivalent for misspellings on wiktionary?
# * Handle multi-word phrases properly, or slice up article titles?
# * Be case-sensitive (need to recover from article text due to first
#   word in article titles always being capitalized, and on the other
#   side need to detect first word in sentence or allow
#   over-capitalization but not under-capitalization)
# * Sort into dialects (American English, British English, Scottish English, etc.)
# * Support {{sic}}, reading and writing
# * Only allow 's on nouns
# * Handle final . properly for real, by detecting end-of-sentence
# * Monitor recent changes (see [[Wikipedia:Recent changes
#   patrol#Monitoring]]) and drop notes on editor talk pages notifying
#   them they may have made a spelling error.  The algorithm needs to
#   be pretty solid.


misspelled_words = {}
# Indexes articles by typo.  For example:
# {'misspellling': (2, ['article1', 'article2'])}


def dump_results():
    global misspelled_words
    misspelled_by_freq = [(value[0], key, value[1]) for (key, value) in misspelled_words.items()]
    misspelled_by_freq = sorted(misspelled_by_freq)
    for (freq, word, article_list) in misspelled_by_freq:
        uniq_list = list(set(article_list))
        uniq_list.sort()
        uniq_string = ""
        if uniq_list:
            uniq_string = u"[[" + u"]], [[".join(uniq_list) + u"]]"
        output_string = u"* %s - [[wikt:%s]] - %s" % (freq, word, uniq_string)
        print(output_string)


start_template_re = re.compile(r"{{")
end_template_re = re.compile(r"}}")
unicode_letters_plus_dashes_re = re.compile(r"^([^\W\d_]|-)+$")
spaced_emdash_re = re.compile(r".{0,10}—\s.{0,10}|.{0,10}\s—.{0,10}")
newline_re = re.compile(r"\n")
comma_missing_whitespace_re = re.compile(r"\w+[a-z],\w\w+|\w+\w,[a-zA-Z]\w+")
caliber_re = re.compile(r"[^ ]?\.\d\ds?$")
batting_average_re = re.compile(r"[^ ]?\.\d\d\d$")

bracket_missing_whitespace_re = re.compile(r"([a-zA-Z]+\([a-zA-Z]+\)?"
                                           r"|[a-zA-Z]+\)[a-zA-Z]+"
                                           r"|[a-zA-Z]+\[[a-zA-Z]+\]?"
                                           r"|[a-zA-Z]+\][a-zA-Z]+)")
# Includes optional closing ] or ) to deal with situations like
# "Chromium(IV)", which is correctly spelled.

punct_extra_whitespace_re = re.compile(r"\w+ ,\w+|\w+ \.\w+|\w+ \)|\( \w+|\[ \w+|\w+ ]")

requested_species_html = ""
with open('/var/local/moss/bulk-wikipedia/Wikispecies:Requested_articles', 'r') as requested_species_file:
    requested_species_html = requested_species_file.read()

article_skip_list = [
    "Unicode subscripts and superscripts",  # Really only need to suppress BC for this article
]

bad_words_apos = sorted([w for w in bad_words if "'" in w], key=lambda w: 100 - len(w))
bad_words_apos_re = re.compile(r"[^a-z](" + "|".join(bad_words_apos) + r")[^a-z]", re.I)

# This is for adding words to the grist
wikt_trans_re = re.compile(r"\{\{trans-see *\|(.*?)\}\}")

gaol_fever_re = re.compile(r"gaol fever")


# Returning True means "yes, ignore"
def ignore_typo_in_context(word_mixedcase, article_text_orig):

    # Hack to avoid having to do even more complicated token
    # re-assembly, though this may cause some unnecessary HTML
    # markup on the same page to be ignored.
    if word_mixedcase == "<li>":
        if "<li value=" in article_text_orig:
            return True
        if "<li value =" in article_text_orig:
            return True
        if "<ol start=" in article_text_orig:
            return True
        if "<ol start =" in article_text_orig:
            return True
    if word_mixedcase == "<ol>":
        if "<ol start=" in article_text_orig:
            return True
        if "<ol start =" in article_text_orig:
            return True

    # TODO: In some situations this might actually be replaced
    # with a streamlined wiki-style list, or footnote syntax.
    if word_mixedcase == "<ol>" and "<ol type=" in article_text_orig:
        return True
    if word_mixedcase == "<li>" and "<ol type=" in article_text_orig:
        return True

    # Keep "gaol fever" as long as "jail fever" is glossed; per Google
    # Ngrams, "gaol fever" is still more common than "jail fever", but
    # "gaol" is not more common than "jail fever".
    if word_mixedcase == "gaol":
        if "jail fever" in article_text_orig:
            article_text_copy = gaol_fever_re.sub("", article_text_orig)
            if "gaol" not in article_text_copy:
                return True

    # Exceptions made by
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Dates_and_numbers#Decimals
    if caliber_re.search(word_mixedcase) and ("caliber" in article_text_orig or "calibre" in article_text_orig):
        return True
    if batting_average_re.search(word_mixedcase):
        # Report as a Z error unless one of these articles is linked
        # in the text (otherwise many readers will not know what
        # e.g. "batting .123" means).
        if "batting average" in article_text_orig:
            return True
        if "fielding percentage" in article_text_orig:
            return True
        if "slugging percentage" in article_text_orig:
            return True

    # e.g. "Microsoft .NET"
    if " " in word_mixedcase:
        words = word_mixedcase.split()
        if all(is_word_spelled_correctly(word) is True for word in words):
            return True

    if is_chess_notation(word_mixedcase):
        return True
    # Must be after is_chess_notation(); they overlap
    if is_chemical_formula(word_mixedcase):
        # Subscripts are stripped out in the main spell check, but the
        # formula only violates [[MOS:SUB]] if it does *not* use
        # subscripts or a chem template. (Thus if the formula has
        # changed due to stripping of <sub>, it can safely be ignored
        # in context.)
        if word_mixedcase not in article_text_orig:
            return True

    return False


language_divider_re = re.compile(r"^== *([^=]+) *==$")


def spellcheck_all_langs_wikt_with_quotations(params):
    return spellcheck_all_langs_wikt(params, include_quotations=True)


def spellcheck_all_langs_wikt(params, include_quotations=False):
    article_title = params[0]
    article_text = params[1]

    language_this_part = ""
    text_this_part = ""
    article_parts = defaultdict(list)
    for line in article_text.split("\n"):
        result = language_divider_re.match(line)
        if result:
            if text_this_part:
                article_parts[language_this_part] = text_this_part
            language_this_part = result.group(1)
            text_this_part = ""
        text_this_part += line + "\n"
    # Last part won't have a section header to trigger it
    if text_this_part:
        article_parts[language_this_part] = text_this_part

    result_list = []
    for (article_part, part_text) in article_parts.items():
        spell_check_result = spellcheck_all_langs(f"{article_title}#{article_part}",
                                                  part_text,
                                                  wiktionary=True,
                                                  include_quotations=include_quotations)
        if spell_check_result and spell_check_result[1]:
            result_list.append(spell_check_result)

    return result_list


def spellcheck_all_langs(article_title, article_text, wiktionary=False, include_quotations=False):
    # WARNING: This function runs in subprocesses, and cannot
    # change global context variables. (It CAN print.)

    # -- Skip article entirely if appropriate --

    # if article_title[0] != "X":
    #     print("S\tSKIPPING due to fast run\t%s" % article_title)
    #     return

    # if not article_title.startswith("List"):
    #     print("S\tSKIPPING due to fast run\t%s" % article_title)
    #     return

    if article_title in article_skip_list:
        print("S\tSKIPPING due to article skip list\t%s" % article_title, flush=True)
        return

    if article_title.endswith("(data page)"):
        print("S\tSKIPPING chemical data page\t%s" % article_title, flush=True)

    if ignore_tags_re.search(article_text):
        print("S\tSKIPPING due to known cleanup tag\t%s" % article_title, flush=True)
        return

    request_search_string_en = 'title="en:%s"' % article_title
    request_search_string_w = 'title="w:%s"' % article_title
    if request_search_string_en in requested_species_html or request_search_string_w in requested_species_html:
        print("S\tSKIPPING - list with requested species\t%s" % article_title, flush=True)
        return

    # -- Fatal problems --

    article_text_orig = article_text
    article_text = wikitext_to_plaintext(article_text)
    article_text = get_main_body_wikitext(article_text, include_quotations=include_quotations)

    # This can break wikitext_to_plaintext() in ways that cause wiki
    # syntax to be mistaken for prose.
    starters = start_template_re.findall(article_text)
    enders = end_template_re.findall(article_text)
    if len(starters) != len(enders):
        print("!\t* [[%s]] - Mismatched {{ }}" % article_title, flush=True)
        return

    # -- Dashes --

    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style#Dashes
    # requires that emdashes be unspaced.
    article_text_safe = newline_re.sub(" ", article_text)
    bad_emdash_context_list = spaced_emdash_re.findall(article_text_safe)
    if bad_emdash_context_list:
        print("D\t* %s - [[%s]]: %s" % (
            len(bad_emdash_context_list),
            article_title,
            " ... ".join(bad_emdash_context_list)),
              flush=True)

    # -- More fatal problems --

    for unmatched_item in ["<ref", "</ref>", "<blockquote", "</blockquote>", "}}", "{{", '"', "colspan", "rowspan", "cellspacing"]:
        if unmatched_item in article_text:
            matches = re.findall(r".{0,20}%s.{0,20}" % unmatched_item, article_text)
            excerpt = " ... ".join(matches)
            if unmatched_item == '"' and ("“" in article_text or "”" in article_text):
                print("!Q\t* [[%s]] - Unmatched %s probably due to violation of [[MOS:STRAIGHT]] near: %s" % (article_title, unmatched_item, excerpt), flush=True)
            else:
                print("!\t* [[%s]] - Unmatched %s near: %s" % (article_title, unmatched_item, excerpt), flush=True)
            # Often due to typo in wiki markup or mismatched English
            # punctuation, but might be due to moss misinterpreting
            # the markup.  (Either way, should be fixed because this
            # blocks spell-checking the entire article.)
            return

    # -- Initialization for main spell check --

    article_oops_list = []
    article_text = article_text.replace("✂", " ")

    # -- Punctuation and whitespace errors not using word_list --

    # NLTK tokenizer usually turns e.g. words with comma missing
    # following whitespace into three tokens, e.g.
    # "xxx,yyy" -> ['xxx', ',', 'yyy']
    missing_comma_typos = comma_missing_whitespace_re.findall(article_text)
    for typo in missing_comma_typos:
        # Ignore chemical names
        if is_chemical_name(typo):
            continue

        # Ignore genetics notation
        if re.match(r"4\d,X[XY]", typo):
            continue

        if is_word_spelled_correctly(typo) in [False, "uncertain"]:
            # The above matches against the dictionary and Wikipedia
            # article titles; some forms are legitimate, like
            # [[46,XX]].  But this is separate from the below loop
            # because we count "uncertain" as misspelled rather than
            # to be ignored.
            article_oops_list.append(typo)

    for typo in bracket_missing_whitespace_re.findall(article_text):
        if is_word_spelled_correctly(typo) in [False, "uncertain"]:
            if not is_chemical_name(typo):
                article_oops_list.append(typo)

    for typo in punct_extra_whitespace_re.findall(article_text):
        if is_word_spelled_correctly(typo) in [False, "uncertain"]:
            article_oops_list.append(typo)

    # The NLTK tokenizer splits contractions in two
    found_bad_words = bad_words_apos_re.findall(article_text)
    for bad_word in found_bad_words:
        article_oops_list.append(bad_word)

    # -- Generate and fix tokenization of word_list --

    word_list = nltk.word_tokenize(article_text.replace("—", " - "))
    # NLTK tokenizer sometimes doesn't split on emdash

    # Requested by User:Hftf
    if wiktionary:
        trans_xrefs = wikt_trans_re.findall(article_text_orig)
        for trans_xref in trans_xrefs:
            more_words_tmp = [param.strip() for param in str(trans_xref).split("|")]
            for param in more_words_tmp:
                word_list.extend(nltk.word_tokenize(param))

    # Old-fashioned loop to allow lookahead and cope with the fact
    # that the length of word_list may change as it is edited in
    # place.
    i = 0
    while i < len(word_list):
        # TODO: Make test cases, especially for beginning and
        # end-of-document HTML entities.

        # Reassemble HTML markup the tokenizer has split into multiple
        # words.  Must double-check because the tokenizer ignores
        # whitespace, and we don't want to accidentally match
        # e.g. where an ampersand in prose is followed shortly by a
        # semicolon.

        # TODO: Parameterize to avoid code duplication

        # Two-token sequences
        if i < len(word_list) - 1:
            # Sometimes tokenization separates final period from the
            # rest of the acronym.
            if "." in word_list[i] and word_list[i + 1] == ".":
                word_list[i] += "."
                del word_list[i + 1]

        # Three-token sequences
        if i < len(word_list) - 2:
            if word_list[i] == "&" and word_list[i + 2] == ";":

                # Protect against & in acronyms, common for railroads
                # and companies like AT&T, PG&E.
                if i == 0 or not (re.match("^[A-Z]+s?$", word_list[i + 1])
                                  and re.match("^[A-Z]+$", word_list[i - 1])):
                    consolidated = "&%s;" % word_list[i + 1]
                    if consolidated in article_text:
                        word_list[i] = consolidated
                        del word_list[i + 2]
                        del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 2] == ">":
                consolidated = "<%s>" % word_list[i + 1]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 2]
                    del word_list[i + 1]

            # In transliterations from Arabic script (which includes
            # Persian), NLTK correctly parses U+0027 (apostrophe) and
            # U+02BE/U+02BF (preferred by the Unicode Consortium and
            # United Nations).
            # https://en.wikipedia.org/wiki/Romanization_of_Persian
            # https://en.wikipedia.org/wiki/Romanization_of_Arabic
            #
            # However, Wikipedia allows the use of U+2019 (right
            # single quote mark) which NLTK will (arguably
            # justifiably) misparse if used as something other than a
            # quotation mark.
            # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Persian
            # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Arabic
            elif word_list[i + 1] == "’":
                # For example "Āb Anbār-e Pā’īn" must be parsed as three words.
                if unicode_letters_plus_dashes_re.search(word_list[i]) and unicode_letters_plus_dashes_re.search(word_list[i + 2]):
                    word_list[i] = word_list[i] + word_list[i + 1] + word_list[i + 2]
                    del word_list[i + 2]
                    del word_list[i + 1]

        # Four-token sequences
        if i < len(word_list) - 3:
            if word_list[i] == "&" and word_list[i + 1] == "#" and word_list[i + 3] == ";":
                consolidated = "&#%s;" % word_list[i + 2]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 1] == "/" and word_list[i + 3] == ">":
                consolidated = "</%s>" % word_list[i + 2]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

            elif word_list[i] == "<" and word_list[i + 2] == "/" and word_list[i + 3] == ">":
                consolidated = "<%s/>" % word_list[i + 1]
                if consolidated in article_text:
                    word_list[i] = consolidated
                    del word_list[i + 3]
                    del word_list[i + 2]
                    del word_list[i + 1]

        i += 1

    # -- Main spellcheck loop --

    for word_mixedcase in word_list:

        # "." is specifically excluded from the below list, due to
        # abbreviations which are handled correctly by spell.py with
        # periods in place.
        word_mixedcase = word_mixedcase.strip(
            # Deal with symmetrical wiki markup
            "=" +
            # Deal with NLTK treatment of hyphenated and slashed words
            "––/-" +

            # TODO: NLTK tokenizer breaks on British quoting style
            # (which is allowed in a small number of circumstances): 'xxx'
            "'"

            # https://en.wikipedia.org/wiki/%CA%BBOkina#Names
            # TODO: NLTK tokenizer breaks on Polynesian words using
            # apostrophes and quote marks to represent 'eta and other
            # glottal stops.  Hawaiian words should use ʻokina which
            # are tokenized correctly, as a letter.
        )

        # Deal with asymmetrical wiki markup
        word_mixedcase = word_mixedcase.lstrip(":")

        if word_mixedcase.startswith("*"):
            word_mixedcase = word_mixedcase.lstrip("*")
            if re.search(r"''\*" + word_mixedcase + r"''", article_text):
                # Unattested forms like "''*tuqlid''" which are not
                # eligible for dictionary entries. The meaning of
                # these strings should be clear in context, so no need
                # to report them.
                continue

        if not word_mixedcase.startswith("&"):
            # Let &xxx; pass through un-stripped so it's easy to identify later
            word_mixedcase = word_mixedcase.strip(";")

        is_spelling_correct = is_word_spelled_correctly(word_mixedcase)
        if is_spelling_correct is True:
            continue
        if is_spelling_correct == "uncertain":
            if not ignore_typo_in_context(word_mixedcase, article_text_orig):
                if not is_chemical_formula(word_mixedcase):
                    print("G\t%s\t%s" % (word_mixedcase, article_title), flush=True)
                    # "G" for "iGnored but maybe shouldn't be"
                    continue

        # - Word is misspelled -

        # Index typo by article
        article_oops_list.append(word_mixedcase)

    # Exceptions - words and written forms not in the dictionary
    article_oops_list = [oops for oops in article_oops_list
                         if not ignore_typo_in_context(oops, article_text_orig)]

    if article_oops_list:
        article_oops_string = u"𝆃".join(article_oops_list)
        print("@\t%s\t%s\t%s" % (len(article_oops_list), article_title, article_oops_string), flush=True)
    return (article_title, article_oops_list)


# Callback from completion of spellcheck_all_langs() that indexes
# articles by typo in a global dictionary in the parent process
def tally_misspelled_words(result):
    if not result:
        return

    # For Wiktionary, which spell-checks each language for an entry
    # separately, and tracks the language name for sorting purposes
    if type(result) is list:
        for result_part in result:
            # Only useful for its side effects
            tally_misspelled_words(result_part)
        return

    (article_title, article_oops_list) = result
    global misspelled_words
    for word_mixedcase in article_oops_list:
        if is_chemical_formula(word_mixedcase):
            # Retain capitalization for correct word categorization later
            word_lower = word_mixedcase
        else:
            word_lower = word_mixedcase.lower()
        (freq, existing_list) = misspelled_words.get(word_lower, (0, []))
        existing_list.append(article_title)
        misspelled_words[word_lower] = (len(existing_list), existing_list)


if __name__ == '__main__':
    # Allow spell-checking a subset of articles based on the first letter of their titles, or all
    which_articles = "ALL"
    if len(sys.argv) > 1:
        which_articles = sys.argv[1]
    print(f"Spell checking articles: {which_articles}", file=sys.stderr)
    read_en_article_text(spellcheck_all_langs, process_result_callback=tally_misspelled_words, parallel="incremental", which_articles=which_articles)
    dump_results()
