#!/usr/bin/bash
set -e
cd /var/local/moss/bulk-wikipedia/

# ONE-TIME SETUP:
# su
# mysql
#  CREATE DATABASE enwiki;
#  USE enwiki;
#  CREATE USER 'beland'@'localhost';
#  GRANT ALL PRIVILEGES ON enwiki TO 'beland'@'localhost' WITH GRANT OPTION;
#  GRANT ALL PRIVILEGES ON enwiki.* TO 'beland'@'localhost' WITH GRANT OPTION;

echo `date`
echo "Adding enwiki categories..."
echo "Starting downloads and decompression..."

rm -f enwiki-latest-categorylinks.sql
# wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-categorylinks.sql.gz
# gunzip enwiki-latest-categorylinks.sql.gz
# echo `date`
# echo "Loading enwiki-latest-categorylinks.sql..."
# cat enwiki-latest-categorylinks.sql | mysql -D enwiki

rm -f enwiki-latest-page.sql
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page.sql.gz
gunzip enwiki-latest-page.sql

echo `date`
echo "Loading enwiki-latest-page.sql..."
# Run time: about 7h20m
cat enwiki-latest-page.sql | mysql -D enwiki

echo `date`
echo "Building page_categories table..."
# Run time: several hours

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiki
echo "CREATE TABLE page_categories (
  title varbinary(255) NOT NULL DEFAULT '',
  category_name varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (title, category_name)
);" | mysql -D enwiki

echo "DELETE FROM page WHERE page_namespace != 0;" | mysql -D enwiki

echo "INSERT INTO page_categories (title, category_name)
 SELECT page_title, cl_to
 FROM page, categorylinks
 WHERE page.page_id = categorylinks.cl_from;" | mysql -D enwiki

echo "ALTER TABLE page_categories ADD INDEX i_title (title);" | mysql -D enwiki
echo "ALTER TABLE page_categories ADD INDEX i_cat (category_name);" | mysql -D enwiki

echo "All done!"
echo `date`
