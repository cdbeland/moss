set -e

echo "Running Wiktionary spell check"
echo `date`

../venv/bin/python3 ../moss_spell_check_wiktionary.py > tmp-wiktionary-spell.txt
# Run time: About 30 min

echo "Post-processing Wiktionary results"
echo `date`

tac tmp-wiktionary-spell.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles-wikt.txt
echo "==T1+ASCII==\n" > post-wikt-t1-ascii.txt
grep ^T1 tmp-words-with-articles-wikt.txt | grep -P '\[\[wikt:[a-z]+\]\]' | perl -pe "s/^T1\t//" >> post-wikt-t1-ascii.txt
grep ^HB tmp-words-with-articles-wikt.txt | perl -pe "s/^HB\t//" | perl -pe 's/</&lt;/g' | perl -pe 's/>/&gt;/g' > post-wikt-html.txt

echo "Done post-processing"
echo `date`
