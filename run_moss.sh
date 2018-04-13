set RUN_NAME=run-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`

mkdir $RUN_NAME
python moss_spell_check.py > $RUN_NAME/tmp-output.txt
cd $RUN_NAME
grep ^@ tmp-output.txt | sort -nr -k2 > tmp-articles-with-words.txt
cat tmp-articles-with-words.txt | grep -vP '^@\t0' | perl -pe 's/.*\t//' >! tmp-misspelled-lists.txt
cat tmp-misspelled-lists.txt | perl -ne 'foreach $word (split(" ")) {print $word . "\n"}' >! tmp-misspelled-words.txt
cat tmp-misspelled-words.txt | perl -pe 'print length($_) - 1; print "\t"' | sort -n >! tmp-misspelled-words-charlen.txt
grep '^*' tmp-output.txt | tac > words-with-articles.txt

cat tmp-articles-with-words.txt | perl -pe 's/^@\t(\d+)\t(.*?)\t/* \1 - [[\2]] - /' > tmp-articles-misspelled-words.txt
head -1000 tmp-articles-misspelled-words.txt > post-articles-with-most-misspelled-words.txt
tac tmp-articles-misspelled-words.txt | grep -P "\* 1 -" | perl -pe 's/ - (\w+)$/ - [[wikt:\1]]/' >! post-articles-with-single-typo.txt

tac words-by-article.txt | head -1000 | python ../summarizer.py > post-most-common-misspellings.txt

# TODO: Link directly to articles where these words were detected
tac misspelled-words-charlen.txt | uniq | perl -pe 's%(\d+)\t(.*)$%* \1 [https://en.wikipedia.org/w/index.php?search=\2 \2]%' | post-longest-shortest-misspelled-words.txt


