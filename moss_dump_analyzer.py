# -*- coding: utf-8 -*-

# http://dumps.wikimedia.org/backup-index.html
# http://meta.wikimedia.org/wiki/Data_dumps

import difflib
import lxml.etree
import re

# Runtime: ~1.5 hours (with a simple callback)

# TODO:
# * Get segmentizer working
#   \w's -> <apos>s
#   LTR quote finding [('")] ... \1
#   ' " -> <lqs id=3> <lqd id=4>
#   unbalanced is possible
#
#  Note that regular expressions will not suffice; wikitext does not
#  follow a regular grammar (in the technical sense).
#  For explanation: https://www.mediawiki.org/wiki/Markup_spec
#  Nested regions are problematic, like:
#  {{template outer {{inner template}} danger zone}}
#
#  Need to tag token-by-token and maintain context (ref, template,
#  table, quote, etc.)

# * Get article blocklist (manual check needed) working
#   -> Category filter
# * Get web server fired up with API-based editing
# * Generalize changes - in: method, edit summary, result object with
#   count, messages.  Then main function can just be a list of calls
#   to that generallized processor, with conditionals around them for
#   dialect, segment type, etc.

# grep '#8223;' /bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml
# Ukrainian alphabet | &amp;amp;#8222; &amp;amp;#8223;
# Quotation marks | U+201F || {{smallcaps|{{lc:Double high-reversed-9 quotation mark}}}} || &amp;amp;#8223;


def read_en_article_text(callback_function, filename=""):
    working_string = ""

    if not filename:
        filename = "/bulk-wikipedia/enwiki-latest-pages-articles-multistream.xml"
    with open(filename, "r") as article_xml_file:
        for line in article_xml_file:
            working_string += line
            if line == "  </page>\n":
                working_string = re.sub(r"^.*(<page.*?</page>).*$", r"\1", working_string, flags=re.MULTILINE+re.DOTALL)
                root_element = lxml.etree.fromstring(working_string)
                working_string = ""

                namespace = root_element.findtext('ns')
                if namespace != '0':
                    # Page is not an article
                    continue

                redirect_target = root_element.find('redirect')
                if redirect_target is not None:
                    # Article is redirect; skip it for now
                    continue

                article_title = root_element.findtext('title')
                article_text = root_element.findtext('.//text')
                callback_function(article_title, article_text)


def changer_callback(article_text, article_title):
    (edit_summary, change_count, new_article_text) = make_changes(article_text)
    if article_text != new_article_text:
        # print ("%s\t%s\t%s\t%s" % (article_title, change_count, edit_summary, new_article_text))
        old = article_text.splitlines(1)
        new = new_article_text.splitlines(1)
        diff = difflib.unified_diff(old, new)
        print("TITLE: " + article_title.encode('utf8'))
        print(''.join(diff).encode('utf8'))


def make_changes(input_wikitext, aggressive=False):
    segments = segmentize(input_wikitext)
    output_wikitext = ''
    edit_summaries = []
    change_count = 0

    # TODO: English dialect detector
    dialect = 'unknown'

    for segment in segments:
        wikitext = segment['wikitext']
        if segment['type'] == 'normal':

            if dialect == 'american':
                # American and Canadian English = U.S.
                new_wikitext = re.sub(r"USA", "U.S.", wikitext)
                if new_wikitext != wikitext:
                    change_count += 1
                    wikitext = new_wikitext
                    edit_summaries.append("USA -> U.S. per [[WP:NOTUSA]]")
            elif dialect == 'british':
                # British/Commonwealth English = US
                pass

            new_wikitext = re.sub(u"[“”]", r'"', wikitext)
            # U+201C, U+201D
            if new_wikitext != wikitext:
                change_count += 1
                edit_summaries.append('“” -> " per [[Wikipedia:Manual of Style#Quotation_marks]]')
                wikitext = new_wikitext

            if aggressive:
                new_wikitext = re.sub(r"(?!')'(\w+)'(?!')(?!\w)", r'"\1"', wikitext)
                if new_wikitext != wikitext:
                    change_count += 1
                    edit_summaries.append("' -> \" per [[Wikipedia:Manual of Style#Quotation_marks]]")
                    wikitext = new_wikitext

        output_wikitext += wikitext
    edit_summary = "; ".join(edit_summaries)
    return (edit_summary, change_count, output_wikitext)


def segmentize(input_wikitext):
    if "<ref>" in input_wikitext:
        return [{'type': 'ref',
                 'wikitext': input_wikitext}]

    if "<!--" in input_wikitext:
        return [{'type': 'comment',
                 'wikitext': input_wikitext}]

    return [{'type': 'normal',
             'wikitext': input_wikitext}]


if __name__ == "__main__":
    read_en_article_text(changer_callback)
