#!/usr/bin/bash

set -e

# --- HTML ENTITIES ---

# Run time for this segment: ~4 h 10 min (8-core parallel)
# Uses 95%+ of all CPUs and it's eagerly awaited every dump, so run solo before everything else

echo "Beginning HTML entity check"
echo `date`
# Keep tmp-entities because it's sometimes used for unlimited runs
../venv/bin/python3 ../moss_entity_check.py > tmp-entities
cat tmp-entities | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt

export LC_ALL=C
grep '*' tmp-entities | perl -pe 's/\]\], \[\[/\n/g' | perl -pe 's/.*\[\[//' | perl -pe 's/\]\]//'  | sort | uniq > jwb-entities-alpha.txt

# --- PARALLELIZED REPORTS ---

# Run serially to avoid exceeding 8 MB RAM
../run_moss_parallel2.sh >& thread2.log
../run_moss_parallel1.sh >& thread1.log

# Sometimes there can be a CPU bottleneck for parent threads, leaving
# child threads underused, so starting two scripts at the same time
# can be more efficient. Also, not all long calculations can be
# parallelized to use all cores.
# ../run_moss_parallel1.sh >& thread1.log &
# ../run_moss_parallel2.sh >& thread2.log &
# echo "Parallel threads started."
# echo `date`

echo "Main thread done."
echo `date`
