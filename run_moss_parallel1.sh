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
grep ^N tmp-style-by-line.txt > fixme-broken-nbsp.txt
grep ^R tmp-style-by-line.txt > fixme-rhyme-scheme.txt
grep ^X tmp-style-by-line.txt > fixme-x-to-times.txt
grep ^FR tmp-style-by-line.txt > fixme-fraction.txt
grep ^QL tmp-style-by-line.txt > fixme-logical-quoting.txt

echo "moss_check-style_by_line.py needs rewrite for performance" > INCOMPLETE.txt
# grep ^L tmp-style-by-line.txt > fixme-liters.txt
# grep ^T tmp-style-by-line.txt > fixme-temp.txt
# grep ^S tmp-style-by-line.txt > fixme-speed.txt
# grep ^FU tmp-style-by-line.txt > fixme-fuel-efficiency.txt
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
../venv/bin/python ../regex_typo_fixer_offline.py | sort > fixme-retf.csv

# ---

echo "Done."
echo `date`
