#!/usr/bin/bash

# Run time for commit 4933ad4: 22h 00m (whata) +/- 10 min
# Run time for commit e20e070: 19h 47m (whata)
# Run time: 12h 38m (whata)
# Run time for commit e317dab: 3 hours (free-spin)

set -e

RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`

mkdir $RUN_NAME
venv/bin/python3 moss_spell_check.py > $RUN_NAME/tmp-output.txt

cd $RUN_NAME
grep ^@ tmp-output.txt | sort -nr -k2 > tmp-articles-with-words.txt
grep '^!' tmp-output.txt > debug-brackets.txt
grep '^I' tmp-output.txt | sort > debug-spellcheck-ignored.txt
cat tmp-articles-with-words.txt | grep -vP '^@\t0' | perl -pe 's/.*\t//' > tmp-misspelled-lists.txt
cat tmp-misspelled-lists.txt | perl -ne 'foreach $word (split(" ")) {print $word . "\n"}' > tmp-misspelled-words.txt
cat tmp-misspelled-words.txt | perl -pe 'print length($_) - 1; print "\t"' | sort -n > tmp-misspelled-words-charlen.txt
grep '^*' tmp-output.txt | tac > tmp-words-with-articles.txt

cat tmp-articles-with-words.txt | perl -pe 's/^@\t(\d+)\t(.*?)\t/* \1 - [[\2]] - /' > tmp-articles-linked-words.txt
grep -P ' - [a-z ]+$' tmp-articles-linked-words.txt | head -1000 > post-articles-with-most-misspelled-words.txt
grep -vP ' - [a-z ]+$' tmp-articles-linked-words.txt | head -1000 > debug-articles-with-most-misspelled-words-intl.txt
# TODO: Download titles only for Wikipedias for all languages, and
# include these in all_words lookup (might need to move to database
# instead of in-memory since this list will get extremely large) so
# -intl channels become useful.  (May also need to remove HTML
# entities and tags.)

tac tmp-articles-linked-words.txt | grep -P "\* 1 -" | grep -P ' - [a-z ]+$' | perl -pe 's/ - (\w+)$/ - [[wikt:\1]]/' > post-articles-with-single-typo.txt
tac tmp-articles-linked-words.txt | grep -P "\* 1 -" | grep -vP ' - [a-z ]+$' | perl -pe 's/ - (\w+)$/ - [[wikt:\1]]/' > debug-articles-with-single-typo-intl.txt

grep -P "\[\[wikt:[a-z]+\]\]" tmp-words-with-articles.txt | head -1000 | ../venv/bin/python3 ../summarizer.py --find-all > post-most-common-misspellings.txt
tac tmp-words-with-articles.txt | grep -P "\[\[wikt:[a-z]+\]\]" | head -1000 | ../venv/bin/python3 ../summarizer.py > post-least-common-misspellings.txt
grep -P "\[\[wikt:&" tmp-words-with-articles.txt | ../venv/bin/python3 ../summarizer.py --find-all > post-html-entities-by-freq.txt
grep -P "\[\[wikt:<" tmp-words-with-articles.txt | ../venv/bin/python3 ../summarizer.py --find-all > post-html-tags-by-freq.txt

cat tmp-words-with-articles.txt | grep -vP "\[\[wikt:[a-z]+\]\]" | grep -vP "\[\[wikt:&" | grep -vP "\[\[wikt:<" | head -1000 | ../venv/bin/python3 ../summarizer.py --find-all > debug-most-common-misspellings-intl.txt

# TODO: Link directly to articles where these words were detected
tac tmp-misspelled-words-charlen.txt | grep -P '\t[a-z]+$' | uniq | perl -pe 's%(\d+)\t(.*)$%* \1 [https://en.wikipedia.org/w/index.php?search=\2 \2]%' > post-longest-shortest-misspelled-words.txt
tac tmp-misspelled-words-charlen.txt | grep -vP '\t[a-z]+$' | uniq | perl -pe 's%(\d+)\t(.*)$%* \1 [https://en.wikipedia.org/w/index.php?search=\2 \2]%' > debug-longest-shortest-misspelled-words-intl.txt

# Generate stats
cat tmp-articles-linked-words.txt | ../venv/bin/python3 ../histogram_text.py > post-misspellings-per-article.txt
echo "Parse errors: " >> post-misspellings-per-article.txt
grep -P "!\tABORT" debug-brackets.txt | wc -l >> post-misspellings-per-article.txt
