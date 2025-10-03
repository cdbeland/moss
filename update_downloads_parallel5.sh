#!/usr/bin/bash
set -e
ORIG_DIR=`pwd`
cd /var/local/moss/bulk-wikipedia/

echo `date`
echo "Building page_categories table..."
# Run time: A minute or two

echo "DROP TABLE IF EXISTS page_categories;" | mysql -D enwiktionary
echo "CREATE TABLE page_categories (
  title varbinary(255) NOT NULL DEFAULT '',
  category_name varbinary(255) NOT NULL DEFAULT '',
  PRIMARY KEY (title, category_name)
);" | mysql -D enwiktionary

echo "DELETE FROM page WHERE page_namespace != 0;" | mysql -D enwiktionary

echo "INSERT INTO page_categories (title, category_name)
 SELECT page_title, lt_title
 FROM page, categorylinks, linktarget
 WHERE page.page_id = categorylinks.cl_from
 AND linktarget.lt_id = categorylinks.cl_target_id;" | mysql -D enwiktionary
# Run time: ~36 min

echo "ALTER TABLE page_categories ADD INDEX i_title (title);" | mysql -D enwiktionary
# Run time: ~5 min
echo "ALTER TABLE page_categories ADD INDEX i_cat (category_name);" | mysql -D enwiktionary
# Run time: ~6 min

echo `date`
cd $ORIG_DIR
venv/bin/python3 extract_english.py > /var/local/moss/bulk-wikipedia/english_words_only.txt
# Run time: 20-30 minutes?

echo `date`
echo "Done."
