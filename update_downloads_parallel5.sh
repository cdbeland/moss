#!/usr/bin/bash
set -e
ORIG_DIR=`pwd`
cd /var/local/moss/bulk-wikipedia/

echo `date`
echo "Building page_categories table..."
# Run time: About 40 minutes

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

echo `date`
cd $ORIG_DIR
venv/bin/python3 extract_english.py > /var/local/moss/bulk-wikipedia/english_words_only.txt
# extract_english.py takes about 2.5 hours

echo `date`
echo "Done."
