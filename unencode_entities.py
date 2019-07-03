import fileinput
import re
import sys


entities_re = re.compile(r"&#?[a-zA-Z0-9]+;")


# Manual transformation probably required
alert = [
    "™", "©", "®",
    "Ⅰ", "Ⅱ", "ⅰ", "ⅱ",
    "¼", "½", "¾", "&frasl;",
    "¹", "⁺", "ⁿ", "₁", "₊", "ₙ",

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
    "‹", "&lsaquo;", "›", "&rsaquo;",
    "«", "&lsaquo;", "»", "&rsaquo;",

    # Probably convert to regular space or no space
    "&ensp;", "&emsp;", "&thinsp;", "&hairsp;",

    # &zwj; usually wants to be &zwnj; and probably that usually isn't
    # needed?
    "&zwj;", "&zwnj;"

    # Probably wants to be wiki-list syntax
    "•", "&bull;", "·", "&middot;", "⋅", "&sdot;",
]

# Ignore these if seen in articles
keep = [
    "&amp;",  # dangerous for e.g. &amp;126;
    "&c;",    # Almost all are in archaic quotations and titles

    # Should be excluded by <source> etc.
    # "&a;",    # Used in computer articles as example of a pointer
    # "&x;",    # Used in computer articles as example of a pointer

    # Allowed for math notation only
    "&prime;", "′", "&Prime;", "″",

    # Definitely confusing, keep forever
    "&ndash;", "&mdash;", "&minus;", "&shy;",
    "&nbsp;", "&lrm;", "&rlm;",

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
    "&vert;",  # |
    "&#123;",  # {
    "&#125;",  # }
    # TODO: Maybe these should be converted to <nowiki>[</nowiki> etc.?

    # https://en.wikipedia.org/wiki/Zero-width_non-joiner Used in
    # German, Arabic, Hebrew, etc.  Sometimes abused to fix wikitext
    # markup issues, but would require manual review to determine
    # that.  TODO: Automate ignoring situations where this is inside
    # {{lang}}.
    "&zwnj;",
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
    # character itself is being discussed.

    # Per [[MOS:FRAC]]
    "¼": "{{frac|1|4}}",
    "½": "{{frac|1|2}}",
    "¾": "{{frac|3|4}}",
    "&frac12": "{{frac|1|2}}",
    "&frac14": "{{frac|1|4}}",
    "&frac16": "{{frac|1|6}}",
    "&frac34": "{{frac|3|4}}",
    "…": "...",
    "&hellip;": "...",

    # Often breaks wiki markup
    # "&#91;": "[",
    # "&#93;": "]",
    "&#x005B;": "&#91;",
    "&#x005D;": "&#93;",
    "&#x091;": "&#91;",
    "&#x093;": "&#93;",
    "&#x5B;": "&#91;",
    "&#x5D;": "&#93;",
    "&#x7C;": "&vert;",
    "&#x007C;": "&vert;",
    "&#x3C;": "&lt;",
    "&#x003C;": "&lt;",
    "&#x3E;": "&gt;",
    "&#x003E;": "&gt;",

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
    "&#8217;": "'",   # ’ -> '

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
}

# Automatically change, with the expectation there will be a
# manual inspection of the diff
transform = {

    "&#x9": "&tab;",
    "&#9": "&tab;",
    "&#09": "&tab;",
    "&#x09": "&tab;",
    "&#x0009": "&tab;",

    # Per [[MOS:FRAC]]
    "&frac12;": "{{frac|1|2}}",
    "&frac14;": "{{frac|1|4}}",
    "&frac34;": "{{frac|3|4}}",
    "&frac16;": "{{frac|1|6}}",

    "&permil;": "‰",

    "&sup1;": "<sup>1</sup>",
    "&sup2;": "<sup>2</sup>",
    "&sup3;": "<sup>3</sup>",

    "&#0033;": "!",
    "&#0047;": "/",
    "&#005B;": "&#91;",  # [
    "&#005C;": "\\",
    "&#0060;": "&lt;",
    "&#0061;": "=",  # Will break markup inside templates
    "&#0062;": "&lt;",
    "&#0093;": "&#93;",  # ]
    "&#0124;": "&#124;",  # |

    "&#043;": "+",
    "&#061;": "=",
    "&#037;": "%",

    "&apos;": "'",
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

    "&#x00B4;": "&acute;",
    "&ordf;": "ª",

    "&#8212;": "—",   # emdash
    "&#X2014;": "—",  # emdash

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


def fix_text(text, transform_greek=False):

    if transform_greek:
        conversion_dict = transform.copy()
        conversion_dict.update(greek_letters)
    else:
        conversion_dict = transform

    new_text = text
    for (from_string, to_string) in conversion_dict.items():
        new_text = new_text.replace(from_string, to_string)

    for string in alert:
        if string in new_text:
            with_context_re = re.compile(r".{0,10}%s.{0,10}" % string)
            with_context_results = with_context_re.findall(text)
            print("FOUND BAD CHARACTER IN TEXT: %s" % " ".join(with_context_results),
                  file=sys.stderr)

    test_string = new_text
    for string in keep:
        test_string = test_string.replace(string, "")
    if not transform_greek:
        for string in greek_letters:
            test_string = test_string.replace(string, "")
    for unknown_entity in re.findall("&#?[a-zA-Z0-9]+;", test_string):
        character = find_char(unknown_entity)
        if character:
            new_text = new_text.replace(unknown_entity, character)
        print("unknown entity: %s  character: %s" % (unknown_entity, character),
              file=sys.stderr)

    return new_text


if len(sys.argv) > 1 and "--safe" in sys.argv:
    pass
else:
    transform.update(transform_unsafe)

if __name__ == '__main__':
    for line in fileinput.input("-"):
        new_line = fix_text(line)
        sys.stdout.write(new_line)
