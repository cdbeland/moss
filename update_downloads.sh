#!/usr/bin/bash

# Download, sort, and uncompress time: About 4 hours

rm -rf /bulk-wikipedia/all-wiktionaries
mkdir /bulk-wikipedia/all-wiktionaries
venv/bin/python3 download_all_wiktionaries.py

cd /bulk-wikipedia/

gunzip all-wiktionaries/*
cat all-wiktionaries/* > /tmp/all-wik-concat
sort --unique all-wiktionaries/* > titles_all_wiktionaries_uniq.txt
# This sort takes about 1 hour

rm -f Wikispecies:Requested_articles
wget https://species.wikimedia.org/wiki/Wikispecies:Requested_articles

rm -f moss
wget https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss

rm -f enwiktionary-latest-page.sql
wget https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-page.sql.gz
gunzip enwiktionary-latest-page.sql

rm -f enwiktionary-latest-categorylinks.sql
wget https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-categorylinks.sql.gz
gunzip enwiktionary-latest-categorylinks.sql

rm -f enwiktionary-latest-all-titles-in-ns0
wget https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-all-titles-in-ns0.gz
gunzip enwiktionary-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-all-titles-in-ns0.gz
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz
gunzip enwiki-latest-all-titles-in-ns0.gz

rm -f specieswiki-latest-all-titles-in-ns0.gz
wget https://dumps.wikimedia.org/specieswiki/latest/specieswiki-latest-all-titles-in-ns0.gz
gunzip specieswiki-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-pages-articles-multistream.xml.bz2
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2
bunzip2 enwiki-latest-pages-articles-multistream.xml.bz2

# FIRST TIME SETUP

# su
# service mariadb restart
# mysql
#  CREATE DATABASE enwiktionary;
#  GRANT ALL PRIVILEGES ON enwiktionary TO 'beland'@'localhost' WITH GRANT OPTION;


cat enwiktionary-latest-categorylinks.sql | mysql -D enwiktionary
# Load time: About 1 hour 10 minutes

cat enwiktionary-latest-page.sql | mysql -D enwiktionary
# Load time: About 25 minutes

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiktionary
echo "CREATE TABLE page_categories (
  title varbinary(255) NOT NULL DEFAULT '',
  category_name varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (title, category_name)
);" | mysql -D enwiktionary

echo "DELETE FROM page WHERE page_namespace != 0;" | mysql -D enwiktionary
# Query OK, 569828 rows affected (2 min 30.10 sec)

echo "INSERT INTO page_categories (title, category_name)
 SELECT page_title, cl_to
 FROM page, categorylinks
 WHERE page.page_id = categorylinks.cl_from;" | mysql -D enwiktionary
# Query OK, 22540237 rows affected (16 min 3.32 sec)

echo "ALTER TABLE page_categories ADD INDEX i_title (title);" | mysql -D enwiktionary
# Query OK, 0 rows affected (5 min 27.56 sec)         
echo "ALTER TABLE page_categories ADD INDEX i_cat (category_name);" | mysql -D enwiktionary
# Query OK, 0 rows affected (5 min 49.56 sec)         
