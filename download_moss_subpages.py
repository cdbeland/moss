import string
import urllib.request


for letter in ["before_A"] + list(string.ascii_uppercase) + ["after_Z"]:
    url = f"https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/{letter}"
    print(f"Downloading {url}")
    urllib.request.urlretrieve(url, f"/bulk-wikipedia/moss-subpages/{letter}")
