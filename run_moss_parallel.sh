#!/usr/bin/bash

set -e

export RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`
mkdir $RUN_NAME
cd $RUN_NAME

export NON_ASCII_LETTERS=ậạàÁáÂâÃãÄäầåấæɑ̠āÇçÈèÉéÊêËëēÌìÍíÎîÏïĭǐīʝÑñÒòÓóÔôÕõÖöớộøōŠšÚúùÙÛûǚÜüũưụÝýŸÿŽžəþɛ

# --- PERFORMANCE ---

# If SSD becomes a bottleneck:
#  https://wiki.archlinux.org/title/Solid_state_drive
# TRIM is enabled on weekly timer by default:
#  systemctl list-timers
# Other optimizations not yet investigated (discard is for TRIM):
#  https://askubuntu.com/questions/78971/best-etc-fstab-settings-for-boosting-ssd-hdd-performance
#  https://askubuntu.com/questions/1400/how-do-i-optimize-the-os-for-ssds

# ---

# Run multiple main threads because even though all the calculations
# are parallelized to use all cores, sometimes the parent thread
# becomes a bottleneck, and CPUs are underused.

../run_moss_parallel1.sh >& thread1.log &
../run_moss_parallel2.sh >& thread2.log &
../superscripts.sh >& superscripts.log &
../run_not_english.sh >& not_english.log &
../run_wiktionary_spell_check.sh >& wiktionary.log &
