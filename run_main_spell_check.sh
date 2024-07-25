#!/usr/bin/bash

set -e

# --- MAIN (WIKIPEDIA) SPELL CHECK ---

echo "Beginning main Wikipedia spell check"
echo `date`

../venv/bin/python3 ../moss_spell_check.py $1 > tmp-output.txt

echo "Beginning word categorization run 1"
echo `date`

# Run time for this segment: ~25 min (8-core parallel)
grep ^@ tmp-output.txt | sort -nr -k2 > /tmp/sorted_by_article.txt
# Sort takes ~37sec
cat /tmp/sorted_by_article.txt | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt
rm -rf /tmp/sorted_by_article.txt
# TODO: Can this run as one line, or is that the source of the .py command not found error?
# grep ^@ tmp-output.txt | sort -nr -k2 | ../venv/bin/python3 ../by_article_processor.py > tmp-articles-linked-words.txt

echo "Primary by-article post-processing"
echo `date`

cat tmp-articles-linked-words.txt | ../venv/bin/python3 ../make_main_listings.py > post-main-listings.txt

echo "Finished main Wikipedia spell check"
echo `date`
