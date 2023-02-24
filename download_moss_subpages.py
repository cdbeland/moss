import string
from time import sleep
import urllib.request


def download_page(letter, delay=10):
    url = f"https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/{letter}"
    print(f"Downloading {url}")
    try:
        urllib.request.urlretrieve(url, f"/bulk-wikipedia/moss-subpages/{letter}")
    except (urllib.error.URLError,  urllib.error.HTTPError) as error:
        print(error)
        print(f"Temporary failure? Retrying in {delay} seconds")
        sleep(delay)
        download_page(letter, delay * 2)


for letter in ["before_A"] + list(string.ascii_uppercase) + ["after_Z"]:
    download_page(letter)
