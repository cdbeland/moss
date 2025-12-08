# For CPU performance trace:
# venv/bin/pip install mtprof
# venv/bin/python3 -m mtprof moss_check_style_by_line.py

# Usage: venv/bin/python3 moss_check_style_by_line.py REDIRECTS_FILE.CSV

# Run time (commit af4ead3, 4 types of complaint): ~2 hours, 8-core parallel

from pprint import pformat
import re
import sys
import traceback
from moss_dump_analyzer import read_en_article_text

print("Loading redirects...", file=sys.stderr)
redirect_filename = sys.argv[1]
redirect_dict = {}
for redirect_pair in open(redirect_filename, "r"):
    (redirect_from, redirect_to) = redirect_pair.split("\t")
    redirect_dict[redirect_from] = redirect_to
print("Finished loading redirects.", file=sys.stderr)

# VALUE CAN BE A STRING OR A LIST OF STRINGS
### TODO: Support both "and" and "or" logic in lists
ascii_equiv_letters = {
    "á": "a",
    "Á": "A",
    "à": "a",
    "ă": "a",
    "â": "a",
    "Â": "A",
    "ấ": "a",
    "ầ": "a",
    "å": "a",
    "Å": "A",
    "ä": "a",
    "Ä": "A",
    "ã": "a",
    "Ã": "A",
    "ā": "a",
    "Ā": "A",
    "ạ": "a",
    "ậ": "a",
    "æ": "ae",
    "ɑ̠": "a",
    "ć": "c",
    "č": "c",
    "ç": "c",
    "Ç": "C",
    "đ": "d",
    "Đ": "D",
    "ḍ": "d",
    "é": "e",
    "É": "E",
    "è": "e",
    "È": "E",
    "ĕ": "e",
    "ê": "e",
    "Ê": "E",
    "Ě": "E",
    "ë": "e",
    "Ë": "E",
    "ē": "e",
    "ǵ": "g",
    "Ǵ": "G",
    "ĥ": "h",
    "ħ": "h",
    "ḥ": "h",
    "Ḥ": "H",
    "í": "i",
    "Í": "I",
    "ì": "i",
    "Ì": "I",
    "ĭ": "i",
    "î": "i",
    "Î": "I",
    "ǐ": "i",
    "ï": "i",
    "Ï": "I",
    "İ": "I",
    "ī": "i",
    "Ī": "I",
    "ı": "i",
    "ɪ": "i",
    "ʝ": "j",
    "ḳ": "k",
    "ł": "l",
    "Ł": "L",
    "ḷ": "l",
    "ń": "n",
    "ñ": "n",
    "Ñ": "N",
    "ṅ": "n",
    "ó": "o",
    "Ó": "O",
    "ò": "o",
    "Ò": "O",
    "ô": "o",
    "Ô": "O",
    "ö": "o",
    "Ö": "O",
    "õ": "o",
    "Õ": "O",
    "ø": "o",
    "ō": "o",
    "Ō": "O",
    "ớ": "o",
    "ộ": "o",
    "Ś": "S",
    "š": "s",
    "Š": "S",
    "ş": "s",
    "Ş": "S",
    "ṣ": "s",
    "Ṣ": "S",
    "ţ": "t",
    "ṭ": "t",
    "Ṭ": "T",
    "ț": "t",
    "ú": "u",
    "Ú": "U",
    "ù": "u",
    "Ù": "U",
    "û": "u",
    "Û": "U",
    "ü": "u",
    "Ü": "U",
    "ǚ": "u",
    "ũ": "u",
    "ū": "u",
    "Ū": "U",
    "ư": "u",
    "ụ": "u",
    "ý": "y",
    "Ý": "Y",
    "ÿ": "y",
    "Ÿ": "Y",
    "ź": "z",
    "ž": "z",
    "Ž": "Z",
    "ż": "z",
    "ẓ": "z",

    "À": "A",
    "Ă": "A",
    "ắ": "a",
    "ằ": "a",
    "ẵ": "a",
    "Ấ": "A",
    "ẫ": "a",
    "ẩ": "a",
    "Ẩ": "A",
    "ǎ": "a",
    "ȧ": "a",
    "Ȧ": "A",
    "ą": "a",
    "Ą": "A",
    "ả": "a",
    "Ả": "A",
    "ặ": "a",
    "Æ": "AE",
    "ǽ": "ae",
    "Ǣ": "AE",
    "ḃ": "b",
    "Ƀ": "B",
    "Ɓ": "B",
    "Ć": "C",
    "ĉ": "c",
    "Ĉ": "C",
    "Č": "C",
    "ċ": "c",
    "Ċ": "C",
    "Ḉ": "C",
    "Ȼ": "C",
    "Ƈ": "C",
    "ď": "d",
    "Ď": "D",
    "ḑ": "d",
    "Ḑ": "D",
    "Ḍ": "D",
    "ḏ": "d",
    "Ḏ": "D",
    "ð": "d",
    "Ð": "D",
    "ɗ": "d",
    "Ɗ": "D",
    "ế": "e",
    "ề": "e",
    "ễ": "e",
    "ể": "e",
    "ě": "e",
    "ẽ": "e",
    "Ẽ": "E",
    "ė": "e",
    "Ė": "E",
    "ę": "e",
    "Ę": "E",
    "Ē": "E",
    "ẻ": "e",
    "ẹ": "e",
    "Ẹ": "E",
    "ệ": "e",
    "Ƒ": "F",
    "ğ": "g",
    "Ğ": "G",
    "ĝ": "g",
    "Ĝ": "G",
    "ǧ": "g",
    "Ǧ": "G",
    "ġ": "g",
    "Ġ": "G",
    "ģ": "g",
    "Ģ": "G",
    "Ꞡ": "G",
    "ɡ": "g",
    "ǥ": "g",
    "Ĥ": "H",
    "ȟ": "h",
    "Ȟ": "H",
    "ḩ": "h",
    "Ḩ": "H",
    "Ħ": "H",
    "ḫ": "h",
    "Ḫ": "H",
    "ẖ": "h",
    "ⱨ": "h",
    "Ⱨ": "H",
    "Ĭ": "I",
    "ĩ": "i",
    "į": "i",
    "Į": "I",
    "ỉ": "i",
    "Ȋ": "I",
    "ị": "i",
    "Ɪ": "I",
    "ɨ": "i",
    "Ĵ": "j",
    "ḱ": "k",
    "Ḱ": "K",
    "Ǩ": "K",
    "ķ": "k",
    "Ķ": "K",
    "Ꞣ": "K",
    "ḵ": "k",
    "Ḵ": "K",
    "Ƙ": "K",
    "ⱪ": "k",
    "ĺ": "l",
    "ľ": "l",
    "Ľ": "L",
    "ļ": "l",
    "Ļ": "L",
    "Ḷ": "L",
    "Ḹ": "L",
    "ḻ": "l",
    "Ḿ": "M",
    "ṁ": "m",
    "ṃ": "m",
    "Ɱ": "M",
    "Ń": "N",
    "Ǹ": "N",
    "ň": "n",
    "Ň": "N",
    "Ṅ": "N",
    "ņ": "n",
    "Ņ": "N",
    "Ꞥ": "N",
    "ṇ": "n",
    "Ṇ": "N",
    "ṉ": "n",
    "Ɲ": "N",
    "ꞑ": "n",
    "ŋ": "n",
    "ŏ": "o",
    "Ŏ": "O",
    "ố": "o",
    "Ố": "O",
    "ồ": "o",
    "ỗ": "o",
    "ổ": "o",
    "ǒ": "o",
    "ő": "o",
    "Ő": "O",
    "Ø": "O",
    "ǫ": "o",
    "Ǫ": "O",
    "ỏ": "o",
    "ơ": "o",
    "Ơ": "O",
    "ờ": "o",
    "ỡ": "o",
    "ở": "o",
    "ợ": "o",
    "ọ": "o",
    "Ọ": "O",
    "œ": "oe",
    "Œ": "OE",
    "Ꝍ": "O",
    "ⱺ": "o",
    "Ṕ": "P",
    "Ƥ": "P",
    "ŕ": "r",
    "Ŕ": "R",
    "ř": "r",
    "Ř": "R",
    "Ꞧ": "R",
    "Ȓ": "R",
    "ṛ": "r",
    "Ṛ": "R",
    "Ṝ": "R",
    "ṟ": "r",
    "𝕊": "S",
    "ś": "s",
    "ŝ": "s",
    "Ŝ": "S",
    "ṡ": "s",
    "Ṡ": "S",
    "Ꞩ": "S",
    "ș": "s",
    "Ș": "S",
    "ť": "t",
    "Ť": "T",
    "Ţ": "T",
    "Ț": "T",
    "ṯ": "t",
    "Ṯ": "T",
    "ᵵ": "t",
    "Ƭ": "T",
    "Ʈ": "T",
    "ŭ": "u",
    "Ŭ": "U",
    "ǔ": "u",
    "ů": "u",
    "ű": "u",
    "Ű": "U",
    "Ũ": "U",
    "ų": "u",
    "Ų": "U",
    "ṻ": "u",
    "ủ": "u",
    "Ư": "U",
    "ứ": "u",
    "Ứ": "U",
    "ừ": "u",
    "ữ": "u",
    "ử": "u",
    "ự": "u",
    "ṳ": "u",
    "ʉ": "u",
    "Ẃ": "W",
    "ẁ": "w",
    "Ẁ": "W",
    "ŵ": "w",
    "Ŵ": "W",
    "Ẋ": "X",
    "ỳ": "y",
    "ŷ": "y",
    "ỹ": "y",
    "Ỹ": "Y",
    "Ȳ": "Y",
    "ỷ": "y",
    "Ỷ": "Y",
    "ỵ": "y",
    "Ƴ": "Y",
    "Ź": "Z",
    "ẑ": "z",
    "Ẑ": "Z",
    "Ż": "Z",
    "Ẓ": "Z",
    "ẕ": "z",
    "Ẕ": "Z",
    "ƶ": "z",
    "Ȥ": "Z",

    # Latin epsilon, used in various languages
    "Ɛ": "E",
    "ɛ": "e",
    "Ɛ̃": "E",

    # Cyrillic but close enough
    "ї": "i",
    "Ӕ": "AE",

    # Greek
    "α": "alpha",
    "Α": "Alpha",
    "β": "beta",
    "Β": "Beta",
    "γ": "gamma",
    "Γ": "Gamma ",
    "δ": "delta",
    "Δ": "Delta",
    "ε": "epsilon",
    "Ε": "Epsilon",
    "κ": "kappa",
    "μ": "u",
    "Ζ": "Zeta",
    "η": "eta",
    "Η": "Eta",
    # "Θ": "",
    "Λ": "Lambda",
    "ν": "v",  # nu
    "Ξ": " Xi ",
    "π": "pi",  # Wave of discussions in 2010s supported keeping with redirect
    "Π": "Pi",
    # "ρ": "",
    "σ": "sigma",
    "Σ": "Sigma",
    # "φ": "",
    # "Φ": "",
    "Ψ": "Psi",
    "ω": " omega ",
    "Ω": "Omega",
}

ascii_equiv_other = {
    "ʻ": "'",  # U+02BB Modifier letter turned comma ('okina)
    "ʾ": "'",  # U+02BE Modifier letter right half ring (hamza)
    "ʿ": "'",  # U+02BF Modier letter left half ring (ayin)
    # "ʽ": "'",  # U+02BD Modier letter reversed comma (ayin) - change to U+02BF?
    "¹": "1",
    "₁": "1",
    "²": "2",
    "₂": "2",
    "³": "3",
    "⁵": "5",
    "½": " 1/2",
    "¼": " 1/4",
    "¾": " 3/4",
    "¢": " cents ",
    "×": "x",    # Times symbol
    "÷": "/",
    "±": " Plus/Minus ",
    "ʼ": "'",    # U+02BC Modifier letter apostrophe ([[Baháʼí orthography]], First Nation languages)
    "—": "-",    # U+2014
    "₀": " subscript zero",
    "ℓ": "l",    # Math
    "⋯": "...",  # Math
    "¥": "Y",

    # Ordinal indicators for some non-English works (restricted by regex later)
    "ª": "a",
    "º": "o",

    "−": "-",  # U+2212 Minus Sign from ASCII dash (needed in some
               # math-related titles, some astronomical objects, and
               # some time zones, but wrong for titles with year
               # ranges and hyphenated words)

    # In some weird proper nouns, titles of works
    "«": '"',   # Musical work
    "»": '"',   # Musical work
    "™": "TM",
    "§": "S",   # Weird poetry; should normally be moved to "Section"
    "®": "^R",  # Musical works
    "·": "-",   # Also STEM, some Spanish places
    "•••–": "dot dot dot dash",

    "♭": " flat ",
    "♯": " sharp ",

    # Imported from Cyrillic as a Latin letter in [[Yañalif]]
    "ь": ["b", "i"],

    # First Nation languages and PIE
    "ʰ": "h",
    "ʷ": "w",
    "ᵘ": "u",
    "ⁿ": "n",

    # In some African languages
    "ɣ": ["g'", "y"],
    "ʔ": ["?", "'"],  # Glottal stop
    "ɂ": ["?", "'"],  # Glottal stop

    # Azerbaijani
    "ə": ["a", "e"],
    "Ə": ["A", "E"],

    # Spanish
    "¿": ["", "?"],
    "¡": ["", "!"],

    # "Ƽ": "",  # U+01BC Latin capital letter tone five
    # "Ꞌ": "",  # U+A78B Latin capital letter saltillo (Mexican glottal stop)
    # "ꞌ": "",  # U+A78C Latin small letter saltillo (Mexican glottal stop)

    "ǃ": "!",   # U+01C3 Latin letter retroflex click
    "ǀ": ["I", ""],   # Dental click
    "ǁ": ["II", ""],  # Lateral click
    "ǂ": "",          # Palatal click
    "þ": "Th",
    "Þ": "th",
    "ß": "ss",
    # Asked about these and others at
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Article_titles#Unusual_characters_in_proper_names
}

disambig_templates = [
    "{{disamb}}",
    "{{mathdab}}",
    "{{dab}}"
    "{{disambiguation}}",
]

# Must be lowercase
disambig_templates_chinese = [
    "{{disambig|chinese",
    "{{disambiguation|chinese",
    "{{dab|chinese",
    "{{chinese title disambiguation}}",
    "{{disambig-chinese-char-title}}",
]

english_ok_chars = r"a-zA-Z0-9/\!\-_\(\)\.–,\":='\?&%\*\+;@~\$\^\\"
english_ok_re = re.compile(rf"[{english_ok_chars}]+")
ok_with_redirect_chars = "".join(ascii_equiv_letters.keys()) + "".join(ascii_equiv_other.keys())
ok_with_redirect_re = re.compile(rf"[{ok_with_redirect_chars}]+")

NON_ASCII_LETTERS = "".join(ascii_equiv_letters.keys())+"əþɛ"
MAJOR_CURRENCY_SYMBOLS = "€$£¥₹₽₩₺"

digit_re = re.compile(r"[0-9]")
remove_math_line_re = re.compile(r"(<math.*?(</math>|$)|\{\{math[^}]+\}?\}?)")
remove_math_article_re = re.compile(r"(<math.*?</math>|\{\{math[^}]+\}?\}?)", flags=re.S)
remove_ref_re = re.compile(r"<ref.*?(\/ ?>|<\/ref>)")
remove_cite_re = re.compile(r"\{\{([Cc]ite|[Ss]fn).*?\}\}")
remove_not_a_typo_re = re.compile(r"\{\{not a typo.*?\}\}")
remove_url_re = re.compile(r"https?:[^ \]\|]+")
remove_image_re = re.compile(r"(\[\[)?(File|Image):.*?[\|\]]")
remove_image_param_re = re.compile(r"\| *(image[0-9]?|logo|screenshot|sound) *=.*$")
remove_image_no_end_re = re.compile(r"(File|Image):.*?\.(JPG|jpg|SVG|svg|PNG|png|OGG|ogg|JPEG|jpeg|WEBM|webm|GIF|gif|TIF|tif|TIFF|tiff|WEBP|webp|PDF|pdf|MP3|mp3|ogv)")
remove_graphchart_re = re.compile(r"{{[Gg]raphChart.*?}}", re.S)

remove_lang_re = re.compile(r"\{\{([Vv]erse translation|[Ll]ang|[Tt]ransliteration|IPA).*?\}\}")

poetry_flags = ["rhym", "poem", "stanza", "verse", "lyric"]
poetry_flags += [word.title() for word in poetry_flags]

remove_code_re = re.compile(r"<code.*?</code>", re.S)
remove_timeline_re = re.compile(r"<timeline.*?</timeline>", re.S)
remove_syntaxhighlight_re = re.compile(r"<syntaxhighlight.*?</syntaxhighlight>", re.S)


def remove_image_filenames(line):
    line = remove_image_re.sub("✂", line)
    line = remove_image_param_re.sub("✂", line)
    line = remove_image_no_end_re.sub("✂", line)
    return line


def poetry_match(text):
    # Considerably faster than a regex
    for word in poetry_flags:
        if word in text:
            return True
    return False


birthplace_param_re = re.compile(r"birth_?place *= *(.*?)(\n|\| )")
birth_date_param_re = re.compile(r"birth_date *= *(.*?)(\n|\| )")
birth_year_re = re.compile(r"[12][0-9][0-9][0-9]")


def birthplace_infobox_match(text):
    if "birth" not in text:
        return False
    matches = birthplace_param_re.findall(text)
    if matches:
        matches = list(matches)
        if len(matches) > 1:
            # Multiple matches mean the situation is complicated
            return False
        else:
            birthplace_value = matches[0][0]
            if birthplace_value:
                return birthplace_value
    return False


def birth_year_match(text):
    matches = birth_date_param_re.findall(text)
    if matches:
        matches = list(matches)
        if len(matches) > 1:
            # Multiple matches mean the situation is complicated
            return False
        else:
            birth_date_value = matches[0][0]
            if birth_date_value:
                matches = birth_year_re.findall(birth_date_value)
                if matches:
                    matches = list(matches)
                    if len(matches) > 1:
                        # Multiple matches mean the parse is unreliable
                        return False
                    else:
                        return matches[0]
    return False


def set_article_flags(article_text):
    article_flags = dict()
    article_flags["poetry"] = poetry_match(article_text)
    article_flags["birthplace_infobox"] = birthplace_infobox_match(article_text)
    if article_flags["birthplace_infobox"]:
        article_flags["birth_year"] = birth_year_match(article_text)
    return article_flags


def set_line_flags(line):
    line_flags = dict()
    if digit_re.search(line):
        line_flags["has_digit"] = True
    else:
        line_flags["has_digit"] = False

    line_tmp = remove_ref_re.sub("✂", line)
    line_tmp = remove_cite_re.sub("✂", line_tmp)
    line_flags["text_no_refs"] = line_tmp
    line_tmp = remove_image_filenames(line_tmp)
    line_tmp = remove_url_re.sub("✂", line_tmp)
    line_flags["text_no_refs_images_urls"] = line_tmp

    return line_flags


def universal_article_text_cleanup(article_text):
    if "math" in article_text:
        article_text = remove_math_article_re.sub("✂", article_text)

    if "syntaxhighlight" in article_text:
        article_text = remove_syntaxhighlight_re.sub("✂", article_text)

    if "code" in article_text:
        article_text = remove_code_re.sub("✂", article_text)

    if "timeline" in article_text:
        article_text = remove_timeline_re.sub("✂", article_text)

    if "raphChart" in article_text:
        article_text = remove_graphchart_re.sub("✂", article_text)

    return article_text


def universal_line_cleanup(line):
    if "ypo" in line:
        line = remove_not_a_typo_re.sub("✂", line)
    return line


sports_category_re = re.compile("Category:[^]]+sport")


def check_style_by_line(article_title, article_text):
    try:
        return check_style_by_line_impl(article_title, article_text)
    except Exception as e:
        print(e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise Exception("FATAL ERROR IN check_style_by_line")


def check_style_by_line_impl(article_title, article_text):
    article_flags = set_article_flags(article_text)
    problem_line_tuples = []
    article_text = universal_article_text_cleanup(article_text)

    result = check_article_title(article_title, article_text)
    if result:
        problem_line_tuples.extend(result)

    for line in article_text.splitlines():
        line = universal_line_cleanup(line)
        line_flags = set_line_flags(line)

        # Avoiding extend() helps performance massively
        if article_flags["birthplace_infobox"] or "nationality2" in line:
            result = nationality_check(line, line_flags, article_flags)
            if result:
                problem_line_tuples.extend(result)
        if article_flags["poetry"]:
            result = rhyme_scheme_check(line, line_flags)
            if result:
                problem_line_tuples.extend(result)
        if not ("Liga " in article_title or "football" in article_title or "F.C." in article_title):
            result = cup_tbsp_tsp_check(line, line_flags)
            if result and not sports_category_re.search(article_text):
                problem_line_tuples.extend(result)
        for check_function in [
                washington_state_check,
                cvt_speed_check,
                man_made_check,
                cvt_fuel_efficiency_check,
                mos_double_check,
                x_to_times_check,
                broken_nbsp_check,
                frac_repair,
                logical_quoting_check,
                liter_lowercase_check,
                currency_hyphen_check,
                decimal_point_check,
                paren_ref_check,
                au_check,
                km_check,
                number_notation_check
        ]:
            result = check_function(line, line_flags)
            if result:
                problem_line_tuples.extend(result)

    if not problem_line_tuples:
        return None
    try:
        line_string = "\n".join([f"{code}\t{article_title}\t{line_text}"
                                 for (code, line_text) in problem_line_tuples])
        return line_string
    except Exception as e:
        print("problem_line_tuples:", file=sys.stderr)
        print(pformat(problem_line_tuples), file=sys.stderr)
        print(e, file=sys.stderr)
        print(traceback.format_exc(), file=sys.stderr)
        raise e


# Can return multiple strings due to ambiguity
def asciify(input_string):
    output_strings = [input_string]

    for (from_char, to_charx) in list(ascii_equiv_letters.items()) + list(ascii_equiv_other.items()) + [("  ", " ")]:
        if type(to_charx) is str:
            output_strings = [s.replace(from_char, to_charx).strip() for s in output_strings]
        elif type(to_charx) is list:
            tmp_strings = []
            for to_char in to_charx:
                if to_char in output_strings[0]:
                    tmp_strings += [s.replace(from_char, to_char).strip() for s in output_strings]
                else:
                    tmp_strings = output_strings
            output_strings = tmp_strings
        else:
            raise ("Bad type in value")
    return output_strings


"""
# unreliable:
import unicodedata
title_asciified = unicodedata.normalize("NFKD", article_title).encode('ascii', 'ignore')
if len(article_title) != len(title_asciified):
print(f"{article_title} asciified to {title_asciified}", file=sys.stderr)
chars = title_no_ascii.replace(" ", "")
for char in chars:
    print(char)
    return
"""


# Cases where disambiguation pages (instead of redirects) link to
# untypeable titles.
#
# TODO: generate a list of links to non-ASCII titles from all
# disambiguation pages so these don't have to be special-cased.

disambig_to_article = {
    "YS": "¥$",
    "Yes": "¥€$",
    "UF": "μF",
    "Theta (disambiguation)": "Θ (set theory)",
    "ST": "ΣΤ",  # Sigma tau
    "AA": "A∴A∴",
}

# Must be lowercase, literal string (not regex)
wiktionary_redirect = [
    "{{wiktionary redirect}}",
    "{{wtsr}}",
    "{{wikt red",
    "{{wi|"
]


# [[WP:TITLESPECIALCHARACTERS]] and [[WP:ENGLISHTITLE]]
def check_article_title(article_title, article_text):
    if article_text.startswith("#REDIRECT") or article_text.startswith("#redirect"):
        return

    disambig_target = disambig_to_article.get(article_title)
    if disambig_target:
        if f"[[{disambig_target}]]" in article_text or f"[[{disambig_target} (disambiguation)]]" in article_text:
            return
        else:
            return [("MD", f"{article_title} -> {disambig_target}")]

    title_no_ascii = english_ok_re.sub("", article_title)
    title_no_ascii = title_no_ascii.strip()
    if not title_no_ascii:
        return

    article_text_lower = article_text.lower()

    if len(article_title) == 1 and any([dt for dt in disambig_templates if dt in article_text_lower]):
        return

    # Special exception for Chinese characters, where different
    # readings produce incoherent romanizations
    if any([dt for dt in disambig_templates_chinese if dt in article_text_lower]):
        return

    if article_title[0] == ".":
        # Skip internationalized top-level domains in DNS
        return

    if any([tag for tag in wiktionary_redirect if tag in article_text_lower]):
        return

    if "°" in title_no_ascii:
        # Special cases for degree sign
        if re.search(r"\([0-9][0-9]°[0-9][0-9]′", article_title):
            # Readers are unlikely to input geographic coordinates
            # used as a disambiguator
            return

        alt_plural = article_title.replace("°", " degrees ").replace("  ", " ").strip()
        if redirect_dict.get(alt_plural) == article_title:
            return

        for replacement in [" degree ", " Degrees ", " Degree "]:
            alt_title = article_title.replace("°", replacement).replace("  ", " ").strip()
            if redirect_dict.get(alt_title) == article_title:
                return

        return [("MR", f"{article_title} -> {alt_plural}")]

    # Special restriction for ordinal indicators (to catch incorrect
    # uses like "Nº")
    if "ª" in title_no_ascii:
        if not re.search(r"[0-9]ª", article_title):
            return [("TC", 'Incorrect use of ordinal indicator "ª" in article title')]
    if "º" in title_no_ascii:
        if not re.search(r"[0-9]ª", article_title):
            return [("TC", 'Incorrect use of ordinal indicator "º" in article title')]

    # U+2212 Minus Sign is the correct character in chemical names
    if "(−)" in article_title:
        return

    title_tmp = ok_with_redirect_re.sub("", title_no_ascii)
    title_tmp = title_tmp.strip()
    if title_tmp:
        # Found disallowed characters
        return [("TC", f'"{title_tmp}" in article title')]
    else:
        # Found Non-ASCII characters allowed with redirect
        titles_asciified = asciify(article_title)
        result = []
        for title_asciified in titles_asciified:
            redirect_target = redirect_dict.get(title_asciified)
            if redirect_target != article_title:
                # Missing redirect
                result += [("MR", f"{title_asciified} -> {article_title}")]
        return result


"""
# This isolates disallowed characters that appear in titles mixed
# with English letters.

import unicodedata
english_letters_re = re.compile(rf"[a-zA-Z]+")
for char in title_no_ascii:
    category = unicodedata.category(char)
    # Category codes and meanings:
    # https://www.unicode.org/reports/tr44/#General_Category_Values
    # if category in ["Ll", "Lu", "Po", "Sm", "Sk", "So", "Lm",
    #                 "Sc", "Pd", "No", "Pi"]:
    #    continue
    # print(f"{char} category: " + category)
    if category == "Lo":
        if english_letters_re.search(article_title):
            return [("CHAR_MIXED", article_title + " [title]")]
"""


washington_state_foo_re = re.compile(r"Washington State [A-Z]")
foo_of_washington_state_re = re.compile(r"[A-Z][A-Za-z]+ of Washington State")


# TODO: Seek consensus on talk page (notifying WikiProject US?)
# https://en.wikipedia.org/wiki/Wikipedia:Naming_conventions_(geographic_names)#States
# proscriptive, not descriptive, if these guidelines are accepted
# across lots of articles.
def washington_state_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    if "Washington" not in line:
        return

    if "state of Washington" in line:
        return [("W", line)]

    if "Washington State" in line:
        line_tmp = washington_state_foo_re.sub("", line)
        line_tmp = foo_of_washington_state_re.sub("", line_tmp)
        if "Washington State" in line_tmp:
            return [("W", line)]
    return


rhyme_fast_re = re.compile(r"[Aa][,\-\.]?[AaBb]")
rhyme_dashed_re = re.compile(r"[^a-z0-9\-A-Z{NON_ASCII_LETTERS}][Aa]-[Bb][^a-zA-Z{NON_ASCII_LETTERS}]")
rhyme_comma_re = re.compile(r"AA,A?B|AB,[ABC]")
rhyme_masked_re = re.compile(r"[^A-Za-z0-9\./%#=_\-]a(a|b|aa|ab|ba|bb|bc|aaa|aba|abb|abc|baa|bab|bba|bca|bcb|bcc|bcd)[^a-z0-9{NON_ASCII_LETTERS}/]")
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

    line_tmp = line_flags["text_no_refs"]
    line_tmp = remove_lang_re.sub("✂", line_tmp)

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
        line_tmp = x_space_exclusions.sub("✂", line)
        if " x " in line_tmp:
            return [("XS", line_tmp)]  # X with Space

    if line_flags["has_digit"]:
        if not x_no_space_re.search(line):
            return
        if x_no_space_exclusions.search(line):
            return
        line_reduced = line_flags["text_no_refs_images_urls"]
        if x_no_space_re.search(line_reduced):
            return [("XNS", line_reduced)]  # X with No Space


broken_nbsp_re = re.compile(r"&nbsp[^;}]")


def broken_nbsp_check(line, line_flags):
    if "&nbsp" not in line:
        return
    if broken_nbsp_re.search(line):
        if not re.search(r"https?:[^ ]+&nbsp", line):
            return [("N", line)]  # broken Nbsp


frac_repair_re = re.compile(r"[0-9]\{\{frac\|[0-9]+\|")
frac_repair_dash_re = re.compile(r"[0-9]-[0-9]+/[0-9]")


def frac_repair(line, line_flags):
    if not line_flags["has_digit"]:
        return
    if frac_repair_dash_re.search(line):
        return [("FR", line)]  # FRaction repair needed
    if "frac" not in line:
        return
    if frac_repair_re.search(line):
        return [("FR", line)]  # FRaction repair needed


logical_quoting_re = re.compile(r'"[a-z ,:\-;]+[,\.]"')


def logical_quoting_check(line, line_flags):
    # Per [[MOS:LOGICAL]]
    if '"' not in line:
        return
    if logical_quoting_re.search(line):
        return [("QL", line)]  # Quoting must be Logical


# --- LITERS ---

# Per April 2021 RFC that updated [[MOS:UNITSYMBOLS]]

liter_with_prefix_alt = r"ql|rl|yl|zl|al|fl|pl|µL|μl|ml|cl|dl|dal|hl|kl|Ml|Gl|Tl|Pl|El|Zl|Yl|Rl|Ql"

liter_link_re = re.compile(r"([Ll]iter|[Ll]itre)s?\|l]]")
liter_convert_re = re.compile(r"{{(convert|cvt)\|[^\}]+\|l(\||}|/)")
liter_parens_re = re.compile(rf"[^a-zA-Z{NON_ASCII_LETTERS}]\(l(/[a-zA-Z/]+)?\)[^a-zA-Z{NON_ASCII_LETTERS}]")
liter_prefix_re = re.compile(rf"[^a-zA-Z0-9{NON_ASCII_LETTERS}][0-9]+( |&nbsp;)?({liter_with_prefix_alt})[^a-zA-Z0-9{NON_ASCII_LETTERS}]")
liter_prefix_exclusion_re = re.compile(r"(El [A-Z]|al-[A-Z]|align|fl\.?( |&nbsp;)?oz)")
liter_illion_re = re.compile(r"[rBbMm]illion( |&nbsp;)l[^a-zA-Z0-9]")
liter_qty_re = re.compile(rf"[0-9]( |&nbsp;)?l[^a-zA-Z0-9'’{NON_ASCII_LETTERS}]")
liter_prefix_qty_re = re.compile(rf"[0-9]( |&nbsp;)?({liter_with_prefix_alt})[^a-zA-Z0-9'’{NON_ASCII_LETTERS}]")
liter_numerator_re = re.compile(rf"(^|[^A-Za-z])[0-9,\.]+( |&nbsp;)?(l|{liter_with_prefix_alt})/[a-zA-Z0-9]")
liter_denominator_re = re.compile(r"[^A-Za-z\./][A-Za-z]{1,4}/(l|" + liter_with_prefix_alt
                                  + rf")[^a-zA-Z{NON_ASCII_LETTERS}'0-9/\-_]")
l7_exclusion_re = re.compile(r"("
                             + r"w/l(-[0-9])? *="
                             + r"|"
                             + r"data:[A-Za-z0-9_\-\./,\+%~;]+/l[^a-zA-Z'’]"
                             + r"|"
                             + r"[^a-zA-Z0-9]r/l"
                             + r"|"
                             + r"[^a-zA-Z0-9]d/l[^a-zA-Z0-9]"
                             + r"|"
                             + r"\[\[(\w+ )+a/l [\w ]+\]\]"
                             + r")")


def liter_lowercase_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]

    if "l" not in line:
        return

    if liter_link_re.search(line):
        return [("L1", line)]

    # "(l)" and "(l/c/d)" (per capita per day) show up in table
    # headers sometimes
    if liter_parens_re.search(line):
        if "(l)!" not in line and "(r)" not in line:  # (r) for right
            return [("L2", line)]

    if "illion" in line and liter_illion_re.search(line):
        return [("L3", line)]

    if not line_flags["has_digit"]:
        return

    if liter_prefix_re.search(line):
        line_tmp = liter_prefix_exclusion_re.sub("✂", line)
        if liter_prefix_re.search(line_tmp):
            return [("L4", line)]
    if liter_qty_re.search(line):
        if r"[[Pound sterling|l" in line:
            return
        if "l.jpg" in line:
            return
        if "l.JPG" in line:
            return

        if "l=" not in line and "uSTR" not in line and "l\\" not in line:
            return [("L5", line)]
    if liter_prefix_qty_re.search(line):
        # Some may be technically allowed unless the page mixes e.g. "L" with "ml"
        return [("L9", line)]

    if liter_numerator_re.search(line):
        return [("L6", line)]

    # Denominator checks
    if "/" in line:

        if not liter_denominator_re.search(line):
            return

        if "/l" in line:
            # May need to manually fix some instances:
            # expand "m/l" to "music and lyrics" or drop
            # expand "w/l" to "win/loss"
            # expand "s/l" to "sideline" "l/b" to "sideline" (line ball)
            # and these:
            if "Malaysian names#Indian names|a/l" in line:
                return
            if "Length at the waterline|w/l" in line:
                return
            if "Length at the waterline|Length w/l" in line:
                return
            if "Waterline length|w/l" in line:
                return

            if l7_exclusion_re.search(line):
                return

            return [("L7", line)]
        else:
            # Some may be technically allowed unless the page mixes e.g. "L" with "ml"
            return [("L8", line)]


# [[MOS:UNITS]]; not compatible with Template:Convert
unicode_fractions = "¼½¾⅓⅔⅐⅑⅒⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞"
ctt_alternation = "(cup|tablespoon|teaspoon|[Tt]bsp|tsp)"
ctt_alternation_re = re.compile(ctt_alternation)
unifrac_re = re.compile(rf"[{unicode_fractions}]")
ctt_digit_re = re.compile(rf"([0-9\-/]+( |&nbsp;)(\[\[)?{ctt_alternation}s?[^A-Za-z])")
ctt_unifrac_re = re.compile(rf"[{unicode_fractions}]( |&nbsp;){ctt_alternation}")
ctt_frac_re = re.compile(r"\{\{[F|f]ract?[^\}]+\}\}( |&nbsp;)" + ctt_alternation)
ctt_ignore_num_re = re.compile(r"[0-9][0-9][0-9][0-9] cup|[0-9][0-9]?[-/-–][0-9]?[0-9] cup")
ctt_ignore_sport_re = re.compile(r"cup[0-9] result|defeat| goals?[^A-Za-z]| games|competition"
                                 r"| won[,; ]|[Ss]occer|football|[Ww]inner|cup matches|[Rr]egional[0-9] cup"
                                 r"|play-?off| league |[Mm]otorsports|tournament|[Cc]hampionship|[Cc]ricket"
                                 r"| win(ning)? |cup final|cup ties| competed | Cup[^A-Za-z]|semi-?final"
                                 r"|player|[Ss]upercup|greyhound|[Rr]ugby| [Ww]ins |scorer"
                                 r"|cups of coffee|cups of( green| black)? tea|cups/day|cups (per|a) day"
                                 r"|cups playing card|,000 cups|cup-mark|cup mark|cup-like|cup-shaped"
                                 r"|cups per shift|cups sold"
                                 r"| finals | prize |basketball| victory"
                                 r"|cup-final| game | played | loss |free kick|Division [0-9] [Cc]up")
ctt_ignore_converted_re = re.compile(rf"{ctt_alternation}s? (\([0-9]+( |&nbsp;)(g|grams|mL|L)\)| / [0-9]+( |&nbsp;)(g|grams|mL|L))")
ctt_ignore_converted_reverse_re = re.compile(rf"[0-9]+( |&nbsp;)(g|grams|mL|L) \(~?[0-9/]+( |&nbsp;){ctt_alternation}s?\)")
# TODO: "half teaspoon, quarter cup, one-eighth cup"


def cup_tbsp_tsp_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]

    unifrac_found = False
    if unifrac_re.search(line):
        unifrac_found = True

    if not (line_flags["has_digit"] or unifrac_found):
        return

    if not ctt_alternation_re.search(line):
        return

    if unifrac_found:
        result = ctt_unifrac_re.search(line)
        if result:
            return [("CTT2", line)]

    line_tmp = ctt_ignore_converted_re.sub("✂", line)
    line_tmp = ctt_ignore_converted_reverse_re.sub("✂", line)

    matches = ctt_digit_re.findall(line_tmp)
    if matches:
        for m in matches:
            if not (ctt_ignore_num_re.match(m[0])
                    or ctt_ignore_sport_re.search(line)):
                return [("CTT1", line)]

        if "rac" in line:
            result = ctt_frac_re.search(line_tmp)
            if result:
                return [("CTT3", line)]


au_unconverted_abbr_re = re.compile(r"\b[0-9,\.]*[0-9]( |&nbsp;)?(AU|au)\b")
au_unconverted_full_re = re.compile(r"\b[0-9,\.]*[0-9]( |&nbsp;)?(\[\[)?[Aa]stronomical unit")
au_converted_re = re.compile(r"r{{ *([Cc]onvert|[Cc]vt)[^}]+(au|AU).*?}}")
convert_proper_start_re = r"{{[Cc]onvert|[0-9,\.]+\|(±\|[0-9,\.]+\|)?(\|(to|by)\|[0-9,\.]+)?"
au_converted_from_properly = re.compile(convert_proper_start_re + r"au\|(e6km|e9km|e12km|ly pc)\|abbr=(unit|off)")
au_converted_to_properly = re.compile(convert_proper_start_re + r"ly|pc au\|")


# [[MOS:CONVERSIONS]]
def au_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    line = remove_lang_re.sub("✂", line)
    if not line_flags["has_digit"]:
        return

    if "stronomical" in line:
        if au_unconverted_full_re.search(line):
            return [("AU_UNCONVERTED_FULL", line)]
    if "au" not in line and "AU" not in line:
        return
    if au_unconverted_abbr_re.search(line):
        return [("AU_UNCONVERTED_ABBR", line)]
    for converted_au_string in au_converted_re.findall(line):
        if au_converted_from_properly:
            continue
        if au_converted_to_properly:
            continue
        return [("AU_CONVERTED_WRONG", line)]


wrong_meters_prefix_re = re.compile(r"\b[0-9,\.]*[0-9]( |&nbsp;)[GTPEZYRQ]m\b")


# [[MOS:CONVERSIONS]] for astronomical distances
def km_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    line = remove_lang_re.sub("✂", line)
    if not line_flags["has_digit"]:
        return

    if wrong_meters_prefix_re.search(line):
        return [("KM_WRONG_PREFIX", line)]


# Inline parenthetical references were banned in 2020 per [[WP:PAREN]]
paren_ref_filter_re = re.compile(r"\([A-Z][^\)]{0,100}[0-9][0-9][0-9][0-9][^\)]{0,100}\)")


def paren_ref_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    if "(" not in line or ")" not in line:
        return
    results = paren_ref_filter_re.findall(line)
    for result in results:
        if (
                result.startswith("(January")
                or result.startswith("(February")
                or result.startswith("(March")
                or result.startswith("(April")
                or result.startswith("(May ")
                or result.startswith("(May,")
                or result.startswith("(June ")
                or result.startswith("(June,")
                or result.startswith("(July")
                or result.startswith("(August")
                or result.startswith("(September")
                or result.startswith("(October")
                or result.startswith("(November")
                or result.startswith("(December")
        ):
            continue
        return [("PAREN_REF", line)]


decimal_middot_re = re.compile(r"[0-9]·[0-9]")
decimal_comma_re = re.compile(r"[0-9],[0-9][0-9]?[^0-9,\.]")
decimal_comma_exclusion_re = re.compile(r"[\[\(\{\-][0-9]+,[0-9]+[\]\)\}\-]"  # math
                                        r"|[0-9],[0-9]-[A-Za-z]"  # chemistry
                                        r"|[0-9],[0-9\.]+,[0-9]")  # lists


# [[MOS:DECIMAL]]
def decimal_point_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    if not line_flags["has_digit"]:
        return

    if "·" in line:
        if decimal_middot_re.search(line):
            return [("DECIMAL_MIDDOT", line)]
    if "," in line:
        if decimal_comma_re.search(line):
            if "InChI" in line:  # chemistry formula
                return

            # TODO: Requires further refinement. Comment patterns are
            # "NN,N%" and "N,N units" and "$N,N fillion". Maybe make
            # "DECIMAL_COMMA_HIGH" for high certainty, and punt
            # sorting out the rest for later?
            if not decimal_comma_exclusion_re.search(line):
                return [("DECIMAL_COMMA", line)]


# ---

# [[MOS:DIGITS]]
spaces_re = r"( |&nbsp;|&thinsp;|\{\{thinsp\}\}|&hairsp;|\{\{hairsp\}\}|&nbsp;|\{\{nbsp\}\})"
digits_with_spaces_re = re.compile(rf"(^|[^A-Za-z0-9])([0-9]\.[0-9][0-9][0-9]{spaces_re}[0-9]|[0-9]{spaces_re}[0-9][0-9][0-9][^0-9A-Za-z])")
# Captures e.g. "5 123", "# 5.123 4"

# Broad filter
scientific_notation_re = re.compile(rf"[0-9]{spaces_re}?[×xX]{spaces_re}?10\<sup")

# Incorrect scientific notation (or engineering notation if exponent is a multiple of 3)
wrong_sci_notation_re = re.compile(r" [0-9][0-9][0-9]?(\.[0-9]+)? ?[×xX] ?10\<sup")

wrong_million_abbr_re = re.compile(r"[0-9] [Mm]io\.? ")
exp_re = re.compile(r"10<sup>((-|−|&minus;)?[0-9]+)</sup>")

bad_per_re = re.compile(r"[0-9 /][a-zA-Z]<sup>[-−][123]</sup>")

# TODO: "10<sup>[69]</sup>" can probably be changed to "million" and
# "billion" in a lot of contexts.

# TODO: r"\{\{[Vv]al[^\}]+(e=|[0-9]e[0-9])"
# ESPECIALLY _ILLIONS: r"\{\{[Vv]al[^\}]+(e=(6|9|12)|[0-9]e(6|9|12))"

# Not worth automating - almost all false positives
# rf" [0-9](\.[0-9]+)?E[0-9][0-9]?( |\.|,)"
# Filter "Class #E#"
# ---


def number_notation_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    if not line_flags["has_digit"]:
        return

    if digits_with_spaces_re.search(line):
        return [("DIGITS_SPACES", line)]

    if wrong_million_abbr_re.search(line):
        return [("DIGITS_MIO", line)]

    # -- Scientific notation validation

    if "<sup>" in line:
        if bad_per_re.search(line):
            # Say e.g. "7 km/s" instead of "7 km s<sup>-1</sup>"
            return [("SCI_NOTATION_PER", line)]
    else:
        return

    if not scientific_notation_re.search(line):
        return

    if wrong_sci_notation_re.search(line):
        # Too many digits before the decimal point
        return [("SCI_NOTATION_WRONG", line)]

    result = exp_re.search(line)
    if not result:
        return [("SCI_NOTATION_MALFORMED", line)]

    exp = result.group(1)
    exp = exp.replace("−", "-")  # U+2212 to U+002D
    exp = exp.replace("&minus;", "-")  # HTML entity to U+002D
    exp = int(exp)
    if exp == 6:
        return [("SCI_NOTATION_XILLION", line)]

    if exp == 9:
        return [("SCI_NOTATION_XILLION", line)]

    if exp == 12:
        return [("SCI_NOTATION_XILLION", line)]

    if exp >= 15:
        # So large that writing this way is fine
        return

    if exp <= -5:
        # So small that writing this way is fine
        return

    return [("SCI_NOTATION_CATCHALL", line)]


no_num_kph_re = re.compile(r"\bkph|KPH\b")
convert_tag_re = re.compile(r"\{\{([Cc]onvert|[Cc]vt).*?\}\}")
kmh_nearby_re = re.compile(r"km/h.{0,30}mph|mph.{0,30}km/h")
mph_isolated_re = re.compile(r"\b(mph|MPH)\b")


def cvt_speed_check(line, line_flags):
    # Per [[MOS:UNITNAMES]]
    line = line_flags["text_no_refs_images_urls"]
    if "ph" not in line and "PH" not in line:
        return
    line_tmp = convert_tag_re.sub("", line)
    if ("mph" in line and "mph=" not in line) or "MPH" in line:
        if "km/h" in line_tmp:
            line_tmp_b = kmh_nearby_re.sub("", line_tmp)
            if "mph" in line_tmp_b:
                return [("SPEED_MPH1", line)]
        elif mph_isolated_re.search(line_tmp):
            return [("SPEED_MPH2", line)]
        # TODO: May need to add equivalent of:
        #  grep -v ", MPH" | grep -iP "(speed|mile|[0-9](&nbsp;| )MPH)"
    if no_num_kph_re.search(line_tmp):
        # Per [[MOS:UNITSYMBOLS]], change "kph" to "km/s"
        return [("SPEED_KPH", line)]
    if "mi/h" in line_tmp:
        # Should be "mph" per [[MOS:UNITSYMBOLS]], and also converted to km/h
        return [("SPEED_MIH", line)]
    # print(f"no hits on {line}")
    return


man_made_re = re.compile(r"[^A-Za-z]([Mm]an[- ]?made|MAN[- ]?MADE)")


def man_made_check(line, line_flags):
    line = line_flags["text_no_refs_images_urls"]
    if man_made_re.findall(line):
        return [("MAN_MADE", line)]
    return


def cvt_fuel_efficiency_check(line, line_flags):
    pass


nationality_citizenship_re = re.compile(r"(nationality|citizenship)[0-9]? *= *(.*?)(\||$)")
usa_re = re.compile(r"({US}|USA|US$|United States|American|U.S.)\]*")
piped_link_re = re.compile(r"\[\[([^\]]+)\|([^\]]+)\]\]")


# Birthright citizenship for everyone born in the territory per
# https://en.wikipedia.org/wiki/Jus_soli#Unrestricted_jus_soli
jus_soli = [
    "td",
    "ls",
    "tz",
    "ag",
    "bb",
    "bz",
    "ca",
    "cr",
    "cu",
    "dm",
    "sv",
    "gd",
    "gt",
    "hn",
    "jm",
    "mx",
    "ni",
    "pa",
    "kn",
    "lc",
    "vc",
    "tt",
    "us",
    "ar",
    "bo",
    "br",
    "cl",
    "ec",
    "gu",
    "py",
    "pe",
    "uy",
    "ve",
    "fj",
    "tv",
]


country_map = {
    "Andorra": "ad",
    "United Arab Emirates": "ae",
    "UAE": "ae",
    "Afghanistan": "af",
    "Antigua and Barbuda": "ag",
    "Albania": "al",
    "Armenia": "am",
    "Angola": "ao",
    "Argentina": "ar",

    "Austria": "at",
    "Australia": "au",
    "Aruba": "aw",
    "Åland Islands": "ax",
    "Azerbaijan": "az",
    "Bosnia and Herzegovina": "ba",
    "Bosnia": "ba",
    "Barbados": "bb",
    "Bangladesh": "bd",
    "Belgium": "be",
    "Burkina Faso": "bf",
    "Bulgaria": "bg",
    "Bahrain": "bh",
    "Burundi": "bi",
    "Benin": "bj",
    "Saint Barthélemy": "bl",
    "Bermuda": "bm",
    "Brunei": "bn",
    "Bolivia": "bo",
    "Bonaire, Sint Eustatius and Saba": "bq",
    "Brazil": "br",
    "Bahamas": "bs",
    "Bhutan": "bt",
    "Bouvet Island": "bv",
    "Botswana": "bw",
    "Belarus": "by",
    "Belize": "bz",
    "Canada": "ca",
    "Cocos (Keeling) Islands": "cc",
    "Democratic Republic of the Congo": "cd",
    "DRC": "cd",
    "Central African Republic": "cf",
    "CAR": "cf",
    "Congo": "cg",
    "Switzerland": "ch",
    "Côte d'Ivoire": "ci",
    "Ivory Coast": "ci",
    "Cook Islands": "ck",
    "Chile": "cl",
    "Cameroon": "cm",
    "China": "cn",
    "Colombia": "co",
    "Costa Rica": "cr",
    "Cuba": "cu",
    "Cabo Verde": "cv",
    "Cape Verde": "cv",
    "Curaçao": "cw",
    "Christmas Island": "cx",
    "Cyprus": "cy",
    "Czechia": "cz",
    "Germany": "de",
    "Djibouti": "dj",
    "Denmark": "dk",
    "Dominica": "dm",
    "Dominican Republic": "do",
    "Algeria": "dz",
    "Ecuador": "ec",
    "Estonia": "ee",
    "Egypt": "eg",
    "Western Sahara": "EH",
    "Spanish Sahara": "EH",
    "Eritrea": "er",
    "Spain": "es",
    "Ethiopia": "et",
    "Finland": "fi",
    "Fiji": "fj",
    "Federated States of Micronesia": "fm",
    "FSM": "fm",
    "Faroe Islands": "fo",
    "France": "fr",
    "Gabon": "ga",

    "United Kingdom": "gb",
    "UK": "gb",
    "Britain": "gb",
    "England": "gb",
    "Scotland": "gb",
    "Wales": "gb",
    "Northern Ireland": "gb",

    # All BOT Citizens (except those attached to Akrotiri and
    # Dhekelia) are full British Citizens now (but possibly not in the
    # past):
    "Falkland Islands": "gb",  # "fk"
    "Gibraltar": "gb",  # "gi"
    "Isle of Man": "gb",  # "im"
    "British Indian Ocean Territory": "gb",  # "io"
    "Montserrat": "gb",  # "ms"
    "Anguilla": "gb",  # "ai"
    "British Virgin Islands": "gb",  # "vg"
    "BVI": "gb",  # "vg"
    "Cayman Islands": "gb",  # "ky"
    "Pitcairn": "gb",  # "pn"
    "Saint Helena, Ascension and Tristan da Cunha": "gb",  # "sh"
    "South Georgia and the South Sandwich Islands": "gb",  # "gs"
    "Turks and Caicos Islands": "gb",  # "tc"

    "Grenada": "gd",
    "Georgia (country)": "ge",
    "Democratic Republic of Georgia": "ge",
    "French Guiana": "gf",
    "Guernsey": "gg",
    "Ghana": "gh",
    "Greenland": "gl",
    "Gambia": "gm",
    "Guinea": "gn",
    "Guadeloupe": "gp",
    "Equatorial Guinea": "gq",
    "Greece": "gr",
    "Guatemala": "gt",
    "Guinea-Bissau": "gw",
    "Guyana": "gy",
    "Hong Kong": "hk",
    "Heard Island and McDonald Islands": "hm",
    "Honduras": "hn",
    "Croatia": "hr",
    "Haiti": "ht",
    "Hungary": "hu",
    "Indonesia": "id",
    "Ireland": "ie",
    "Israel": "il",
    "India": "in",
    "Iraq": "iq",
    "Iran": "ir",
    "Iceland": "is",
    "Italy": "it",
    "Jersey": "je",
    "Jamaica": "jm",
    "Jordan": "jo",
    "Japan": "jp",
    "Kenya": "ke",
    "Kyrgyzstan": "kg",
    "Cambodia": "kh",
    "Kiribati": "ki",
    "Comoros": "km",
    "Saint Kitts and Nevis": "kn",
    "North Korea": "kp",
    "Democratic People's Republic of Korea": "kp",
    "DPRK": "kp",
    "South Korea": "kr",
    "Republic of Korea": "kr",
    "Kuwait": "kw",
    "Kazakhstan": "kz",
    "Lao People's Democratic Republic": "la",
    "Laos": "la",
    "Lebanon": "lb",
    "Saint Lucia": "lc",
    "Liechtenstein": "li",
    "Sri Lanka": "lk",
    "Ceylon": "lk",
    "Liberia": "lr",
    "Lesotho": "ls",
    "Lithuania": "lt",
    "Luxembourg": "lu",
    "Latvia": "lv",
    "Libya": "ly",
    "Morocco": "ma",
    "Monaco": "mc",
    "Moldova": "md",
    "Montenegro": "me",
    "Saint Martin": "mf",  # French part
    "Madagascar": "mg",
    "Marshall Islands": "mh",
    "North Macedonia": "mk",
    "Republic of Macedonia": "mk",
    "Mali": "ml",
    "Myanmar": "mm",
    "Burma": "mm",
    "Mongolia": "mn",
    "Macao": "mo",
    "Martinique": "mq",
    "Mauritania": "mr",
    "Malta": "mt",
    "Mauritius": "mu",
    "Maldives": "mv",
    "Malawi": "mw",
    "Mexico": "mx",
    "Malaysia": "my",
    "Mozambique": "mz",
    "Namibia": "na",
    "New Caledonia": "nc",
    "Niger": "ne",
    "Norfolk Island": "nf",
    "Nigeria": "ng",
    "Nicaragua": "ni",
    "Netherlands": "nl",
    "Norway": "no",
    "Nepal": "np",
    "Nauru": "nr",
    "Niue": "nu",
    "New Zealand": "nz",
    "Oman": "om",
    "Panama": "pa",
    "Peru": "pe",
    "French Polynesia": "pf",
    "Papua New Guinea": "pg",
    "Philippines": "ph",
    "Pakistan": "pk",
    "Poland": "pl",
    "Saint Pierre and Miquelon": "pm",
    "Palestine": "ps",
    "Portugal": "pt",
    "Palau": "pw",
    "Paraguay": "py",
    "Qatar": "qa",
    "Réunion": "re",
    "Romania": "ro",
    "Serbia": "rs",
    "Russia": "ru",
    "Russian Federation": "ru",
    "Rwanda": "rw",
    "Saudi Arabia": "sa",
    "Solomon Islands": "sb",
    "Seychelles": "sc",
    "Sudan": "sd",
    "Sweden": "se",
    "Singapore": "sg",
    "Slovenia": "si",
    "Slovakia": "sk",
    "Sierra Leone": "sl",
    "San Marino": "sm",
    "Senegal": "sn",
    "Somalia": "so",
    "Suriname": "sr",
    "South Sudan": "ss",
    "Sao Tome and Principe": "st",
    "São Tomé and Príncipe": "st",
    "El Salvador": "sv",
    "Sint Maarten": "sx",
    "Syria": "sy",
    "Eswatini": "sz",
    "Chad": "td",
    "Togo": "tg",
    "Thailand": "th",
    "Tajikistan": "tj",
    "Tokelau": "tk",
    "Timor-Leste": "tl",
    "Turkmenistan": "tm",
    "Tunisia": "tn",
    "Tonga": "to",
    "Turkey": "tr",
    "Trinidad and Tobago": "tt",
    "Tuvalu": "tv",
    "Taiwan": "tw",
    "Tanzania": "tz",
    "Ukraine": "ua",
    "Uganda": "ug",

    "United States of America": "us",
    "United States": "us",
    "USA": "us",
    "US": "us",
    "U.S.": "us",
    "U. S.": "us",
    "America": "us",

    # U.S. nationals by birth location, possibly citizens by
    # parentage, depending on year of birth
    "American Samoa": "as",

    # U.S. citizens by birth location, depending on year of birth
    "US Virgin Islands": "vi",
    "U.S. Virgin Islands": "vi",
    "United States Virgin Islands": "vi",
    "Guam": "gu",
    "Puerto Rico": "pr",
    "Northern Mariana Islands": "mp",

    "Uruguay": "uy",
    "Uzbekistan": "uz",
    "Vatican City": "va",
    "Saint Vincent and the Grenadines": "vc",
    "Venezuela": "ve",
    "Vietnam": "vn",
    "Vanuatu": "vu",
    "Wallis and Futuna": "wf",
    "Samoa": "ws",
    "Yemen": "ye",
    "Mayotte": "yt",
    "South Africa": "za",
    "Zambia": "zm",
    "Zimbabwe": "zw",

    # Historical and disputed countries (using 3-letter codes so they
    # won't collide with official codes)
    "Holy Roman Empire": "hre",
    "Prussia": "pru",
    "Soviet Union": "usr",
    "Soviet": "usr",
    "USSR": "usr",
    "Ottoman Empire": "oem",
    "Czechoslovakia": "czs",
    "Roman": "rom",
    "Republic of Geneva": "gen",
    "Venetian": "ven",
    "Venice": "ven",
    "Castilian": "cas",
    "Castile": "cas",
    "Byzantine Empire": "byz",
    "Kingdom of Bavaria": "bav",
    "Kingdom of Sardinia": "sar",
    "Kingdom of Naples": "nap",
    "Kosovo": "kos",
    "Manchukuo": "man",
    "Somaliland": "som",
    "Yugoslavia": "yug",
    "Abkhazia": "abk",
    "Colony of Newfoundland": "new",
    "Dominion of Newfoundland": "new",
    "Papal States": "pap",
    "Qing Dynasty": "qin",

    # Domestic nations of the United States
    "Navajo": "na_nvj",
    "Osage": "na_osg",
    "Cherokee": "na_chk",
    "Choctaw": "na_ctw",
    "Iñupiaq": "na_ipq",

    # Demonyms
    "Falkland Islander": "gb",
    "English": "gb",
    "British": "gb",
    "Northern Irish": "gb",
    "Welsh": "gb",
    "Scottish": "gb",

    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Spanish": "es",
    "Spaniard": "es",
    "Portuguese": "pt",
    "American": "us",
    "Irish": "ie",
    "Polish": "pl",
    "Australian": "au",
    "Canadian": "ca",
    "Dutch": "nl",
    "Netherlandish": "nl",
    "Danish": "dk",
    "Danes": "dk",
    "Norse": "no",
    "Norwegian": "no",
    "Swedish": "se",
    "Swede": "se",
    "Ivorian": "ci",
    "Turkish": "tr",
    "Greek": "gr",
    "Hungarian": "hu",
    "Belgian": "be",
    "Saudi": "sa",
    "Kazakh": "kz",
    "Emirati": "ae",
    "Egyptian": "eg",
    "Swiss": "ch",
    "Chinese": "cn",
    "Czech": "cz",
    "Mexican": "mx",
    "Finnish": "fi",
    "Finn": "fi",
    "Serb": "rs",
    "Puerto Rican": "pr",
    "Georgian": "ge",
    "Argentine": "ar",
    "Honduran": "hn",
    "Afghan": "af",
    "Burmese": "mm",
    "Filipino": "ph",
    "Filipina": "ph",
    "Philippine": "ph",
    "Lebanese": "lb",
    "Moroccan": "ma",
    "Mozambiquan": "mz",
    "Ottoman": "oem",
    "Thai": "th",
    "Trinidadian": "tt",
    "Tobagonian": "tt",
    "Ukrainian": "ua",
    "Yugoslav": "yug",
    "Abkhaz": "abk",
    "Bahamian": "bs",
    "Barbadian": "bb",
    "Bermudian": "bm",
    "Canadien": "ca",
    "Caymanian": "ky",
    "Central African": "cf",
    "Cook Islander": "ck",
    "Croat": "hr",
    "Faroe Islander": "fo",
    "Faroese": "fo",
    "Guyanese": "gy",
    "Guianese": "fr",  # French Guiana
    "Honduran": "hn",
    "Italia": "it",
    "Kyrgyz": "kg",
    "Lebanese": "lb",
    "Macedonian": "mk",
    "Maldivian": "mv",
    "Maltese": "mt",
    "Manx": "im",
    "Mauritian": "mr",
    "Moldovian": "md",
    "Montenegrin": "me",
    "Palestinian": "ps",
    "Persian": "ir",
    "Rwandese": "rw",
    "Salvadoran": "sv",
    "Santomean": "st",
    "Seychellois": "sc",
    "Slovak": "sk",
    "Slovene": "si",
    "Solomon Islander": "sb",
    "Somali people": "so",
    "Turkmen": "tm",
    "Uzbek": "uz",
}
country_keys = sorted(country_map.keys(), key=lambda s: len(s), reverse=True)


usa_place_strings = [
    # MOS:USPLACE city names (understood without state name per AP)
    "Atlanta",
    "Baltimore",
    "Boston",
    "Chicago",
    "Cincinnati",
    "Cleveland",
    "Dallas",
    "Denver",
    "Detroit",
    "Honolulu",
    "Houston",
    "Indianapolis",
    "Las Vegas",
    "Los Angeles",
    "Miami",
    "Milwaukee",
    "Minneapolis",
    "New Orleans",
    "New York",
    "New York City",
    "Oklahoma City",
    "Philadelphia",
    "Phoenix",
    "Pittsburgh",
    "St. Louis",
    "Salt Lake City",
    "San Antonio",
    "San Diego",
    "San Francisco",
    "Seattle",

    # States and postal abbreviations (which should not be used)
    "Washington, D.C."
    "DC"
    "Alabama",
    "AL",
    "Alaska",
    "AK",
    "Arizona",
    "AZ",
    "Arkansas",
    "AR",
    "California",
    "CA",
    "Colorado",
    "CO",
    "Connecticut",
    "CT",
    "Delaware",
    "DE",
    "Florida",
    "FL",
    "Georgia (U.S. state)",
    "GA",
    "Hawaii",
    "HI",
    "Idaho",
    "ID",
    "Illinois",
    "IL",
    "Indiana",
    "IN",
    "Iowa",
    "IA",
    "Kansas",
    "KS",
    "Kentucky",
    "KY",
    "Louisiana",
    "LA",
    "Maine",
    "ME",
    "Maryland",
    "MD",
    "Massachusetts",
    "MA",
    "Michigan",
    "MI",
    "Minnesota",
    "MN",
    "Mississippi",
    "MS",
    "Missouri",
    "MO",
    "Montana",
    "MT",
    "Nebraska",
    "NE",
    "Nevada",
    "NV",
    "New Hampshire",
    "NH",
    "New Jersey",
    "NJ",
    "New Mexico",
    "NM",
    "New York",
    "NY",
    "North Carolina",
    "NC",
    "North Dakota",
    "ND",
    "Ohio",
    "OH",
    "Oklahoma",
    "OK",
    "Oregon",
    "OR",
    "Pennsylvania",
    "PA",
    "Rhode Island",
    "RI",
    "South Carolina",
    "SC",
    "South Dakota",
    "SD",
    "Tennessee",
    "TN",
    "Texas",
    "TX",
    "Utah",
    "UT",
    "Vermont",
    "VT",
    "Virginia",
    "VA",
    "Washington",
    "WA",
    "West Virginia",
    "WV",
    "Wisconsin",
    "WI",
    "Wyoming",
    "WY",
]
usa_place_strings = sorted(usa_place_strings, key=lambda s: len(s), reverse=True)


def country_match(input_str):
    country_codes = []
    for match_str in country_keys:
        if match_str in input_str:
            country_codes.append(country_map[match_str])

    if country_codes:
        if len(country_codes) > 1:
            # Uniqify; country name and demonym often both match
            country_codes = list(set(country_codes))
        return country_codes
    for match_str in usa_place_strings:
        if match_str in input_str:
            return ["us_state"]
    return []


def nationality_check(line, line_flags, article_flags):
    if "nationality2" in line:
        return [("INFONAT_REDUNDANT", line)]
    line_tmp = piped_link_re.sub(r"[[\1 PIPE \2]]", line)
    param_match = nationality_citizenship_re.search(line_tmp)
    if not param_match:
        return
    param_str = param_match.group(2).strip()

    if "==" in param_str:
        return
    if "Infobox" in line or "infobox" in param_str:
        return [("INFONAT_ERR", line)]

    if not param_str:
        return [("INFONAT_BIRTHPLACE_ONLY", line)]
    if "be inferred from" in param_str or "same as citizenzhip" in param_str:
        return [("INFONAT_BIRTHPLACE_ONLY", line)]
    if "<!-- use only when necessary per [[WP:INFONAT]] -->" == param_str:
        return [("INFONAT_BIRTHPLACE_ONLY", line)]
    if "<!-- will not display if national_team is defined -->" == param_str:
        return [("INFONAT_BIRTHPLACE_ONLY", line)]
    if "implied by birthplace" in param_str or "different from birthplace" in param_str:
        return [("INFONAT_BIRTHPLACE_ONLY", line)]

    # Complicated cases that deserve the parameter
    if "<br" in param_str or "," in param_str or "(" in param_str:
        return
    list_types = ["{{hlist", "{{plainlist", "{{ubl", "{{Ubl", "{{flatlist",
                  "{{cslist", "{{Hlist", "{{Plainlist", "{{Unbullletd"]
    if any(t in param_str for t in list_types):
        return
    if "File:" in param_str or "flag" in param_str or "Flag" in param_str or "{{" in param_str:
        # Remove flag per [[MOS:FLAGBIO]]
        return [("INFONAT_FLAG", line)]

    # If birthplace country matches nationality or citizenship, only
    # birthplace should be kept. Country should be added to birthplace
    # if missing.

    birthplace = article_flags["birthplace_infobox"]
    birthplace_countries = country_match(birthplace)
    citnat_countries = country_match(param_str)

    if len(birthplace_countries) > 1:
        return [("INFONAT_BIRTHPLACE_MULTI_COUNTRY", birthplace)]
    if len(citnat_countries) > 1:
        # Complicated case
        return
    if not citnat_countries:
        return [("INFONAT_CITNAT_NO_COUNTRY",
                 line + " ❦ " + param_str)]
    if not birthplace_countries:
        country_code = citnat_countries[0]
        return [(f"INFONAT_BIRTHPLACE_NO_COUNTRY_{country_code}",
                 line + " ❦ " + birthplace)]

    country_code = birthplace_countries[0]
    birth_year = article_flags["birth_year"]
    birth_century = "UNK"
    if birth_year:
        birth_year = int(birth_year)
        if birth_year > 1999:
            birth_century = "2000s"
        elif birth_year > 1899:
            birth_century = "1900s"
        elif birth_year > 1799:
            birth_century = "1800s"
        elif birth_year > 1699:
            birth_century = "1700s"
        else:
            birth_century = "MISC"

    if birthplace_countries[0] == citnat_countries[0]:
        if country_code in jus_soli:
            return [(f"INFONAT_REDUNDANT_{country_code}_JUS_SOLI_{birth_century}",
                     line + " ❦ " + birthplace)]
        else:
            return [(f"INFONAT_REDUNDANT_{country_code}_{birth_century}",
                     line + " ❦ " + birthplace)]
    if "not needed" in param_str or "Not needed" in param_str:
        return [("INFONAT_REDUNDANT", line)]

    # Remove flag per [[MOS:FLAGBIO]]
    if "Flag" in birthplace or "flag" in birthplace:
        return [("INFONAT_FLAG_BIRTHPLACE", line)]
    if "<ref" not in birthplace and "{{" in birthplace:
        return [("INFONAT_FLAG_BIRTHPLACE", line)]

    # When did citizenship or nationality change?
    if "{{explain citnat" not in line and "{{Explain citnat" not in line:
        return [(f"INFONAT_EXPLAIN_{country_code}",
                 line + " ❦ " + birthplace)]


currency_hyphen = re.compile(rf"[{MAJOR_CURRENCY_SYMBOLS}][0-9]+-[mb]illion")


def currency_hyphen_check(line, line_flags):
    if currency_hyphen.search(line):
        return [("$H", line)]
    else:
        return


def mos_double_check(line, line_flags):
    pass


def cvt_temperature_check(line, line_flags):
    pass


r"""

TODO: Finish rewrite of the below code into Python functions for
increased performance. The old style was abandoned at commit d0f8fb1

# "N°" or any "[^0-9]° should probably not have degree symbol

# ---
# Feet and inches - [[MOS:UNITNAMES]]

$ wc -l *feet*
   36663 jwb-feet-inches-all.txt
   62922 jwb-feet-inches-err.txt
       8 tmp-feet-inches1.txt
     951 tmp-feet-inches2.txt
   61963 tmp-feet-inches3.txt
     271 tmp-feet-inches-all1.txt
    4302 tmp-feet-inches-all2.txt
  259654 tmp-feet-inches-all3.txt
  426734 total

### TODO: This also needs to handle {{frac}} in place of pure digits
# {{s?frac|[0-9]+|[0-9]+(|[0-9]+)?}}
../venv/bin/python3 ../dump_grep_csv.py "[0-9\.]+(&nbsp;| )?'[0-9\.]+(&nbsp;| ) ?\"[^0-9\.]" > tmp-feet-inches-all1.txt
../venv/bin/python3 ../dump_grep_csv.py '[0-9\.]+"(&nbsp;| )?(x|by|×)(&nbsp;| )?[0-9\./]+"' > tmp-feet-inches-all2.txt
../venv/bin/python3 ../dump_grep_csv.py ' [^"][0-9]"' tmp-feet-inches-all3.txt
 | perl -pe 's/<.*?>//g'
 | perl -pe 's/[\( \|]"[a-zA-Z][^"]*[0-9]"//g'
 | perl -pe 's/"[0-9\.]+"//g'
 | grep -P '[0-9]"'
 > tmp-feet-inches-all3.txt
cat tmp-feet-inches-all2.txt tmp-feet-inches-all1.txt tmp-feet-inches-all3.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-feet-inches-all.txt

# TODO:
https://en.wikipedia.org/wiki/Template_talk:Convert#Inches_to_cm_vs._mm

Add "|cm" to {{convert}} and {{cvt}} instances where a distance is
expressed in whole inches, from 1 to 39 inches (1-100 cm).
 -> One-time run, doesn't need to be done in all instances, depending
    on the application, and 100+ cm might be OK sometimes, too.

# ---

# "internet" -> "Internet" outside of quotations

# TODO: Ignore articles with "unmanned aerial vehicle" to reduce
# false positives on this.
# "manned",
# "unmanned",

# --- ELLIPSES ---

# These are handled by moss_entity_check.py, but this will get a full list:
../venv/bin/python ../dump_grep_csv.py … | perl -pe 's/^(.*?):.*/$1/' | uniq | sort | uniq > fixme-ellipses.txt


# --- FUEL EFFICIENCY CONVERSION ---

echo "Beginning MPG conversion scan"
echo `date`

# Run time for this segment: About 1 h 30 min

# {{cvt}} or {{convert}} should probably be used in all instances to
# convert between US and imperial gallons (ug!)
# ../venv/bin/python3 ../dump_grep_csv.py 'mpg|MPG' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g"
| perl -pe "s%<ref.*?</ref>%%g" | grep -iP "\bmpg\b" | grep -iP "[0-9]( |&nbsp;)mpg"
| grep -vP 'L/100.{0,30}mpg' | grep -vP 'mpg.{0,30}L/100'| sort > tmp-mpg-convert.txt

../venv/bin/python3 ../dump_grep_csv.py 'mpg|MPG' | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g"
| perl -pe "s%<ref.*?</ref>%%g" | grep -iP "\bmpg\b" | grep -iP "[0-9]( |&nbsp;)mpg" | sort > tmp-mpg-convert.txt


cat tmp-mpg-convert.txt | perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-mpg-convert.txt

# DEPENDING ON CONTEXT, WILL NEED:
# {{convert|$1|mpgUS}}
# {{convert|$1|mpgimp}}

# Add to run_moss_parallel1.sh:
grep ^FE tmp-style-by-line.txt | sort > fixme-fuel-efficiency.txt

# --- MOS:DOUBLE ---

# Run time for this segment: ~20 min

echo "Beginning MOS:DOUBLE scan"
echo `date`
../venv/bin/python3 ../dump_grep_csv.py " '[A-Za-z ,:\-;]+'[,\. \}\)]" | grep -v '"' | grep -vP "{{([Ll]ang|[Tt]ransliteration|IPA)" | perl -pe 's/^(.*?):.*/$1/' > tmp-MOS-double.txt
cat tmp-MOS-double.txt | perl ../count.pl | sort -rn > tmp-double-most.txt
grep -vP "(grammar|languag|species| words)" tmp-double-most.txt | perl -pe "s/^\d+\t//" | head -1000 > jwb-double-most.txt


# --- TEMPERATURE CONVERSION ---

# Run time for this segment: ~2h (8-core parallel)

echo "Beginning temperature conversion scan"
echo `date`

# per [[MOS:UNITSYMBOLS]], need to convert to C

echo "  Beginning F scan..."
echo `date`
../venv/bin/python3 ../dump_grep_csv.py F | grep -P "(°F|0s( |&nbsp;)F[^b-z])" > tmp-temp-F.txt

grep '°F' tmp-temp-F.txt | perl -pe "s/\{\{([Cc]onvert|[Cc]vt).*?\}\}//g" | grep -vP '°C.{0,30}°F'
| grep -vP '°F.{0,30}°C' | grep -vP "(min|max|mean)_temp_[0-9]" | grep "°F"
| sort > tmp-temp-convert1.txt

grep "[0-9]0s( |&nbsp;)?F[^b-z]" tmp-temp-F.txt | grep -vP "[0-9]{3}0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep "0s" | sort > tmp-temp-convert5.txt

echo "  Beginning weather scan..."
echo `date`
../venv/bin/python3 ../dump_grep_csv.py "([Ww]eather|WEATHER|[Tt]emperature|TEMPERATURE|[Hh]eat|HEAT|[Cc]hill|CHILL)" > tmp-temp-weather.txt

grep '[ \(][0-9](C|F)[^a-zA-Z0-9]' tmp-temp-weather.txt | sort > tmp-temp-convert2.txt
grep "[0-9]+s?( |&nbsp;)(C|F)[^a-zA-Z0-9]" tmp-temp-weather.txt | sort > tmp-temp-convert3.txt
grep '[0-9]°' tmp-temp-weather.txt | sort > tmp-temp-convert4b.txt
grep '[0-9][0-9],' tmp-temp-weather.txt | grep -iP "weather=" | sort > tmp-temp-convert4c.txt
../venv/bin/python3 ../dump_grep_csv.py "(low|lower|mid|middle|high|upper|the)[ \-][0-9][0-9]?0s" | perl -pe "s%<ref.*?</ref>%%g" | grep -v "Celsius" | grep "0s" | sort > tmp-temp-convert6.txt

FROM:([0-9]+)° (and|to)([0-9]+)°(&nbsp;| )?(C|F)
TO:$1 $2°&nbsp;$4

FROM:([0-9]+)°( |-)([0-9]+)°(&nbsp;| )?(C|F)
TO:$1-$2°&nbsp;$4

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
../venv/bin/python3 ../dump_grep_csv.py "degrees? \[*(C|c|F)" | perl -pe "s%<ref.*?</ref>%%g"
| grep -P "degrees? \[*(C|c|F)" | sort > tmp-temp-convert4.txt

cat tmp-temp-convert1.txt tmp-temp-convert2.txt tmp-temp-convert3.txt tmp-temp-convert4.txt tmp-temp-convert4b.txt tmp-temp-convert4c.txt tmp-temp-convert5.txt tmp-temp-convert6.txt
| perl -pe 's/^(.*?):.*/$1/' | uniq > jwb-temperature-convert.txt

# rm -f tmp-temp-weather.txt
# rm -f tmp-temp-F.txt

# Add to run_moss_parallel1.sh:
grep ^TEMP tmp-style-by-line.txt | sort > fixme-temp.txt

# --- MORE METRIC CONVERSIONS ---

# TODO:
# insource:/[¼¾½]( |&nbsp;)(cm|mm|mL|L)/

# TODO:
# * miles, including {{frac|...}} miles and e.g. "1 1/2 miles"
#   (and fractions for other US units)
# * inch and foot, cu ft, cfs - adapt from run_moss_parallel2.sh
# * pounds (weight vs. money)
# * oz (troy, avdp, etc.), fl oz, pint (various), quart (various), gallon (various)
# * psi
# * tons (various)
# * hp
# * hand
# * knot
# * carat
# * cal, kcal
# * furlong

# --- PRIME ---

echo "Beginning prime template check"
echo `date`

# Run time for this segment: ~3 h 50 min

# Incorrect template usage
../venv/bin/python3 ../dump_grep_csv.py "\{\{prime\}\}" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort > jwb-articles-prime.txt
../venv/bin/python3 ../dump_grep_csv.py "\{\{prime\|'" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort >> jwb-articles-prime.txt

# Can be converted to {{coord}} or {{sky}} or {{prime}}
../venv/bin/python3 ../dump_grep_csv.py "[0-9]+° ?[0-9]+['′] ?" | perl -pe 's/^(.*?):.*/$1/' | uniq | sort >> jwb-articles-prime.txt

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

per annum -> per year

FROM:"([a-z]{4})&nbsp;([a-z]{4})"
TO:"$1 $2"

* External links not inside <ref></ref> or in "External links" section
"""


if __name__ == "__main__":
    read_en_article_text(check_style_by_line, parallel="incremental")
