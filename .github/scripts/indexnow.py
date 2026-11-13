"""Tell Bing (and other IndexNow search engines) which pages of the site changed.

IndexNow is an open protocol: the site proves it owns its pages by serving a key file
(site/<key>.txt, copied into the site by the Pages workflow), then this script posts the page
addresses from the sitemap to https://api.indexnow.org. Google does not use IndexNow; it reads
the sitemap you submit in Search Console.

    python3 indexnow.py public/sitemap.xml all     every page (when the site itself changed)
    python3 indexnow.py public/sitemap.xml fresh   only the pages that change daily

It never fails the build: a search engine being unreachable is not a reason to stop a deploy.
Set INDEXNOW_DRY=1 to print what would be sent.
"""
import glob, json, os, re, sys, urllib.request, xml.etree.ElementTree as ET
from urllib.parse import urlparse

sitemap, mode = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "all")
urls = [e.text.strip() for e in ET.parse(sitemap).getroot().iter() if e.tag.endswith("loc") and e.text]
if not urls:
    sys.exit("no URLs in the sitemap")
home = min(urls, key=len)  # the home page is the shortest address
host = urlparse(home).netloc
base = urlparse(home).path if urlparse(home).path.endswith("/") else urlparse(home).path + "/"  # e.g. /BBC-Radio-6-Music-Collection/

keys = [os.path.basename(p)[:-4] for p in glob.glob(os.path.join(os.path.dirname(__file__), "..", "..", "site", "*.txt"))]
keys = [k for k in keys if re.fullmatch(r"[0-9a-f]{32}", k)]
if len(keys) != 1:
    sys.exit(f"expected one IndexNow key file in site/, found {len(keys)}")
key = keys[0]

if mode == "fresh":
    # the pages that change every day: the home page, the charts, the newest tracklists
    fresh = ("", "latest/", "years/", "crate-dive/")
    urls = [u for u in urls if (lambda r: r in fresh or r.startswith("most-played/"))(urlparse(u).path[len(base):])]

body = {"host": host, "key": key, "keyLocation": f"https://{host}{base}{key}.txt"}
print(f"IndexNow: {len(urls)} URLs ({mode}) for {host}{base}")
if os.environ.get("INDEXNOW_DRY"):
    print(json.dumps(body), urls[:3], "...")
    sys.exit(0)
for i in range(0, len(urls), 9000):  # the limit is 10,000 per request
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=json.dumps({**body, "urlList": urls[i:i + 9000]}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print("IndexNow replied", r.status)
    except Exception as e:  # noqa: BLE001 - never fail the deploy
        print("IndexNow did not accept the request:", e)
