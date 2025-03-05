set -e

# TODO
# * Sort by language (suggested by Wiktionary User:Jberkel)
#   -> Look for most recent language-specific header?

echo "Running Wiktionary spell check"
echo `date`

../venv/bin/python3 ../moss_spell_check_wiktionary.py > tmp-wiktionary-spell.txt
# Run time: About 30 min

../venv/bin/python3 ../moss_spell_check_wiktionary_with_quotations.py > tmp-wiktionary-spell-with-quotations.txt
# Run time: About 30 min

# --- WITHOUT QUOTATIONS ---

echo "Post-processing Wiktionary results"
echo `date`

# Few if any English misspellings: H, BW, TF, T/, A, BC, P, L

tac tmp-wiktionary-spell.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles-wikt.txt

echo "==Possible typos from (DUMP NAME) ==" > post-wikt-typos.txt

echo "===T1+ASCII===" > post-wikt-typos.txt
echo "Possible English-language typos." >> post-wikt-typos.txt
echo '{| class="wikitable sortable"' >> post-wikt-typos.txt
echo "|-" >> post-wikt-typos.txt
echo "! Typo freq" >> post-wikt-typos.txt
echo "! Possible typo" >> post-wikt-typos.txt
echo "! Pages" >> post-wikt-typos.txt
grep ^T1 tmp-words-with-articles-wikt.txt | grep -P '\[\[wikt:[a-z]+\]\]' | perl -pe 's/^T1\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> post-wikt-typos.txt
echo "|}" >> post-wikt-typos.txt
echo >> post-wikt-typos.txt

echo "===ME===" >> post-wikt-typos.txt
echo "Probable English-language compounds (with and without hyphen)." >> post-wikt-typos.txt
echo '{| class="wikitable sortable"' >> post-wikt-typos.txt
echo "|-" >> post-wikt-typos.txt
echo "! Typo freq" >> post-wikt-typos.txt
echo "! Possible typo" >> post-wikt-typos.txt
echo "! Pages" >> post-wikt-typos.txt
grep ^ME tmp-words-with-articles-wikt.txt | perl -pe 's/^ME\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> post-wikt-typos.txt
echo "|}" >> post-wikt-typos.txt
echo >> post-wikt-typos.txt

echo "===TE===" >> post-wikt-typos.txt
echo "Possible English-language typos." >> post-wikt-typos.txt
echo >> post-wikt-typos.txt
echo '{| class="wikitable sortable"' >> post-wikt-typos.txt
echo "|-" >> post-wikt-typos.txt
echo "! Typo freq" >> post-wikt-typos.txt
echo "! Possible typo" >> post-wikt-typos.txt
echo "! Pages" >> post-wikt-typos.txt
grep ^TE tmp-words-with-articles-wikt.txt | perl -pe 's/^TE\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> post-wikt-typos.txt
echo "|}" >> post-wikt-typos.txt
echo >> post-wikt-typos.txt

echo "===C===" >> post-wikt-typos.txt
echo "Chemistry-related words." >> post-wikt-typos.txt
echo >> post-wikt-typos.txt
echo '{| class="wikitable sortable"' >> post-wikt-typos.txt
echo "|-" >> post-wikt-typos.txt
echo "! Typo freq" >> post-wikt-typos.txt
echo "! Possible typo" >> post-wikt-typos.txt
echo "! Pages" >> post-wikt-typos.txt
grep ^C tmp-words-with-articles-wikt.txt | perl -pe 's/^C\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> post-wikt-typos.txt
echo "|}" >> post-wikt-typos.txt
echo >> post-wikt-typos.txt

echo "===TS===" >> post-wikt-typos.txt
echo "These are suspected whitespace errors." >> post-wikt-typos.txt
echo >> post-wikt-typos.txt
echo >> post-wikt-typos.txt
echo '{| class="wikitable sortable"' >> post-wikt-typos.txt
echo "|-" >> post-wikt-typos.txt
echo "! Typo freq" >> post-wikt-typos.txt
echo "! Possible typo" >> post-wikt-typos.txt
echo "! Pages" >> post-wikt-typos.txt
grep ^TS tmp-words-with-articles-wikt.txt | perl -pe 's/^TS\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> post-wikt-typos.txt
echo "|}" >> post-wikt-typos.txt
echo >> post-wikt-typos.txt

# --- WITH QUOTATIONS ---

# Run time: About 10 min
tac tmp-wiktionary-spell-with-quotations.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles-wikt-with-quotations.txt

grep -P "^(HB|HL)" tmp-words-with-articles-wikt-with-quotations.txt | perl -pe "s/^HB\t//" | perl -pe 's/</&lt;/g' | perl -pe 's/>/&gt;/g' | grep -v "Unsupported titles/HTML" > post-wikt-html-with-quotations.txt

grep -vP "^(HB|HL|BW|BC|H|TS)" tmp-words-with-articles-wikt-with-quotations.txt | perl -pe "s/^.*?\t//" | grep -v "(" | grep -v ")" | sort -rn -k2 | head -50 > post-wikt-most-wanted-with-quotations.txt

echo "Done post-processing"
echo `date`
