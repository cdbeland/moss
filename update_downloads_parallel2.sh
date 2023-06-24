#!/usr/bin/bash
set -e
ORIG_DIR=`pwd`
cd /var/local/moss/bulk-wikipedia/

# Largest dump file - long pole sequence

echo `date`

rm -f enwiki-latest-pages-articles-multistream.xml.bz2
wget -o - --no-verbose https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2

# Wait until here to kick this off to keep only one dump server
# connection at a time
echo `date`
cd $ORIG_DIR
./update_downloads_parallel4.sh >& /bulk-wikipedia/download-parallel4.log &
echo "parallel4 launched"
cd /var/local/moss/bulk-wikipedia/

echo `date`
echo "Decompressing enwiki multistream..."
bunzip2 enwiki-latest-pages-articles-multistream.xml.bz2
# About 2 hours

echo `date`
echo "Converting enwiki XML to CSV..."
# About 4 h 40 min
cd $ORIG_DIR
venv/bin/python3 xml_to_csv.py /var/local/moss/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml > /var/local/moss/bulk-wikipedia/enwiki-articles-no-redir.csv

echo `date`
echo "Done."
