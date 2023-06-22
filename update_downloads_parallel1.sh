#!/usr/bin/bash
set -e
# Downloads of small Wiktionary and Wikipedia pages, and fast processing

echo `date`
echo "Starting..."

mkdir -p /var/local/moss/bulk-wikipedia/all-wiktionaries
venv/bin/python3 download_all_wiktionaries.py

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

cd $ORIG_DIR
echo `date`
echo "Transliterating..."
venv/bin/python3 transliterate.py > /var/local/moss/bulk-wikipedia/transliterations.txt
# Takes about 10 sec

echo `date`
echo "Downloading special pages..."

# Sync with spell.py, moss_not_english.py
rm -f Wikispecies:Requested_articles
wget --continue https://species.wikimedia.org/wiki/Wikispecies:Requested_articles
rm -f Before_2019
wget --continue https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/Before_2019
rm -f 2020
wget --continue https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2020
rm -f 2021
wget --continue https://species.wikimedia.org/wiki/Wikispecies:Requested_articles/2021

rm -f moss
wget --continue https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss

rm -f For_Wiktionary
wget --continue https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/For_Wiktionary

rm -f Old_case_notes
wget --continue https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/Old_case_notes

echo `date`
echo "Done."
