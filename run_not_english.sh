echo `date`

RUN_NAME=run-not-english-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`
mkdir $RUN_NAME
cd $RUN_NAME

../venv/bin/python3 ../moss_not_english.py > not-english-output.csv
# Both # and % seem like good red flags, so take the highest from both metrics
sort not-english-output.csv -k3 -nr -t$'\t' | head -250 > tmp-not-english.csv
sort not-english-output.csv -k2 -nr -t$'\t' | head -250 >> tmp-not-english.csv
echo '{|class="wikitable sortable"' > post-not-english.txt
echo '! Article !! # non-Eng !! % non-Eng !! [[Language code|Lang code]] !! Sample words' >> post-not-english.txt
sort tmp-not-english.csv -k3 -nr -t$'\t' | uniq | perl -pe 's/(.*?)\t/|-\n| [[$1]]\t/' | perl -pe 's/\t/ || /g' >> post-not-english.txt
echo "|}" >> post-not-english.txt

echo "Finished"
echo `date`
