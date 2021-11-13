#!/usr/bin/bash

# Run time for commit 2ec07e4: 4h30m to start of readability report,
#  5h50m overall (8-core parallel, big-bucks)
# Run time for commit 17ca7d3: ~4h to start of readability report,
#  5.5h overall (8-core parallel, big-bucks)
# Run time for commit c6ce3ab: ~26h (whata)
# Run time for commit 5e6b2ce: 21h 18m (whata)
# Run time for commit 10512ac: 23h 19m (whata)
# Run time for commit 4933ad4: 22h 00m (whata) +/- 10 min
# Run time for commit e20e070: 19h 47m (whata)
# Run time: 12h 38m (whata)
# Run time for commit e317dab: 3 hours (free-spin)

set -e

RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`
mkdir $RUN_NAME
cd $RUN_NAME

# --- HTML ENTITIES ---

echo "Beginning HTML entity check"
echo `date`

# Run time for this segment: ~45 min (8-core parallel)

# ../venv/bin/python3 ../moss_entity_check.py | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt
../venv/bin/python3 ../moss_entity_check.py > tmp-entities
cat tmp-entities | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt
# "Worst" report disabled because it's mostly [[MOS:STRAIGHT]]
# violations, which are not a priority.
# ../venv/bin/python3 ../moss_entity_check.py > tmp-entities.txt
# mv tmp-worst.txt post-entities.txt
# cat tmp-entities.txt | ../venv/bin/python3 ../summarizer.py --find-all >> post-entities.txt

# --- MAIN SPELL CHECK ---

# Run time for this segment: ~3h (8-core parallel)

echo "Beginning main spell check"
echo `date`

../venv/bin/python3 ../moss_spell_check.py > tmp-output.txt

# --- SPELL CHECK WORD CATEGORIZATION AND PARSE FAILURE POST-PROCESSING ---

echo "Beginning word categorization run 1"
echo `date`

# Run time for this segment: ~36 min (8-core parallel)
grep ^@ tmp-output.txt | sort -nr -k2 > /tmp/sorted_by_article.txt
# Sort takes ~37sec
cat /tmp/sorted_by_article.txt | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt
rm -rf /tmp/sorted_by_article.txt
# TODO: Can this run as one line, or is that the source of the .py command not found error?
# grep ^@ tmp-output.txt | sort -nr -k2 | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt

grep -P '^!\t' tmp-output.txt | perl -pe 's/.*?\t//' | sort > post-parse-failures.txt
grep -P '^\!Q' tmp-output.txt | perl -pe 's/^\!Q\t\* \[\[(.*?)\]\].*$/$1/' | sort | ../venv/bin/python3 ../sectionalizer.py LARGE > jwb-straight-quotes-unbalanced.txt
grep ^G tmp-output.txt | ../venv/bin/python3 ../rollup_ignored.py | sort -nr -k2 > debug-spellcheck-ignored.txt

echo "Beginning word categorization run 2"
echo `date`

# Run time for this line: ~30 min (8-core parallel)
tac tmp-output.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles.txt

# --- BY ARTICLE ---

echo "Beginning by-article post-processing"
echo `date`

# Run time for here to beginning of readability report: ~1 minute

cat tmp-articles-linked-words.txt | ../venv/bin/python3 ../make_main_listings.py > post-main-listings.txt

# Dealing with the remaining pile of typos:
# * Improve transliterate.py
#  * Valid word + hyphen + invalid word - probably a typo especially
#    if the invalid one is T1.  Maybe classify both sides?
# * Refine "A" category to require {{math}} be tagged but otherwise
#   allow forms in compliance with the Manual of Style?

# Also helps stats a lot:
# * Tagging articles for {{cleanup HTML}} from the appropriate report
# * Tagging articles with the most misspelled words with:
#   {{cleanup |reason=Need to use {{tl|lang}} to tag non-English words for consistent formatting, screen readers, and automated spell checkers}}
#   (probably the top 3000 or so articles with the most misspellings,
#   down to about 20 or so, though there are many mixed in at lower
#   frequencies)

head -50 tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' > beland-articles-most-typos-raw.txt
head -10000 tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | grep -P '^[\[\] \-\w\*,:]+$' | grep -v "List of drugs" | head -50 > beland-articles-most-typos-refined.txt

grep BW,BW,BW,BW,BW tmp-articles-linked-words.txt | grep wikt:you | grep -vP "\[\[[^\]]+ (grammar|languages?|dialect|tenses|phrases|pronoun|verbs|adjectives|syntax|contractions|prepositions|mood)\]\]" | grep -vP "(Latin indirect speech|WYSIWYG|Stress and vowel reduction in English|Wh-movement|Tag question|Southern American English|The Mad Magazine Game|Field sobriety testing|Cardiff English)" | head -50 | perl -pe 's/.*?\t//' > post-you.txt
# TODO: Suppression of language-related articles and specific titles
# can be relaxed once "you" and contractions can be ignored inside
# italics.

grep TF+la tmp-articles-linked-words.txt | grep species | perl -pe 's/^.*?\t\*/*/' | perl -pe 's/ - \[\[/ - \[\[w:/' | perl -pe 's/\[\[wikt:/\[\[/g' > beland-species1.txt
grep TF+la,TF+la tmp-articles-linked-words.txt | grep -v species | perl -pe 's/^.*?\t\*/*/' | grep -P "^[A-Za-z0-9,\[\]\*:\- \']+$" | perl -pe 's/ - \[\[/ - \[\[w:/' | perl -pe 's/\[\[wikt:/\[\[/g' > beland-species2.txt

# --- BY FREQUENCY ---

echo "Beginning by-frequency post-processing"
echo `date`

# Lots of correctly-classified typos have been fixed, so the below algorithms now are unreliable classifiers.
# grep -P '^(TS|ME)' tmp-words-with-articles.txt | grep -vP 'wikt:[^\]]+[\(\[\),\.]' | grep -vP "\w\]\w" | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-compound.txt
# grep ^T1 tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-edit1.txt
# grep -P '^(?!T1|TS|TE|P|D|C|H|U|BC|BW|N|Z|A|T/|L)' tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-new-words.txt
# So, just make one big pile...
grep -P '^(?!BC|BW|H|TS|A|Z|L|U|N|T/)' tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-all-words.txt

echo "===Known bad HTML tags (HB) ===" > post-html-by-freq.txt
echo "These are also included in the main listings." >> post-html-by-freq.txt
grep ^HB tmp-words-with-articles.txt | perl -pe 's/^HB\t//' | ../venv/bin/python3 ../summarizer.py --find-all >> post-html-by-freq.txt

echo >> post-html-by-freq.txt
echo "===Bad link formatting (HL) ===" >> post-html-by-freq.txt
echo "These are also included in the main listings." >> post-html-by-freq.txt
echo 'Angle brackets are not used for external links (per {{section link|Wikipedia:Manual of Style/Computing|Exposed_URLs}}); "tags" like <nowiki><https> and <www></nowiki> are actually just bad link formatting.' >> post-html-by-freq.txt
echo "See [[Wikipedia:External links#How to link]] for external link syntax; use {{tl|cite web}} for footnotes." >> post-html-by-freq.txt
grep ^HL tmp-words-with-articles.txt | perl -pe 's/^HL\t//' | ../venv/bin/python3 ../summarizer.py --find-all >> post-html-by-freq.txt

echo >> post-html-by-freq.txt
echo "===Unsorted (H) ===" >> post-html-by-freq.txt
echo "Many of these can be replaced by {{tl|var}} (for text to be replaced) or {{tl|angbr}} (e.g. for linguistic notation). Enclose in {{tag|code}} for inline software source code." >> post-html-by-freq.txt
grep -P '^H\t' tmp-words-with-articles.txt | perl -pe 's/^H\t//' | ../venv/bin/python3 ../summarizer.py --find-all | head -50 >> post-html-by-freq.txt

# TODO: Search for bad attributes on HTML tags:
#  https://en.wikipedia.org/wiki/Wikipedia:HTML_5#Table_attributes
#  https://en.wikipedia.org/wiki/Wikipedia:HTML_5#Other_obsolete_attributes


# Dealing with these types without posting, since they can all be
# fixed in one sitting
grep ^P tmp-words-with-articles.txt | perl -pe 's/^P\t//' > beland-pattern-by-freq.txt
grep ^D tmp-words-with-articles.txt | perl -pe 's/^D\t//' > beland-dna-by-freq.txt
grep ^N tmp-words-with-articles.txt | perl -pe 's/^N\t//'| grep -vP 'wikt:[\w-]+\]' > beland-punct-weirdness-by-freq.txt

# --- COLLECTION FOR POSTING ---

echo "Beginning collection"
echo `date`

# This just automates the collection of some of the above output files
# into a single file for posting to the moss project page.

../venv/bin/python3 ../collect.py > collected_by_article_and_freq.txt

# --- ARTICLES THAT NEED {{copyedit}} ---

grep -v "TF+" tmp-articles-linked-words.txt | grep -vP "(U|BC|Z)," | grep -v "&gt;" | grep -P "[a-z][\,\.][A-z]" | grep -v "* [0123456] -" | perl -pe 's/\[\[wikt:(.*?)\]\]/"\1"/g' | perl -pe 's/.*?\t//' | grep -vP '[a-zA-Z][\(\)\[\]][A-Za-z]' > post-copyedit.txt

# --- BY WORD LENGTH ---

echo "Beginning by-length post-processing"
echo `date`

cat tmp-words-with-articles.txt | ../venv/bin/python3 ../charlen_extractor.py | sort -k3 -nr > tmp-misspelled-words-charlen-cat.txt

echo "=== Possible typos by length ==="  > collected_by_length.txt
echo "Longest or shortest in certain categories are shown, sometimes just for fun and sometimes because they form a useful group. Please use strikethrough (or leave a note) for this section rather than removing lines, to avoid repeating work done while the dumps were being processed. Thanks!" >> collected_by_length.txt
echo "" >> collected_by_length.txt

echo "==== Likely chemistry words ====" >> collected_by_length.txt
echo "These need to be checked by a chemist and marked as {{tl|not a typo}}." >> collected_by_length.txt
grep ^C tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^C\t//' | head -20 >> collected_by_length.txt
echo "" >> collected_by_length.txt

echo "==== Missing articles on single characters ====" >> collected_by_length.txt
echo "" >> collected_by_length.txt
echo "Every character should either have a Wikipedia article, redirect to a Wikipedia article, or Wiktionary entry." >> collected_by_length.txt
echo "" >> collected_by_length.txt
grep -P '^I\t\* 1 -' tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^I\t//' >> collected_by_length.txt
echo "" >> collected_by_length.txt

# --- STATS ---

echo "Beginning stats"
echo `date`

echo "Possible typos per article: " > post-stats.txt
cat tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../histogram_text.py >> post-stats.txt
echo "Parse errors: " >> post-stats.txt
wc -l post-parse-failures.txt >> post-stats.txt
echo "Parse errors with [[MOS:STRAIGHT]] violations:" >> post-stats.txt
wc -l jwb-straight-quotes-unbalanced.txt >> post-stats.txt
echo "Possible typos by type: " >> post-stats.txt
cat tmp-words-with-articles.txt | ../venv/bin/python3 ../count_by_rating.py >> post-stats.txt


# --- DASHES ---

echo "Beginning dash report"
echo `date`

grep ^D tmp-output.txt | perl -pe 's/^D\t'// | sort -k3 | ../venv/bin/python3 ../sectionalizer.py > debug-dashes.txt
# TODO: Are spaced emdashes more common than unspaced?  I like them
# better but they go against the style guide. -- Beland
#
# grep line counts from enwiki-latest-pages-articles-multistream.xml:
# "—"      4148695
# " — "    1340803
# "\w—\w"   486271
#
# -> Write some code to run a report that accumulates info on what
#    characters exactly are before and after (count before and after
#    separately, or else there are too many combinations)


# --- READABILITY ---

echo "Beginning readability check"
echo `date`

# Run time for this segment: 1h (8-core parallel)

../venv/bin/python3 ../moss_readability_check.py > tmp-readability.txt
sort -k2 -n tmp-readability.txt > post-readability.txt
rm tmp-readability.txt

# --- SUPERSCRIPTS AND SUBSCRIPTS ---

# Run time for this segment: ~11 min (8-core parallel)

echo "Beginning superscript/subscript audit"
../superscripts.sh

echo "Done"
echo `date`

# --- CHEMICAL FORMULAS ---

echo "Starting chemical formulas report"
echo `date`
echo "====Possible chemical formulas that don't use subscripts====" > beland-chemical-formulas.txt
grep -P ' ((H|He|Li|Be|B|C|N|O|F|Ne|Na|Mg|Al|Si|P|S|Cl|Ar|K|Ca|Sc|Ti|V|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Y|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|I|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|W|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|U|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|R)([2-9]|[1-9][0-9]))+$' debug-spellcheck-ignored.txt | grep -vP ' [KQRBNP][a-h][1-8]$' | grep -vP ' [A-Z]\d\d$' | head -100 >> beland-chemical-formulas.txt
# [KQRBNP][a-h][1-8] is to exclude [[Algebraic notation (chess)]]

echo "" >> beland-chemical-formulas.txt
echo "====Known chemical formulas that don't use subscripts====" >> beland-chemical-formulas.txt
../venv/bin/python3 ../chemical_formula_report.py >> beland-chemical-formulas.txt

echo "Done"
echo `date`
