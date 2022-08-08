# REMEMBER: First, remove any existing dump due to limited hard drive space!

cd /bulk-wikipedia/

echo `date`
echo "Loading page data..."
wget https://dumps.wikimedia.org/enwiki/20220801/enwiki-20220801-page.sql.gz
gunzip enwiki-20220801-page.sql.gz
cat enwiki-20220801-page.sql | mysql -D enwiki
echo "ALTER TABLE page DROP KEY page_name_title, DROP KEY page_random, DROP KEY page_redirect_namespace_len;" | mysql -D enwiki
# 1 min
echo "DELETE FROM page WHERE page_namespace != 0;" | mysql -D enwiki
# 56,288,207 -> 16,716,261 rows for 2022-08-01 dump in 7 min

echo `date`
echo "Loading page links..."
wget https://dumps.wikimedia.org/enwiki/20220801/enwiki-20220801-pagelinks.sql.gz
gunzip enwiki-20220801-pagelinks.sql.gz
cat /home/beland/moss/pagelinks_fast.sql | mysql -D enwiki
cat enwiki-20220801-pagelinks.sql | grep ^INSERT | mysql -D enwiki
# 4 hours
echo "DELETE FROM pagelinks WHERE pl_namespace != 0 OR pl_from_namespace != 0;" | mysql -D enwiki
# 1,492,380,988 -> 641,503,901 rows in 2022-08-01 dump in about 1 hour

cat /home/beland/moss/named_page_links.sql | mysql -D enwiki

echo "INSERT INTO named_page_links SELECT page.page_title AS pl_from, pl_title AS pl_to FROM page, pagelinks WHERE pl_from = page.page_id;" | mysql -D enwiki
# 5 hours
echo "ALTER TABLE named_page_links ADD INDEX (pl_from);" | mysql -D enwiki
# 1 hour
echo "ALTER TABLE named_page_links ADD INDEX (pl_to);" | mysql -D enwiki
# 2 hours

cd /home/beland/moss/
venv/bin/python3 walled_garden.py
