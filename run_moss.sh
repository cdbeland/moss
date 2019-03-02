#!/usr/bin/bash

# Run time for commit c6ce3ab: ~26h (whata)
# Run time for commit 5e6b2ce: 21h 18m (whata)
# Run time for commit 10512ac: 23h 19m (whata)
# Run time for commit 4933ad4: 22h 00m (whata) +/- 10 min
# Run time for commit e20e070: 19h 47m (whata)
# Run time: 12h 38m (whata)
# Run time for commit e317dab: 3 hours (free-spin)

set -e

# --- MAIN SPELL CHECK ---

# Run time for this segment: ~26h 07m

echo "Beginning main spell check"
echo `date`

RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`

mkdir $RUN_NAME
venv/bin/python3 moss_spell_check.py > $RUN_NAME/tmp-output.txt

cd $RUN_NAME

# --- SPELL CHECK WORD CATEGORIZATION AND PARSE FAILURE POST-PROCESSING ---

echo "Beginning word categorization run 1"
echo `date`

# Run time for this segment: ~3h 25m
grep ^@ tmp-output.txt | sort -nr -k2 > /tmp/sorted_by_article.txt
cat /tmp/sorted_by_article.txt | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt
rm -rf /tmp/sorted_by_article.txt
# TODO: Can this run as one line, or is that the source of the .py command not found error?
# grep ^@ tmp-output.txt | sort -nr -k2 | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt

grep '^!' tmp-output.txt | perl -pe 's/.*?\t//' | sort > post-parse-failures.txt
# grep '^G' tmp-output.txt | sort > debug-spellcheck-ignored.txt  # Not currently used, may reactivate in future

echo "Beginning word categorization run 2"
echo `date`

# Run time for this line: ~2h 23m
tac tmp-output.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles.txt

# --- BY ARTICLE ---

echo "Beginning by-article post-processing"
echo `date`

# Run time for here to beginning of HTML tag report: ~2 minutes

grep -P "^T1(,T1)*\t" tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-edit1.txt
grep -P "^T[12](,T[12])*\t" tmp-articles-linked-words.txt | grep T2 | grep T1 | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-edit1+2.txt
grep -P "^T[123](,T[123])*\t" tmp-articles-linked-words.txt | grep T3 | grep T1 | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-edit1+3.txt
grep -P "^TS(,TS)*\t" tmp-articles-linked-words.txt | grep 'wikt:.*\.'| perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-TS+dot.txt

# TODO: Once these are done, post:
# (these require deactivating the above to prevent overlap)
# * grep -P "^TS(,TS)*\t" tmp-articles-linked-words.txt | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-TS.txt
# * grep -P "^T[1S](,T[1S])*\t" tmp-articles-linked-words.txt | grep T1 | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-TS_edit1.txt
# * grep -P "^T[12S](,T[12S])*\t" tmp-articles-linked-words.txt | grep T2 | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-TS_edit2.txt
# * grep -P "^T[123S](,T[123S])*\t" tmp-articles-linked-words.txt | grep T3 | perl -pe 's/^.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-TS_edit3.txt
#
# * Enhance word_categorizer.py or moss_spell_check.py to look at all
#   Wiktionaries and only leave words that don't appear in any
#   language's dictionary (though all should appear in the English
#   dictionary of all languages).  Possibly produce lists of untagged
#   words by language, so people interested in those languages can go
#   tag the English articles?  Produce most-common lists for English
#   Wikipedia definition writers.
# * If this is too expensive, try:
#   * T1/T2/T3 mixed in with all other T#, segratating the higher T#s,
#     starting with articles with the lowest number of typos?
#   * (T4 are hardly ever misspellings, don't post those)
# Also helps stats a lot:
# * Tagging articles for {{cleanup HTML}} from the appropriate report
# * Tagging articles with the most misspelled words with:
#   {{cleanup |reason=Need to use {{tl|lang}} to tag non-English words so screen readers and automated spell check will work}}
#   (probably the top 3000 or so articles with the most misspellings,
#   down to about 20 or so, though there are many mixed in at lower
#   frequencies)


# grep -P "^TS(,TS)*\t" tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../sectionalizer.py > post-by-article-compound.txt
# Posting by-frequency instead, to avoid mixing in whitespace errors

head -200 tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' > beland-articles-most-typos-raw.txt
head -1000 tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | grep -P '^[\[\] \-\w\*,:]+$' | head -200 > beland-articles-most-typos-refined.txt

# --- BY FREQUENCY ---

echo "Beginning by-frequency post-processing"
echo `date`

grep ^TS tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-compound.txt
grep ^T1 tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-edit1.txt
grep -P '^(?!T1|TS|I|P|D|C)' tmp-words-with-articles.txt | head -200 | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > tmp-most-common-new-words.txt

echo "===Known bad HTML tags===" > beland-html-by-freq.txt
grep ^HB tmp-words-with-articles.txt | perl -pe 's/^HB\t//' | ../venv/bin/python3 ../summarizer.py --find-all >> beland-html-by-freq.txt

echo >> beland-html-by-freq.txt
echo "===Bad link formatting===" >> beland-html-by-freq.txt
echo 'Angle brackets are not used for external links (per {{section link|Wikipedia:Manual of Style/Computing|Exposed_URLs}}); "tags" like <nowiki><https> and <www></nowiki> are actually just bad link formatting.' >> beland-html-by-freq.txt
echo "See [[Wikipedia:External links#How to link]] for external link syntax; use {{tl|cite web}} for footnotes." >> beland-html-by-freq.txt
grep ^HL tmp-words-with-articles.txt | perl -pe 's/^HL\t//' | ../venv/bin/python3 ../summarizer.py --find-all >> beland-html-by-freq.txt

echo >> beland-html-by-freq.txt
echo "===Unsorted===" >> beland-html-by-freq.txt
grep -P '^H\t' tmp-words-with-articles.txt | perl -pe 's/^H\t//' | ../venv/bin/python3 ../summarizer.py --find-all >> beland-html-by-freq.txt

# TODO: Search for bad attributes on HTML tags:
#  https://en.wikipedia.org/wiki/Wikipedia:HTML_5#Table_attributes
#  https://en.wikipedia.org/wiki/Wikipedia:HTML_5#Other_obsolete_attributes


# Dealing with these types without posting, since they can all be
# fixed in one sitting
grep ^P tmp-words-with-articles.txt | perl -pe 's/^P\t//' > beland-pattern-by-freq.txt
grep ^D tmp-words-with-articles.txt | perl -pe 's/^P\t//' > beland-dna-by-freq.txt

grep ^I tmp-words-with-articles.txt | grep -vP "\[\[wikt:&" | grep -vP "\[\[wikt:<" | head -200 > tmp-words-with-articles-truncated.txt
cat tmp-words-with-articles-truncated.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../summarizer.py --find-all > debug-most-common-misspellings-intl.txt
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

echo "Beginning collection"
echo `date`

# This just automates the collection of some of the above output files
# into a single file for posting to the moss project page.

../venv/bin/python3 ../collect.py > collected_by_article_and_freq.txt

# --- BY WORD LENGTH ---

echo "Beginning by-length post-processing"
echo `date`

cat tmp-words-with-articles.txt | ../venv/bin/python3 ../charlen_extractor.py | sort -k3 -nr > tmp-misspelled-words-charlen-cat.txt

echo "=== Possible typos by length ==="  > collected_by_length.txt
echo "Longest or shortest in certain categories are shown, sometimes just for fun and sometimes because they form a useful group. Please use strikethrough (or leave a note) for this section rather than removing lines, to avoid repeating work done while the dumps were being processed. Thanks!" >> collected_by_length.txt
echo "" >> collected_by_length.txt

# Redundant to by-article and by-frequency
# echo "==== Likely misspellings (longest) ====" >> collected_by_length.txt
# grep -P "^T1\t" tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^T1\t//' | head -20 >> collected_by_length.txt

# Redundant to by-article
# echo "==== Likely missing whitespace ====" >> collected_by_length.txt
# grep ^TS tmp-misspelled-words-charlen-cat.txt | perl -pe 's/^TS\t//' | head -200 >> collected_by_length.txt
# echo "" >> collected_by_length.txt

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

# --- STATS ---

echo "Beginning stats"
echo `date`

echo "Possible typos per article: " > post-stats.txt
cat tmp-articles-linked-words.txt | perl -pe 's/.*?\t//' | ../venv/bin/python3 ../histogram_text.py >> post-stats.txt
echo "Parse errors: " >> post-stats.txt
wc -l post-parse-failures.txt >> post-stats.txt

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


# --- HTML ENTITIES ---

echo "Beginning HTML entity check"
echo `date`

# Run time for this segment: ~2h

../venv/bin/python3 ../moss_entity_check.py > tmp-entities.txt

# Separate operations to avoid "broken pipe" error.
cat tmp-entities.txt | ../venv/bin/python3 ../summarizer.py --find-all > tmp-entities-summarized.txt
head -1000 tmp-entities-summarized.txt > post-entities.txt

echo "Done"
echo `date`
