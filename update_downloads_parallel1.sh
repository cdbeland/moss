#!/usr/bin/bash
set -e
# Downloads of small Wiktionary and Wikipedia pages, and fast processing

echo `date`
echo "Downloading all wiktionaries..."

mkdir -p /var/local/moss/bulk-wikipedia/all-wiktionaries
venv/bin/python3 download_all_wiktionaries.py

echo "Downloading moss subpages..."

rm -rf /var/local/moss/bulk-wikipedia/moss-subpages
mkdir -p /var/local/moss/bulk-wikipedia/moss-subpages
venv/bin/python3 download_moss_subpages.py

echo `date`
echo "Uncompressing and sorting..."
# Takes about 12 minutes

ORIG_DIR=`pwd`

cd /var/local/moss/bulk-wikipedia/
gunzip all-wiktionaries/*
sort --unique all-wiktionaries/* > titles_all_wiktionaries_uniq.txt

echo `date`
echo "Downloading special pages..."
cd /var/local/moss/bulk-wikipedia/

export WGET_COMMAND='wget -o - --no-verbose --user-agent="$MOSS_USER_AGENT"'

# Sync with spell.py, moss_not_english.py
rm -f Wikispecies:Requested_articles
$WGET_COMMAND https://species.wikimedia.org/wiki/Wikispecies:Requested_articles
rm -f Before_2019
$WGET_COMMAND https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/Before_2019
rm -f 2020
$WGET_COMMAND https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2020
rm -f 2021
$WGET_COMMAND https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2021

rm -f moss
$WGET_COMMAND https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss

rm -f For_Wiktionary
$WGET_COMMAND https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/For_Wiktionary

rm -f Old_case_notes
$WGET_COMMAND https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/Old_case_notes

# For retf_offline_scan.py
$WGET_COMMAND https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/Typos

echo "Done."
