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

    # Convert to straight quotes per [[MOS:CONFORM]]
    # but LEAVE when internal to non-English text per [[MOS:STRAIGHT]]
    # Also seen in URL titles (used as stylized field separators)
    # TODO: Detect these in the moss_spell_check run.
    # "‹",  # lsaquo
    # "›",  # rsaquo
    # "«",  # laquo
    # "»",  # rsaquo
    # "„",  # bdquo

    # For native [[Greek numerals]]
    "&#x0374;",  # : "{{keraia}}",

    # Per https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Abbreviations#Unicode_abbreviation_ligatures

    # https://en.wikipedia.org/wiki/CJK_Compatibility
    "㍘", "㍙", "㍚", "㍛", "㍜", "㍝", "㍞", "㍟", "㍠", "㍡", "㍢", "㍣", "㍤", "㍥", "㍦", "㍧", "㍨", "㍩", "㍪", "㍫", "㍬", "㍭", "㍮", "㍯", "㍰",
    "㏠", "㏡", "㏢", "㏣", "㏤", "㏥", "㏦", "㏧", "㏨", "㏩", "㏪", "㏫", "㏬", "㏭", "㏮", "㏯", "㏰", "㏱", "㏲", "㏳", "㏴", "㏵", "㏶", "㏷", "㏸", "㏹", "㏺", "㏻", "㏼", "㏽", "㏾",

    # https://en.wikipedia.org/wiki/Enclosed_CJK_Letters_and_Months
    "㋀", "㋁", "㋂", "㋃", "㋄", "㋅", "㋆", "㋇", "㋈", "㋉", "㋊", "㋋",

    # https://en.wikipedia.org/wiki/Enclosed_Alphanumeric_Supplement
    "🄋", "🄌",
    "🄐", "🄑", "🄒", "🄓", "🄔", "🄕", "🄖", "🄗", "🄘", "🄙", "🄚", "🄛", "🄜", "🄝", "🄞", "🄟",
    "🄠", "🄡", "🄢", "🄣", "🄤", "🄥", "🄦", "🄧", "🄨", "🄩", "🄪", "🄫", "🄬", "🄭", "🄮", "🄯",
    "🄰", "🄱", "🄲", "🄳", "🄴", "🄵", "🄶", "🄷", "🄸", "🄹", "🄺", "🄻", "🄼", "🄽", "🄾", "🄿",
    "🅀", "🅁", "🅂", "🅃", "🅄", "🅅", "🅆", "🅇", "🅈", "🅉", "🅊", "🅋", "🅌", "🅍", "🅎", "🅏",
    "🅐", "🅑", "🅒", "🅓", "🅔", "🅕", "🅖", "🅗", "🅘", "🅙", "🅚", "🅛", "🅜", "🅝", "🅞", "🅟",
    "🅠", "🅡", "🅢", "🅣", "🅤", "🅥", "🅦", "🅧", "🅨", "🅩",
    "🅰", "🅲", "🅳", "🅴", "🅵", "🅶", "🅷", "🅸", "🅹", "🅺", "🅻", "🅼", "🅽", "🅾", "🅿",
    "🆀", "🆁", "🆂", "🆃", "🆄", "🆅", "🆆", "🆇", "🆈", "🆉", "🆊", "🆋", "🆌", "🆍", "🆎", "🆏",
    "🆐", "🆑", "🆓", "🆔", "🆖", "🆗", "🆘", "🆛", "🆜", "🆝", "🆞", "🆟",
    "🆠", "🆡", "🆢", "🆣", "🆤", "🆥", "🆦", "🆧", "🆨", "🆩", "🆪", "🆫", "🆬",
    # "🆙", "🆒", "🆚", "🆕",  # Used in titles from Twitter and Facebook only
    # "🅱", Used in [[satirical misspelling]]
]

# Ignore these if seen in articles
keep = [
    "&lbrace;",  # {} sometimes needed due to template syntax
    "&rbrace;",  # Or can use Template:( and Template ) which make {}
    "&lsqb;",  # [] needed when adding a link in a quote, rarely
    "&rsqb;",
    "&comma;",  # Template weirdness on [[Nuremburg]]
    "&excl;",   # !! is problematic in some tables
    "&ast;",    # * causes problems sometimes because it's used to mark
                # a list in wiki syntax; usually <nowiki>*</nowiki> works but not always
    "&amp;",    # dangerous for e.g. &amp;126;
    "&num;",    # hash symbol, needed in rare cases for section link in template call
    "&period;",  # When needed to stop template from dropping "." from abbreviations

    # Should be excluded by <source> etc.
    # "&a;",    # Used in computer articles as example of a pointer
    # "&x;",    # Used in computer articles as example of a pointer

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

    # Needed for Malaysian-language citations, makes a
    # difference. Should be tagged {{lang}} but this is not possible
    # inside <ref> tags.
    "&zwj;",

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

    # Per [[MOS:LATINABBR]]
    # These are not allowed, but they show up mostly in quotations
    # where they ARE allowed. So declaring "keep" for the entity
    # report, but let the spell-checker deal with them since it only
    # looks outside quotations.
    "&c.",  # Archaic "etc."
    "&c;",  # Archaic "etc."

    # Replacment character. [[User:Spitzak]] thinks editors may be
    # confused and think that some other character has been replaced.
    "&#xFFFD;",
]

controversial = {
    "&dashv;": "⊣",

    # Objections from User:Jacobolus due to what they think is
    # excessive whitespace added by the template, though Beland thinks
    # it's actually necessary whitespace.
    "′": "{{prime}}",
    "&prime;": "{{prime}}",
    "″": "{{pprime}}",
    "&Prime;": "{{pprime}}",

    # Following objections from User:Headbomb (though they later said
    # substituting for ± was OK) and User:Deacon Vorbis (retired), and
    # User:jacobolus, keep these in articles with <math> markup. In
    # these articles, some editors prefer to be able to search by the
    # TeX name (usually the same as the HTML entity) rather than by
    # the Unicode character.
    "&bigcap;": "⋂",
    "&asymp;": "≈",
    "&empty;": "∅",
    "&emptyset;": "∅",
    "&part;": "∂",
    "&otimes;": "⊗",
    "&exist;": "∃",
    "&equiv;": "≡",
    "&oplus;": "⊕",
    "&CirclePlus;": "⊕",
    "&ne;": "≠",
    "&not;": "¬",
    "&forall;": "∀",
    "&sup;": "⊃",
    "&supe;": "⊇",
    "&sim;": "∼",
    "&isin;": "∈",
    "&fnof;": "ƒ",
    "&infin;": "∞",
    "&lowast;": "∗",  # When used in math, otherwise use ASCII *
    "&int;": "∫",
    "&real;": "ℜ",
    "&sdot;": "⋅",  # Multiplication dot, not to be confused with middot
    "&alefsym;": "ℵ",
    "&weierp;": "℘",
    "&nabla;": "∇",
    "&cong;": "≅",
    "&perp;": "⊥",
    "&notin;": "∉",
    "&sube;": "⊆",
    "&times;": "×",  # not hard to distinguish from "x"
    "&geq;": "≥",
    "&leq;": "≤",
    "&plusmn;": "±",
    "&PlusMinus;": "±",
    "&mnplus;": "∓",
    "&vellip;": "⋮",
    "&ctdot;": "⋯",
    "&dtdot;": "⋱",
    "&sum;": "Σ",  # U+03A3 Greek Capital Letter Sigma
    "&rarr;": "→",
    "&rarrow;": "→",
    "&larr;": "←",
    "&uparrow;": "↑",
    "&swarr;": "↙",
    "&varr;": "↕",
    "&map;": "↦",
    "&le;": "≤",  # available at the bottom of the wikitext edit window
    "&ge;": "≥",  # available at the bottom of the wikitext edit window
    "&GreaterEqual;": "≥",  # available at the bottom of the wikitext edit window
    "&setminus;": "∖",
    "&approx;": "≈",
    "&vdash;": "⊢",
    "&bottom;": "⊥",
    "&propto;": "∝",
    "&nvap;": "≍⃒",
    "&NotEqual;": "≠",
    "&aleph;": "ℵ",
    "&beth;": "ℶ",
    "&parallel;": "∥",
    "&darr;": "↓",  # {{down-arrow}} is also available
    "&uarr;": "↑",  # {{up-arrow}} is also available
    "&pm;": "±",
    "&therefore;": "∴",
    "&in;": "∈",
    "&epsi;": "ε",
    "&thickapprox;": "≈",
    "&prop;": "∝",
    "&subsetneq;": "⊊",
    "&cir;": "○",
    "&compfn;": "∘",
    "&rightleftharpoons;": "⇌",
    "&subseteq;": "⊆",
    "&rceil;": "⌉",
    "&lceil;": "⌈",
    "&rfloor;": "⌋",
    "&lfloor;": "⌊",
    "&hArr;": "⇔",
    "&rArr;": "⇒",
    "&lArr;": "⇐",
    "&harr;": "↔",
    "&uArr;": "⇑",
    "&crarr;": "↵",
    "&Lt;": "≪",
    "&Gt;": "≫",
    "&GT;": "&gt;",
    "&vDash;": "⊨",
    "&nvDash;": "⊭",
    "&odot;": "⊙",
    "&ll;": "≪",
    "&gg;": "≫",
    "&marker;": "▮",
    "&langle;": "⟨",
    "&rangle;": "⟩",
    "&pre;": "⪯",
    "&mid;": "{{pipe}}",
    "&afr;": "𝔞",
    "&top;": "⊤",
    "&bot;": "⊥",
    "&upharpoonright;": "↾",
    "&lrarr;": "⇆",
    "&preceq;": "(⪯)",
    "&cfr;": "𝔠",
    "&angzarr;": "⍼",
    "&hbar;": "ℏ",
    "ϕ": "φ",  # Phi conversion from U+03D5 phi symbol to lowercase phi U+03C6
    "&NestedGreaterGreater;": "≫",
    "&NestedLessLess;": "≪",
    "&SubsetEqual;": "⊆",
}

# keep.extend(controversial.keys())

transform_unsafe = {
    # These transformations can't be made in places where the
    # character itself is being discussed, or are just rules of thumb
    # based on observed misuse.

    # "ʾ": "{{hamza}}",
    "ʾ": "'",
    # U+02BE Modifier Letter Right Half Ring to ASCII
    #
    # ASCII apostrophe is used in Hebrew transliterations by default, per
    # [[Wikipedia:Naming conventions (Hebrew)]] which uses the Hebrew Academy scheme at
    # [[Romanization_of_Hebrew#Table]]
    # Hebrew letter [[yodh]] can be left as raw U+05D9 since it should
    # be clear from context it's not an apostrophe
    #
    # For Arabic, basic transliteration with apostrophe is used in
    # most cases per [[Wikipedia:Manual of Style/Arabic]], {{hamza}}
    # is used in strict transliteration for linguistics (should be
    # inside {{transliteration}}) unless there is a common
    # transliteration.  See also [[MOS:APOSTROPHE]].

    # "ʿ": "{{ayin}}",
    "ʿ": "'",
    # U+02BF Modifier letter left half ring to ASCII
    # Use apostrophe for basic transliteration (most cases) per
    # [[Wikipedia:Manual of Style/Arabic]], and {{ayin}} in strict
    # transliteration, inside {{transliteration}} unless there is a
    # common transliteration. See also [[MOS:APOSTROPHE]].

    # Per [[MOS:MATHSPECIAL]]; may need to convert the remainder of
    # the expression
    "∘": r"<math>\circ</math>",
    "○": r"<math>\circ</math>",

    # Per [[MOS:CURRENCY]] should be £ for pound currencies (GBP, AUP,
    # NZP, etc.)  CAUTION: Keep ₤ or lira and link, e.g.: [[Italian lira|₤]]
    "₤": "£",
    "￡": "£",  # U+FFE1 (full width) to U+00A3

    "&s;": "'",

    # "&#91;": "&lsqb;",   # [  {{!(}} will also work
    # "&#93;": "&rsqb;",   # ]  {{)!}} will also work
    # "&#091;": "&lsqb;",
    # "&#093;": "&rsqb;",
    # "&#0091;": "&lsqb;",
    # "&#0093;": "&rsqb;",
    # "&#00091;": "&lsqb;",
    # "&#00093;": "&rsqb;",
    # "&00091;": "&lsqb;",
    # "&00093;": "&rsqb;",
    # "&lbrack;": "&lsqb;",  # [
    # "&rbrack;": "&rsqb;",  # ]
    # "&#093;": "&rsqb;",  # ]
    # "&#0093;": "&rsqb;",  # ]
    # "&#91;": "&lsqb;",
    # "&#93;": "&rsqb;",
    # "&#x005B;": "&lsqb;",
    # "&#x005D;": "&rsqb;",
    # "&#x5b;": "&lsqb;",
    # "&#x5d;": "&rsqb;",
    "&#x5B;": "%5B",  # Usually in URLs; otherwise, "&lsqb;",
    "&#x5D;": "%5D",  # Usually in URLs; otherwise, "&rsqb;",

    # Usually not needed; especially after converting [] links to
    # {{cite web}}, but substitute &lsqb; and &rsqb; if absolutely
    # necessary.
    "&#91;": "[",
    "&#93;": "]",
    "&#091;": "[",
    "&#093;": "]",
    "&#0091;": "[",
    "&#0093;": "]",
    "&#00091;": "[",
    "&#00093;": "]",
    "&00091;": "[",
    "&00093;": "]",
    "&lbrack;": "[",
    "&rbrack;": "]",
    "&#093;": "]",
    "&#0093;": "]",
    "&#91;": "[",
    "&#93;": "]",
    "&#x005B;": "[",
    "&#x005D;": "]",
    "&#x5b;": "[",
    "&#x5d;": "]",

    "&lpar;": "(",
    "&rpar;": ")",

    "&#145;": "'",
    "&commat;": "@",

    "&equals;": "=",  # Can mess up wikitext
    "&lowbar;": "_",  # Sometimes needed in links to avoid AWB, etc. auto-deleting

    # Might want to be wiki-list syntax
    "&bull;": "•",

    # [[MOS:RADICAL]]
    "&radic;": "√",  # May need to use <math>\sqrt{}</math>
    "∛": r"<math>\sqrt[3]{}</math>",

    # Non-compliant and incorrect uses of superscript o and similar characters
    "n<sup>o<sup>": "no.",
    "N<sup>o<sup>": "No.",
    "⁰ C": "°C",
    "⁰C": "°C",
    "<sup>o<sup>C": "°C",
    "<sup>o<sup> C": "°C",
    "⁰ F": "°F",
    "⁰F": "°F",
    "<sup>o<sup>F": "°F",
    "<sup>o<sup> F": "°F",
    "ºF": "°F",
    "ºC": "°C",

    # Per [[MOS:UNITSYMBOLS]]
    "° C": "°C",
    "° F": "°F",
    "F°": "°F",
    "C°": "°C",
    "°K": "K",

    # Some of the below might be ordinal indicators for Romance
    # languages, in which case they should use "º" per [[MOS:ORDINAL]]
    "0<sup>o<sup>C": "0°",
    "1<sup>o<sup>C": "1°",
    "2<sup>o<sup>C": "2°",
    "3<sup>o<sup>C": "3°",
    "4<sup>o<sup>C": "4°",
    "5<sup>o<sup>C": "5°",
    "6<sup>o<sup>C": "6°",
    "7<sup>o<sup>C": "7°",
    "8<sup>o<sup>C": "8°",
    "9<sup>o<sup>C": "9°",

    "&#x20;": "%20",  # Usually, but not always. Sometimes this should just be a regular space.
    "&#8239;": "&nbsp;",    # narrow no-break space
    "&#32;": "{{sp}}",  # When used with {{linktext}} but otherwise should just be a regular space.

    # Probably convert to regular space or no space
    "&ensp;": " ",  # Or {{sp}} if a regular space is needed
    "&emsp;": " ",  # Or {{sp}} if a regular space is needed

    "&thnsp;": "&thinsp;",
    "&thisp;": "&thinsp;",
    "&thnisp;": "&thinsp;",
    "&thisnp;": "&thinsp;",

    "&ThinSpace;": " ",
    "&thinsp;": " ",  # Use "{{thin space}}" if retained
    "&thinspace;": " ",
    "&hairsp;": "",   # Use "{{hair space}}" if retained
    "&emsp13;": " ",
    "&emsp14;": " ",
    "&numsp;": "{{figure space}}",
    "&puncsp;": " ",
    "&MediumSpace;": " ",

    # --- MATH STANDARDIZATION
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Mathematics#Special_symbols

    # (should be μ (&mu;) per [[MOS:NUM#Specific units]]
    "µ": "μ",  # micro to mu
    "&micro;": "μ",  # micro to mu

    "∑": "Σ",  # U+2211 N-Ary Summation to Sigma
    "∏": "Π",  # U+220F N-Ary Product to Pi

    "ϑ": "θ",  # U+03D1 Greek Theta Symbol to U+03B8 Green Small Letter Theta
    "∼": "~",  # U+223C Tilde Operator to ASCII U+007E Tilde
               # Should be ≈ for approximation per [[MOS:MATHSPECIAL]]
    "∕": "/",  # U+2215 Division Slash to ASCII U+002F Solidus
    "∖": "\\",  # U+2216 Set Minus
    "∶": ":",   # U+2236 Ratio to ASCII U+003A Colon
    "&ratio;": ":",

    # Ohm to Omega
    "&ohm;": "Ω",
    "Ω": "Ω",

    # ---

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
    "&numero;": "No.",

    # &#x2011; should be kept if it is at the beginning or end of a
    # word, so the hyphen doesn't break onto a new line (due to bug in
    # Chrome, reported 27 Jul 2019 - see
    # https://en.wikipedia.org/wiki/Talk:B%C3%B6rje#Hyphens_and_linebreaks)
    "&#8209;": "-",   # U+2011 Non-breaking hyphen to ASCII
    "&#x2011;": "-",   # U+2011 Non-breaking hyphen to ASCII

    # Per [[MOS:FRAC]]; note important exceptions there!
    "¼": "{{frac|1|4}}",
    "½": "{{frac|1|2}}",
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
    "&frac13;": "{{frac|1|3}}",
    "&frac14;": "{{frac|1|4}}",
    "&frac15;": "{{frac|1|5}}",
    "&frac16;": "{{frac|1|6}}",
    "&frac18;": "{{frac|1|8}}",
    "&frac23;": "{{frac|2|3}}",
    "&frac25;": "{{frac|2|5}}",
    "&frac34;": "{{frac|3|4}}",
    "&frac38;": "{{frac|3|8}}",
    "&frac45;": "{{frac|4|5}}",
    "&frac56;": "{{frac|5|6}}",
    "&frac58;": "{{frac|5|8}}",
    "&frac78;": "{{frac|7|8}}",
    "&#8531;": "{{frac|1|3}}",

    "&sol;": "/",

    # [[MOS:1ST]]
    "ˢᵗ": "st",
    "ⁿᵈ": "nd",
    "ʳᵈ": "rd",
    "ᵗʰ": "th",

    "…": "...",
    "&#8230;": "...",
    "&hellip;": "...",
    "&mldr;": "...",

    # "&#123;": "&lbrace;",  # {
    # "&lcub;": "&lbrace;",  # {
    # "&#125;": "&rbrace;",  # }
    # "&rcub;": "&rbrace;",  # }
    "&#123;": "{",
    "&lcub;": "{",
    "&#125;": "}",
    "&rcub;": "}",

    # This is a pipe, and usually happens in URL titles
    "&#124;": "{{pipe}}",
    "&VerticalLine;": "{{pipe}}",
    "&verbar;": "{{pipe}}",
    "&vert;": "{{pipe}}",
    "&pipe;": "{{pipe}}",
    # {{!}} in tables?
    # https://www.mediawiki.org/wiki/Help:Magic_words#Other

    "&Vert;": "‖",
    "&Verbar;": "‖",
    "&squ;": "□",

    # These are usually spurious, per [[MOS:TMRULES]]
    "&trade;": "",  # ™
    "&reg;": "",  # ®
    "&circledR;": "",  # ®
    "&COPY;": "&copy;",  # ©
    "&copy;": "",  # ©
    "&copysr;": "℗",
    "™": "",
    "℠": "",
    "®": "",
    "©": "",
    "&8482;": "",   # ™

    # Normalizing quote marks
    '‘’': '"',
    "``": '"',
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
    "&#39;'": '"',
    "'&#39;": '"',
    "&#039;": "'",
    "&#039 ": "' ",
    "&#96;": "'",
    "&#8220;": '"',  # “ -> "
    "&#8221;": '"',  # ” -> "
    "&#8216;": "'",   # ‘ -> '
    "&#x2018;": "'",   # ’ -> '
    "&#8217;": "'",   # ’ -> '
    "&#x2019;": "'",   # ’ -> '
    "&#x201C;": '"',
    "&#x201D;": '"',
    "&#146;": "'",  # mojibake

    # See "controversial" section for the named entities.
    "&#8242;": "{{prime}}",
    "&#x2032;": "{{prime}}",
    "&#8243;": "{{pprime}}",
    "&#x2033;": "{{pprime}}",
    "&x2034": "{{pprime}}",

    # These are OK to transform, but must be in a {{lang}} or {{transl}} tag
    "&#700;": "ʼ",
    "&#702;": "ʾ",
    "&#703;": "ʿ",
    "&#x02BD;": "ʽ",
    "&#x2bb;": "ʻ",

    # ʻOkina is U+02BB, and should be used in Polynesian languages
    # only, not as an apostrophe.
    "ʻ": "{{okina}}",
    # Use {{asper}} not {{okina}} for Wade-Giles transliteration of
    # Chinese, per:
    # https://en.wikipedia.org/wiki/Talk:Wade%E2%80%93Giles#%CA%BB_or_%60_???

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
    "&lsaquo;": "‹",
    "&rsaquo;": "›",

    # https://en.wikipedia.org/wiki/Zero-width_non-joiner Used in
    # German, Arabic, Hebrew, etc.  Sometimes abused to fix wikitext
    # markup issues, but would require manual review to determine
    # that.  Ignore inside {{lang}}.
    "&zwnj;": "",

    # Usually just not needed
    "&ZeroWidthSpace;": "",
    "&NoBreak;": "",

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

    # TODO: Activate these and see what happens
    # Small caps for [[MOS:SMALLCAPS]]

    # "ᴀ": "A",
    # "ʙ": "B",
    # "ᴄ": "C",
    # "ᴅ": "D",
    # "ᴇ": "E",
    # "ꜰ": "F",
    # "ɢ": "G",
    # "ʜ": "H",
    # "ɪ": "I",
    # "ᴊ": "J",
    # "ᴋ": "K",
    # "ʟ": "L",
    # "ᴍ": "M",
    # "ɴ": "N",
    # "ᴏ": "O",
    # "ᴘ": "P",
    # "ꞯ": "Q",
    # "ʀ": "R",
    # "ꜱ": "S",
    # "ᴛ": "T",
    # "ᴜ": "U",
    # "ᴠ": "V",
    # "ᴡ": "W",
    # "ʏ": "Y",
    # "ᴢ": "Z",
    # "ᴁ": "Æ",
    # "ᴃ": "Ƀ",
    # "ᴆ": "Ð",
    # "ᴣ": "Ʒ",
    # "ⱻ": "Ǝ",
    # "ʛ": "Ɠ",
    # "ᵻ": "Ɨ",
    # "ᴌ": "Ł",
    # "ꟺ": ꟽ/Ɯ  (?)
    # "ɶ": "Œ",
    # "ᴐ": "Ɔ",
    # "ᴕ": "Ȣ",
    # "ꝶ": "ꝵ",
    # "ᵾ": "Ʉ",
    # "ᴦ": "Γ",
    # "ᴧ": "Λ",
    # "ᴨ": "Π",
    # "ᴩ": "Ρ",
    # "ᴪ": "Ψ",
    # "ꭥ": "Ω",

    # SMALL CAPS SUPERSCRIPT:
    # ᶦ ᶧ ᶫ ᶰ ʶ ᶸ

    # [[MOS:BBB]]
    "𝔸": r"<math>\mathbb{A}</math>",
    "𝔹": r"<math>\mathbb{B}</math>",
    "ℂ": r"<math>\mathbb{C}</math>",
    "𝔻": r"<math>\mathbb{D}</math>",
    "𝔼": r"<math>\mathbb{E}</math>",
    "𝔽": r"<math>\mathbb{F}</math>",
    "𝔾": r"<math>\mathbb{G}</math>",
    "ℍ": r"<math>\mathbb{H}</math>",
    "𝕀": r"<math>\mathbb{I}</math>",
    "𝕁": r"<math>\mathbb{J}</math>",
    "𝕂": r"<math>\mathbb{K}</math>",
    "𝕃": r"<math>\mathbb{L}</math>",
    "𝕄": r"<math>\mathbb{M}</math>",
    "ℕ": r"<math>\mathbb{N}</math>",
    "𝕆": r"<math>\mathbb{O}</math>",
    "ℙ": r"<math>\mathbb{P}</math>",
    "ℚ": r"<math>\mathbb{Q}</math>",
    "ℝ": r"<math>\mathbb{R}</math>",
    "𝕊": r"<math>\mathbb{S}</math>",
    "𝕋": r"<math>\mathbb{T}</math>",
    "𝕌": r"<math>\mathbb{U}</math>",
    "𝕍": r"<math>\mathbb{V}</math>",
    "𝕎": r"<math>\mathbb{W}</math>",
    "𝕏": r"X",  # Because Twitter
    "𝕐": r"<math>\mathbb{Y}</math>",
    "ℤ": r"<math>\mathbb{Z}</math>",
    "&Zopf;": r"<math>\mathbb{Z}</math>",
    "𝕒": r"<math>\mathbb{a}</math>",
    "𝕓": r"<math>\mathbb{b}</math>",
    "𝕔": r"<math>\mathbb{c}</math>",
    "𝕕": r"<math>\mathbb{d}</math>",
    "𝕖": r"<math>\mathbb{e}</math>",
    "𝕗": r"<math>\mathbb{f}</math>",
    "𝕘": r"<math>\mathbb{g}</math>",
    "𝕙": r"<math>\mathbb{h}</math>",
    "𝕚": r"<math>\mathbb{i}</math>",
    "𝕛": r"<math>\mathbb{j}</math>",
    "𝕜": r"<math>\mathbb{k}</math>",
    "𝕝": r"<math>\mathbb{l}</math>",
    "𝕞": r"<math>\mathbb{m}</math>",
    "𝕟": r"<math>\mathbb{n}</math>",
    "𝕠": r"<math>\mathbb{o}</math>",
    "𝕡": r"<math>\mathbb{p}</math>",
    "𝕢": r"<math>\mathbb{q}</math>",
    "𝕣": r"<math>\mathbb{r}</math>",
    "𝕤": r"<math>\mathbb{s}</math>",
    "𝕥": r"<math>\mathbb{t}</math>",
    "𝕦": r"<math>\mathbb{u}</math>",
    "𝕧": r"<math>\mathbb{v}</math>",
    "𝕨": r"<math>\mathbb{w}</math>",
    "𝕩": r"<math>\mathbb{x}</math>",
    "𝕪": r"<math>\mathbb{y}</math>",
    "𝕫": r"<math>\mathbb{z}</math>",
    "ℾ": r"<math>\mathbb{\Gamma}</math>",
    "ℽ": r"<math>\mathbb{\gamma}</math>",
    "ℿ": r"<math>\mathbb{\Pi}</math>",
    "ℼ": r"<math>\mathbb{\pi}</math>",
    "⅀": r"<math>\mathbb{\Sigma}</math>",
    "𝟘": r"<math>\mathbb{0}</math>",
    "𝟙": r"<math>\mathbb{1}</math>",
    "𝟚": r"<math>\mathbb{2}</math>",
    "𝟛": r"<math>\mathbb{3}</math>",
    "𝟜": r"<math>\mathbb{4}</math>",
    "𝟝": r"<math>\mathbb{5}</math>",
    "𝟞": r"<math>\mathbb{6}</math>",
    "𝟟": r"<math>\mathbb{7}</math>",
    "𝟠": r"<math>\mathbb{8}</math>",
    "𝟡": r"<math>\mathbb{9}</math>",
    "&rationals;": r"<math>\mathbb{Q}</math>",
    "&integers;": r"<math>\mathbb{Z}</math>",
    "&reals;": r"<math>\mathbb{R}</math>",
    "&Ropf;": r"<math>\mathbb{R}</math>",
    "&Popf;": r"<math>\mathbb{P}</math>",
    "&Kopf;": r"<math>\mathbb{K}</math>",
    "&Copf;": r"<math>\mathbb{C}</math>",
    "&complexes;": r"<math>\mathbb{C}</math>",

    "&#x0261;": "g",  # g for gravity distinguished from g for gram

    # Below sections per:
    # https://en.wikipedia.org/wiki/Wikipedia:Manual_of_Style/Abbreviations#Unicode_abbreviation_ligatures
    # Explicitly excluded:
    # "₨": "Rs",

    # https://en.wikipedia.org/wiki/Unicode_compatibility_characters#Semantically_distinct_characters
    # "ℵ": "א",  # From U+2135  Used in math without the RTL direction, probably OK
    "ℶ": "ב",  # From U+2136
    "ℷ": "ג",  # From U+2137
    "ℸ": "ד‎",  # From U+2138
    "ϐ": "β",  # From U+03D0
    # "ϖ": "π", # U+03D6 seems to be used legitimately, visually
    #           distinct, this looks like a combined omega + pi,
    #           and matches the presentation in some TeX used in articles.
    "ϰ": "κ",  # From U+03F0
    "ϱ": "ρ",  # From U+03F1
    "ϴ": "Θ",  # From U+03F4
    "ℇ": "ε",  # From U+2107 Euler constant
    # "․": ".",  # From U+2024 - Armenian center-of-line period - retain
    "ℹ": "i",  # From U+2139

    # Unclear these are substitutable directly:
    #  lunate epsilon (ϵ U+03F5)
    #  lunate sigma (ϲ U+03F2)
    #  capital lunate sigma (Ϲ U+03F9)
    #  upsilon with hook (ϒ U+03D2)
    #  Planck constant (ℎ U+210E)
    #  reduced Planck constant (ℏ U+210F)

    # https://en.wikipedia.org/wiki/CJK_Compatibility
    "㍱": "hPa",
    "㍲": "da",
    "㍳": "AU",
    "㍴": "bar",
    "㍵": "oV",
    "㍶": "pc",
    "㍷": "dm",
    "㍸": "dm<sup>2</sup>",
    "㍹": "dm<sup>3</sup>",
    "㍺": "IU",
    "㎀": "pA",
    "㎁": "nA",
    "㎂": "μA",
    "㎃": "mA",
    "㎄": "kA",
    "㎅": "KB",
    "㎆": "MB",
    "㎇": "GB",
    "㎈": "cal",
    "㎉": "kcal",
    "㎊": "pF",
    "㎋": "nF",
    "㎌": "μF",
    "㎍": "μg",
    "㎎": "mg",
    "㎏": "kg",
    "㎐": "Hz",
    "㎑": "kHz",
    "㎒": "MHz",
    "㎓": "GHz",
    "㎔": "THz",
    "㎕": "uL",
    "㎖": "mL",
    "㎗": "dL",
    "㎘": "kL",
    "㎙": "fm",
    "㎚": "nm",
    "㎛": "μm",
    "㎜": "mm",
    "㎝": "cm",
    "㎞": "km",
    "㎟": "mm<sup>2</sup>",
    "㎠": "cm<sup>2</sup>",
    "㎡": "m<sup>2</sup>",
    "㎢": "km<sup>2</sup>",
    "㎣": "mm<sup>3</sup>",
    "㎤": "cm<sup>3</sup>",
    "㎥": "m<sup>3</sup>",
    "㎦": "km<sup>3</sup>",
    "㎧": "m/s",
    "㎨": "{{frac|m|s<sup>2</sup>}}",
    "㎩": "Pa",
    "㎪": "kPa",
    "㎫": "MPa",
    "㎬": "GPa",
    "㎭": "rad",
    "㎮": "rad/s",
    "㎯": "{{frac|rad|s<sup>2</sup>}}",
    "㎰": "ps",
    "㎱": "ns",
    "㎲": "μs",
    "㎳": "ms",
    "㎴": "pV",
    "㎵": "nV",
    "㎶": "μV",
    "㎷": "mV",
    "㎸": "kV",
    "㎹": "MV",
    "㎺": "pW",
    "㎻": "nW",
    "㎼": "μW",
    "㎽": "mW",
    "㎾": "kW",
    "㎿": "MW",
    "㏀": "kΩ",
    "㏁": "MΩ",
    "㏂": "am",
    "㏃": "Bq",
    "㏄": "cc",
    "㏅": "cd",
    "㏆": "C/kg",
    "㏇": "Co.",
    "㏈": "dB",
    "㏉": "Gy",
    "㏊": "ha",
    "㏋": "HP",
    "㏌": "in",
    "㏍": "KK",
    "㏎": "KM",
    "㏏": "kt",
    "㏐": "lm",
    "㏑": "ln",
    "㏒": "log",
    "㏓": "lx",
    "㏔": "mb",
    "㏕": "mil",
    "㏖": "mol",
    "㏗": "pH",
    "㏘": "pm",
    "㏙": "ppm",
    "㏚": "PR",
    "㏛": "sr",
    "㏜": "Sv",
    "㏝": "Wb",
    "㏞": "V/m",
    "㏟": "A/m",
    "㏿": "gal",

    # https://en.wikipedia.org/wiki/Enclosed_CJK_Letters_and_Months
    "㋌": "Hg",
    "㋍": "erg",
    "㋎": "eV",
    "㋏": "LTD",

    # https://en.wikipedia.org/wiki/Enclosed_Alphanumeric_Supplement
    "🄀": "0.",
    "🄁": "0,",
    "🄂": "1,",
    "🄃": "2,",
    "🄄": "3,",
    "🄅": "4,",
    "🄆": "5,",
    "🄇": "6,",
    "🄈": "7,",
    "🄉": "8,",
    "🄊": "9,",
    "🅪": "MC",
    "🅫": "MD",
    "🅬": "MR",

    # https://en.wikipedia.org/wiki/Letterlike_Symbols
    "℀": "a/c",  # Account of
    "℁": "a/s",  # Addressed to the subject
    "℃": "°C",
    "℅": "c/o",  # Care of
    "℆": "c/u",  # Cada una ("each")
    "℉": "°F",
    "№": "No.",
    "℞": "Rx",
    "℡": "Tel",
    "Ω": "Ω",
    "K": "K",
    "Å": "Å",
    "℻": "Fax",
    "⅍": "A/S",

    # https://en.wikipedia.org/wiki/Wikipedia:AutoWikiBrowser/Typos
    "㉐": "PTE",

    # See similar list in spell.py!
    # [[MOS:LIGATURE]], list adapted from
    # https://en.wikipedia.org/wiki/Ligature_(writing)
    "Ꜳ": "AA",
    "ꜳ": "aa",
    "Ꜵ": "AO",
    "ꜵ": "ao",
    "Ꜷ": "AU",
    "ꜷ": "au",
    "Ꜹ": "AV",
    "ꜹ": "av",
    "🙰": "et",
    "ﬀ": "ff",
    "ﬃ": "ffi",
    "ﬄ": "ffl",
    "ﬁ": "fi",
    "ﬂ": "fl",
    "Ƕ": "Hv",
    "ƕ": "hv",
    "℔": "lb",
    "Ỻ": "lL",
    "ỻ": "ll",
    "Ꝏ": "OO",
    "ꝏ": "oo",
    "ﬆ": "st",
    "Ꜩ": "Tz",
    "ꜩ": "tz",
    "ᵫ": "ue",
    "ꭣ": "uo",
    "Ꝡ": "VY",
    "ꝡ": "vy",

    # These are extremely common in standard French and Scandanavian
    # languages, where they are allowed by [[MOS:LIGATURE]] because
    # they are considered standard spellings.
    # "Æ": "AE",
    # "Œ": "OE",
    # "æ": "ae",
    # "œ": "oe",

    # ---

    # https://en.wikipedia.org/wiki/Halfwidth_and_Fullwidth_Forms_(Unicode_block)
    # No objections from:
    # https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_China/Archive_31#Conversion_of_full-width_Latin_letters_and_Arabic_numbers
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Manual_of_Style/Japan-related_articles/Archive_28#Conversion_of_full-width_Latin_letters_and_Arabic_numbers
    # https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Korea/Archive_21#Conversion_of_full-width_Latin_letters_and_Arabic_numbers
    "０": "0",
    "１": "1",
    "２": "2",
    "３": "3",
    "４": "4",
    "５": "5",
    "６": "6",
    "７": "7",
    "８": "8",
    "９": "9",
    "Ａ": "A",
    "Ｂ": "B",
    "Ｃ": "C",
    "Ｄ": "D",
    "Ｅ": "E",
    "Ｆ": "F",
    "Ｇ": "G",
    "Ｈ": "H",
    "Ｉ": "I",
    "Ｊ": "J",
    "Ｋ": "K",
    "Ｌ": "L",
    "Ｍ": "M",
    "Ｎ": "N",
    "Ｏ": "O",
    "Ｐ": "P",
    "Ｑ": "Q",
    "Ｒ": "R",
    "Ｓ": "S",
    "Ｔ": "T",
    "Ｕ": "U",
    "Ｖ": "V",
    "Ｗ": "W",
    "Ｘ": "X",
    "Ｙ": "Y",
    "Ｚ": "Z",
    "ａ": "a",
    "ｂ": "b",
    "ｃ": "c",
    "ｄ": "d",
    "ｅ": "e",
    "ｆ": "f",
    "ｇ": "g",
    "ｈ": "h",
    "ｉ": "i",
    "ｊ": "j",
    "ｋ": "k",
    "ｌ": "l",
    "ｍ": "m",
    "ｎ": "n",
    "ｏ": "o",
    "ｐ": "p",
    "ｑ": "q",
    "ｒ": "r",
    "ｓ": "s",
    "ｔ": "t",
    "ｕ": "u",
    "ｖ": "v",
    "ｗ": "w",
    "ｘ": "x",
    "ｙ": "y",
    "ｚ": "z",


    # Asked about these at:
    # https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_China#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Manual_of_Style/Korea-related_articles/Archive_3#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Japan/Archive/July_2024#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Manual_of_Style/China-_and_Chinese-related_articles/Archive_8#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_Korea/Archive_24#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # https://en.wikipedia.org/wiki/Wikipedia_talk:Manual_of_Style/Japan-related_articles/Archive_29#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # and updated:
    #  [[Wikipedia:Manual of Style/China- and Chinese-related articles]]
    #  [[Wikipedia:Manual of Style/Korea-related articles]]
    #  [[Wikipedia:Manual of Style/Japan-related articles]]

    "＂": '"',
    "＃": "#",
    "＄": "$",
    "％": "%",
    "＆": "&",
    "＇": "'",
    "＋": "+",
    "／": "/",
    "＠": "@",
    "＼": "\\",
    "＾": "^",
    "＿": "_",  # U+FF3F full-width underscore
    "｀": "`",
    "￠": "¢",
    "￥": "¥",
    "￦": "₩",
    "＝": "=",
    "｜": "{{pipe}}",
    "￤": "¦",
    "　": " ",  # U+3000 full-width space

    # Todo: Find these when not in CJK text
    # Comments from Dekimasu on
    # https://en.wikipedia.org/w/index.php?title=Wikipedia_talk%3AWikiProject_Japan#Converting_full-width_punctuation_and_currency_symbols_in_horizontal_text
    # "＊": "*",  # "often equivalent to a bullet point rather than an asterisk"
    # "＜": "<",  # "often used to denote parts of titles or quotations and in these cases are not equivalent to < and >"
    # "＞": ">",  # "(ditto)"
    # "－": "-",  # "no problem if the characters are really intending minuses rather than dashes"

    # Ignoring for now:
    # ￣
    # Half-width:
    # "｡": "。",
    # "｢": "「",
    # "｣": "」",
    # "￨": "{{pipe}}",
    # ￩ ￪ ￫ ￬ ￭ ￮
    # ､ ･ ｦ ｧ ｨ ｩ ｪ ｫ ｬ ｭ ｮ ｯ
    # ｰ ｱ ｲ ｳ ｴ ｵ ｶ ｷ ｸ ｹ ｺ ｻ ｼ ｽ ｾ ｿ
    # ﾀ ﾁ ﾂ ﾃ ﾄ ﾅ ﾆ ﾇ ﾈ ﾉ ﾊ ﾋ ﾌ ﾍ ﾎ ﾏ
    # ﾐ ﾑ ﾒ ﾓ ﾔ ﾕ ﾖ ﾗ ﾘ ﾙ ﾚ ﾛ ﾜ ﾝ ﾞ ﾟ
    # https://en.wikipedia.org/wiki/Half-width_kana

    "{{reflist|2}}": "<references />",
    "{{reflist|3}}": "<references />",
}

transform_conditional = {
    # Need to be retained in e.g. Chinese text per https://en.wikipedia.org/wiki/Chinese_punctuation#Marks_similar_to_European_punctuation
    # but should be transformed in e.g. English text
    "！": "!",
    "（": "(",
    "）": ")",
    "，": ",",
    "．": ".",
    "：": ":",
    "；": ";",
    "？": "?",
    "［ ": "[",
    "］": "]",

    "～": "~",
    # ASCII preferred in Korean per
    # https://en.wikipedia.org/wiki/Korean_punctuation
    # Should be ≈ for # approximation per [[MOS:MATHSPECIAL]]

    # Per https://en.wikipedia.org/wiki/Wikipedia_talk:WikiProject_China/Archive_31#Conversion_of_full-width_Latin_letters_and_Arabic_numbers
    "｛": "{",
    "｝": "}",
    "｟": "⸨",
    "｠": "⸩",
}


# Automatically change, with the expectation there will be a
# manual inspection of the diff
transform = {
    "&lcub;": "&lbrace;",
    "&rcub;": "&rbrace;",
    "&flat;": "♭",
    "&sharp;": "♯",
    "&rlhar;": "⇌",
    "&ap;": "&approx;",
    "&ell;": "ℓ",
    "&Rarr;": "↠",
    "&star;": "☆",
    "&starf;": "★",
    "&digamma;": "ϝ",
    "&varepsilon;": "ϵ",
    "&bigcup;": "⋃",
    "&models;": "⊧",
    "&iexcl;": "¡",
    "&DoubleLongRightArrow;": "⟹",
    "&rightarrow;": "→",
    "&mapsto;": "↦",
    "&Lscr;": "ℒ",
    "&LowerLeftArrow;": "↙",
    "&LowerRightArrow;": "↘",
    "&shortmid;": "{{pipe}}",
    "&hearts;": "♥",
    "&Sqrt;": "√",
    "&tilde;": "~",
    "&Rang;": "⟫",
    "&Lang;": "⟪",

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
    "&#x200B;": "&ZeroWidthSpace;",
    "&#x200b;": "&ZeroWidthSpace;",
    "&#8203;": "&ZeroWidthSpace;",
    "&#x200C;": "&zwnj;",
    "&#8204;": "&zwnj;",
    "&#x200D;": "&zwj;",
    "&#8205;": "&zwj;",
    "&#x2060;": "&NoBreak;",
    "&#8288;": "&NoBreak;",
    "&#xFEFF;": "",
    "&#65279;": "",

    "&#8206;": "&lrm;",

    "&#x7C;": "{{pipe}}",  # |
    "&#x7c;": "{{pipe}}",  # |
    "&#x007C;": "{{pipe}}",  # |
    "&#0124;": "{{pipe}}",  # |
    "&#x3C;": "&lt;",
    "&#x003C;": "&lt;",
    "&#x3E;": "&gt;",
    "&#x003E;": "&gt;",
    "&#60;": "&lt;",
    "&#060;": "&lt;",
    "&#0060;": "&lt;",
    "&#61;": "=",  # OK for URLs, but in other places use the below:
    # "&#61;": "<nowiki>=</nowiki>",  # Will break markup inside templates
    "&#061;": "<nowiki>=</nowiki>",  # Will break markup inside templates
    "&#0061;": "<nowiki>=</nowiki>",  # Will break markup inside templates
    "&#62;": "&gt;",
    "&#062;": "&gt;",
    "&#0062;": "&gt;",

    "&gtdot;": "⋗",
    "&ltdot;": "⋖",
    "&esdot;": "≐",
    "&bullet;": "•",
    "&hyphen;": "-",

    # Raw non-breaking space
    "\xA0": "&nbsp;",

    "&#160;": "&nbsp;",
    "&#xA0;": "&nbsp;",
    "&#xa0;": "&nbsp;",
    "&#x0A0;": "&nbsp;",
    "&#x00A0;": "&nbsp;",

    "&#x9;": "&Tab;",
    "&#9;": "&Tab;",
    "&#09;": "&Tab;",
    "&#x09;": "&Tab;",
    "&#x0009;": "&Tab;",
    "&tab;": "&Tab;",

    "&permil;": "‰",

    # [[MOS:SUPERSCRIPT]]

    "&sup1;": "<sup>1</sup>",
    "&sup2;": "<sup>2</sup>",
    "&sup3;": "<sup>3</sup>",

    "⅟": "{{frac|1|",     # [[Number Forms]]
    "↉": "{{frac|0|3}}",  # [[Number Forms]]

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

    "ᵃ": "<sup>a</sup>",
    "ᵇ": "<sup>b</sup>",
    "ᶜ": "<sup>c</sup>",
    "ᵈ": "<sup>d</sup>",
    "ᵉ": "<sup>e</sup>",
    "ᶠ": "<sup>f</sup>",
    "ᵍ": "<sup>g</sup>",
    "ʰ": "<sup>h</sup>",
    "ⁱ": "<sup>i</sup>",
    "ʲ": "<sup>j</sup>",
    "ᵏ": "<sup>k</sup>",
    "ˡ": "<sup>l</sup>",
    "ᵐ": "<sup>m</sup>",
    "ⁿ": "<sup>n</sup>",
    "ᵒ": "<sup>o</sup>",
    "ᵖ": "<sup>p</sup>",
    "ʳ": "<sup>r</sup>",
    "ˢ": "<sup>s</sup>",
    "ᵗ": "<sup>t</sup>",
    "ᵘ": "<sup>u</sup>",
    "ᵛ": "<sup>v</sup>",
    "ʷ": "<sup>w</sup>",
    "ˣ": "<sup>x</sup>",
    "ʸ": "<sup>y</sup>",
    "ᶻ": "<sup>z</sup>",
    "ᴬ": "<sup>A</sup>",
    "ᴮ": "<sup>B</sup>",
    "ᴰ": "<sup>D</sup>",
    "ᴱ": "<sup>E</sup>",
    "ᴳ": "<sup>G</sup>",
    "ᴴ": "<sup>H</sup>",
    "ᴵ": "<sup>I</sup>",
    "ᴶ": "<sup>J</sup>",
    "ᴷ": "<sup>K</sup>",
    "ᴸ": "<sup>L</sup>",
    "ᴹ": "<sup>M</sup>",
    "ᴺ": "<sup>N</sup>",
    "ᴼ": "<sup>O</sup>",
    "ᴾ": "<sup>P</sup>",
    "ᴿ": "<sup>R</sup>",
    "ᵀ": "<sup>T</sup>",
    "ᵁ": "<sup>U</sup>",
    "ⱽ": "<sup>V</sup>",
    "ᵂ": "<sup>W</sup>",

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
    "ₕ": "<sub>h</sub>",
    "ᵢ": "<sub>i</sub>",
    "ⱼ": "<sub>j</sub>",
    "ₖ": "<sub>k</sub>",
    "ₗ": "<sub>l</sub>",
    "ₘ": "<sub>m</sub>",
    "ₙ": "<sub>n</sub>",
    "ₒ": "<sub>o</sub>",
    "ₚ": "<sub>p</sub>",
    "ᵣ": "<sub>r</sub>",
    "ₛ": "<sub>s</sub>",
    "ₜ": "<sub>t</sub>",
    "ᵤ": "<sub>u</sub>",
    "ᵥ": "<sub>v</sub>",
    "ₓ": "<sub>x</sub>",

    "ꟹ": "<sup>oe</sup>",

    "ᵝ": "<sup>β</sup>",
    "ᵞ": "<sup>γ</sup>",
    "ᵟ": "<sup>δ</sup>",
    "ᵋ": "<sup>ε</sup>",
    "ᶿ": "<sup>θ</sup>",
    "ᶥ": "<sup>ι</sup>",
    "ᶹ": "<sup>υ</sup>",
    "ᵠ": "<sup>φ</sup>",
    "ᵡ": "<sup>χ</sup>",

    "ᵦ": "<sub>β</sub>",
    "ᵧ": "<sub>γ</sub>",
    "ᵨ": "<sub>ρ</sub>",
    "ᵩ": "<sub>φ</sub>",
    "ᵪ": "<sub>χ</sub>",

    "ᵅ": "<sup>ɑ</sup>",
    "ᶜ̧": "<sup>ç</sup>",
    "ᶞ": "<sup>ð</sup>",
    "ᵊ": "<sup>ə</sup>",
    "ᶪ": "<sup>ᶅ</sup>",
    "ᶴ": "<sup>ʃ</sup>",
    "ᶵ": "<sup>ƫ</sup>",
    "ꭩ": "<sup>ʍ</sup>",
    "ˀ": "<sup>ʔ</sup>",

    "ₔ": "<sub>Ə</sub>",

    "ᵑ": "<sup>ŋ</sup>",

    # Necessary to clean up the above subscript and superscript
    # transforms, when they affect multiple sequential characters
    "</sup><sup>": "",
    "</sub><sub>": "",

    # TODO: https://en.wikipedia.org/wiki/Unicode_subscripts_and_superscripts#Other_superscript_and_subscript_characters


    "&#46;": "&period;",  # When needed to stop template from dropping "." from abbreviations
    "&point;": "&period;",

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
    "&QUOT;": '"',
    "&#8220;": '"',
    "&#8221;": '"',

    # "&lt;": "<",
    # "&gt;": ">",

    # Common symbols
    "&iquest;": "¿",
    "&pound;": "£",
    "&#163;": "£",
    "&sect;": "§",
    "&para;": "¶",
    "&brvbar;": "¦",
    "&euro;": "€",
    "&curren;": "¤",
    "&dagger;": "†",  # {{dagger}} is also available
    "&Dagger;": "‡",  # {{double-dagger}} is also available
    "&ddagger;": "‡",
    "&clubs;": "♣",
    "&diams;": "♦",
    "&spades;": "♠",
    "&deg;": "°",
    "&degree;": "°",
    "&oline;": "‾",
    "&plus;": "+",
    "&mp;": "∓",
    "&cent;": "¢",
    "&circ;": "ˆ",
    "&yen;": "¥",
    "&Tcedil;": "Ţ",
    "&tcedil;": "ţ",
    "&Scedil;": "Ş",
    "&scedil;": "ş",
    "&divide;": "÷",
    "&male;": "♂",
    "&female;": "♀",

    "㎆": "MB",
    "㎅": "KB",
    "&#x00B4;": "&acute;",
    "&ordf;": "ª",
    "&ordm;": "º",
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
    "&Ccirc;": "Ĉ",
    "&ccaron;": "č",
    "&eth;": "ð",
    "&Eacute;": "É",
    "&eacute;": "é",
    "&ecirc;": "ê",
    "&Egrave;": "È",
    "&egrave;": "è",
    "&emacr;": "ē",
    "&Euml;": "Ë",
    "&euml;": "ë",
    "&#X1E24;": "Ḥ",
    "&iacute;": "í",
    "&Iacute;": "Í",
    "&icirc;": "î",
    "&igrave;": "ì",
    "&iuml;": "ï",
    "&nacute;": "ń",
    "&Ntilde;": "Ñ",
    "&ntilde;": "ñ",
    "&oacute;": "ó",
    "&Oacute;": "Ó",
    "&ocirc;": "ô",
    "&ocy;": "о̀",
    "&ograve;": "ò",
    "&omacr;": "ō",
    "&Omacr;": "Ō",
    "&Oslash;": "Ø",
    "&oslash;": "ø",
    "&otilde;": "õ",
    "&Otilde;": "Õ",
    "&Ouml;": "Ö",
    "&ouml;": "ö",
    "&#X14D;": "ō",
    "&rcaron;": "ř",
    "&Scaron;": "Š",
    "&scaron;": "š",
    "&#X161;": "š",
    "&szlig;": "ß",
    "&Uacute;": "Ú",
    "&uacute;": "ú",
    "&Ucirc;": "Û",
    "&ucirc;": "û",
    "&ugrave;": "ù",
    "&umacr;": "ū",
    "&Uuml;": "Ü",
    "&uuml;": "ü",
    "&yacute;": "ý",
    "&ycirc;": "ŷ",
    "&thorn;": "þ",
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

    # Ligatures in HTML entities
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
    "&NBSP;": "&nbsp;",
    "&nbsP;": "&nbsp;",
    "&6nbsp;": "&nbsp;",
    "&Ndash;": "&ndash;",
    "&nybsp;": "&nbsp;",
    "&nbsop;": "&nbsp;",
    "&nbdsp;": "&nbsp;",
    "&nbzp;": "&nbsp;",
    "&nbap;": "&nbsp;",
    "&hnbsp;": "&nbsp;",
    "&nbspc;": "&nbsp;",
    "&ndsah;": "&ndash;",
    "&ndasg;": "&ndash;",
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
    "&ndashl;": "&ndash;",
    "&nbdash;": "&ndash;",
    "&endash;": "&ndash;",
    "&bdash;": "&ndash;",
    "&ndahs;": "&ndash;",
    "&ndadh;": "&ndash;",
    "&ndas;": "&ndash;",
    "&dnash;": "&ndash;",
    "&ndasgh;": "&ndash;",
    "&mdasg;": "&mdash;",
    "&nsbp;": "&nbsp;",
    "&nbps;": "&nbsp;",
    "&nbps;": "&nbsp;",
    "&bnsp;": "&nbsp;",
    "&spnb;": "&nbsp;",
    "&ndsp;": "&nbsp;",
    "&nbsap;": "&nbsp;",
    "&nbp;": "&nbsp;",
    "&nhsp;": "&nbsp;",
    "&ngsp;": "&nbsp;",
    "&nbvsp;": "&nbsp;",
    "&nbsvp;": "&nbsp;",
    "&nbsb;": "&nbsp;",
    "&nbsf;": "&nbsp;",
    "&nbso;": "&nbsp;",
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
    "&nbdp;": "&nbsp;",
    "&nbsps;": "&nbsp;",
    "&nbstp;": "&nbsp;",
    "&mdaash;": "&mdash;",
    "&mdasha;": "&mdash;",
    "&nsbsp;": "&nbsp;",
    "&msdash;": "&mdash;",
    "&Nbsp;": "&nbsp;",
    "&nbwsp;": "&nbsp;",
    "&bnbsp;": "&nbsp;",
    "&nbash;": "&ndash;",
    "&nbssp;": "&nbsp;",
    "&mndash;": "&mdash;",
    "&bsnp;": "&nbsp;",
    "&nbasp;": "&nbsp;",
    "&nadash;": "&ndash;",
    "&ngash;": "&ndash;",
    "&nsb;": "&nbsp;",
    "&ndah;": "&ndash;",
    "&ndaah;": "&ndash;",
    "&nbsssp;": "&nbsp;",
    "&ndashc;": "&ndash;",
    "&emdash;": "&mdash;",
    "&nbsbp;": "&nbsp;",
    "&bbsp;": "&nbsp;",
    "&nbsbp;": "&nbsp;",
    "&nbaps;": "&nbsp;",
    "&mnsp;": "&nbsp;",
    "&ndasj;": "&ndash;",
    "&ndash0;": "&ndash;",
    "&npsp;": "&nbsp;",
    "&nbspp;": "&nbsp;",
    "&ndsash;": "&ndash;",
    "&nbsh;": "&nbsp;",
    "&nbsdp;": "&nbsp;",
    "&mnbsp;": "&nbsp;",
    "&nabs;": "&nbsp;",
    "&mdahs;": "&mdash;",
    "&nmsp;": "&nbsp;",

    # Used in tables, horizontal list formatting
    "&middot;": "·",
    # Replace with &sdot; in math expressions

    "&centerdot;": "·",
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
    "&vartheta;": "ϑ",
    "&iota;": "ι",
    "&lambda;": "λ",
    "&mu;": "μ",
    "&nu;": "ν",
    "&xi;": "ξ",
    "&pi;": "π",
    "&sigma;": "σ",
    "&tau;": "τ",
    "&upsilon;": "υ",
    "&phi;": "φ",  # lowercase phi U+03C6
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
    "&Phi;": "Φ",  # capital phi U+03A6
    "&Psi;": "Ψ",
    "&Omega;": "Ω",
    "&varphi;": "ϕ",  # U+03D5 phi symbol

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

    if num_value < 1:
        print(f"Low character value '{num_value}' for '{entity}'",
              file=sys.stderr)
        return True

    if num_value > 0x110000:
        print(f"Excessively high character value {num_value} for '{entity}'",
              file=sys.stderr)
        return True

    if unicodedata.combining(chr(num_value)):
        # Combining characters are too difficult to edit as themselves
        return True
    if variant_selectors_re.match(entity):
        return True

    # Avoid changing entities into characters that would normalize
    # into a different character.
    # https://en.wikipedia.org/wiki/Unicode_equivalence#Normalization
    transformed = unicodedata.normalize("NFC", entity)
    if entity != transformed:
        return True

    # This makes a difference; not sure why.
    if num_value == 0xFA1e:
        return True


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
