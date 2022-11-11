from os.path import exists
import re
from time import sleep
import urllib.request


directory_html = urllib.request.urlopen("https://dumps.wikimedia.org/backup-index-bydb.html").read().decode('utf-8')
language_codes = re.findall(r"([_a-z]+)wiktionary</a>: <span class='(done|partial-dump)'>", directory_html)
# Excludes closed wiktionaries

for (language_code, _dump_status) in language_codes:
    file_name = "%swiktionary-latest-all-titles-in-ns0.gz" % language_code
    full_path = "/bulk-wikipedia/all-wiktionaries/%s" % file_name
    if exists(full_path):
        print(f"Skipping existing file - {full_path}")
        continue
    dump_url = "https://dumps.wikimedia.org/%swiktionary/latest/%s" % (language_code, file_name)
    sleep(1)
    print("Downloading %s" % dump_url)
    try:
        urllib.request.urlretrieve(dump_url, full_path)
    except urllib.error.HTTPError:
        print("FAILED, skipping...")
