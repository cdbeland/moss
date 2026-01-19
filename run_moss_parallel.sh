#!/usr/bin/bash

set -e

# Keep in sync with update_downloads_parallel.sh.
export commit_id=`git log | head -c 14 | perl -pe "s/commit //"`
export RUN_NAME=run-${commit_id}+`date "+%Y-%m-%dT%T"`
export MOSS_USER_AGENT="mossbot/${commit_id} https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss"
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


# --- PARTIAL SPELL-CHECK BYPASS ---

if [[ $1 == "--spell-check-only" ]]; then
    ../run_main_spell_check.sh $2
    exit 0
fi

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
../run_moss_parallel1.sh >& thread2.log
../run_moss_parallel2.sh >& thread1.log

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
