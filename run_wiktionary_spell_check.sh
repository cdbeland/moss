set -e

echo "Running Wiktionary spell check"
echo `date`

../venv/bin/python3 ../moss_spell_check_wiktionary.py > tmp-wiktionary-spell.txt
# Run time: About 8 min (big-board SSD)

../venv/bin/python3 ../moss_spell_check_wiktionary_with_quotations.py > tmp-wiktionary-spell-with-quotations.txt
# Run time: About 8 min (big-board SSD)

# --- WITHOUT QUOTATIONS ---

echo "Post-processing Wiktionary results"
echo `date`

# Few if any English misspellings: H, BW, TF, T/, A, BC, P, L

tac tmp-wiktionary-spell.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles-wikt.txt

# TODO: Permute "box(es)" and "box[es]" into "box" and "boxes", so
# removal of unmatched ()[] are not necessary here and elsewhere.
cat tmp-words-with-articles-wikt.txt | grep -vP "wikt:[^\]]*[\(\)]" | grep -viP '[a-z: ][\]\[][a-z ]' > tmp-words-with-articles-wikt-filtered.txt

echo "==Possible typos from (DUMP NAME) ==" > tmp-wikt-typos.txt

echo "===T1+ASCII===" > tmp-wikt-typos.txt
echo "Possible English-language typos." >> tmp-wikt-typos.txt
echo '{| class="wikitable sortable"' >> tmp-wikt-typos.txt
echo "|-" >> tmp-wikt-typos.txt
echo "! Typo freq" >> tmp-wikt-typos.txt
echo "! Possible typo" >> tmp-wikt-typos.txt
echo "! Pages" >> tmp-wikt-typos.txt
echo "! Language" >> tmp-wikt-typos.txt
grep ^T1 tmp-words-with-articles-wikt-filtered.txt | grep -P '\[\[wikt:[a-z]+\]\]' | perl -pe 's/^T1\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> tmp-wikt-typos.txt
echo "|}" >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt

echo "===ME===" >> tmp-wikt-typos.txt
echo "Probable English-language compounds (with and without hyphen)." >> tmp-wikt-typos.txt
echo '{| class="wikitable sortable"' >> tmp-wikt-typos.txt
echo "|-" >> tmp-wikt-typos.txt
echo "! Typo freq" >> tmp-wikt-typos.txt
echo "! Possible typo" >> tmp-wikt-typos.txt
echo "! Pages" >> tmp-wikt-typos.txt
echo "! Language" >> tmp-wikt-typos.txt
grep ^ME tmp-words-with-articles-wikt-filtered.txt | perl -pe 's/^ME\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> tmp-wikt-typos.txt
echo "|}" >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt

echo "===TE===" >> tmp-wikt-typos.txt
echo "Possible English-language typos." >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt
echo '{| class="wikitable sortable"' >> tmp-wikt-typos.txt
echo "|-" >> tmp-wikt-typos.txt
echo "! Typo freq" >> tmp-wikt-typos.txt
echo "! Possible typo" >> tmp-wikt-typos.txt
echo "! Pages" >> tmp-wikt-typos.txt
echo "! Language" >> tmp-wikt-typos.txt
grep ^TE tmp-words-with-articles-wikt-filtered.txt | perl -pe 's/^TE\t\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> tmp-wikt-typos.txt
echo "|}" >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt

echo "===CN===" >> tmp-wikt-typos.txt
echo "Chemistry-related words." >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt
echo '{| class="wikitable sortable"' >> tmp-wikt-typos.txt
echo "|-" >> tmp-wikt-typos.txt
echo "! Typo freq" >> tmp-wikt-typos.txt
echo "! Possible typo" >> tmp-wikt-typos.txt
echo "! Pages" >> tmp-wikt-typos.txt
echo "! Language" >> tmp-wikt-typos.txt
grep ^CN tmp-words-with-articles-wikt-filtered.txt | perl -pe 's/^CN\t\* ([0-9]+) - (\[\[.+?\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> tmp-wikt-typos.txt
echo "|}" >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt

echo "===TS===" >> tmp-wikt-typos.txt
echo "These are suspected whitespace errors." >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt
echo '{| class="wikitable sortable"' >> tmp-wikt-typos.txt
echo "|-" >> tmp-wikt-typos.txt
echo "! Typo freq" >> tmp-wikt-typos.txt
echo "! Possible typo" >> tmp-wikt-typos.txt
echo "! Pages" >> tmp-wikt-typos.txt
echo "! Language" >> tmp-wikt-typos.txt
grep ^TS tmp-words-with-articles-wikt-filtered.txt | perl -pe 's/^TS\t\* ([0-9]+) - (\[\[.+?\]\]) - (.*$)/|-\n| $1 || $2 || $3/'  >> tmp-wikt-typos.txt
echo "|}" >> tmp-wikt-typos.txt
echo >> tmp-wikt-typos.txt

# Add language column data requested by User:Jberkel
cat tmp-wikt-typos.txt | perl -pe 's/#([^\[]+)\]\]$/#$1]] || $1/' > post-wikt-typos.txt

# --- MOST WANTED NO QUOTATIONS ---

echo '{| class="wikitable sortable"' > post-wikt-most-wanted-no-quotations.txt
echo "|-" >> post-wikt-most-wanted-no-quotations.txt
echo "! Typo class" >> post-wikt-most-wanted-no-quotations.txt
echo "! Typo freq" >> post-wikt-most-wanted-no-quotations.txt
echo "! Possible typo" >> post-wikt-most-wanted-no-quotations.txt
echo "! Pages" >> post-wikt-most-wanted-no-quotations.txt
echo "! Language" >> post-wikt-most-wanted-no-quotations.txt


echo "|}" >> post-wikt-most-wanted-no-quotations.txt

# --- WITH QUOTATIONS ---

# Run time: About 1 min (big-board SSD)
tac tmp-wiktionary-spell-with-quotations.txt | grep '^*' | ../venv/bin/python3 ../word_categorizer.py > tmp-words-with-articles-wikt-with-quotations.txt

# Most common HTML typos
grep -P "^(HB|HL)" tmp-words-with-articles-wikt-with-quotations.txt | perl -pe "s/^HB\t//" | perl -pe 's/</&lt;/g' | perl -pe 's/>/&gt;/g' | grep -v "Unsupported titles/HTML" > post-wikt-html-with-quotations.txt

# Most common typos / wanted entries with quotations
echo '{| class="wikitable sortable"' > post-wikt-most-wanted-with-quotations.txt
echo "|-" >> post-wikt-most-wanted-with-quotations.txt
echo "! Typo freq" >> post-wikt-most-wanted-with-quotations.txt
echo "! Possible typo" >> post-wikt-most-wanted-with-quotations.txt
echo "! Pages" >> post-wikt-most-wanted-with-quotations.txt
echo "! Language" >> post-wikt-most-wanted-with-quotations.txt
grep -vP "^(H|HB|HL|BC|BW|TS)" tmp-words-with-articles-wikt-with-quotations.txt | perl -pe "s/^.*?\t//" | grep -v "(" | grep -v ")" | sort -rn -k2 | head -50 | perl -pe 's/^\* ([0-9]+) - (\[\[[^\]]+\]\]) - (.*$)/|-\n| $1 || $2 || $3 || $4/' | perl -pe 's/#([^\[]+)\]\] \|\| $/#$1\]\] || $1/' >> post-wikt-most-wanted-with-quotations.txt
echo "|}" >> post-wikt-most-wanted-with-quotations.txt

# ---

cat tmp-words-with-articles-wikt.txt | ../venv/bin/python3 ../count_by_rating.py --wiktionary > post-stats-wikt.txt


echo "Done post-processing"
echo `date`
