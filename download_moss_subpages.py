import os
import string
from time import sleep
import urllib.request


def download_page(letter, delay=10):
    url = f"https://en.wikipedia.org/wiki/Wikipedia:Typo_Team/moss/{letter}"
    print(f"Downloading {url}")
    try:
        request = urllib.request.Request(
            url,
            data=None,
            headers={
                "User-Agent": MOSS_USER_AGENT,
            }
        )
        result = urllib.request.urlopen(request)
        output_filename = f"/var/local/moss/bulk-wikipedia/moss-subpages/{letter}"
        with open(output_filename, "w") as output_file:
            print(result.read().decode('utf-8'), file=output_file)
    except (urllib.error.URLError,  urllib.error.HTTPError) as error:
        print(error)
        print(error.fp.read())
        if error.code == 403:
            exit(1)
        elif delay > 500:
            print("Giving up!")
            exit(1)
        else:
            print(f"Temporary failure? Retrying in {delay} seconds")
            sleep(delay)
            download_page(letter, delay * 2)
    sleep(1)  # Prevent too-fast downloading


MOSS_USER_AGENT = os.environ["MOSS_USER_AGENT"]
if not MOSS_USER_AGENT:
    print("Please set MOSS_USER_AGENT environment variable")
    exit(1)

for letter in ["before_A"] + list(string.ascii_uppercase) + ["after_Z"]:
    download_page(letter)
