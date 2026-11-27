#!/usr/bin/env python3
"""Check that the GitHub Pages build and the itch.io build, and the two
storefront blurbs, stay in agreement.

Usage: python3 tools/check_sync.py
Exit 0 = fully in sync, 1 = drift detected.
"""
import hashlib
import re
import sys
import urllib.request

GH_GAME = "https://stan-hypnos.github.io/wuming-daoke/"
ITCH_GAME = "https://html-classic.itch.zone/html/20864978/index.html"
PAGES = [
    "https://github.com/stan-hypnos/wuming-daoke",
    "https://stan-hypnos.itch.io/wuming-daoke",
]
KEYWORDS = ["184 AD China", "permadeath", "zero deps"]

failures = []


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "sync-check/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def normalize(raw):
    """Drop the analytics script itch injects, and trailing whitespace, so the
    comparison is on game content only."""
    text = raw.decode("utf-8", "replace")
    text = re.sub(r"<script[^>]*htmlgame\.js[^>]*></script>", "", text)
    return text.rstrip("\n").encode("utf-8")


gh = itch = None
for name, url in (("GitHub Pages", GH_GAME), ("itch embed", ITCH_GAME)):
    try:
        data = normalize(fetch(url))
    except Exception as exc:
        failures.append("{} unreachable: {}".format(name, exc))
        continue
    print("{:<12} {}... {} B".format(name, hashlib.sha256(data).hexdigest()[:16], len(data)))
    if name == "GitHub Pages":
        gh = data
    else:
        itch = data

if gh is not None and itch is not None:
    if gh == itch:
        print("PASS  game build identical on both platforms")
    else:
        failures.append("game build differs - re-upload index.html to itch")
        import difflib

        a = gh.decode("utf-8", "replace").splitlines()
        b = itch.decode("utf-8", "replace").splitlines()
        for line in list(difflib.unified_diff(a, b, lineterm=""))[:20]:
            print(line)

for url in PAGES:
    try:
        page = fetch(url).decode("utf-8", "replace")
    except Exception as exc:
        failures.append("{} unreachable: {}".format(url, exc))
        continue
    missing = [k for k in KEYWORDS if k.lower() not in page.lower()]
    if missing:
        failures.append("{} blurb missing: {}".format(url, ", ".join(missing)))
    else:
        print("PASS  blurb in sync -> {}".format(url))

if failures:
    print("\n== DRIFT DETECTED ==")
    for item in failures:
        print("- " + item)
    sys.exit(1)

print("\n== ALL IN SYNC ==")
