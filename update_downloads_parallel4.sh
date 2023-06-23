#!/usr/bin/bash
set -e
ORIG_DIR=`pwd`
cd /var/local/moss/bulk-wikipedia/


# Medium-to-large dump files

# -- Downloads --

# Network load first because this script gets kicked off when the
# largest file is using the CPU

echo `date`
echo "Starting medium-sized downloads..."
rm -f enwiktionary-latest-pages-articles-multistream.xml.bz2
wget -o - --no-verbose https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2
echo `date`
rm -f enwiktionary-latest-page.sql
wget -o - --no-verbose https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-page.sql.gz
echo `date`
rm -f enwiktionary-latest-categorylinks.sql
wget -o - --no-verbose https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-categorylinks.sql.gz
echo `date`
rm -f enwiktionary-latest-all-titles-in-ns0
wget -o - --no-verbose https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-all-titles-in-ns0.gz
echo `date`
rm -f enwiki-latest-all-titles-in-ns0.gz
wget -o - --no-verbose https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz
echo `date`
rm -f specieswiki-latest-all-titles-in-ns0.gz
wget -o - --no-verbose https://dumps.wikimedia.org/specieswiki/latest/specieswiki-latest-all-titles-in-ns0.gz
echo `date`

echo `date`
echo "Done with downloads."

# -- Processing --

echo `date`
echo "Processing medium-sized dumps..."

echo `date`
echo "Decompressing enwiktionary multistream..."
bunzip2 enwiktionary-latest-pages-articles-multistream.xml.bz2  # ~20 min
echo `date`
echo "Decompressing enwiktionary titles..."
gunzip enwiktionary-latest-all-titles-in-ns0.gz
echo `date`
echo "Loading enwiktionary-latest-page.sql..."
gunzip enwiktionary-latest-page.sql
cat enwiktionary-latest-page.sql | mysql -D enwiktionary  # ~45 min
echo `date`
echo "Loading enwiktionary-latest-categorylinks.sql..."
gunzip enwiktionary-latest-categorylinks.sql
cat enwiktionary-latest-categorylinks.sql | mysql -D enwiktionary

# Prereqs for this very long page_categories table rebuild are now
# done; parallelize this because it only uses 1 CPU (for mysqld)
echo `date`
cd $ORIG_DIR
./update_downloads_parallel5.sh >& /bulk-wikipedia/download-parallel5.log &
echo "parallel5 launched"
cd /var/local/moss/bulk-wikipedia/

echo `date`
echo "Decompressing enwiki titles..."
gunzip enwiki-latest-all-titles-in-ns0.gz
echo `date`
echo "Decompressing specieswiki titles..."
gunzip specieswiki-latest-all-titles-in-ns0.gz

echo `date`
echo "XML to CSV for enwiktionary..."
# Run time: About 50 minutes
cd $ORIG_DIR
venv/bin/python3 xml_to_csv.py /var/local/moss/bulk-wikipedia/enwiktionary-latest-pages-articles-multistream.xml > /var/local/moss/bulk-wikipedia/enwiktionary-articles-no-redir.csv

echo `date`
echo "Done."
