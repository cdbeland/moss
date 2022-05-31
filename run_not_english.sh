echo `date`

RUN_NAME=run-not-english-`git log | head -c 14 | perl -pe "s/commit //"`+`date "+%Y-%m-%dT%T"`
mkdir $RUN_NAME
cd $RUN_NAME

../venv/bin/python3 ../moss_not_english.py > not-english-output.csv
sort not-english-output.csv -k3 -nr -t$'\t' | head -500 > tmp-not-english.csv
echo '{|class="wikitable sortable"' > post-not-english.txt
echo '! Article !! # non-Eng !! % non-Eng !! [[Language code|Lang code]] !! Sample words' >> post-not-english.txt
cat tmp-not-english.csv | perl -pe 's/(.*?)\t/|-\n| [[$1]]\t/' | perl -pe 's/\t/ || /g' >> post-not-english.txt
echo "|}" >> post-not-english.txt

echo "Finished"
echo `date`
