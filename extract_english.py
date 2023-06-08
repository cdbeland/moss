import sys
from grammar import fetch_parts_of_speech

print("Loading English Wiktionary...", file=sys.stderr)
with open("/var/local/moss/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0", "r") as title_list:
    english_wiktionary = set([line.strip() for line in title_list if "_" not in line])
print("Printing English words only...", file=sys.stderr)
[print(word) for word in english_wiktionary if fetch_parts_of_speech(word)]
