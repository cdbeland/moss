#!/usr/bin/bash

set -e


# *** STANDALONE REPORTS ***


# --- HTML ENTITIES ---

echo "Beginning HTML entity check"
echo `date`

# Run time for this segment: ~4 h 10 min (8-core parallel)

# ../venv/bin/python3 ../moss_entity_check.py | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt
../venv/bin/python3 ../moss_entity_check.py > tmp-entities
cat tmp-entities | ../venv/bin/python3 ../summarizer.py --find-all > post-entities.txt
# "Worst" report disabled because it's mostly [[MOS:STRAIGHT]]
# violations, which are not a priority.
# ../venv/bin/python3 ../moss_entity_check.py > tmp-entities.txt
# mv tmp-worst.txt post-entities.txt
# cat tmp-entities.txt | ../venv/bin/python3 ../summarizer.py --find-all >> post-entities.txt

# --- l TO L FOR LITERS ---
echo "Starting liters style check"
echo `date`

# Per April 2021 RFC that updated [[MOS:UNITSYMBOLS]]

# Run time: 9-22 min per regex

# For "(l)", "(l/c/d)", etc. in table headers
../venv/bin/python3 ../dump_grep_csv.py '\(l(/[a-zA-Z/]+)?\)' | grep -v '(l)\!' | grep -v '(r)' | grep -vP "[a-zA-Z${NON_ASCII_LETTERS}]\(l\)" | grep -vP "\(l\)[a-zA-Z${NON_ASCII_LETTERS}]" | grep -vP '</?math' | sort > liters-fixme0.txt

../venv/bin/python3 ../dump_grep_csv.py "[0-9] l" | perl -pe "s%\{\{cite.*?\}\}%%g" | perl -pe "s%\{\{(Transliteration|lang|IPA|not a typo).*?\}\}%%g" | perl -pe "s%<math.*?</math>%%g" | perl -pe "s/(File|Image):.*?[\|\n]//g" | grep -P "[^p][^.]\s?[0-9]+ l[^a-zA-Z0-9'’${NON_ASCII_LETTERS}]" | grep -vi " l.jpg" | grep -vP "image[0-9]? *=.* l[ \.].jpg" | grep -v "AD-1 l" | grep -v "l=" | grep -v "\[\[Pound sterling|l" | grep -v "{{not English inline}}" | sort > liters-fixme1.txt

../venv/bin/python3 ../dump_grep_csv.py "[rBbMm]illion l[^a-zA-Z0-9']" | sort > liters-fixme2.txt

../venv/bin/python3 ../dump_grep_csv.py '([Ll]iter|[Ll]itre)s?\|l]]'| perl -pe "s%\{\{cite.*?\}\}%%g" | sort > liters-fixme3.txt

../venv/bin/python3 ../dump_grep_csv.py "[0-9]&nbsp;l[^A-Za-z'0-9]" | sort > liters-fixme4.txt

../venv/bin/python3 ../dump_grep_csv.py "/l" | perl -pe "s/{{not a typo.*?}}//" | perl -pe "s/{{math.*?}}//" | perl -pe "s%<math>.*?</math>%%g" | perl -pe "s/(File|Image):.*?\|//g" | grep -P "[^A-Za-z\./][A-Za-z]{1,4}/l[^a-zA-Z${NON_ASCII_LETTERS}'0-9/\-_]" | grep -vP "w/l(-[0-9])? *=" | grep -vP "(https?://|data:)[A-Za-z0-9_\-\./,\+%~;]+/l[^a-zA-Z'’]" | grep -vP "[^a-zA-Z0-9]r/l" | grep -vP "[^a-zA-Z0-9]d/l[^a-zA-Z0-9]" | grep -vP "\[\[(\w+ )+a/l [\w ]+\]\]" | grep -vP "\{\{cite.{5,100} a/l .{5,100}\}\}" | grep -v "Malaysian names#Indian names|a/l" | grep -vP "Length at the waterline\|(Length )?w/l" | grep -v "Waterline length|w/l" | sort > liters-fixme5.txt
# Done for fixme5:
# expand "m/l" to "music and lyrics" or drop
# expand "w/l" to "win/loss"
# expand "s/l" to "sideline" "l/b" to "sideline" (line ball)
# change "a/l" to "[[Malaysian names#Indian names|a/l]]" except inside internal or external links

../venv/bin/python3 ../dump_grep_csv.py '{{(convert|cvt)\|[^\}]+\|l(\||}|/)' | sort > liters-fixme6.txt

../venv/bin/python3 ../dump_grep_csv.py ' [0-9,\.]+( |&nbsp;)?l/[a-zA-Z0-9]' | sort > liters-fixme7.txt

cat liters-fixme* | perl -pe 's/(.*?):.+/$1/' | uniq > liters-all.txt

# --- X TO TIMES SYMBOL ---

echo "Starting x-to-times"
echo `date`

../venv/bin/python3 ../dump_grep_csv.py '[0-9]x[^a-zA-Z]' | perl -pe 's/\[\[(File|Image):.*?\]\]//' | perl -pe s'/\| *image[0-9]? *=$//' | perl -pe 's/https?:.*? //' | grep -vP '[a-zA-Z\-_][0-9]+x' | grep -vP 'x[a-zA-Z]' | grep -vP '( 4x4 | 6x6 )' | grep -vP '[0-9]+x[0-9]+px' | grep -v '<math' | grep -vP '[^0-9]0x[0-9]+' | grep -P '[0-9]+x[0-9]*' | perl -pe 's/:.*$//' | uniq | sort > x-correct-nospace-with-article.txt
../venv/bin/python3 ../dump_grep_csv.py " x " | perl -pe 's/:.*$//' | uniq | sort > x-correct-space-with-article.txt

# --- RHYME SCHEMES ---

# Run time: About 2 h

echo "Starting rhyme scheme report"
echo `date`

../venv/bin/python3 ../dump_grep_regex.py "[Rr]hym|[Pp]oem|[Ss]tanza|[Vv]erse|[Ll]yric" > tmp-rhyme-dump.xml

cat tmp-rhyme-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py "[^a-z0-9\-A-Z${NON_ASCII_LETTERS}][Aa]-[Bb][^a-zA-Z${NON_ASCII_LETTERS}]" | perl -pe 's/\<math.*?\<\/math\>//ig' | perl -pe 's/<ref.*?(\/ ?>|<\/ref>)//ig' | perl -pe 's/\{\{cite.*?\}\}//ig' | grep -i "a-b" | grep -v "A-B-C-D-E-F-G" | sort > tmp-rhyme-a-b.txt
cat tmp-rhyme-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py "[^,]AB,[ABC]|AA,AB|AA,B|AB,[ABC]" | grep -v "<math" | grep -vP "^(Rhyme scheme:|The Raven:)" | sort > tmp-rhyme-AB-comma.txt
cat tmp-rhyme-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py "[^A-Za-z0-9\./%#=_\-](aa|ab|aaa|aab|aba|abb|abc|aaaa|aaba|aabb|aabc|abaa|abab|abba|abca|abcb|abcc|abcd)[^a-z0-9/]" | perl -pe 's/<ref.*?(\/ ?>|<\/ref>)//ig' | grep -P "(aa|ab)" | sort > tmp-rhyme-masked-words.txt
cat tmp-rhyme-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py "([^a-z\+/]a\.b\.[^d-z]|[^a-z\+/]a\. b\. [^d-z])" | grep -v "Exemplum:" | sort > tmp-rhyme-a.b.txt

# These may need to be relaxed in the future
grep -v "{{not a typo" tmp-rhyme-AB-comma.txt > tmp-rhyme.txt
grep -iP "rhym" tmp-rhyme-masked-words.txt | grep -v "{{not a typo" >> tmp-rhyme.txt
grep --no-filename -iP "rhym|poem" tmp-rhyme-a-b.txt tmp-rhyme-a.b.txt | grep -v "{{not a typo" >> tmp-rhyme.txt
cat tmp-rhyme.txt | perl -pe 's/^(.*?):(.*)$/* [[$1]] - <nowiki>$2<\/nowiki>/' > beland-rhyme.txt

rm -f tmp-rhyme-dump.xml

# --- TEMPERATURE CONVERSION ---

# Run time for this segment: ~2h (8-core parallel)

echo "Beginning temperature conversion scan"
echo `date`

# per [[MOS:UNITSYMBOLS]]

# Need to convert to C:
../venv/bin/python3 ../dump_grep_csv.py '°F' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | grep -vP '°C.{0,30}°F' | grep -vP '°F.{0,30}°C' | grep -vP "(min|max|mean)_temp_[0-9]" | grep "°F" | sort > tmp-temperature-convert1.txt

../venv/bin/python3 ../dump_grep_csv.py '[ \(][0-9](C|F)[^a-zA-Z0-9]' | grep -iP "weather|temperature" | sort > tmp-temperature-convert2.txt
../venv/bin/python3 ../dump_grep_csv.py "[0-9]+s?( |&nbsp;)(C|F)[^a-zA-Z0-9]" | grep -iP "weather|temperature" | sort > tmp-temperature-convert3.txt
../venv/bin/python3 ../dump_grep_csv.py "degrees? \[*(C|c|F)" | perl -pe "s%<ref.*?</ref>%%g" | grep -P "degrees? \[*(C|c|F)" | sort > tmp-temperature-convert4.txt
../venv/bin/python3 ../dump_grep_csv.py '[0-9]°' | grep -iP "heat|chill|weather" | sort > tmp-temperature-convert4b.txt
../venv/bin/python3 ../dump_grep_csv.py '[0-9][0-9],' | grep -iP "weather=" | sort > tmp-temperature-convert4c.txt

../venv/bin/python3 ../dump_grep_csv.py "[0-9]0s( |&nbsp;)?F[^b-z]" | grep -vP "[0-9]{3}0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep "0s" | sort > tmp-temperature-convert5.txt
../venv/bin/python3 ../dump_grep_csv.py "(low|lower|mid|middle|high|upper|the)[ \-][0-9][0-9]?0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep -i "temperature" | grep "0s" | sort > tmp-temperature-convert6.txt

# low 40s F (~5°C)
# mid 40s F (~7°C)
# high 40s F (~9°C)
# low 50s F (~11°C)
# mid 50s F (~13°C)
# high 50s F (~14°C)
# low 60s F (~16°C)
# mid 60s F (~18°C)
# high 60s F (~20°C)
# low 70s F (~22°C)
# mid 70s F (~24°C)
# high 70s F (~25°C)
# low 80s F (~27°C)
# mid 80s F (~29°C)
# high 80s F (~31°C)
# low 90s F (~33°C)
# mid 90s F (~35°C)
# high 90s F (~36°C)
#
# F  C
# 40 4.4
# 45 7.2
# 50 10
# 55 12.8
# 60 15.5
# 65 18.3
# 70 21.1
# 75 23.8
# 80 26.7
# 85 29.4
# 90 32.2
# 95 35
# 100 37.8

cat tmp-temperature-convert1.txt tmp-temperature-convert2.txt tmp-temperature-convert3.txt tmp-temperature-convert4.txt tmp-temperature-convert4b.txt tmp-temperature-convert4c.txt tmp-temperature-convert5.txt tmp-temperature-convert6.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-temperature-convert.txt

# --- SPEED CONVERSION ---

# [[MOS:UNITNAMES]]

echo "Beginning speed conversion scan"
echo `date`

# Run time for this segment: About 1 h 40 min

../venv/bin/python3 ../dump_grep_csv.py 'mph|MPH' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | perl -pe "s%<ref.*?</ref>%%g" | grep -vP 'km/h.{0,30}mph' | grep -vP 'mph.{0,30}km/h' | grep -iP "\bmph\b" | grep -v ", MPH" | grep -iP "(speed|mile|[0-9](&nbsp;| )MPH)" | grep -v "mph=" | sort > tmp-mph-convert.txt
cat tmp-mph-convert.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-speed-convert.txt

../venv/bin/python3 ../dump_grep_csv.py '[0-9](&nbsp;| )?kph|KPH' | sort > tmp-kph-convert.txt

# --- MORE METRIC CONVERSIONS ---

# TODO:
# * miles
# * pounds (weight vs. money)
# * tons (various)
# * hp
# * gallons (various)

# --- FUEL EFFICIENCY CONVERSION ---

echo "Beginning MPG conversion scan"
echo `date`

# Run time for this segment: About 1 h 30 min

# {{cvt}} or {{convert}} should probably be used in all instances to
# convert between US and imperial gallons (ug!)
# ../venv/bin/python3 ../dump_grep_csv.py 'mpg|MPG' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | perl -pe "s%<ref.*?</ref>%%g" | grep -iP "\bmpg\b" | grep -iP "[0-9]( |&nbsp;)mpg" | grep -vP 'L/100.{0,30}mpg' | grep -vP 'mpg.{0,30}L/100'| sort > tmp-mpg-convert.txt
../venv/bin/python3 ../dump_grep_csv.py 'mpg|MPG' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | perl -pe "s%<ref.*?</ref>%%g" | grep -iP "\bmpg\b" | grep -iP "[0-9]( |&nbsp;)mpg" | sort > tmp-mpg-convert.txt

cat tmp-mpg-convert.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-mpg-convert.txt

# DEPENDING ON CONTEXT, WILL NEED:
# {{convert|$1|mpgUS}}
# {{convert|$1|mpgimp}}

# --- PRIME ---

echo "Beginning prime template check"
echo `date`

# Run time for this segment: ~3 h 50 min

# Incorrect template usage
../venv/bin/python3 ../dump_grep_csv.py "\{\{prime\}\}" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort > jwb-articles-prime.txt
../venv/bin/python3 ../dump_grep_csv.py "\{\{prime\|'" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort >> jwb-articles-prime.txt

# Can be converted to {{coord}} or {{sky}} or {{prime}}
../venv/bin/python3 ../dump_grep_csv.py "[0-9]+° ?[0-9]+['′] ?" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort >> jwb-articles-prime.txt

# --- FRAC REPAIR ---

# Run time for this segment: ~2 h (8-core parallel)

echo "Beginning {{frac}} repair scan"
echo `date`

../venv/bin/python3 ../dump_grep_csv.py '[0-9]\{\{frac\|[0-9]+\|' | perl -pe 's/^(.*?):.*/$1/' | uniq | sort > jwb-frac-repair.txt

# --- BROKEN NBSP ---

# Run time for this segment: ?

echo "Beginning broken nbsp scan"
echo `date`

../venv/bin/python3 ../dump_grep_csv.py "&nbsp[^;}]" | grep -vP 'https?:[^ ]+&nbsp' | perl -pe 's/^(.*?):.*/$1/' | uniq | sort | perl -pe 's/^(.*)$/* [[$1]]/' > beland-broken-nbsp.txt

# --- MOS:LOGICAL ---

# Run time for this segment: ~15 min (8-core parallel)

echo "Beginning MOS:LOGICAL scan"
echo `date`
../venv/bin/python3 ../dump_grep_csv.py '"[a-z ,:\-;]+[,\.]"' | perl -pe 's/^(.*?):.*/$1/' | uniq | sort | uniq > beland-MOS-LOGICAL.txt

# --- MOS:DOUBLE ---

# Run time for this segment: ~20 min

echo "Beginning MOS:DOUBLE scan"
echo `date`
../venv/bin/python3 ../dump_grep_csv.py " '[A-Za-z ,:\-;]+'[,\. \}\)]" | grep -v '"' | grep -vP "{{([Ll]ang|[Tt]ransl|IPA)" | perl -pe 's/^(.*?):.*/$1/' > tmp-MOS-double.txt
cat tmp-MOS-double.txt | perl ../count.pl | sort -rn > tmp-double-most.txt
grep -vP "(grammar|languag|species| words)" tmp-double-most.txt | perl -pe "s/^\d+\t//" | head -1000 > jwb-double-most.txt

# --- BAD QUOTE MARKS ---

echo "Starting bad quote mark report..."
echo `date`

# ../venv/bin/python3 ../dump_grep_csv.py '\{\{[Cc]ite (web|news|journal)[^\}]+(quote|title) *= *"' | sort > tmp-bad-quotes1.txt
# Run time: About 2h per regex

../venv/bin/python3 ../dump_grep_regex.py "(\{\{[Cc]ite |<blockquote>|(C|c|R|r|Block|block)[Qq]uote)" > tmp-quote-dump.xml
# Run time: About 3h

cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '\{\{[Cc]ite (web|news|journal)[^\}]+(quote|title) *= *"' | sort > tmp-bad-quotes1.txt
cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '\{\{[Cc]ite book[^\}]+chapter *= *"' | sort > tmp-bad-quotes2.txt
cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '<blockquote>[ \n]*"' | sort > tmp-bad-quotes3.txt
cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '\{\{([Bb]lockquote|[Qu]uote|[Cc]quote|[Qq]uote frame) *\| *"' | sort > tmp-bad-quotes4.txt
cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '\{\{([Bb]lockquote|[Qu]uote)[^\}]*?\| *text *= *"' | sort > tmp-bad-quotes5.txt
cat tmp-quote-dump.xml | ../venv/bin/python3 ../dump_grep_inline.py '\{\{([Qu]uote box|[Qq]uote frame|[Rr]quote]|[Cc]quote)[^\}]*?\| *quote *= *"' | sort > tmp-bad-quotes6.txt

cat tmp-bad-quotes1.txt tmp-bad-quotes2.txt tmp-bad-quotes3.txt tmp-bad-quotes4.txt tmp-bad-quotes5.txt tmp-bad-quotes6.txt | perl -pe 's/(.*?):.+/$1/' | uniq > jwb-bad-quotes.txt

rm -f tmp-quote-dump.xml

echo "Done"
echo `date`

# --- READABILITY ---

echo "Beginning readability check"
echo `date`

# Run time for this segment: ~1h (8-core parallel)

../venv/bin/python3 ../moss_readability_check.py > tmp-readability.txt
sort -k2 -n tmp-readability.txt > post-readability.txt
rm tmp-readability.txt

