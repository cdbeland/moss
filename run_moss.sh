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

../run_moss_background.sh >& thread_main.log&

echo "moss started; logging to ${RUN_NAME}/thread_main.log"
