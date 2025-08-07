#!/usr/bin/bash

set -e

echo "Thread 2 starting"
echo `date`

# Run time: About 1 hour 10 min (8-core parallel) when nothing else is running
../run_wiktionary_spell_check.sh >& wiktionary.log

# Run time: About 25 hours (8-core parallel) while other thread is running
../run_main_spell_check.sh >& main_spell_check.log

echo "Failure post-processing"
echo `date`

grep -P '^!\t' tmp-output.txt | perl -pe 's/.*?\t//' | sort > err-parse-failures.txt
grep -P '^\!Q' tmp-output.txt | perl -pe 's/^\!Q\t\* \[\[(.*?)\]\].*$/$1/' | sort > jwb-straight-quotes-unbalanced.txt
grep ^G tmp-output.txt | ../venv/bin/python3 ../rollup_ignored.py | sort -nr -k2 > debug-spellcheck-ignored.txt

echo "Beginning word categorization run 2"
echo `date`

# Run time for this line: ~20 min (8-core parallel)
tac tmp-output.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles.txt

# --- BY ARTICLE ---

# Fast
echo "Secondary by-article post-processing"
echo `date`

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

grep BW,BW,BW,BW,BW tmp-articles-linked-words.txt | grep wikt:you | head -50 | perl -pe 's/.*?\t//' > post-you.txt

grep TF+la tmp-articles-linked-words.txt | grep species | perl -pe 's/^.*?\t\*/*/' | perl -pe 's/ - \[\[/ - \[\[w:/' | perl -pe 's/\[\[wikt:/\[\[/g' > beland-species1.txt
grep TF+la,TF+la tmp-articles-linked-words.txt | grep -v species | perl -pe 's/^.*?\t\*/*/' | grep -P "^[A-Za-z0-9,\[\]\*:\- \']+$" | perl -pe 's/ - \[\[/ - \[\[w:/' | perl -pe 's/\[\[wikt:/\[\[/g' > beland-species2.txt

# --- BY FREQUENCY ---

# Fast
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

# Fast
echo "Beginning collection"
echo `date`

# This just automates the collection of some of the above output files
# into a single file for posting to the moss project page.

../venv/bin/python3 ../collect.py > collected_by_article_and_freq.txt

# --- ARTICLES THAT NEED {{copyedit}} ---

# Fast
echo "Beginning copyedit collection..."
echo `date`

grep -v "TF+" tmp-articles-linked-words.txt | grep -vP "(U|BC|Z)," | grep -v "&gt;" | grep -P "[a-z][\,\.][A-z]" | grep -v "* [0123456] -" | perl -pe 's/\[\[wikt:(.*?)\]\]/"\1"/g' | perl -pe 's/.*?\t//' | grep -vP '[a-zA-Z][\(\)\[\]][A-Za-z]' > post-copyedit.txt

# --- PARSE FAILURE FIXES ---

# Run time: About 4 hours
echo "Beginning foot/inch conversion scan"
echo `date`

# Feet and inches - [[MOS:UNITNAMES]]

### TODO: This also needs to handle {{frac}} in place of pure digits
# {{s?frac|[0-9]+|[0-9]+(|[0-9]+)?}}
# Integrate with moss_check_style_by_line.py ?

grep -P "[0-9\.]+(&nbsp;| )?'[0-9\.]+(&nbsp;| ) ?\"[^0-9\.]" err-parse-failures.txt | grep -v ° > tmp-feet-inches1.txt
grep -P '[0-9\.]+"(&nbsp;| )?(x|by|×)(&nbsp;| )?[0-9\./]+"' err-parse-failures.txt > tmp-feet-inches2.txt
grep -P '[0-9\.]+"' err-parse-failures.txt > tmp-feet-inches3.txt
cat tmp-feet-inches2.txt tmp-feet-inches1.txt tmp-feet-inches3.txt | perl -pe 's/^\* \[\[(.*?)\]\] - .*$/$1/' | uniq > jwb-feet-inches-err.txt
../venv/bin/python3 ../dump_grep_csv.py "[0-9\.]+(&nbsp;| )?'[0-9\.]+(&nbsp;| ) ?\"[^0-9\.]" > tmp-feet-inches-all1.txt
../venv/bin/python3 ../dump_grep_csv.py '[0-9\.]+"(&nbsp;| )?(x|by|×)(&nbsp;| )?[0-9\./]+"' > tmp-feet-inches-all2.txt
../venv/bin/python3 ../dump_grep_csv.py ' [^"][0-9]"' tmp-feet-inches-all3.txt | perl -pe 's/<.*?>//g' | perl -pe 's/[\( \|]"[a-zA-Z][^"]*[0-9]"//g' | perl -pe 's/"[0-9\.]+"//g' | grep -P '[0-9]"' > tmp-feet-inches-all3.txt
cat tmp-feet-inches-all2.txt tmp-feet-inches-all1.txt tmp-feet-inches-all3.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-feet-inches-all.txt

# Units of arc - [[MOS:UNITNAMES]]
grep -P "[0-9]+° ?[0-9]+' ?[0-9]+\"" err-parse-failures.txt | perl -pe 's/^\* \[\[(.*?)\]\] - .*$/$1/' | sort | uniq > jwb-arc-units.txt
../venv/bin/python3 ../dump_grep_csv.py "[0-9]+° ?[0-9]+' ?[0-9]+\"" > tmp-arc-units-all.txt
cat tmp-arc-units-all.txt | perl -pe 's/^(.*?):.*/$1/' | sort | uniq >> jwb-arc-units.txt

# See also: jwb-straight-quotes-unbalanced.txt

# TODO (enhances semantic web, gives readers a clickable link, but doesn't resolve parse failures):
# Consider scanning for lat/lon with:
#  ([0-9]+)° ?([0-9]+)(′|\{\{prime\}\}) ?([0-9]+)(″|\{\{pprime\}\}) ?(N|S) ([0-9]+)° ?([0-9]+)(′|\{\{prime\}\}) ?([0-9]+)(″|\{\{pprime\}\}) ?(E|W)
# and substituting:
#  {{coord|$1|$2|$4|$6|$7|$8|$10|$12|display=inline}}

# --- BY WORD LENGTH ---

# Fast
echo "Beginning by-length post-processing"
echo `date`

cat tmp-words-with-articles.txt | ../venv/bin/python3 ../charlen_extractor.py | sort -k3 -nr > tmp-misspelled-words-charlen-cat.txt

echo "=== Possible typos by length ==="  > collected_by_length.txt
echo "Longest or shortest in certain categories are shown, sometimes just for fun and sometimes because they form a useful group. Feel free to delete articles that are fixed or tagged." >> collected_by_length.txt
echo "" >> collected_by_length.txt

echo "==== Likely chemistry words ====" >> collected_by_length.txt
echo "These need to be checked by a chemist and redirect created (if article exists) or marked as {{tl|chem name}} (if no article exists)." >> collected_by_length.txt
grep ^CN tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^CN\t//' | head -30 >> collected_by_length.txt
echo "" >> collected_by_length.txt

echo "==== Missing articles on single characters ====" >> collected_by_length.txt
echo "" >> collected_by_length.txt
echo "Every character should either have a Wikipedia article, redirect to a Wikipedia article, or Wiktionary entry." >> collected_by_length.txt
echo "" >> collected_by_length.txt
grep -P '^I\t\* 1 -' tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^I\t//' >> collected_by_length.txt
echo "" >> collected_by_length.txt

# --- STATS ---

# Fast
echo "Beginning stats"
echo `date`

echo "Possible typos per article: " > post-stats.txt
cat tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../histogram_text.py >> post-stats.txt
echo "Parse errors: " >> post-stats.txt
wc -l err-parse-failures.txt >> post-stats.txt
echo "Parse errors with [[MOS:STRAIGHT]] violations:" >> post-stats.txt
wc -l jwb-straight-quotes-unbalanced.txt >> post-stats.txt
echo "Possible typos by type: " >> post-stats.txt
cat tmp-words-with-articles.txt | ../venv/bin/python3 ../count_by_rating.py >> post-stats.txt


# --- DASHES ---

# Fast
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

# --- CHEMICAL FORMULAS ---

# Fast
echo "Starting chemical formulas report"
echo `date`
echo "====Possible chemical formulas that don't use subscripts====" > post-chemical-formulas.txt

grep ^CF tmp-words-with-articles.txt | grep -P "wikt:[^\]]*[0-9]" | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-all-cf-num.txt

# TODO: Use word_categorizer.chem_re here in a Python filtering script
grep -P "chem|compounds|acid|ferr|oxy|ide\]\]|ate\]\]|materials|alloy|mono|hydro|pent|hex|hept|nona|deca|ium\]\]|[hntkp]yl|fluor|chlor|cyclo|poly|iso" tmp-all-cf-num.txt >> post-chemical-formulas.txt

echo "" >> post-chemical-formulas.txt
echo "====Known chemical formulas that don't use subscripts====" >> post-chemical-formulas.txt
echo "" >> post-chemical-formulas.txt

echo "Starting slow chemical formulas report"
echo `date`
# Run time: About 1.2 h
../venv/bin/python3 ../chemical_formula_report.py >> post-chemical-formulas.txt
echo "Done slow chemical formulas report"
echo `date`


# Run time: About 6.5 hours
echo "Beginning not-English check"
echo `date`

../run_not_english.sh >& not_english.log


echo "Beginning superscript/subscript check"
echo `date`

../superscripts.sh >& superscripts.log

echo "Done."
echo `date`
