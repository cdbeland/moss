from collections import defaultdict
from pprint import pformat
import unittest

# Enabling this makes init fast but breaks spelling tests
# import os
# os.environ["NO_LOAD"] = "1"
from .spell import is_word_spelled_correctly  # noqa: E402

from .wikitext_util import remove_structure_nested, wikitext_to_plaintext  # noqa: E402
from .word_categorizer import (letters_introduced_alphabetically, make_suggestion_dict, make_edits_lowfi)  # noqa: E402


class WikitextUtilTest(unittest.TestCase):

    def test_whitespace(self):
        self.assertEqual(
            wikitext_to_plaintext("xxx\nyyy"),
            "xxx yyy")
        self.assertEqual(
            wikitext_to_plaintext("one ONE\n\n==Section==\n\ntwo TWO"),
            "one ONE\n==Section==\ntwo TWO")
        self.assertEqual(
            wikitext_to_plaintext("==Section==\n[[File:xxx]]\naaa"),
            "==Section==\naaa")

    def test_tags(self):
        self.assertEqual(
            wikitext_to_plaintext("bbb\n<timeline arg=1>\nccc\n</timeline>\nddd"),
            "bbb\nddd")
        self.assertEqual(
            wikitext_to_plaintext("eee\n<code>\nfff\n</code>\nggg"),
            "eee\nggg")

        text = """hhh
<gallery>
qqq.jpg|- www
rrr.jpg|- ttt
</gallery>
iii"""
        self.assertEqual(
            wikitext_to_plaintext(text),
            "hhh\niii")

        self.assertEqual(
            remove_structure_nested("aaa {{bbb {{ccc}} ddd}} eee", "{{", "}}"),
            "aaa ✂✂✂ eee")

        self.assertEqual(
            remove_structure_nested("{{xxx yyy}} zzz", "{{", "}}"),
            "✂ zzz")

    def test_links(self):
        self.assertEqual(
            wikitext_to_plaintext("[[Regular page]]s"),
            "Regular pages")
        self.assertEqual(
            wikitext_to_plaintext("[[Target page|Display text]]"),
            "Display text")
        self.assertEqual(
            wikitext_to_plaintext("[[Namespace:Target page]]"),
            "")

        # From https://en.wikipedia.org/wiki/Scott_Shiflett
        self.assertEqual(
            wikitext_to_plaintext("*''[[Face to Face (1996 Face to Face album)|Face to Face]]'' (1996)"),
            "*Face to Face (1996)")

    def test_ŁośVaught(self):
        # From https://en.wikipedia.org/wiki/Łoś–Vaught test
        text_in = "a satisfiable theory is [[Morley's categoricity theorem|{{mvar|&kappa;}}-categorical]] (there exists an infinite cardinal {{mvar|&kappa;}} such that)"
        self.assertEqual(
            wikitext_to_plaintext(text_in),
            "a satisfiable theory is ✂-categorical (there exists an infinite cardinal ✂ such that)")


class WordCategorizerTest(unittest.TestCase):
    def test_letters_introduced(self):
        self.assertTrue(letters_introduced_alphabetically("aAbB"))
        self.assertTrue(letters_introduced_alphabetically("AbcabD"))
        self.assertFalse(letters_introduced_alphabetically("baa"))
        self.assertFalse(letters_introduced_alphabetically("abd"))

    def test_make_lowfi_one(self):
        actual = make_edits_lowfi(["xyz"], 1)
        correct = {
            1: set(["*xyz", "*xy", "*yz", "*xz", "*yz", "*xz", "xy", "yz", "xz"]),
        }
        self.assertEqual(actual, correct)

    def test_make_lowfi_two(self):
        actual = make_edits_lowfi(["xyz"], 2)
        print(pformat(actual))
        correct = {
            1: set(["*xyz", "*xy", "*yz", "*xz", "*yz", "*xz", "xy", "yz", "xz"]),
            2: set(["x", "y", "z", "*x", "*y", "*z"]),
        }
        self.assertEqual(actual, correct)

    def test_make_suggestion_dict(self):
        actual = dict(make_suggestion_dict(["qwerty", "asd", "a"]))
        print(pformat(actual))

        correct = {
            1: defaultdict(set, {
                "*a": {"a"},
                "": {"a"},
                "*": {"a"},
                "*ads": {"asd"},
                "ds": {"asd"},
                "ad": {"asd"},
                "as": {"asd"},
                "*ds": {"asd"},
                "*ad": {"asd"},
                "*as": {"asd"},
                "*eqrtwy": {"qwerty"},
                "qrtwy": {"qwerty"},
                "ertwy": {"qwerty"},
                "eqtwy": {"qwerty"},
                "eqrwy": {"qwerty"},
                "eqrty": {"qwerty"},
                "eqrtw": {"qwerty"},
                "*qrtwy": {"qwerty"},
                "*ertwy": {"qwerty"},
                "*eqtwy": {"qwerty"},
                "*eqrwy": {"qwerty"},
                "*eqrty": {"qwerty"},
                "*eqrtw": {"qwerty"},
            })}

        # If MAX_EDIT_DISTANCE is higher, these are needed:
        """
            2: defaultdict(set, {
                '*a': {'asd'},
                '*d': {'asd'},
                '*eqrt': {'qwerty'},
                '*eqrw': {'qwerty'},
                '*eqry': {'qwerty'},
                '*eqtw': {'qwerty'},
                '*eqty': {'qwerty'},
                '*eqwy': {'qwerty'},
                '*ertw': {'qwerty'},
                '*erty': {'qwerty'},
                '*erwy': {'qwerty'},
                '*etwy': {'qwerty'},
                '*qrtw': {'qwerty'},
                '*qrty': {'qwerty'},
                '*qrwy': {'qwerty'},
                '*qtwy': {'qwerty'},
                '*rtwy': {'qwerty'},
                '*s': {'asd'},
                'a': {'asd'},
                'd': {'asd'},
                'eqrt': {'qwerty'},
                'eqrw': {'qwerty'},
                'eqry': {'qwerty'},
                'eqtw': {'qwerty'},
                'eqty': {'qwerty'},
                'eqwy': {'qwerty'},
                'ertw': {'qwerty'},
                'erty': {'qwerty'},
                'erwy': {'qwerty'},
                'etwy': {'qwerty'},
                'qrtw': {'qwerty'},
                'qrty': {'qwerty'},
                'qrwy': {'qwerty'},
                'qtwy': {'qwerty'},
                'rtwy': {'qwerty'},
                's': {'asd'}}),
            3: defaultdict(set, {
                '': {'asd'},
                '*': {'asd'},
                '*eqr': {'qwerty'},
                '*eqt': {'qwerty'},
                '*eqw': {'qwerty'},
                '*eqy': {'qwerty'},
                '*ert': {'qwerty'},
                '*erw': {'qwerty'},
                '*ery': {'qwerty'},
                '*etw': {'qwerty'},
                '*ety': {'qwerty'},
                '*ewy': {'qwerty'},
                '*qrt': {'qwerty'},
                '*qrw': {'qwerty'},
                '*qry': {'qwerty'},
                '*qtw': {'qwerty'},
                '*qty': {'qwerty'},
                '*qwy': {'qwerty'},
                '*rtw': {'qwerty'},
                '*rty': {'qwerty'},
                '*rwy': {'qwerty'},
                '*twy': {'qwerty'},
                'eqr': {'qwerty'},
                'eqt': {'qwerty'},
                'eqw': {'qwerty'},
                'eqy': {'qwerty'},
                'ert': {'qwerty'},
                'erw': {'qwerty'},
                'ery': {'qwerty'},
                'etw': {'qwerty'},
                'ety': {'qwerty'},
                'ewy': {'qwerty'},
                'qrt': {'qwerty'},
                'qrw': {'qwerty'},
                'qry': {'qwerty'},
                'qtw': {'qwerty'},
                'qty': {'qwerty'},
                'qwy': {'qwerty'},
                'rtw': {'qwerty'},
                'rty': {'qwerty'},
                'rwy': {'qwerty'},
                'twy': {'qwerty'}
            }),
        """
        self.assertEqual(actual, correct)


class SpellTest(unittest.TestCase):

    def test_dashes(self):
        # May also return "uncertain", which is the wrong answer (but
        # evaluates to True)
        self.assertTrue(is_word_spelled_correctly("entirely-wet") is True)
        self.assertTrue(is_word_spelled_correctly("jelly—otherwise") is True)
        self.assertTrue(is_word_spelled_correctly("entirely-wet") is True)
        self.assertTrue(is_word_spelled_correctly("Arabic-based") is True)

    def test_unknown_html_tag(self):
        self.assertFalse(is_word_spelled_correctly("<nowiki/>"))

    def test_transliterations(self):
        # Dashes in a proper noun
        self.assertTrue(is_word_spelled_correctly("Anbār-e"))
        # Single quote marks in a proper noun
        self.assertTrue(is_word_spelled_correctly("Pā’īn"))
        # Non-ASCII capitals make it a proper noun
        self.assertTrue(is_word_spelled_correctly("Ḩasan"))

    def period_splices(self):
        self.assertFalse(is_word_spelled_correctly("again.The"))
        self.assertFalse(is_word_spelled_correctly("Everest.Another"))
        self.assertTrue(is_word_spelled_correctly("Ph.B"))
        self.assertEqual(is_word_spelled_correctly("Im.C23", "uncertain"))
