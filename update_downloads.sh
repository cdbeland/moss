cd /bulk-wikipedia/

rm -f enwiktionary-latest-all-titles-in-ns0
wget https://dumps.wikimedia.org/enwiktionary/latest/enwiktionary-latest-all-titles-in-ns0.gz
gunzip enwiktionary-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-all-titles-in-ns0.gz
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-all-titles-in-ns0.gz
gunzip enwiki-latest-all-titles-in-ns0.gz

rm -f specieswiki-latest-all-titles-in-ns0.gz
wget https://dumps.wikimedia.org/specieswiki/latest/specieswiki-latest-all-titles-in-ns0.gz
gunzip specieswiki-latest-all-titles-in-ns0.gz

rm -f enwiki-latest-pages-articles-multistream.xml.bz2
wget https://dumps.wikimedia.org/enwiki/latest/enwiki-latest-pages-articles-multistream.xml.bz2
bunzip2 enwiki-latest-pages-articles-multistream.xml.bz2
