import fileinput
import re
import sys

# Manual transformation probably required
alert = [
    "™", "©", "®",
    "Ⅰ", "Ⅱ", "ⅰ", "ⅱ",
    "¼", "½", "¾", "&frasl;"
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
    "&plusmn;": "±",
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
    "&le;": "≤",
    "&fnof;": "ƒ",
    "&infin;": "∞",
    "&ge;": "≥",
    "&lowast;": "∗",
    "&cong;": "≅",
    "&weierp;": "℘",
    "&hArr": "⇔",
    "&rArr": "⇒",
    "&rarr;": "→",
    "&larr;": "←",
    "&harr;": "↔",
    "&darr;": "↓",
    "&uarr;": "↑",
}

keep.extend(controversial.keys())

# Automatically change, with the expectation there will be a
# manual inspection of the diff
transform = {
    "&#043;": "+",
    "&#061;": "=",
    "&#037;": "%",
    "&quot;": '"',
    "&hellip;": "...",
    "…": "...",
    "&trade;": "™",
    "&copy;": "©",
    "&reg;": "®",

    "&amp;": "&",
    "&lt;": "<",
    "&gt;": ">",
    "&#91;": "[",
    "&#93;": "]",
    "&apos;": "'",

    "&#124;": "-",
    # This is a pipe, but usually happens in URL titles, in which case
    # making a dash is easier.

    # Very common symbols, to change outside of math/science articles
    "&pound;": "£",
    "&sect;": "§",
    "&deg;": "°",

    # Latin and Germanic letters
    "&aacute;": "á",
    "&agrave;": "à",
    "&Aring;": "Å",
    "&aring;": "å",
    "&atilde;": "ã",
    "&auml;": "ä",
    "&szlig;": "ß",
    "&ccedil;": "ç",
    "&Eacute;": "É",
    "&eacute;": "é",
    "&ecirc;": "ê",
    "&egrave;": "è",
    "&iacute;": "í",
    "&Iacute;": "Í",
    "&igrave;": "ì",
    "&iuml;": "ï",
    "&ntilde;": "ñ",
    "&oacute;": "ó",
    "&ocirc;": "ô",
    "&ograve;": "ò",
    "&oslash;": "ø",
    "&ouml;": "ö",
    "&Uacute;": "Ú",
    "&uacute;": "ú",
    "&ugrave;": "ù",
    "&uuml;": "ü",

    "&#163;": "£",
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

    # Greek letters only found in actual Greek words
    "&sigmaf;": "ς",  # Written this way when word-final
    "&#x1F7B;": "ύ",
    "&#x1F76;": "ὶ",
    "&#x1FC6;": "ῆ",
    "&#x1F10;": "ἐ",
    "&#x1FF7;": "ῷ",
    "&#x1FC6;": "ῆ",

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
    "&#8211;": "–",  # endash

    "&#8216;": "'",  # ‘ -> '
    "&#8217;": "'",  # ’ -> '
    "&#8212;": "—",  # emdash

    # Per [[MOS:CONFORM]]
    "« ": '"',
    " »": '"',
    "«": '"',
    "»": '"',
    "&raquo;": '"',
    "&laquo;": '"',
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


def make_useful(entity):
    result = re.match("&#(x?[0-9a-fA-F]+);", entity)
    if result:
        number = result.group(1)
        if number.startswith("x"):
            number = number.strip("x")
            number = int(number, 16)
        else:
            number = int(number)
        converted_entity = chr(number)
        return "%s (%s)" % (entity, converted_entity)
    else:
        return entity


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
    unknown_entities = re.findall("&#?[a-zA-Z0-9]+;", test_string)
    if unknown_entities:
        sys.stderr.write(new_text)
        raise Exception("Unknown HTML entity: %s" % " ".join([
            make_useful(string) for string in unknown_entities
        ]))

    return new_text


if __name__ == '__main__':
    for line in fileinput.input("-"):
        new_line = fix_text(line)
        sys.stdout.write(new_line)
