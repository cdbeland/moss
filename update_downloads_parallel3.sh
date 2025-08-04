#!/usr/bin/bash
set -e

# DISABLED DUE TO EXCESSIVE TIME TO COMPLETION. USING API QUERIES
# INSTEAD BECAUSE ONLY A SMALL NUMBER OF CATEGORIES ARE NEEDED. IF
# THIS CHANGES IN THE FUTURE, IT'S POSSIBLE THIS SQL LOADING TECHNIQUE
# IS SUBOPTIMAL?

# Loads enwiki categories

cd /var/local/moss/bulk-wikipedia/

echo `date`

# Run time: About 20 min
echo "Adding enwiki categories..."
echo "Starting downloads and decompression..."
rm -f enwiki-latest-categorylinks.sql
wget -o - --no-verbose https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-categorylinks.sql.gz
gunzip enwiki-latest-categorylinks.sql.gz

echo `date`

# Run time: ~52 hours!!!
echo "Loading enwiki-latest-categorylinks.sql..."
cat enwiki-latest-categorylinks.sql | mysql -D enwiki

# Fast
rm -f enwiki-latest-page.sql
wget -o - --no-verbose https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-page.sql.gz
gunzip enwiki-latest-page.sql

echo `date`
# Run time: ~2 hours
echo "Loading enwiki-latest-page.sql..."
cat enwiki-latest-page.sql | mysql -D enwiki

echo `date`
echo "Building page_categories table..."
# Run time: About 3 hours

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

echo "DROP TABLE categorylinks;" | mysql -D enwiki
echo "DROP TABLE page;" | mysql -D enwiki

echo "All done!"
echo `date`
