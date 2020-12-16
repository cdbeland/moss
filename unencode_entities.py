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
    "&frasl;",

    "₤",  # per [[MOS:CURRENCY]] should be £ for GBP, but this is used for Italian Lira

    # Probably would be controversial to change these
    "∑", "&sum;",
    "∏",

    # Convert to straight quotes per [[MOS:CONFORM]]
    # but LEAVE when internal to non-English text per [[MOS:STRAIGHT]]
    # Also seen in URL titles (used as stylized field separators)
    # TODO: Detect these in the moss_spell_check run.
    # "‹",  # lsaquo
    # "›",  # rsaquo
    # "«",  # laquo
    # "»",  # rsaquo
    # "„",  # bdquo

    # &zwj; usually wants to be &zwnj; and probably that usually isn't
    # needed?
    "&zwj;", "&zwnj;"

    # Might want to be wiki-list syntax
    "•",
    "&bull;",

    # CONFLICTING SUBSTITUTIONS FOR ARABIC VS. HEBREW:
    # "ʾ": "{{lenis}}",  # For transliterated Arabic alpeh and hamza
    # -> Or maybe make separate templates for these

    # Probably a miscoding of a Hebrew or Arabic letter
    "&#700;",  # U+02BC
    "ʼ",  # U+02BC
    "&#x02BC;",

    "&#701;",
    "&#x02BD;",

    "&#x02BE;",  # : "'",
    "&#702;",  # : "'",
    "ʾ",       #: "'",  # U+02BE Modifier Letter Right Half Ring to ASCII
    # ASCII apostrophe is used in transliterations by default, per
    # [[Wikipedia:Naming conventions (Hebrew)]] which uses the Hebrew Academy scheme at
    # [[Romanization_of_Hebrew#Table]]
    # Hebrew letter [[yodh]] can be left as raw U+05D9 since it should
    # be clear from context it's not an apostrophe
    # For Arabic, this is should be changed to {{hamza}}

    # For native [[Greek numerals]]
    "&#x0374;",  # : "{{keraia}}",

    # For transliterated Arabic ayin
    "&#703;",  # : "{{ayin}}",
    "ʿ",  # : "{{ayin}}",

    # MISUSE OF OKINA FOR CHINESE
    # ʻOkina is U+02BB.
    "ʻ",         # : "{{okina}}",
    "&#x02BB;",  # : "{{okina}}",
    "&#x2bb;",   # : "{{asper}}",
    # Okina is wrong if used as an apostrophe but OK in Hawaiian and
    # maybe other languages.  Per [[Talk:Wade-Giles]], [[spiritus
    # asper]] is preferred (strongly over okina and weakly over
    # apostrophes) for Chinese romanizations using that system.
]

# Ignore these if seen in articles
keep = [
    "&amp;",  # dangerous for e.g. &amp;126;
    "&num;",  # hash symbol, needed in rare cases for section link in template call
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
    "&cap;",    # ∩
    "&cup;",    # ∪
    "&sub;",    # ⊂

    # Would otherwise break markup
    "&lt;",    # <
    "&gt;",    # >
    "&#91;",   # [  {{!(}} will also work
    "&#93;",   # ]  {{)!}} will also work
    # TODO: Maybe these should be converted to <nowiki>[</nowiki> etc.?

    # https://en.wikipedia.org/wiki/Zero-width_non-joiner Used in
    # German, Arabic, Hebrew, etc.  Sometimes abused to fix wikitext
    # markup issues, but would require manual review to determine
    # that.  TODO: Automate ignoring situations where this is inside
    # {{lang}}.
    "&zwnj;",

    "&#x1F610;",   # Emoji presentation selector, non-printing

    "&#xFA9A;",  # Compatibility character identical with U+6F22

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
    "&#x20E0;",  # Combining prohibition sign
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
    "&equiv;": "≡",
    "&oplus;": "⊕",
    "&ne;": "≠",
    "&sube;": "⊆",
    "&subseteq;": "⊆",
    "&not;": "¬",
    "&radic;": "√",
    "&forall;": "∀",
    "&sup;": "⊃",
    "&supe;": "⊇",
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
    "&int;": "∫",
    "&rceil;": "⌉",
    "&lceil;": "⌈",
    "&rfloor;": "⌋",
    "&lfloor;": "⌊",
    "&real;": "ℜ",
    "&sdot;": "⋅",  # Multiplication dot, not to be confused with middot
}

# keep.extend(controversial.keys())

transform_unsafe = {
    # These transformations can't be made in places where the
    # character itself is being discussed, or are just rules of thumb
    # based on observed misuse.

    "&equals;": "=",

    "&#8239;": "&nbsp;",    # narrow no-break space

    # Probably convert to regular space or no space
    "&ensp;": " ",
    "&emsp;": " ",
    "&thinsp;": "{{thin space}}",
    "&hairsp;": "{{hair space}}",
    "&emsp13;": " ",
    "&emsp14;": " ",
    "&numsp;": "{{figure space}}",
    "&puncsp;": " ",
    "&MediumSpace;": " ",

    # (should be μ (&mu;) per [[MOS:NUM#Specific units]]
    "µ": "μ",  # micro to mu
    "&micro;": "μ",  # micro to mu

    "&#x202F;": "",  # Narrow non-breaking space, usually not needed
    "&#x202f;": "",

    # Used in math and tables and horizontal list formatting
    # "⋅": "-",

    "&#x2010;": "-",  # Hyphen
    "&#x2027;": "-",  # Hyphenation point
    "‐": "-",         # U+2010 Hyphen to ASCII

    # Usually a typo for &ndash;
    # "&dash;": "-",  # ASCII hyphen
    "&dash;": "&ndash;",  # ASCII hyphen

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
    "½": "{{frac|1|2}}",  # Except ½ is allowed in chess articles
    "¾": "{{frac|3|4}}",
    "⅓": "{{frac|1|3}}",
    "⅔": "{{frac|2|3}}",
    "⅐": "{{frac|1|7}}",
    "⅑": "{{frac|1|9}}",
    "⅒": "{{frac|1|10}}",
    "⅕": "{{frac|1|5}}",
    "⅖": "{{frac|2|5}}",
    "⅗": "{{frac|3|5}}",
    "⅘": "{{frac|4|5}}",
    "⅙": "{{frac|1|6}}",
    "⅚": "{{frac|5|6}}",
    "⅛": "{{frac|1|8}}",
    "⅜": "{{frac|3|8}}",
    "⅝": "{{frac|5|8}}",
    "⅞": "{{frac|7|8}}",

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
    "&half;": "{{frac|1|2}}",
    "&frac12;": "{{frac|1|2}}",
    "&frac14;": "{{frac|1|4}}",
    "&frac16;": "{{frac|1|6}}",
    "&frac18;": "{{frac|1|8}}",
    "&frac23;": "{{frac|2|3}}",
    "&frac34;": "{{frac|3|4}}",
    "&#8531;": "{{frac|1|3}}",

    "&sol;": "/",

    # [[MOS:1ST]]
    "ˢᵗ": "st",
    "ⁿᵈ": "nd",
    "ʳᵈ": "rd",
    "ᵗʰ": "th",
    # TODO: https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts

    "…": "...",
    "&#8230;": "...",
    "&hellip;": "...",

    "&#123;": "&lbrace;",  # {
    "&#125;": "&rbrace;",  # }

    # This is a pipe, and usually happens in URL titles
    "&#124;": "{{pipe}}",
    "&VerticalLine;": "{{pipe}}",
    "&verbar;": "{{pipe}}",
    "&vert;": "{{pipe}}",
    # {{!}} in tables?
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
    "&bdquo;": "„",  # OK when internal to non-English text

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

    "&#42;": "&ast;",  # * (causes problems with wikitext syntax sometimes)

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
    "&#x2006;": "{{thin space}}",
    "&#8198;": "{{thin space}}",
    "&#x2007;": "&numsp;",
    "&#8199;": "&numsp;",
    "&#2008x;": "&puncsp;",
    "&#8200;": "&puncsp;",
    "&#x2009;": "{{thin space}}",
    "&#8201;": "{{thin space}}",
    "&#x200A;": "{{hair space}}",
    "&#8202;": "{{hair space}}",
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
    "&00091;": "&#91;",
    "&00093;": "&#93;",
    "&#x5B;": "&#91;",
    "&#x5D;": "&#93;",
    "&#x7C;": "{{!}}",  # |
    "&#x7c;": "{{!}}",  # |
    "&#x007C;": "{{!}}",  # |
    "&#0124;": "{{!}}",  # |
    "&#x3C;": "&lt;",
    "&#x003C;": "&lt;",
    "&#x3E;": "&gt;",
    "&#x003E;": "&gt;",
    "&#60;": "&lt;",
    "&#060;": "&lt;",
    "&#0060;": "&lt;",
    "&#61;": "{{=}}",  # Will break markup inside templates
    "&#061;": "{{=}}",  # Will break markup inside templates
    "&#0061;": "{{=}}",  # Will break markup inside templates
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

    "¹": "<sup>1</sup>",
    "²": "<sup>2</sup>",
    "³": "<sup>3</sup>",
    "⁴": "<sup>4</sup>",
    "⁵": "<sup>5</sup>",
    "⁶": "<sup>6</sup>",
    "⁷": "<sup>7</sup>",
    "⁸": "<sup>8</sup>",
    "⁹": "<sup>9</sup>",
    "⁰": "<sup>0</sup>",
    "ⁱ": "<sup>i</sup>",

    "⁺": "<sup>+</sup>",
    "⁻": "<sup>-</sup>",
    "⁼": "<sup>=</sup>",
    "⁽": "<sup>(</sup>",
    "⁾": "<sup>)</sup>",
    "ⁿ": "<sup>n</sup>",

    "₀": "<sub>0</sub>",
    "₁": "<sub>1</sub>",
    "₂": "<sub>2</sub>",
    "₃": "<sub>3</sub>",
    "₄": "<sub>4</sub>",
    "₅": "<sub>5</sub>",
    "₆": "<sub>6</sub>",
    "₇": "<sub>7</sub>",
    "₈": "<sub>8</sub>",
    "₉": "<sub>9</sub>",
    "₊": "<sub>+</sub>",
    "₋": "<sub>-</sub>",
    "₌": "<sub>=</sub>",
    "₍": "<sub>(</sub>",
    "₎": "<sub>)</sub>",

    "ₐ": "<sub>a</sub>",
    "ₑ": "<sub>e</sub>",
    "ₒ": "<sub>o</sub>",
    "ₓ": "<sub>x</sub>",
    "ₔ": "<sub>Ə</sub>",
    "ₕ": "<sub>h</sub>",
    "ₖ": "<sub>k</sub>",
    "ₗ": "<sub>l</sub>",
    "ₘ": "<sub>m</sub>",
    "ₙ": "<sub>n</sub>",
    "ₚ": "<sub>p</sub>",
    "ₛ": "<sub>s</sub>",
    "ₜ": "<sub>t</sub>",

    "ꟹ": "<sup>oe</sup>",
    "ⱼ": "<sub>j</sub>",

    "&#0033;": "!",
    "&#0047;": "/",
    "&#005C;": "\\",

    "&#043;": "+",
    "&#037;": "%",
    "&colon;": ":",  # {{colon}} is also available
    "&check;": "✓",

    "&apos;": "'",  # Or {{'}}
    "&Apos;": "'",  # Or {{'}}
    "&#8216;": "'",
    "&#8217;": "'",

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
    "&divide;": "÷",

    "&leq;": "≤",
    "&rationals;": "ℚ",
    "&integers;": "ℤ",
    "&reals;": "ℝ",
    "&mp;": "∓",
    "&therefore;": "∴",
    "&in;": "∈",
    "&epsi;": "ε",
    "&Ropf;": "ℝ",
    "&Kopf;": "𝕂",
    "&Copf;": "ℂ",
    "&approx;": "≈",
    "&prop;": "∝",
    "&complexes;": "ℂ",

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
    "&amacr;": "ā",
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
    "&icirc;": "î",
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

    "―": "—",  # horbar to emdash
    "&horbar;": "&mdash;",

    "&#x2013;": "–",  # endash
    "&#8211;": "–",  # endash

    # Broken (typo on page)
    "&#150;": "-",
    "&#151;": "-",
    "&ccedi;": "ç",
    "&Amp;": "&amp;",
    "&AMP;": "&amp;",
    "&6nbsp;": "&nbsp;",
    "&Ndash;": "&ndash;",
    "&nybsp;": "&nbsp;",
    "&nbsop;": "&nbsp;",
    "&nbdsp;": "&nbsp;",
    "&ndsah;": "&ndash;",
    "&ndaash;": "&ndash;",
    "&ndssh;": "&ndash;",
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
    "&nsash;": "&ndash;",
    "&nbdash;": "&ndash;",
    "&endash;": "&ndash;",
    "&bdash;": "&ndash;",
    "&ndahs;": "&ndash;",
    "&dnash;": "&ndash;",
    "&ndasgh;": "&ndash;",
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
    "&nvsp;": "&nbsp;",
    "&nbnsp;": "&nbsp;",
    "&knbsp;": "&nbsp;",
    "&uumml;": "&uuml;",
    "&bsp;": "&nbsp;",
    "&Quot;": '"',
    "&sbquo;": "‚",
    "&nbs;": "&nbsp;",
    "&nbspb;": "&nbsp;",
    "&ndassh;": "&ndash;",
    "&nndash;": "&nndash;",
    "&npsb;": "&nbsp;",
    "&nsp;": "&nbsp;",
    "&124;": "&#124;",
    "&tbsp;": "&nbsp;",

    # Used in tables, horizontal list formatting
    "&middot;": "·",
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

    # Non-characters
    # http://www.unicode.org/faq/private_use.html
    if num_value >= 0xFDD0 and num_value <= 0xFDEF:
        return True
    if num_value in [
            "0000FFFE",
            "0001FFFE",
            "0002FFFE",
            "0003FFFE",
            "0004FFFE",
            "0005FFFE",
            "0006FFFE",
            "0007FFFE",
            "0008FFFE",
            "0009FFFE",
            "000AFFFE",
            "000BFFFE",
            "000CFFFE",
            "000DFFFE",
            "000EFFFE",
            "000FFFFE",
            "0010FFFE",
            "0000FFFF",
            "0001FFFF",
            "0002FFFF",
            "0003FFFF",
            "0004FFFF",
            "0005FFFF",
            "0006FFFF",
            "0007FFFF",
            "0008FFFF",
            "0009FFFF",
            "000AFFFF",
            "000BFFFF",
            "000CFFFF",
            "000DFFFF",
            "000EFFFF",
            "000FFFFF",
            "0010FFFF"]:
        return True
    if unicodedata.combining(chr(num_value)):
        # Combining characters are too difficult to edit as themselves
        return True
    if variant_selectors_re.match(entity):
        return True

    # Avoid changing entities into characters that would normalized
    # into a different
    # character.
    # https://en.wikipedia.org/wiki/Unicode_equivalence#Normalization
    transformed = unicodedata.normalize("NFC", entity)
    if entity != transformed:
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
        conversion_dict.update(controversial)
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
