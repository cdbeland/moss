from unidecode import unidecode

for filename in [
    "/var/local/moss/bulk-wikipedia/enwiktionary-latest-all-titles-in-ns0"
]:
    with open(filename, "r") as title_list:
        for line in title_list:
            entry = line.strip()
            if any(ord(char) for char in entry if ord(char) > 591):
                romanized = unidecode(entry)
                if romanized != entry:
                    print("%s\t%s" % (entry, romanized))

# TODO: Compare e.g.
# https://en.wikipedia.org/wiki/ISO_9
# https://en.wikipedia.org/wiki/List_of_ISO_romanizations
# https://en.wikipedia.org/wiki/Romanization
