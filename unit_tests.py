import unittest

from .wikitext_util import remove_structure_nested, wikitext_to_plaintext


class WikitextUtilTest(unittest.TestCase):

    def test_remove_structure_nested(self):
        self.assertEqual(
            remove_structure_nested("aaa {{bbb {{ccc}} ddd}} eee", "{{", "}}"),
            "aaa  eee")

        self.assertEqual(
            remove_structure_nested("{{xxx yyy}} zzz", "{{", "}}"),
            " zzz")

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
            "a satisfiable theory is -categorical (there exists an infinite cardinal  such that)")


class SpellTest(unittest.TestCase):

    def test_unknown_html_tag(self):
        from .spell import is_word_spelled_correctly  # This takes a long time
        self.assertFalse(is_word_spelled_correctly("<nowiki/>"))

    def test_transliteration(self):
        from .spell import is_word_spelled_correctly
        self.assertTrue(is_word_spelled_correctly("Āb Anbār-e Pā’īn"))
