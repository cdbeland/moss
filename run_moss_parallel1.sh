#!/usr/bin/bash

# *** ONE-LINE-AT-A-TIME STYLE PROBLEMS ***

set -e
echo "Starting style check by line..."
echo `date`
../venv/bin/python3 ../moss_check_style_by_line.py > tmp-style-by-line.txt
# "grep" returns non-zero exit status if there are no matches
echo "Finished style check by line; processing..."
echo `date`

set +e
grep ^N tmp-style-by-line.txt | sort > fixme-broken-nbsp.txt
grep ^R tmp-style-by-line.txt | sort | perl -pe 's/^R\t(.*?)\t(.*)/* [[$1]] - <nowiki>$2<\/nowiki>/' > fixme-rhyme-scheme.txt
grep ^X tmp-style-by-line.txt | sort > fixme-x-to-times.txt
grep ^FR tmp-style-by-line.txt | sort > fixme-fraction.txt
grep ^QL tmp-style-by-line.txt | sort > fixme-logical-quoting.txt
grep ^L tmp-style-by-line.txt | sort > fixme-liters.txt
grep ^W tmp-style-by-line.txt | sort > fixme-washington-state.txt
grep ^SPEED tmp-style-by-line.txt | sort > fixme-speed.txt
grep ^MAN_MADE tmp-style-by-line.txt | sort > fixme-man-made.txt
grep ^FE tmp-style-by-line.txt | sort > fixme-fuel-efficiency.txt
grep ^TEMP tmp-style-by-line.txt | sort > fixme-temp.txt
grep '^\$H' tmp-style-by-line.txt | sort > fixme-currency-hyphen.txt
grep ^PAREN_REF tmp-style-by-line.txt | sort > fixme-paren-ref.txt

grep ^DIGITS_MIO tmp-style-by-line.txt | sort > fixme-digits-mio.txt
grep ^DIGITS_SPACES tmp-style-by-line.txt | sort > fixme-digits-spaces.txt

grep ^SCI_NOTATION_XILLION tmp-style-by-line.txt | sort > fixme-scinot-xillion.txt
grep ^SCI_NOTATION_WRONG tmp-style-by-line.txt | sort > fixme-scinot-wrong.txt
grep ^SCI_NOTATION_MALFORMED tmp-style-by-line.txt | sort > fixme-scinot-malformed.txt
grep ^SCI_NOTATION_PER tmp-style-by-line.txt | sort > fixme-scinot-per.txt
grep ^SCI_NOTATION_CATCHALL tmp-style-by-line.txt | sort > fixme-scinot-cachall.txt

grep ^AU tmp-style-by-line.txt | sort > tmp-au.txt
cat tmp-au.txt | perl -pe 's/^AU_\w+\t(.*?)\t.*$/$1/' | uniq > fixme-au.txt

grep ^KM tmp-style-by-line.txt | sort > tmp-km.txt
cat tmp-km.txt | perl -pe 's/^KM_\w+\t(.*?)\t.*$/$1/' | uniq > fixme-km.txt

grep ^CTT tmp-style-by-line.txt | perl -pe 's/.*?\t(.*)\t(.*)$/$1/' | uniq > beland-ctt.txt

grep ^DECIMAL_MIDDOT tmp-style-by-line.txt | sort | perl -pe 's/^DECIMAL_MIDDOT\t(.*?)\t.*$/$1/' | uniq > fixme-decimal-middot.txt
grep ^DECIMAL_COMMA tmp-style-by-line.txt | sort | perl -pe 's/^DECIMAL_COMMA\t(.*?)\t.*$/$1/' | uniq > fixme-decimal-comma.txt

grep ^L tmp-style-by-line.txt | sort > fixme-liters.txt

grep ^ET tmp-style-by-line.txt | sort | perl -pe 's/^ET\t(.*?)\t.*$/$1/' | uniq > fixme-ellipsis-in-title.txt

grep ^INFONAT tmp-style-by-line.txt | sort > tmp-infonat.txt

# TODO:
# * USA -> US, U.S.A. -> U.S. in infoboxes, prose
# * Unpipe country name in birth_place

cat tmp-infonat.txt | perl -pe 's/^(.*?_[A-Z]*?)[_ \t].*$/$1/'  | sort | perl ../count.pl | sort -n > infonat-count-overall.txt
cat tmp-infonat.txt | perl -pe 's/^(.*?)\t.*$/$1/' | sort | perl ../count.pl | sort -n > infonat-count-detail.txt

# -- Remove citizenship/nationality fields --

# Can be updated from infonat-count-detail.txt
grep -P '^INFONAT_REDUNDANT_\w+_JUS_SOLI_(1700s|MISC|2000s)' tmp-infonat.txt | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' > infonat-redundant-jus-soli-misc.txt
grep -P '^INFONAT_REDUNDANT_\w+_JUS_SOLI_1[89]' tmp-infonat.txt | grep -vP 'INFONAT_REDUNDANT_(ar|br|ca|cl|mx|us)' | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' >> infonat-redundant-jus-soli-misc.txt

grep -P '^INFONAT_REDUNDANT_\w+_JUS_SOLI_1800s' tmp-infonat.txt | grep -P 'INFONAT_REDUNDANT_(ar|br|ca|cl|mx|us)' | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' > infonat-redundant-jus-soli-1800s-big-countries.txt
grep -P '^INFONAT_REDUNDANT_\w+_JUS_SOLI_1900s' tmp-infonat.txt | grep -P 'INFONAT_REDUNDANT_(ar|br|ca|cl|mx|us)' | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' > infonat-redundant-jus-soli-1900s-big-countries.txt
grep -P '^INFONAT_REDUNDANT_\w+_JUS_SOLI_UNK' tmp-infonat.txt | grep -P 'INFONAT_REDUNDANT_(ar|br|ca|cl|mx|us)' | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' > infonat-redundant-jus-soli-UNK-big-countries.txt

grep -P '^INFONAT_EXPLAIN_us_state' tmp-infonat.txt | sort | perl -pe 's/^INF\w*\t(.*?)\t.*$/$1/' > infonat-redundant-us-state.txt

grep -P '^INFONAT_REDUNDANT_(au|be|cn|de|dk|es|fi|fr|gb|hu|ie|in|ir|it|jp|nl|no|ph|pl|se|tr|ug|za)' tmp-infonat.txt | sort > tmp-infonat-large-non-jus-soli.txt
grep -P '^INFONAT_REDUNDANT_(al|am|ao|at|az|bd|bg|by|ch|cm|co|cz|dz|ee|eg|gh|gr|hr|id|il|in|iq|is|ke|kr|lb|lk|lt|lu|lv|ma|mk|mm|my|np|nz|pk|pr|ps|pt|ru|sa|sg|si|sn|sy|th|tn|tw|ua|vn)' tmp-infonat.txt | sort > tmp-infonat-medium-non-jus-soli.txt
grep -P '^INFONAT_REDUNDANT_' tmp-infonat.txt | grep -v JUS_SOLI | grep -v _us_state | grep -vP '^INFONAT_REDUNDANT_(au|be|cn|de|dk|es|fi|fr|gb|hu|ie|in|ir|it|jp|nl|no|ph|pl|se|tr|ug|za|al|am|ao|at|az|bd|bg|by|ch|cm|co|cz|dz|ee|eg|gh|gr|hr|id|il|in|iq|is|ke|kr|lb|lk|lt|lu|lv|ma|mk|mm|my|np|nz|pk|pr|ps|pt|ru|sa|sg|si|sn|sy|th|tn|tw|ua|vn)' | sort > tmp-infonat-small-non-jus-soli.txt

grep -P '_UNK' tmp-infonat-small-non-jus-soli.txt > infonat-redundant-small-non-jus-soli-unk.txt
grep -P '_(1700s|MISC)' tmp-infonat-small-non-jus-soli.txt > infonat-redundant-small-non-jus-soli-1700s-misc.txt
grep -P '_1800s' tmp-infonat-small-non-jus-soli.txt > infonat-redundant-small-non-jus-soli-1800s.txt
grep -P '_1900s' tmp-infonat-small-non-jus-soli.txt > infonat-redundant-small-non-jus-soli-1900s.txt
grep -P '_2000s' tmp-infonat-small-non-jus-soli.txt > infonat-redundant-small-non-jus-soli-2000s.txt
grep -P '_UNK' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-unk.txt
grep -P '_MISC' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-misc.txt
grep -P '_1700s' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-1700s.txt
grep -P '_1800s' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-1800s.txt
grep -P '_1900s' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-1900s.txt
grep -P '_2000s' tmp-infonat-medium-non-jus-soli.txt > infonat-redundant-medium-non-jus-soli-2000s.txt
grep -P '_UNK' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-unk.txt
grep -P '_MISC' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-misc.txt
grep -P '_1700s' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-1700s.txt
grep -P '_1800s' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-1800s.txt
grep -P '_1900s' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-1900s.txt
grep -P '_2000s' tmp-infonat-large-non-jus-soli.txt > infonat-redundant-large-non-jus-soli-2000s.txt


# grep ^INFONAT_REDUNDANT tmp-infonat.txt | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-redundant.txt
# grep ^INFONAT_REDUNDANT tmp-infonat.txt | grep JUS_SOLI | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-redundant-jus-soli.txt
# grep ^INFONAT_REDUNDANT tmp-infonat.txt | grep -v JUS_SOLI | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-redundant-not-jus-soli.txt

# --

# Remove flag per [[MOS:FLAGBIO]]
grep ^INFONAT_FLAG tmp-infonat.txt | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | sort | uniq > fixme-infonat-mos-flagbio.txt

# Remove citizenship/nationality fields and add ", United States" to birth_place
grep ^INFONAT_EXPLAIN_us_state tmp-infonat.txt | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-add-usa.txt
grep ^INFONAT_BIRTHPLACE_NO_COUNTRY tmp-infonat.txt | sort -k3 -t $'\t' > fixme-infonat-add-country.txt

# Probably need to improve demonym list in moss_check_style_by_line.py
grep ^INFONAT_CITNAT_NO_COUNTRY tmp-infonat.txt | sort -k3 -t $'\t' > fixme-infonat-no-country.txt

# Either the field is being abused or change of status needs to be
# dated or explained as from-birth or something.
grep ^INFONAT_EXPLAIN_us tmp-infonat.txt | grep -v ^INFONAT_us_state | grep "citizenship" | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-citizenship-usa.txt
grep ^INFONAT_EXPLAIN_us tmp-infonat.txt | grep -v ^INFONAT_us_state | grep "nationality" | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | uniq > fixme-infonat-nationality-usa.txt

grep ^INFONAT_ERR tmp-infonat.txt | sort > fixme-infonat-err.txt

echo "moss_check-style_by_line.py needs rewrite for performance" > INCOMPLETE.txt
# grep ^P tmp-style-by-line.txt > fixme-prime.txt
# grep ^QB tmp-style-by-line.txt > fixme-bad-quoting.txt
# grep ^QD tmp-style-by-line.txt | perl ../count.pl | sort -rn | perl -pe "s/^\d+\t//" | head -1000 > jwb-double-most.txt
set -e

# --- READABILITY ---

echo "Beginning readability check..."
echo `date`

# Run time for this segment: ~1h (8-core parallel)

../venv/bin/python3 ../moss_readability_check.py > tmp-readability.txt
sort -k2 -n tmp-readability.txt > post-readability.txt
rm tmp-readability.txt

# --- RETF ---

echo "Beginning RETF scan..."
echo `date`
../venv/bin/python ../retf_offline_scan.py | sort > tmp-retf.csv
cat tmp-retf.csv | perl -pe 's/^.*\t(.*?)\t.*?$/$1/' | sort | perl ../count.pl | sort -n > retf-counts.txt
sort tmp-retf.csv --stable -n -k5 -t "	" > retf-by-regex.csv
# Above, -t "(tab character)"
rm -f tmp-retf.csv
cat retf-counts.txt | perl -pe 's/^(.*?)\t"(.*?)"$/    "$2": $1,/' > retf-stat-array.py
cat retf-by-regex.csv | grep -vP "(0–0–0|0–0|2–1–1|2–1|ELLIPSIS|'s)" | perl -pe 's/^(.*?)\t.*$/$1/' | uniq | head -5000 > retf-high-priority-articles.txt

# ---

echo "Done."
echo `date`
