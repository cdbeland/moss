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
./update_downloads_parallel4.sh >& /var/local/moss/bulk-wikipedia/download-parallel4.log &
echo "parallel4 launched"
cd /var/local/moss/bulk-wikipedia/

echo `date`
echo "Decompressing enwiki multistream and converting XML to CSV..."
cd $ORIG_DIR
# Run time: About 4 hours (on big-bucks)
bunzip2 -c /var/local/moss/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml.bz2 | venv/bin/python3 xml_to_csv.py > /var/local/moss/bulk-wikipedia/enwiki-articles-no-redir.csv
rm -f /var/local/moss/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml.bz2
# 1 Aug 2023: .xml.bz2 20GB, .xml 90GB, .csv 54GB

echo `date`
echo "Done."
