# Before running, create user-config.py

from pywikibot import pagegenerators
from subprocess import call
import sys
from unencode_entities import fix_text


input_safe = sys.argv[1].replace("<", "\<")
input_safe = input_safe.replace("/", "\/")
query = "insource:/%s/i" % input_safe

# import wikipedia
# results = wikipedia.search(query, results=5)
# print([r for r in results])


# pywikibot documentation:
# https://doc.wikimedia.org/pywikibot/master/api_ref/pywikibot.html
results = pagegenerators.SearchPageGenerator(query, namespaces=[0], total=5)

for page in results:
    print(page.title())
    new_text = fix_text(page.text)
    title_safe = page.title().replace(" ", "_")
    with open("swap/%s" % title_safe, 'w') as output_file:
        output_file.write(new_text)
    call(["firefox",
          "https://en.wikipedia.org/w/index.php?title=%s&action=edit" % title_safe])
