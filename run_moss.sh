#!/usr/bin/bash

# Run time for commit 5e6b2ce: 21h 18m (whata)
# Run time for commit 10512ac: 23h 19m (whata)
# Run time for commit 4933ad4: 22h 00m (whata) +/- 10 min
# Run time for commit e20e070: 19h 47m (whata)
# Run time: 12h 38m (whata)
# Run time for commit e317dab: 3 hours (free-spin)

set -e

# --- MAIN SPELL CHECK ---

echo "Beginning main spell check"
echo `date`

RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`

mkdir $RUN_NAME
venv/bin/python3 moss_spell_check.py > $RUN_NAME/tmp-output.txt

cd $RUN_NAME

# --- SPELL CHECK WORD CATEGORIZATION AND PARSE FAILURE POST-PROCESSING ---

echo "Beginning word categorization run 1"
echo `date`

# Run time for this segment: 4h+
grep ^@ tmp-output.txt | sort -nr -k2 > /tmp/sorted_by_article.txt
cat /tmp/sorted_by_article.txt | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt
rm -rf /tmp/sorted_by_article.txt
# TODO: Can this run as one line, or is that the source of the .py command not found error?
# grep ^@ tmp-output.txt | sort -nr -k2 | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt

grep '^!' tmp-output.txt | perl -pe 's/.*\t//' | sort > post-parse-failures.txt
# grep '^G' tmp-output.txt | sort > debug-spellcheck-ignored.txt  # Not currently used, may reactivate in future

echo "Beginning word categorization run 2"
echo `date`

# Run time for this line: ~2h 45m
tac tmp-output.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles.txt

# --- BY ARTICLE ---

echo "Beginning by-article post-processing"
echo `date`

# TODO: Post other useful patterns once these are done (e.g. mix in T2s)
grep -P "^T1(,T1)*\t" tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > tmp-by-article-edit1.txt

# grep -P "^TS(,TS)*\t" tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-compound.txt
# Posting by-frequency instead, to avoid mixing in whitespace errors

head -200 tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' > beland-articles-most-typos-raw.txt


# --- BY FREQUENCY ---

grep ^TS tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-compound.txt
grep ^T1 tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-edit1.txt
grep -P '^(?\!T1|TS|I|P|D|C)' tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-new-words.txt

grep -P "\[\[wikt:<" tmp-words-with-articles.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all | grep -v "<nowiki></" | head -200 > post-html-tags-by-freq.txt
# Skip </xxx> tags because they duplicate <xxx> tags.

grep ^I tmp-words-with-articles.txt | grep -vP "\[\[wikt:&" | grep -vP "\[\[wikt:<" | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > debug-most-common-misspellings-intl.txt
# TODO for intl:
# * Separate words into the scripts they use:
#  -> See https://en.wikipedia.org/wiki/Wikipedia:Language_recognition_chart
# * Start with an easy-to-identify language (like Hebrew, Arabic,
#   Korean, Japanese, Chinese, German [with ß])
# * Download all Wikipedias and Wiktionaries (titles only) for
#   languages that use this script
# * Produce a list of words from this language which might be typos or
#   might need to be added to the English or non-English Wiktionary or
#   Wikipedia.
# * If there's no way to distinguish proper nouns in a language, we
#   may just need to ignore all text from that language so we don't
#   alert on non-notable proper names.  But do such entities deserve
#   translation in the English Wikipedia?  If so, it would be nice to
#   have editors manually check the spelling of such words and add
#   {{proper name}} to those instances.  Though we don't do that for
#   English proper names.

# --- COLLECTION FOR POSTING ---

# This just automates the collection of some of the above output files
# into a single file for posting to the moss project page.

../venv/bin/python3 ../collect.py > collected_by_article_and_freq.txt

# --- BY WORD LENGTH ---

cat tmp-words-with-articles.txt | ../venv/bin/python3 ../charlen_extractor.py | sort -k3 -nr > tmp-misspelled-words-charlen-cat.txt

echo "=== Possible typos by length ==="  > collected_by_length.txt
echo "Longest or shortest in certain categories are shown, sometimes just for fun and sometimes because they form a useful group. Please use strikethrough (or leave a note) for this section rather than removing lines, to avoid repeating work done while the dumps were being processed. Thanks!" >> collected_by_length.txt
echo "" >> collected_by_length.txt

# Redundant to by-article and by-frequency
# echo "==== Likely misspellings (longest) ====" >> collected_by_length.txt
# grep -P "^T1\t" tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^T1\t//' | head 20 >> collected_by_length.txt

echo "==== Likely missing whitespace ====" >> collected_by_length.txt
grep ^TS tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^TS\t//' | head -20 >> collected_by_length.txt

echo "" >> collected_by_length.txt
echo "==== Likely chemistry words ====" >> collected_by_length.txt
grep ^C tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^C\t//' | head -20 >> collected_by_length.txt
echo "" >> collected_by_length.txt

echo "==== Missing articles on single characters ====" >> collected_by_length.txt
echo "" >> collected_by_length.txt
echo "Every character should either have a Wikipedia article, redirect to a Wikipedia article, or Wiktionary entry." >> collected_by_length.txt
echo "" >> collected_by_length.txt
grep -P '^I\t\* 1 -' tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^I\t//' >> collected_by_length.txt
echo "" >> collected_by_length.txt

# Mix of foreign words and whitespace problems; redundant to
# by-article so skipping for now.
# grep -P "^T(?\!1\t)\d+" tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^.*?\t//' > post-longest-shortest-other.txt

# Skipping in favor of most-common-misspellings-intl (see below)
# grep '^[IN]' tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^[IN]\t//' > post-longest-shortest-intl.txt

# Dealing with these types offline, since they can all be fixed
grep ^P tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^P\t//' > beland-longest-shortest-pattern.txt
grep ^D tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^D\t//' > beland-longest-shortest-dna.txt

# --- STATS ---

cat tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../histogram_text.py > post-misspellings-per-article.txt
echo "Parse errors: " >> post-misspellings-per-article.txt
wc -l post-parse-failures.txt >> post-misspellings-per-article.txt

# --- HTML ENTITIES ---

echo "Beginning HTML entity check"
echo `date`

# Run time for this segment: ~2h

../venv/bin/python3 ../moss_entity_check.py > tmp-entities.txt
cat tmp-entities.txt | ../venv/bin/python3 ../summarizer.py --find-all | head -1000 > post-entities.txt

echo "Done"
echo `date`
