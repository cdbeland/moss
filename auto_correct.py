# Before running, create user-config.py

# This takes one command line argument, for example
#  &egrave;   (will do a search)
#  titles:Article A, Article B   (will tee up fixes for all these articles)

from pywikibot import pagegenerators, Page, Site
import re
from subprocess import call
import sys
from unencode_entities import fix_text


input_safe = sys.argv[1].replace("<", "\<")
input_safe = input_safe.replace("/", "\/")
query = "insource:/%s/i" % input_safe

results = []
if sys.argv[1].startswith("titles:"):
    title_list = re.sub("^titles:", "", sys.argv[1])
    title_list = title_list.replace(" ", "_")
    title_list = title_list.split(",")
    site = Site()
    results = [Page(site, title=title) for title in title_list]
else:
    # pywikibot documentation:
    # https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
    results = pagegenerators.SearchPageGenerator(query, namespaces=[0], total=10)

for page in results:
    print(page.title())
    new_text = fix_text(page.text)
    title_safe = page.title().replace(" ", "_")
    with open("swap/%s" % title_safe, 'w') as output_file:
        output_file.write(new_text)
    call(["firefox",
          "https://en.wikipedia.org/w/index.php?title=%s&action=edit" % title_safe])