import fileinput
import re
import sys
import unicodedata

# To make a string of all whitespace characters in Unicode:
# s = ''.join(chr(c) for c in range(sys.maxunicode+1))
# ws = ''.join(re.findall(r'\s', s))
# https://stackoverflow.com/questions/37903317/is-there-a-python-constant-for-unicode-whitespace

# To separate out control characters from printable and whitespace
# characters, see the General Category attribute and subcategories:
# http://www.unicode.org/versions/Unicode11.0.0/ch04.pdf#G91002

entities_re = re.compile(r"&#?[a-zA-Z0-9]+;")
variant_selectors_re = re.compile(r"^&#x(FE0.|E01..|180B|180C|180D|1F3F[B-F]);", flags=re.I)
# https://en.wikipedia.org/wiki/Variant_form_(Unicode)
# U+1F3FB–U+1F3FF are emoji skin tone selectors
# https://en.wikipedia.org/wiki/Miscellaneous_Symbols_and_Pictographs#Emoji_modifiers

# Manual transformation probably required
alert = [
    "™", "©", "®",
    "Ⅰ", "Ⅱ", "ⅰ", "ⅱ",
    "¼", "¾", "&frasl;",
    "¹", "⁺", "ⁿ", "₁", "₊", "ₙ",

    "½",  # Allowed in chess articles only
    "₤",  # per [[MOS:CURRENCY]] should be £ for GBP, but this is used for Italian Lira

    # (should be μ (&mu;) per [[MOS:NUM#Specific units]]
    "µ", "&micro;",

    # Probably would be controversial to change these
    "∑", "&sum;",
    "∏",

    # Try &mdash instead
    "―", "&horbar;",

    # Convert to straight quotes, or keep &-encoded version
    "‘", "&lsquo;",
    "’", "&rsquo;",
    "‚", "&sbquo;",
    "“", "&ldquo;",
    "”", "&rdquo;",
    "„", "&bdquo;",
    "´", "&acute;",
    "`", "&#96;",

    # Convert to straight quotes per [[MOS:CONFORM]]
    # but NOT in foreign-language internal text
    "‹", "&lsaquo;", "›", "&rsaquo;",
    "«", "&lsaquo;", "»", "&rsaquo;",

    # Probably convert to regular space or no space
    "&ensp;", "&emsp;", "&thinsp;", "&hairsp;",

    # &zwj; usually wants to be &zwnj; and probably that usually isn't
    # needed?
    "&zwj;", "&zwnj;"

    # Might want to be wiki-list syntax
    "•",
    "&bull;",

    # Convert to dot form
    "&middot;",
    "&sdot;",

]

# Ignore these if seen in articles
keep = [
    # Used in math, tables, horizontal list formatting, so keep
    "·",  # middot
    "⋅",  # sdot

    "&amp;",  # dangerous for e.g. &amp;126;
    "&c;",    # Almost all are in archaic quotations and titles

    "&#x0261;",  # g for gravity distinguished from g for gram

    # Should be excluded by <source> etc.
    # "&a;",    # Used in computer articles as example of a pointer
    # "&x;",    # Used in computer articles as example of a pointer

    # Allowed for math notation only
    "&prime;", "′", "&Prime;", "″", "&x2034", "‴",

    "ʼ",  # U+02BC, used in IPA and a letter in some languages, including Klingon

    # Definitely confusing, keep forever
    "&ndash;", "&mdash;", "&minus;", "&shy;",
    "&nbsp;", "&lrm;", "&rlm;",

    # Directionality controls
    "&#x200E;",
    "&#x061C;",
    "&#x202A;",
    "&#x202B;",
    "&#x202C;",
    "&#x202D;",
    "&#x202E;",
    "&#x200e;",
    "&#x061c;",
    "&#x202a;",
    "&#x202b;",
    "&#x202c;",
    "&#x202d;",
    "&#x202e;",
    "&#x2066;",
    "&#x2066;",
    "&#x2067;",
    "&#x2068;",
    "&#x2069;",

    # Definitely confusing, probably keep forever
    "&times;",  # ×
    "&and;",    # ∧
    "&or;",     # ∨
    "&lang;",   # 〈
    "&rang;",   # 〉

    # Would otherwise break markup
    "&lt;",    # <
    "&gt;",    # >
    "&#91;",   # [
    "&#93;",   # ]
    "&#123;",  # {
    "&#124;",  # |  &vert; doesn't work
    "&#125;",  # }
    # TODO: Maybe these should be converted to <nowiki>[</nowiki> etc.?

    # https://en.wikipedia.org/wiki/Zero-width_non-joiner Used in
    # German, Arabic, Hebrew, etc.  Sometimes abused to fix wikitext
    # markup issues, but would require manual review to determine
    # that.  TODO: Automate ignoring situations where this is inside
    # {{lang}}.
    "&zwnj;",

    "&#x1F610;",   # Emoji presentation selector, non-printing

    # Combining characters, apparently unlabelled
    "&#x114c1;",
    "&#x114bf;",
    "&#x114be;",
    "&#x114bd;",
    "&#x114bc;",
    "&#x114bb;",
    "&#x114ba;",
    "&#x114b9;",
    "&#x114b8;",
    "&#x114b7;",
    "&#x114b6;",
    "&#x114b5;",
    "&#x114b4;",
    "&#x114b3;",
    "&#x114b2;",
    "&#x114b1;",
    "&#x114b0;",
    "&#x114c0;"
    "&#x20DD;",
    "&#x20DE;",
    "&#x20E3;",
    "&#x20e3;",
    "&#x20e4;",  # Combining triangle
]

controversial = {
    # Possibly controversial (math and science people have been somewhat upset)
    "&asymp;": "≈",
    "&empty;": "∅",
    "&part;": "∂",
    "&notin;": "∉",
    "&otimes;": "⊗",
    "&exist;": "∃",
    "&nabla;": "∇",
    "&sub;": "⊂",
    "&equiv;": "≡",
    "&cap;": "∩",
    "&cup;": "∪",
    "&oplus;": "⊕",
    "&ne;": "≠",
    "&sube;": "⊆",
    "&not;": "¬",
    "&radic;": "√",
    "&forall;": "∀",
    "&sup;": "⊃",
    "&sim;": "∼",
    "&perp;": "⊥",
    "&alefsym;": "ℵ",
    "&isin;": "∈",
    "&le;": "≤",  # available at the bottom of the wikitext edit window
    "&fnof;": "ƒ",
    "&infin;": "∞",
    "&ge;": "≥",  # available at the bottom of the wikitext edit window
    "&lowast;": "∗",
    "&cong;": "≅",
    "&weierp;": "℘",
    "&hArr;": "⇔",
    "&rArr;": "⇒",
    "&rarr;": "→",
    "&larr;": "←",
    "&lArr;": "⇐",
    "&harr;": "↔",
    "&darr;": "↓",
    "&uarr;": "↑",
    "&uArr;": "⇑",
    "&crarr;": "↵",
    "&prop;": "∝",
    "&int;": "∫",
    "&rceil;": "⌉",
    "&lceil;": "⌈",
    "&real;": "ℜ",
}

keep.extend(controversial.keys())

transform_unsafe = {
    # These transformations can't be made in places where the
    # character itself is being discussed, or are just rules of thumb
    # based on observed misuse.

    "&#8239; ": "&nbsp;",    # narrow no-break space

    "µ": "μ",  # micro to mu

    "&#x202F;": "",  # Narrow non-breaking space, usually not needed
    "&#x202f;": "",

    # Used in math and tables and horizontal list formatting
    # "⋅": "-",

    "&#x2010;": "-",  # Hyphen
    "&#x2027;": "-",  # Hyphenation point
    "‐": "-",         # U+2010 Hyphen to ASCII
    "&#2027;": "&middot;",  # Changing from hyphenation point to middot
    "&#x2116;": "No.",
    "&#8470;": "No.",

    # &#x2011; should be kept if it is at the beginning or end of a
    # word, so the hyphen doesn't break onto a new line (due to bug in
    # Chrome, reported 27 Jul 2019 - see
    # https://en.wikipedia.org/wiki/Talk:B%C3%B6rje#Hyphens_and_linebreaks)
    "&#8209;": "-",   # U+2011 Non-breaking hyphen to ASCII
    "&#x2011;": "-",   # U+2011 Non-breaking hyphen to ASCII

    # Per [[MOS:FRAC]]
    "¼": "{{frac|1|4}}",
    "½": "{{frac|1|2}}",
    "¾": "{{frac|3|4}}",
    "⅓": "{{frac|1|3}}",
    "⅔": "{{frac|2|3}}",

    "&#x2150;": "{{frac|1|7}}",
    "&#x2151;": "{{frac|1|9}}",
    "&#x2152;": "{{frac|1|10}}",
    "&#x2153;": "{{frac|1|3}}",
    "&#x2154;": "{{frac|2|3}}",
    "&#x2155;": "{{frac|1|5}}",
    "&#x2156;": "{{frac|2|5}}",
    "&#x2157;": "{{frac|3|5}}",
    "&#x2158;": "{{frac|4|5}}",
    "&#x2159;": "{{frac|1|6}}",
    "&#x215A;": "{{frac|5|6}}",
    "&#x215B;": "{{frac|1|8}}",
    "&#x215C;": "{{frac|3|8}}",
    "&#x215D;": "{{frac|5|8}}",
    "&#x215E;": "{{frac|7|8}}",
    "&frac12;": "{{frac|1|2}}",
    "&frac14;": "{{frac|1|4}}",
    "&frac16;": "{{frac|1|6}}",
    "&frac34;": "{{frac|3|4}}",
    "&#8531;": "{{frac|1|3}}",
    "…": "...",
    "&#8230;": "...",
    "&hellip;": "...",

    # These often break wiki markup
    # "&#91;": "[",
    # "&#93;": "]",

    # This is a pipe, but usually happens in URL titles, in which case
    # making a dash is easier.
    "&#124;": "-",
    # If a pipe character is needed, use {{!}}
    # https://www.mediawiki.org/wiki/Help:Magic_words#Other

    # These are usually spurious, per [[MOS:TMRULES]]
    "&trade;": "",  # ™
    "&reg;": "",  # ®
    "&copy;": "",  # ©
    "™": "",
    "®": "",
    "©": "",
    "&8482;": "",   # ™

    # Normalizing quote marks
    "‘": "'",
    "&lsquo;": "'",
    "’": "'",
    "&rsquo;": "'",
    "“": '"',
    "&ldquo;": '"',
    "”": '"',
    "&rdquo;": '"',
    "´": "'",
    "&acute;": "'",
    "`": "'",
    "&#x27;": "'",
    "&#39;": "'",
    "&#039;": "'",
    "&#96;": "'",
    "&#8220;": '"',  # “ -> "
    "&#8221;": '"',  # ” -> "
    "&#8216;": "'",   # ‘ -> '
    "&#x2018;": "'",   # ’ -> '
    "&#8217;": "'",   # ’ -> '
    "&#x2019;": "'",   # ’ -> '
    "&#x201C;": '"',
    "&#x201D;": '"',

    # CONFLICTING SUBSTITUTIONS FOR ARABIC VS. HEBREW:
    # "ʾ": "{{lenis}}",  # For transliterated Arabic alpeh and hamza
    # -> Or maybe make separate templates for these

    "&#x02BE;": "'",
    "&#702;": "'",
    "ʾ": "'",  # U+02BE Modifier Letter Right Half Ring to ASCII
    # ASCII apostrophe is used in transliterations by default, per
    # [[Wikipedia:Naming conventions (Hebrew)]] which uses the Hebrew Academy scheme at
    # [[Romanization_of_Hebrew#Table]]
    # Hebrew letter [[yodh]] can be left as raw U+05D9 since it should
    # be clear from context it's not an apostrophe

    # For native [[Greek numerals]]
    "&#x0374;": "{{keraia}}",

    # For transliterated Arabic ayin
    "&#703;": "{{ayin}}",
    "ʿ": "{{ayin}}",

    # MISUSE OF OKINA FOR CHINESE
    # ʻOkina is U+02BB.
    "ʻ": "{{okina}}",
    "&#x02BB;": "{{okina}}",
    "&#x2bb;": "{{asper}}",
    # Okina is wrong if used as an apostrophe but OK in Hawaiian and
    # maybe other languages.  Per [[Talk:Wade-Giles]], [[spiritus
    # asper]] is preferred (strongly over okina and weakly over
    # apostrophes) for Chinese romanizations using that system.


    # NOT SURE THIS IS A GOOD IDEA.
    # Per [[MOS:CONFORM]]
    # "« ": '"',
    # " »": '"',
    # "«": '"',
    # "»": '"',
    # "&raquo;": '"',
    # "&laquo;": '"',
    #
    # At least normalize to characters instead of HTML entities; there
    # are 70k+ pages with « or », so those can be ignored for now.
    "&laquo;": "«",
    "&raquo;": "»",

    "&ensp;": " ",
    "&emsp;": " ",
    "&emsp13;": " ",
    "&emsp14;": " ",
    "&thinsp;": "",
    "&numsp;": " ",
    "&puncsp;": " ",
    "&hairsp;": " ",
    "&MediumSpace;": " ",

    "&zwj;": "",
    "&zwnj;": "",

    # https://en.wikipedia.org/wiki/Numerals_in_Unicode#Roman_numerals
    "Ⅰ": "I",
    "Ⅱ": "II",
    "Ⅲ": "III",
    "Ⅳ": "IV",
    "Ⅴ": "V",
    "Ⅵ": "VI",
    "Ⅶ": "VII",
    "Ⅷ": "VIII",
    "Ⅸ": "IX",
    "Ⅹ": "X",
    "Ⅺ": "XI",
    "Ⅻ": "XII",
    "Ⅼ": "L",
    "Ⅽ": "C",
    "Ⅾ": "D",
    "Ⅿ": "M",
    "ⅰ": "i",
    "ⅱ": "ii",
    "ⅲ": "iii",
    "ⅳ": "iv",
    "ⅴ": "v",
    "ⅵ": "vi",
    "ⅶ": "vii",
    "ⅷ": "viii",
    "ⅸ": "ix",
    "ⅹ": "x",
    "ⅺ": "xi",
    "ⅻ": "xii",
    "ⅼ": "l",
    "ⅽ": "c",
    "ⅾ": "d",
    "ⅿ": "m",
}

# Automatically change, with the expectation there will be a
# manual inspection of the diff
transform = {

    "&#x22c5;": "&sdot;",
    "&#8416;": "&#x20E0;",  # Combining Enclosing Circle Backslash

    "&#6;": " ",   # ^F
    "&#06;": " ",   # ^F
    "&#22;": " ",   # ^V
    "&#13;": "\n",   # ^M
    "&#013;": "\n",   # ^M

    "&#x200C;": "&zwnj;",

    "&#8207;": "&rlm;",
    "&#x200F;": "&rlm;",
    "&#x02C6;": "&circ;",
    "&#x710;": "&circ;",
    "&#8242;": "&prime;",
    "&#x2032;": "&prime;",
    "&#8243;": "&Prime;",  # Double prime
    "&#x2033;": "&Prime;",  # Double prime

    "&#x2000;": "&ensp;",
    "&#8192;": "&ensp;",
    "&#x2002;": "&ensp;",
    "&#8194;": "&ensp;",
    "&#x2001;": "&emsp;",
    "&#8193;": "&emsp;",
    "&#x2003;": "&emsp;",
    "&#8195;": "&emsp;",

    "&#x2004;": "&emsp13;",
    "&#8196;": "&emsp13;",
    "&#x2005;": "&emsp14;",
    "&#8127;": "&emsp14;",
    "&#x2006;": "&thinsp;",
    "&#8198;": "&thinsp;",
    "&#x2007;": "&numsp;",
    "&#8199;": "&numsp;",
    "&#2008x;": "&puncsp;",
    "&#8200;": "&puncsp;",
    "&#x2009;": "&thinsp;",
    "&#8201;": "&thinsp;",
    "&#x200A;": "&hairsp;",
    "&#8202;": "&hairsp;",
    "&#x205F;": "&MediumSpace;",
    "&#8287;": "&MediumSpace;",
    "&#x200B;": "&zwsp;",
    "&#x200b;": "&zwsp;",
    "&#8203;": "&zwsp;",
    "&#x200C;": "&zwnj;",
    "&#8204;": "&zwnj;",
    "&#x200D;": "&zwj;",
    "&#8205;": "&zwj;",
    "&#x2060;": "&NoBreak;",
    "&#8288;": "&NoBreak;",
    "&#xFEFF;": "",
    "&#65279;": "",

    "&#8206;": "&lrm;",

    "&#x005B;": "&#91;",  # [
    "&#x005D;": "&#93;",  # ]
    "&#x5b;": "&#91;",
    "&#x5d;": "&#93;",
    "&#091;": "&#91;",
    "&#093;": "&#93;",
    "&#0091;": "&#91;",
    "&#0093;": "&#93;",
    "&#00091;": "&#91;",
    "&#00093;": "&#93;",
    "&#x5B;": "&#91;",
    "&#x5D;": "&#93;",
    "&#x7C;": "&#124;",  # |
    "&#x7c;": "&#124;",  # |
    "&#x007C;": "&#124;",  # |
    "&#0124;": "&#124;",  # |
    "&#x3C;": "&lt;",
    "&#x003C;": "&lt;",
    "&#x3E;": "&gt;",
    "&#x003E;": "&gt;",
    "&#60;": "&lt;",
    "&#060;": "&lt;",
    "&#0060;": "&lt;",
    "&#61;": "=",  # Will break markup inside templates
    "&#061;": "=",  # Will break markup inside templates
    "&#0061;": "=",  # Will break markup inside templates
    "&#62;": "&gt;",
    "&#062;": "&gt;",
    "&#0062;": "&gt;",
    "&#093;": "&#93;",  # ]
    "&#0093;": "&#93;",  # ]
    "&lsqb;": "&#91;",
    "&rsqb;": "&#93;",

    "&#160;": "&nbsp;",
    "&#xA0;": "&nbsp;",
    "&#x0A0;": "&nbsp;",
    "&#x00A0;": "&nbsp;",

    "&#x9;": "&tab;",
    "&#9;": "&tab;",
    "&#09;": "&tab;",
    "&#x09;": "&tab;",
    "&#x0009;": "&tab;",

    "&permil;": "‰",

    "&sup1;": "<sup>1</sup>",
    "&sup2;": "<sup>2</sup>",
    "&sup3;": "<sup>3</sup>",

    "&#0033;": "!",
    "&#0047;": "/",
    "&#005C;": "\\",

    "&#043;": "+",
    "&#037;": "%",

    "&apos;": "'",
    "&#8216;": "'",
    "&#8217;": "'",
    "&#700;": "'",  # U+02BC
    "ʼ": "'",  # U+02BC
    "&#x02BC;": "'",

    "&quot;": '"',
    "&#8220;": '"',
    "&#8221;": '"',

    # "&lt;": "<",
    # "&gt;": ">",

    # Common symbols, to change outside of math/science articles
    "&iquest;": "¿",
    "&pound;": "£",
    "&#163;": "£",
    "&sect;": "§",
    "&para;": "¶",
    "&brvbar;": "¦",
    "&euro;": "€",
    "&curren;": "¤",
    "&dagger;": "†",
    "&Dagger;": "‡",
    "&clubs;": "♣",
    "&diams;": "♦",
    "&spades;": "♠",
    "&deg;": "°",
    "&oline;": "‾",
    "&plusmn;": "±",
    "&cent;": "¢",
    "&circ;": "ˆ",
    "&yen;": "¥",
    "&Tcedil;": "Ţ",
    "&tcedil;": "ţ",
    "&Scedil;": "Ş",
    "&scedil;": "ş",

    "㎆": "MB",
    "㎅": "KB",
    "&#x00B4;": "&acute;",
    "&ordf;": "ª",
    "&ang;": "∠",

    # Latin and Germanic letters
    "&Aacute;": "Á",
    "&aacute;": "á",
    "&acirc;": "â",
    "&Acirc;": "Â",
    "&Agrave;": "À",
    "&agrave;": "à",
    "&Aring;": "Å",
    "&aring;": "å",
    "&Atilde;": "Ã",
    "&atilde;": "ã",
    "&Auml;": "Ä",
    "&auml;": "ä",
    "&#X101;": "ā",
    "&Ccedil;": "Ç",
    "&ccedil;": "ç",
    "&eth;": "ð",
    "&Eacute;": "É",
    "&eacute;": "é",
    "&ecirc;": "ê",
    "&Egrave;": "È",
    "&egrave;": "è",
    "&euml;": "ë",
    "&#X1E24;": "Ḥ",
    "&iacute;": "í",
    "&Iacute;": "Í",
    "&igrave;": "ì",
    "&iuml;": "ï",
    "&Ntilde;": "Ñ",
    "&ntilde;": "ñ",
    "&oacute;": "ó",
    "&ocirc;": "ô",
    "&Oacute;": "Ó",
    "&ograve;": "ò",
    "&Oslash;": "Ø",
    "&oslash;": "ø",
    "&otilde;": "õ",
    "&Otilde;": "Õ",
    "&Ouml;": "Ö",
    "&ouml;": "ö",
    "&#X14D;": "ō",
    "&Scaron;": "Š",
    "&scaron;": "š",
    "&#X161;": "š",
    "&szlig;": "ß",
    "&Uacute;": "Ú",
    "&uacute;": "ú",
    "&Ucirc;": "Û",
    "&ucirc;": "û",
    "&ugrave;": "ù",
    "&Uuml;": "Ü",
    "&uuml;": "ü",
    "&yacute;": "ý",

    "&#214;": "Ö",
    "&#225;": "á",
    "&#227;": "ã",
    "&#228;": "ä",
    "&#229;": "å",
    "&#230;": "æ",
    "&#233;": "é",
    "&#234;": "ê",
    "&#237;": "í",
    "&#246;": "ö",
    "&#248;": "ø",
    "&#250;": "ú",
    "&#287;": "ğ",
    "&#304;": "İ",

    # Removed from "alert": "Æ", "æ", "Œ", "œ",
    # Per [[MOS:LIGATURES]], allowed in proper names and text in
    # languages in which they are standard. Usually not worth
    # reviewing. Non-proper names will show up on spell check anyway
    # if it's not a standard rendering.
    "&aelig;": "æ",
    "&oelig;": "œ",
    "&AElig;": "Æ",
    "&OElig;": "Œ",

    # Greek letters only found in actual Greek words
    "&sigmaf;": "ς",  # Written this way when word-final
    "&#x1F7B;": "ύ",
    "&#x1F76;": "ὶ",
    "&#x1FC6;": "ῆ",
    "&#x1F10;": "ἐ",
    "&#x1FF7;": "ῷ",
    "&#x1FC6;": "ῆ",

    "&#8212;": "—",   # emdash
    "&#X2014;": "—",  # emdash
    "&#x2014;": "—",  # emdash

    "&#x2013;": "–",  # endash
    "&#8211;": "–",  # endash

    # Usually a typo for &ndash;
    # "&dash;": "-",  # ASCII hyphen

    # Broken (typo on page)
    "&ccedi;": "ç",
    "&Amp;": "&amp;",
    "&6nbsp;": "&nbsp;",
    "&Ndash;": "&ndash;",
    "&nybsp;": "&nbsp;",
    "&nbsop;": "&nbsp;",
    "&ndsah;": "&ndash;",
    "&ndaash;": "&ndash;",
    "&ndsh;": "&ndash;",
    "&nfash;": "&ndash;",
    "&nbbsp;": "&nbsp;",
    "&nhdash;": "&ndash;",
    "&19ndash;": "&ndash;",
    "&nsah;": "&ndash;",
    "&nnbsp;": "&nbsp;",
    "&NDASH;": "&ndash;",
    "&mbsp;": "&nbsp;",
    "&nadsh;": "&ndash;",
    "&nash;": "&ndash;",
    "&nbdash;": "&ndash;",
    "&nsbp;": "&nbsp;",
    "&nbps;": "&nbsp;",
    "&bnsp;": "&nbsp;",
    "&spnb;": "&nbsp;",
    "&ndsp;": "&nbsp;",
    "&nbp;": "&nbsp;",
    "&nhsp;": "&nbsp;",
    "&ngsp;": "&nbsp;",
    "&nbvsp;": "&nbsp;",
    "&nbsvp;": "&nbsp;",
    "&nbsb;": "&nbsp;",
    "&nbnsp;": "&nbsp;",
    "&uumml;": "&uuml;",
    "&bsp;": "&nbsp;",
    "&Quot;": '"',
}

greek_letters = {
    "&alpha;": "α",
    "&beta;": "β",
    "&gamma;": "γ",
    "&delta;": "δ",
    "&epsilon;": "ε",
    "&zeta;": "ζ",
    "&eta;": "η",
    "&theta;": "θ",
    "&iota;": "ι",
    "&lambda;": "λ",
    "&mu;": "μ",
    "&nu;": "ν",
    "&xi;": "ξ",
    "&pi;": "π",
    "&sigma;": "σ",
    "&tau;": "τ",
    "&upsilon;": "υ",
    "&phi;": "φ",
    "&chi;": "χ",
    "&psi;": "ψ",
    "&omega;": "ω",
    "&Gamma;": "Γ",
    "&Delta;": "Δ",
    "&Theta;": "Θ",
    "&Lambda;": "Λ",
    "&Xi;": "Ξ",
    "&Pi;": "Π",
    "&Sigma;": "Σ",
    "&Phi;": "Φ",
    "&Psi;": "Ψ",
    "&Omega;": "Ω",

    # There are strong objections to changing these outside of
    # Greek words, because they look too much like Latin letters.
    "&kappa;": "κ",
    "&omicron;": "ο",
    "&rho;": "ρ",
    "&Alpha;": "Α",
    "&Beta;": "Β",
    "&Epsilon;": "Ε",
    "&Zeta;": "Ζ",
    "&Eta;": "Η",
    "&Iota;": "Ι",
    "&Kappa;": "Κ",
    "&Mu;": "Μ",
    "&Nu;": "Ν",
    "&Omicron;": "Ο",
    "&Rho;": "Ρ",
    "&Tau;": "Τ",
    "&Upsilon;": "Υ",
    "&Chi;": "Χ",
}


def find_char_num(entity):
    result = re.match("&#(x?[0-9a-fA-F]+);", entity)
    if result:
        number = result.group(1)
        if number.startswith("x"):
            number = number.strip("x")
            number = int(number, 16)
        else:
            try:
                number = int(number)
            except ValueError:
                return None
        return number
    else:
        return None


def find_char(entity):
    number = find_char_num(entity)
    if number:
        return chr(number)
    else:
        return None


def should_keep_as_is(entity):
    num_value = find_char_num(entity)
    if num_value is None:
        return False

    if num_value >= 0xE000 and num_value <= 0xF8FF:
        # Private Use Area
        return True
    if num_value >= 0xF0000 and num_value <= 0xFFFFD:
        # Supplemental Private Use Area-A
        return True
    if num_value >= 0x100000 and num_value <= 0x10FFFD:
        # Supplemental Private Use Area-B
        return True
    if unicodedata.combining(chr(num_value)):
        # Combining characters are too difficult to edit as themselves
        return True
    if variant_selectors_re.match(entity):
        return True

    return False


def make_character_or_ignore(entity):
    # Returns the Unicode character for this entity, or None if the
    # entity should not be changed.

    character = find_char(entity)
    if not character:
        return None
    if should_keep_as_is(entity):
        return None
    return character


def fix_text(text, transform_greek=False):

    if transform_greek:
        conversion_dict = transform.copy()
        conversion_dict.update(greek_letters)
    else:
        conversion_dict = transform

    new_text = text
    for (from_string, to_string) in conversion_dict.items():
        new_text = new_text.replace(from_string, to_string)

    test_string = new_text
    for string in keep:
        test_string = test_string.replace(string, "")
    if not transform_greek:
        for string in greek_letters:
            test_string = test_string.replace(string, "")
    for unknown_entity in re.findall("&#?[a-zA-Z0-9]+;", test_string):
        character = make_character_or_ignore(unknown_entity)
        if character is not None:
            new_text = new_text.replace(unknown_entity, character)

    return new_text


if len(sys.argv) > 1 and "--safe" in sys.argv:
    pass
else:
    transform.update(transform_unsafe)

if __name__ == '__main__':
    for line in fileinput.input("-"):
        new_line = fix_text(line)
        sys.stdout.write(new_line)
