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
grep ^R tmp-style-by-line.txt| sort  > fixme-rhyme-scheme.txt
grep ^X tmp-style-by-line.txt | sort > fixme-x-to-times.txt
grep ^FR tmp-style-by-line.txt | sort > fixme-fraction.txt
grep ^QL tmp-style-by-line.txt | sort > fixme-logical-quoting.txt
grep ^L tmp-style-by-line.txt | sort > fixme-liters.txt
grep ^W tmp-style-by-line.txt | sort > fixme-washington-state.txt
grep ^SPEED tmp-style-by-line.txt | sort > fixme-speed.txt
grep ^MAN_MADE tmp-style-by-line.txt | sort > fixme-man-made.txt
grep ^FE tmp-style-by-line.txt | sort > fixme-fuel-efficiency.txt
grep ^TEMP tmp-style-by-line.txt | sort > fixme-temp.txt

grep ^INFONAT tmp-style-by-line.txt | sort > tmp-infonat.txt

# Remove flag per [[MOS:FLAGBIO]]
grep ^INFONAT_FLAG tmp-infonat.txt | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' | sort > fixme-infonat-mos-flagbio.txt

# Remove citizenship/nationality fields
grep ^INFONAT_REDUNDANT tmp-infonat.txt | sort | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' > fixme-infonat-redundant.txt

# Remove citizenship/nationality fields and add ", United States" to birth_place
grep ^INFONAT_EXPLAIN_us_state tmp-infonat.txt | sort | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' > fixme-infonat-add-usa.txt

# Probably need to improve demonym list in moss_check_style_by_line.py
grep NO_COUNTRY tmp-infonat.txt | sort -k3 -t $'\t' > fixme-infonat-no-country.txt

# Either the field is being abused or change of status needs to be
# dated or explained as from-birth or something.
grep ^INFONAT_EXPLAIN_us tmp-infonat.txt | grep -v ^INFONAT_us_state | grep "citizenship" | sort | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' > fixme-infonat-citizenship-usa.txt
grep ^INFONAT_EXPLAIN_us tmp-infonat.txt | grep -v ^INFONAT_us_state | grep "nationality" | sort | perl -pe 's/INFONAT.*?\t(.*?)\t.*/$1/' > fixme-infonat-nationality-usa.txt

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
