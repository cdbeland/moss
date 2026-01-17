#!/usr/bin/bash

# RUN TIME

# About 6 hours (as of July 2024)

set -e

# Keep in sync with run_moss_parallel.sh.
export commit_id=`git log | head -c 14 | perl -pe "s/commit //"`
export MOSS_USER_AGENT="mossbot/${commit_id} https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss"

echo `date`
echo "Dropping walled garden data..."
# Both can't fit in storage at the same time

echo "DROP TABLE IF EXISTS page;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS pagelinks;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS named_page_links;" | mysql -D enwiki

echo `date`
echo "Dropping tables to be regenerated..."
# Breathing room while regenerating

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS categorylinks;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS page;" | mysql -D enwiktionary
echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiki

echo `date`

./update_downloads_parallel1.sh >& /var/local/moss/bulk-wikipedia/download-parallel1.log &
./update_downloads_parallel2.sh >& /var/local/moss/bulk-wikipedia/download-parallel2.log &
# 4 and 5 are kicked off from 2

# ./update_downloads_parallel3.sh >& /var/local/moss/bulk-wikipedia/download-parallel3.log &
# Only used by chemical formula report, takes more than 24 hours,
# disabled until performance can be improved or the report is manually
# run.

echo `date`
echo "Parallel scripts launched."
