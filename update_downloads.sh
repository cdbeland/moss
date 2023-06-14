#!/usr/bin/bash

set -e

echo `date`
echo "Dropping walled garden data..."

# Both can't fit at the same time

echo "DROP TABLE IF EXISTS page;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS pagelinks;" | mysql -D enwiki
echo "DROP TABLE IF EXISTS named_page_links;" | mysql -D enwiki

echo `date`

# Download, extract, sort, and uncompress time: About 5 hours

# rm -rf /var/local/moss/bulk-wikipedia/all-wiktionaries
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

cd /var/local/moss/bulk-wikipedia/

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

rm -f enwiktionary-latest-page.sql
wget --continue https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-page.sql.gz
gunzip enwiktionary-latest-page.sql

rm -f enwiktionary-latest-categorylinks.sql
wget --continue https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-categorylinks.sql.gz
gunzip enwiktionary-latest-categorylinks.sql

rm -f enwiktionary-latest-all-titles-in-ns0
wget --continue https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-all-titles-in-ns0.gz
gunzip enwiktionary-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-all-titles-in-ns0.gz
wget --continue https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz
gunzip enwiki-latest-all-titles-in-ns0.gz

rm -f specieswiki-latest-all-titles-in-ns0.gz
wget --continue https://dumps.wikimedia.org/specieswiki/latest/specieswiki-latest-all-titles-in-ns0.gz
gunzip specieswiki-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-pages-articles-multistream.xml.bz2
wget --continue https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2

`date`
echo "Decompressing enwiki multistream..."
bunzip2 enwiki-latest-pages-articles-multistream.xml.bz2

# FIRST TIME SETUP

# Change "beland" to the Unix user you want to set up for

# su
# apt-get install mariadb-server
# service mariadb restart
# mysql
#  CREATE DATABASE enwiktionary;
#  USE enwiktionary;
#  CREATE USER 'beland'@'localhost';
#  GRANT ALL PRIVILEGES ON enwiktionary TO 'beland'@'localhost' WITH GRANT OPTION;
#  GRANT ALL PRIVILEGES ON enwiktionary.* TO 'beland'@'localhost' WITH GRANT OPTION;

# Optimization suggestions for my.cnf:
#
# [mysqld]
#
# # OPTIMIZE FOR LOADING LARGE DUMPS
# max_allowed_packet=1GB
#
# # THESE SACRIFICE DATA INTEGRITY FOR PERFORMANCE WHEN LOADING LARGE DUMPS
# innodb_buffer_pool_size = 4G
# innodb_log_buffer_size = 256M
# innodb_log_file_size = 1G
# innodb_flush_log_at_trx_commit = 0
# innodb_doublewrite = 0
#
# # Optimize for SSD
# # https://dev.mysql.com/doc/refman/5.6/en/optimizing-innodb-diskio.html
# innodb_checksum_algorithm = crc32
# innodb_flush_neighbors = 0
# innodb_io_capacity = 1000
# innodb_log_compressed_pages = OFF
# binlog_row_image = minimal
# # innodb_flush_method parameter = O_DSYNC  # Tries to open too many files


echo `date`
echo "Loading enwiktionary-latest-categorylinks.sql..."
cat enwiktionary-latest-categorylinks.sql | mysql -D enwiktionary
# Load time: About 4 hours

echo `date`
echo "Loading enwiktionary-latest-page.sql..."
cat enwiktionary-latest-page.sql | mysql -D enwiktionary
# Load time: About 45 minutes

echo `date`
echo "Building page_categories table..."
# Run time for this section: About 31 hours

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiktionary
echo "CREATE TABLE page_categories (
  title varbinary(255) NOT NULL DEFAULT '',
  category_name varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (title, category_name)
);" | mysql -D enwiktionary

echo "DELETE FROM page WHERE page_namespace != 0;" | mysql -D enwiktionary

echo "INSERT INTO page_categories (title, category_name)
 SELECT page_title, cl_to
 FROM page, categorylinks
 WHERE page.page_id = categorylinks.cl_from;" | mysql -D enwiktionary

echo "ALTER TABLE page_categories ADD INDEX i_title (title);" | mysql -D enwiktionary
echo "ALTER TABLE page_categories ADD INDEX i_cat (category_name);" | mysql -D enwiktionary

cd $ORIG_DIR
echo `date`
venv/bin/python3 extract_english.py > /var/local/moss/bulk-wikipedia/english_words_only.txt
# extract_english.py takes about 2.5 hours
echo `date`

# TODO:
# 1. From this script, run pywikibot in a Python script and get all
# the names of articles in
# https://en.wikipedia.org/w/index.php?title=Category:Redirects_from_misspellings
# 2. At spell-check time load these into memory. Use them to mark
# words as known misspellings.


echo "Converting enwiki XML to CSV..."
echo `date`
# Run time: ~21 hours?
venv/bin/python3 xml_to_csv.py /var/local/moss/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml > /var/local/moss/bulk-wikipedia/enwiki-articles-no-redir.csv

echo `date`
./load_enwiki_categories.sh
echo `date`

echo "Preparing for enwiktionary spell check"
# Run time: about 20 minutes
cd /var/local/moss/bulk-wikipedia/
rm -f enwiktionary-latest-pages-articles-multistream.xml.bz2
wget --continue https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-pages-articles-multistream.xml.bz2
bunzip2 enwiktionary-latest-pages-articles-multistream.xml.bz2

echo `date`
echo "XML to CSV for enwiktionary"
# Run time: About 50 minutes
cd $ORIG_DIR
venv/bin/python3 xml_to_csv.py /var/local/moss/bulk-wikipedia/enwiktionary-latest-pages-articles-multistream.xml > /var/local/moss/bulk-wikipedia/enwiktionary-articles-no-redir.csv

echo `date`
echo "Done"
