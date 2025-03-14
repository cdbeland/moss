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

# Sync with spell.py, moss_not_english.py
rm -f Wikispecies:Requested_articles
wget -o - --no-verbose https://species.wikimedia.org/wiki/Wikispecies:Requested_articles
rm -f Before_2019
wget -o - --no-verbose https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/Before_2019
rm -f 2020
wget -o - --no-verbose https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2020
rm -f 2021
wget -o - --no-verbose https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2021

rm -f moss
wget -o - --no-verbose https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss

rm -f For_Wiktionary
wget -o - --no-verbose https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/For_Wiktionary

rm -f Old_case_notes
wget -o - --no-verbose https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/Old_case_notes

# For retf_offline_scan.py
wget -o - --no-verbose https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/Typos

echo `date`
echo "Done."
