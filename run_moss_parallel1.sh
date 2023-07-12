#!/usr/bin/bash

set -e


# *** ONE-LINE-AT-A-TIME STYLE PROBLEMS ***

../venv/bin/python3 ../moss_check_style_by_line.py > tmp-style-by-line.txt

grep ^L tmp-style-by-line.txt > fixme-liters.txt
grep ^X tmp-style-by-line.txt > fixme-x-to-times.txt
grep ^T tmp-style-by-line.txt > fixme-temp.txt
grep ^S tmp-style-by-line.txt > fixme-speed.txt
grep ^FU tmp-style-by-line.txt > fixme-fuel-efficiency.txt
grep ^P tmp-style-by-line.txt > fixme-prime.txt
grep ^FR tmp-style-by-line.txt > fixme-fraction.txt
grep ^N tmp-style-by-line.txt > fixme-broken-nbsp.txt
grep ^R tmp-style-by-line.txt > fixme-rhyme-scheme.txt

grep ^QL tmp-style-by-line.txt > fixme-logical-quoting.txt
grep ^QB tmp-style-by-line.txt > fixme-bad-quoting.txt

grep ^QD tmp-style-by-line.txt > tmp-double-quoting.txt
cat tmp-double-quoting.txt | perl ../count.pl | sort -rn > tmp-double-most.txt
grep -vP "(grammar|languag|species| words)" tmp-double-most.txt | perl -pe "s/^\d+\t//" | head -1000 > jwb-double-most.txt

# --- READABILITY ---

echo "Beginning readability check..."
echo `date`

# Run time for this segment: ~1h (8-core parallel)

../venv/bin/python3 ../moss_readability_check.py > tmp-readability.txt
sort -k2 -n tmp-readability.txt > post-readability.txt
rm tmp-readability.txt

echo "Done."
echo `date`
