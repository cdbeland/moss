import re
import urllib.request


directory_html = urllib.request.urlopen("https://dumps.wikimedia.org/backup-index-bydb.html").read().decode('utf-8')
language_codes = re.findall(r"([_a-z]+)wiktionary</a>: <span class='done'>", directory_html)
# Excludes closed wiktionaries

for language_code in language_codes:
    file_name = "%swiktionary-latest-all-titles-in-ns0.gz" % language_code
    dump_url = "https://dumps.wikimedia.org/%swiktionary/latest/%s" % (language_code, file_name)
    print("Downloading %s" % dump_url)
    urllib.request.urlretrieve(dump_url, "/bulk-wikipedia/all-wiktionaries/%s" % file_name)