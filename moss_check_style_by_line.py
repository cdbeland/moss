# For CPU performance trace:
# venv/bin/pip install mtprof
# venv/bin/python3 -m mtprof moss_check_style_by_line.py

# Run time (commit af4ead3, 4 types of complaint): ~2 hours, 8-core parallel

import re
from moss_dump_analyzer import read_en_article_text

NON_ASCII_LETTERS = "ậạàÁáÂâÃãÄäầåấæɑ̠āÇçÈèÉéÊêËëēÌìÍíÎîÏïĭǐīʝÑñÒòÓóÔôÕõÖöớộøōŠšÚúùÙÛûǚÜüũưụÝýŸÿŽžəþɛ"

digit_re = re.compile(r"[0-9]")
remove_math_line_re = re.compile(r"(<math.*?(</math>|$)|\{\{math[^}]+\}?\}?)")
remove_math_article_re = re.compile(r"(<math.*?</math>|\{\{math[^}]+\}?\}?)", flags=re.S)
remove_ref_re = re.compile(r"<ref.*?(\/ ?>|<\/ref>)")
remove_cite_re = re.compile(r"\{\{cite.*?\}\}")
remove_not_a_typo_re = re.compile(r"\{\{not a typo.*?\}\}")
remove_url_re = re.compile(r"https?:[^ \]]+")
remove_image_re = re.compile(r"\[\[(File|Image):.*?\|")
remove_image_param_re = re.compile(r"\| *image[0-9]? *=.*$")

poetry_flags = ["rhym", "poem", "stanza", "verse", "lyric"]
poetry_flags += [word.title() for word in poetry_flags]

remove_code_re = re.compile(r"<code.*?</code>", re.S)
remove_syntaxhighlight_re = re.compile(r"<syntaxhighlight.*?</syntaxhighlight>", re.S)


def remove_image_filenames(line):
    remove_image_re.sub("✂", line)
    remove_image_param_re.sub("✂", line)
    return line


def poetry_match(text):
    # Considerably faster than a regex
    for word in poetry_flags:
        if word in text:
            return True
    return False


def set_article_flags(article_text):
    article_flags = dict()
    article_flags["poetry"] = poetry_match(article_text)
    return article_flags


def set_line_flags(line):
    line_flags = dict()
    if digit_re.search(line):
        line_flags["has_digit"] = True
    else:
        line_flags["has_digit"] = False
    return line_flags


def universal_article_text_cleanup(article_text):
    if "math" in article_text:
        article_text = remove_math_article_re.sub("✂", article_text)

    if "syntaxhighlight" in article_text:
        article_text = remove_syntaxhighlight_re.sub("✂", article_text)

    if "code" in article_text:
        article_text = remove_code_re.sub("✂", article_text)

    return article_text


def universal_line_cleanup(line):
    if "ypo" in line:
        line = remove_not_a_typo_re.sub("✂", line)
    return line


def check_style_by_line(article_title, article_text):
    article_flags = set_article_flags(article_text)
    problem_line_tuples = []
    article_text = universal_article_text_cleanup(article_text)

    for line in article_text.splitlines():
        line = universal_line_cleanup(line)
        line_flags = set_line_flags(line)

        # Avoiding extend() helps performance massively
        if article_flags["poetry"]:
            result = rhyme_scheme_check(line, line_flags)
            if result:
                problem_line_tuples.extend(result)
        for check_function in [x_to_times_check,
                               broken_nbsp_check,
                               frac_repair]:
            result = check_function(line, line_flags)
            if result:
                problem_line_tuples.extend(result)

    if not problem_line_tuples:
        return None
    line_string = "\n".join([f"{code}\t{article_title}\t{line_text}"
                             for (code, line_text) in problem_line_tuples])
    return line_string


rhyme_fast_re = re.compile(r"[Aa][,\-\.]?[AaBb]")
rhyme_dashed_re = re.compile(r"[^a-z0-9\-A-Z{NON_ASCII_LETTERS}][Aa]-[Bb][^a-zA-Z{NON_ASCII_LETTERS}]")
rhyme_comma_re = re.compile(r"AA,A?B|AB,[ABC]")
rhyme_masked_re = re.compile(r"[^A-Za-z0-9\./%#=_\-]a(a|b|aa|ab|ba|bb|bc|aaa|aba|abb|abc|baa|bab|bba|bca|bcb|bcc|bcd)[^a-z0-9/]")
rhyme_dot_re = re.compile(r"([^a-z\+/]a\.b\.[^d-z]|[^a-z\+/]a\. b\. [^d-z])")


def rhyme_scheme_check(line, line_flags):
    if "a" in line:
        line_flags["a"] = True
    else:
        line_flags["a"] = False
    if "A" in line:
        line_flags["A"] = True
    else:
        line_flags["A"] = False

    if not (line_flags["a"] or line_flags["A"]):
        return

    if not rhyme_fast_re.search(line):
        return

    outer_match = False
    if rhyme_dashed_re.search(line):
        outer_match = True
    if line_flags["a"] and (rhyme_dot_re.search(line) or rhyme_masked_re.search(line)):
        outer_match = True
        outer_match = True
    if line_flags["A"] and rhyme_comma_re.search(line):
        outer_match = True

    if not outer_match:
        return

    line_tmp = remove_ref_re.sub("✂", line)
    line_tmp = remove_cite_re.sub("✂", line_tmp)
    # line_tmp = remove_math_line_re.sub("✂", line_tmp)
    if "A-B-C-D-E-F-G" in line_tmp:
        return
    # Re-confirm match after filtering:
    if poetry_match(line_tmp):
        if rhyme_dashed_re.search(line_tmp) or rhyme_comma_re.search(line_tmp) or rhyme_dot_re.search(line_tmp) or rhyme_masked_re.search(line_tmp):
            return [("R", line)]
    return


x_no_space_re = re.compile(r"[0-9]x[0-9]")
x_no_space_exclusions = re.compile(r"([a-zA-Z\-_][0-9]+x"
                                   r"| 4x4 "
                                   r"| 6x6 "
                                   r"|[0-9]+x[0-9]+px"
                                   r"|[^0-9]0x[0-9]+)")
x_space_exclusions = re.compile(r"("
                                r"x ="
                                r"|\| x \|"
                                r")")


def x_to_times_check(line, line_flags):
    if " x " in line:
        # line_tmp = remove_math_line_re.sub("✂", line)
        line_tmp = x_space_exclusions.sub("✂", line)
        if " x " in line_tmp:
            return [("XS", line_tmp)]  # X with Space

    if line_flags["has_digit"]:
        if not x_no_space_re.search(line):
            return
        if x_no_space_exclusions.search(line):
            return
        line_tmp = remove_image_filenames(line)
        line_tmp = remove_url_re.sub("✂", line_tmp)
        # line_tmp = remove_math_line_re.sub("✂", line_tmp)
        if x_no_space_re.search(line_tmp):
            return [("XNS", line_tmp)]  # X with No Space


broken_nbsp_re = re.compile(r"&nbsp[^;}]")


def broken_nbsp_check(line, line_flags):
    if "&nbsp" not in line:
        return
    if broken_nbsp_re.search(line):
        if not re.search(r"https?:[^ ]+&nbsp", line):
            return [("N", line)]  # broken Nbsp


frac_repair_re = re.compile(r"[0-9]\{\{frac\|[0-9]+\|")


def frac_repair(line, line_flags):
    if not line_flags["has_digit"]:
        return
    if "frac" not in line:
        return
    if frac_repair_re.search(line):
        return [("FR", line)]  # FRaction repair needed


r"""

# --- SPEED CONVERSION ---

# [[MOS:UNITNAMES]]

echo "Beginning speed conversion scan"
echo `date`

# Run time for this segment: About 1 h 40 min

../venv/bin/python3 ../dump_grep_csv.py 'mph|MPH' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | perl -pe "s%<ref.*?</ref>%%g" | grep -vP 'km/h.{0,30}mph' | grep -vP 'mph.{0,30}km/h' | grep -iP "\bmph\b" | grep -v ", MPH" | grep -iP "(speed|mile|[0-9](&nbsp;| )MPH)" | grep -v "mph=" | sort > tmp-mph-convert.txt
cat tmp-mph-convert.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-speed-convert.txt

../venv/bin/python3 ../dump_grep_csv.py '[0-9](&nbsp;| )?kph|KPH' | sort > tmp-kph-convert.txt


# --- MOS:LOGICAL ---

# Run time for this segment: ~15 min (8-core parallel)

echo "Beginning MOS:LOGICAL scan"
echo `date`
../venv/bin/python3 ../dump_grep_csv.py '"[a-z ,:\-;]+[,\.]"' | perl -pe 's/^(.*?):.*/$1/' | uniq | sort | uniq > beland-MOS-LOGICAL.txt

# ---

def liter_lowercase_check(line, line_flags):
    # Per April 2021 RFC that updated [[MOS:UNITSYMBOLS]]

    if "l" not in line:
        return []

# For "(l)", "(l/c/d)", etc. in table headers


../venv/bin/python3 ../dump_grep_csv.py "[0-9] l" | perl -pe "s%\{\{cite.*?\}\}%%g" | perl -pe "s%\{\{(Transliteration|lang|IPA|not a typo).*?\}\}%%g" | perl -pe "s%<math.*?</math>%%g" | perl -pe "s/(File|Image):.*?[\|\n]//g" | grep -P "[^p][^.]\s?[0-9]+ l[^a-zA-Z0-9'’{NON_ASCII_LETTERS}]" | grep -vi " l.jpg" | grep -vP "image[0-9]? *=.* l[ \.].jpg" | grep -v "AD-1 l" | grep -v "l=" | grep -v "\[\[Pound sterling|l" | grep -v "{{not English inline}}" | sort > tmp-liters-fixme1.txt

../venv/bin/python3 ../dump_grep_csv.py "[rBbMm]illion l[^a-zA-Z0-9']" | sort > tmp-liters-fixme2.txt
../venv/bin/python3 ../dump_grep_csv.py "[0-9]&nbsp;l[^A-Za-z'0-9]" | sort > tmp-liters-fixme4.txt
../venv/bin/python3 ../dump_grep_csv.py ' [0-9,\.]+( |&nbsp;)?l/[a-zA-Z0-9]' | sort > tmp-liters-fixme7.txt

../venv/bin/python3 ../dump_grep_csv.py '([Ll]iter|[Ll]itre)s?\|l]]'| perl -pe "s%\{\{cite.*?\}\}%%g" | sort > tmp-liters-fixme3.txt
../venv/bin/python3 ../dump_grep_csv.py '{{(convert|cvt)\|[^\}]+\|l(\||}|/)' | sort > tmp-liters-fixme6.txt
../venv/bin/python3 ../dump_grep_csv.py '\(l(/[a-zA-Z/]+)?\)' | grep -v '(l)\!' | grep -v '(r)' | grep -vP "[a-zA-Z{NON_ASCII_LETTERS}]\(l\)" | grep -vP "\(l\)[a-zA-Z{NON_ASCII_LETTERS}]" | grep -vP '</?math' | sort > tmp-liters-fixme0.txt

../venv/bin/python3 ../dump_grep_csv.py "/l" | perl -pe "s/{{not a typo.*?}}//" | perl -pe "s/{{math.*?}}//" | perl -pe "s%<math>.*?</math>%%g" | perl -pe "s/(File|Image):.*?\|//g" | grep -P "[^A-Za-z\./][A-Za-z]{1,4}/l[^a-zA-Z{NON_ASCII_LETTERS}'0-9/\-_]" | grep -vP "w/l(-[0-9])? *=" | grep -vP "(https?://|data:)[A-Za-z0-9_\-\./,\+%~;]+/l[^a-zA-Z'’]" | grep -vP "[^a-zA-Z0-9]r/l" | grep -vP "[^a-zA-Z0-9]d/l[^a-zA-Z0-9]" | grep -vP "\[\[(\w+ )+a/l [\w ]+\]\]" | grep -vP "\{\{cite.{5,100} a/l .{5,100}\}\}" | grep -v "Malaysian names#Indian names|a/l" | grep -vP "Length at the waterline\|(Length )?w/l" | grep -v "Waterline length|w/l" | sort > tmp-liters-fixme5.txt
# Done for fixme5:
# expand "m/l" to "music and lyrics" or drop
# expand "w/l" to "win/loss"
# expand "s/l" to "sideline" "l/b" to "sideline" (line ball)
# change "a/l" to "[[Malaysian names#Indian names|a/l]]" except inside internal or external links
"""

r"""


# --- TEMPERATURE CONVERSION ---

# Run time for this segment: ~2h (8-core parallel)

echo "Beginning temperature conversion scan"
echo `date`

# per [[MOS:UNITSYMBOLS]], need to convert to C

echo "  Beginning F scan..."
echo `date`
../venv/bin/python3 ../dump_grep_csv.py F | grep -P "(°F|0s( |&nbsp;)F[^b-z])" > tmp-temp-F.txt

grep '°F' tmp-temp-F.txt | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | grep -vP '°C.{0,30}°F' | grep -vP '°F.{0,30}°C' | grep -vP "(min|max|mean)_temp_[0-9]" | grep "°F" | sort > tmp-temperature-convert1.txt
grep "[0-9]0s( |&nbsp;)?F[^b-z]" tmp-temp-F.txt | grep -vP "[0-9]{3}0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep "0s" | sort > tmp-temperature-convert5.txt

echo "  Beginning weather scan..."
echo `date`
../venv/bin/python3 ../dump_grep_csv.py "([Ww]eather|WEATHER|[Tt]emperature|TEMPERATURE|[Hh]eat|HEAT|[Cc]hill|CHILL)" > tmp-temp-weather.txt

grep '[ \(][0-9](C|F)[^a-zA-Z0-9]' tmp-temp-weather.txt | sort > tmp-temperature-convert2.txt
grep "[0-9]+s?( |&nbsp;)(C|F)[^a-zA-Z0-9]" tmp-temp-weather.txt | sort > tmp-temperature-convert3.txt
grep '[0-9]°' tmp-temp-weather.txt | sort > tmp-temperature-convert4b.txt
grep '[0-9][0-9],' tmp-temp-weather.txt | grep -iP "weather=" | sort > tmp-temperature-convert4c.txt
../venv/bin/python3 ../dump_grep_csv.py "(low|lower|mid|middle|high|upper|the)[ \-][0-9][0-9]?0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep "0s" | sort > tmp-temperature-convert6.txt

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


echo "  Beginning degree scan..."
../venv/bin/python3 ../dump_grep_csv.py "degrees? \[*(C|c|F)" | perl -pe "s%<ref.*?</ref>%%g" | grep -P "degrees? \[*(C|c|F)" | sort > tmp-temperature-convert4.txt

cat tmp-temperature-convert1.txt tmp-temperature-convert2.txt tmp-temperature-convert3.txt tmp-temperature-convert4.txt tmp-temperature-convert4b.txt tmp-temperature-convert4c.txt tmp-temperature-convert5.txt tmp-temperature-convert6.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-temperature-convert.txt

# rm -f tmp-temp-weather.txt
# rm -f tmp-temp-F.txt

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


# TODO:
# " ,". "( ", " )", " !", " .[^0-9]", "[0-9]%"

"""


if __name__ == "__main__":
    read_en_article_text(check_style_by_line, parallel=True)
