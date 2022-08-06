# REMEMBER: First, remove any existing dump due to limited hard drive space!

echo `date`
echo "Loading page data..."
wget https://dumps.wikimedia.org/enwiki/20220801/enwiki-20220801-page.sql.gz
gunzip enwiki-20220801-page.sql.gz
cat enwiki-20220801-page.sql | mysql -D enwiki

echo `date`
echo "Loading page links..."
wget https://dumps.wikimedia.org/enwiki/20220801/enwiki-20220801-pagelinks.sql.gz
gunzip enwiki-20220801-pagelinks.sql.gz
cat pagelinks_fast.sql | mysql -D enwiki
cat enwiki-20220801-pagelinks.sql | grep ^INSERT | mysql -D enwiki

DELETE FROM pagelinks WHERE pl_namespace != 0 OR pl_from_namespace != 0;
# -> No effect, possibly due to corruption?
# 313,335,135 rows in 2022-08-01 dump (might be corrupted due to power outage during load?)

ALTER TABLE page DROP KEY page_name_title, DROP KEY page_random, DROP KEY page_redirect_namespace_len;
# 1 min
DELETE FROM page WHERE page_namespace != 0;
# 56,288,207 -> 16,716,261 for 2022-08-01 dump in 7 min

cat named_page_links.sql | mysql -D enwiki

INSERT INTO named_page_links SELECT page.page_title AS pl_from, pl_title AS pl_to FROM page, pagelinks WHERE pl_from = page.page_id;
# 20 min
ALTER TABLE named_page_links ADD INDEX (pl_from);
# 21 min

venv/bin/python3 walled_garden.py
