from wikitext_util import remove_structure_nested, wikitext_to_plaintext
from spell import is_word_spelled_correctly

# TODO: Use a test framework

test_result = remove_structure_nested("aaa {{bbb {{ccc}} ddd}} eee", "{{", "}}")
if test_result != "aaa  eee":
    raise Exception("Broken remove_structure_nested returned: '%s'" % test_result)

test_result = remove_structure_nested("{{xxx yyy}} zzz", "{{", "}}")
if test_result != " zzz":
    raise Exception("Broken remove_structure_nested returned: '%s'" % test_result)

test_result = is_word_spelled_correctly("<nowiki/>")
if not test_result:
    raise Exception("Unknown HTML tags not considered incorrect")

# From https://en.wikipedia.org/wiki/Łoś–Vaught test

text_in = "a satisfiable theory is [[Morley's categoricity theorem|{{mvar|&kappa;}}-categorical]] (there exists an infinite cardinal {{mvar|&kappa;}} such that)"
text_out = wikitext_to_plaintext(text_in)
if not text_out == "a satisfiable theory is -categorical (there exists an infinite cardinal {{mvar|&kappa;}} such that)":
    raise Exception("Failed Łoś–Vaught")
