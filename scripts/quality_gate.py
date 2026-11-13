#!/usr/bin/env python3
"""Read-only quality gate for Coupon World static publishing artifacts."""
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
issues = []
warnings = []
def fail(message): issues.append(message)
def warn(message): warnings.append(message)

sitemap = ROOT / "sitemap.xml"
robots = ROOT / "robots.txt"
if not sitemap.exists(): fail("sitemap.xml missing")
else:
    try:
        tree = ET.parse(sitemap)
        urls = [n.text.strip() for n in tree.iter() if n.tag.endswith("}loc") and n.text]
        if not urls: fail("sitemap has no URLs")
        if len(urls) != len(set(urls)): fail("sitemap contains duplicate URLs")
        for url in urls:
            parsed = urlparse(url)
            if parsed.scheme != "https" or parsed.netloc != "coupon-world.in":
                fail("invalid sitemap origin: " + url)
            if parsed.query or parsed.fragment: warn("noncanonical sitemap URL: " + url)
        if "https://coupon-world.in/" not in urls: fail("homepage missing from sitemap")
        for section in ("phones", "tvs", "accessories"):
            if not any(urlparse(u).path.startswith("/" + section + "/") for u in urls):
                warn(section + " section absent from sitemap; verify generated routes before adding")
        print("Sitemap entries:", len(urls))
    except ET.ParseError as exc: fail("invalid sitemap XML: " + str(exc))
if not robots.exists(): fail("robots.txt missing")
else:
    body = robots.read_text(encoding="utf-8")
    if "Sitemap: https://coupon-world.in/sitemap.xml" not in body:
        fail("robots.txt missing canonical sitemap declaration")
home = ROOT / "index.html"
if home.exists():
    body = home.read_text(encoding="utf-8")
    if not re.search(r'<link\s+rel="canonical"\s+href="https://coupon-world.in/"', body):
        fail("homepage canonical missing")
    if not re.search(r'<meta\s+name="description"', body):
        fail("homepage description missing")
else: fail("index.html missing")
print("\n".join("WARNING: " + w for w in warnings))
print("\n".join("ERROR: " + e for e in issues))
print("PASS" if not issues else "FAIL")
sys.exit(bool(issues))
