#!/usr/bin/bash

set -e

export RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`
mkdir $RUN_NAME
cd $RUN_NAME

# --- PERFORMANCE ---

# If SSD becomes a bottleneck:
#  https://wiki.archlinux.org/title/Solid_state_drive
# TRIM is enabled on weekly timer by default:
#  systemctl list-timers
# Other optimizations not yet investigated (discard is for TRIM):
#  https://askubuntu.com/questions/78971/best-etc-fstab-settings-for-boosting-ssd-hdd-performance
#  https://askubuntu.com/questions/1400/how-do-i-optimize-the-os-for-ssds


# --- HTML ENTITIES ---

# Run time for this segment: ~4 h 10 min (8-core parallel)
# Uses 95%+ of all CPUs and it's eagerly awaited every dump, so run solo before everything else

echo "Beginning HTML entity check"
echo `date`
# Keep tmp-entities because it's sometimes used for unlimited runs
../venv/bin/python3 ../moss_entity_check.py > tmp-entities
cat tmp-entities | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt


# --- PARALLELIZED REPORTS ---

# Run multiple main threads because even though most calculations are
# parallelized to use all cores, some are not, and sometimes the
# parent thread becomes a bottleneck, and CPUs are underused. Only run
# 2 tasks at a time to avoid CPU bottleneck that slows down the first
# reports to finish (which are usually urgently needed).

../run_moss_parallel1.sh >& thread1.log &
../run_moss_parallel2.sh >& thread2.log &

echo "Parallel threads started."
echo `date`
