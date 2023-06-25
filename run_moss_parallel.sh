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

# Run multiple main threads because even though all the calculations
# are parallelized to use all cores, sometimes the parent thread
# becomes a bottleneck, and CPUs are underused.

../run_moss_parallel1.sh >& thread1.log &
../run_moss_parallel2.sh >& thread2.log &

# TODO: Add the below to whichever of the above finishes first.

# The first two are fast; run these sequentially to avoid CPU
# over-tasking
../run_wiktionary_spell_check.sh >& wiktionary.log
../superscripts.sh >& superscripts.log
../run_not_english.sh >& not_english.log
