#!/usr/bin/env python3
"""Read-only LIVE indexability evidence for the generated public sitemap.

This checks HTTP, redirects, canonicals, robots and release sitemap parity.
It is not Google Search Console and never estimates Google's indexed count.
No website files, prices, products, or sitemap entries are modified.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from scripts.sitemap_canonical_audit import SITE, _entries

USER_AGENT = "CouponWorldIndexabilityMonitor/1.0 (+read-only release QA)"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class Metadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals = []
        self.robots = []
        self.refresh = False

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if tag == "link" and "canonical" in (attributes.get("rel") or "").lower().split():
            self.canonicals.append((attributes.get("href") or "").strip())
        if tag == "meta":
            name = (attributes.get("name") or "").lower()
            if name in ("robots", "googlebot"):
                self.robots.append((attributes.get("content") or "").lower())
            if (attributes.get("http-equiv") or "").lower() == "refresh":
                self.refresh = True


def get(url, timeout=15, opener=urlopen):
    """Bounded GET; catch HTTP failures as evidence rather than crashing audit."""
    for attempt in range(2):
        try:
            request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xml"})
            with opener(request, timeout=timeout) as response:
                body = response.read(2_000_001)
                if len(body) > 2_000_000:
                    return {"status": response.status, "error": "BODY_TOO_LARGE"}
                return {
                    "status": response.status,
                    "final_url": response.geturl(),
                    "content_type": response.headers.get("Content-Type", ""),
                    "x_robots_tag": response.headers.get("X-Robots-Tag", ""),
                    "body": body.decode("utf-8", errors="replace"),
                }
        except HTTPError as error:
            if error.code in (429, 500, 502, 503, 504) and attempt == 0:
                time.sleep(1)
                continue
            return {"status": error.code, "error": "HTTP_" + str(error.code)}
        except (URLError, TimeoutError, OSError, ValueError) as error:
            if attempt == 0:
                time.sleep(1)
                continue
            return {"status": None, "error": type(error).__name__ + ": " + str(error)[:180]}
    return {"status": None, "error": "UNKNOWN_NETWORK_ERROR"}


def check_page(expected, origin=SITE, getter=get):
    path = urlsplit(expected).path
    actual = origin.rstrip("/") + path
    fetched = getter(actual)
    result = {"url": expected, "http_status": fetched.get("status"),
              "final_url": fetched.get("final_url"), "canonical": None,
              "noindex": False, "status": "PASS", "details": ""}
    if fetched.get("error"):
        result["status"], result["details"] = "HTTP_OR_FETCH_ERROR", fetched["error"]
        return result
    if fetched.get("status") != 200:
        result["status"] = "NOT_HTTP_200"
        return result
    if fetched.get("final_url") != actual:
        result["status"], result["details"] = "REDIRECTED", "Final URL differs from sitemap entry"
        return result
    if "text/html" not in fetched.get("content_type", "").lower():
        result["status"] = "NOT_HTML"
        return result
    parser = Metadata()
    parser.feed(fetched.get("body", ""))
    result["canonical"] = parser.canonicals[0] if len(parser.canonicals) == 1 else None
    robots = ",".join(parser.robots + [fetched.get("x_robots_tag", "").lower()])
    result["noindex"] = "noindex" in robots.replace(" ", "")
    if result["noindex"]:
        result["status"] = "NOINDEX"
    elif parser.refresh:
        result["status"] = "META_REFRESH"
    elif len(parser.canonicals) != 1 or parser.canonicals[0] != expected:
        result["status"] = "CANONICAL_MISMATCH"
    return result


def audit(root: Path, origin=SITE, getter=get, workers=8):
    _, _, _, entries = _entries(root)
    urls = [url for _, url in entries]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(check_page, url, origin, getter): url for url in urls}
        pages = [future.result() for future in as_completed(futures)]
    pages.sort(key=lambda row: row["url"])
    live_sitemap = getter(origin.rstrip("/") + "/sitemap.xml")
    parity = "UNVERIFIED"
    live_count = None
    if live_sitemap.get("status") == 200 and not live_sitemap.get("error"):
        try:
            xml = ET.fromstring(live_sitemap["body"])
            live_urls = [node.text.strip() for node in xml.iter(NS + "loc") if node.text]
            live_count = len(live_urls)
            parity = "MATCH" if set(live_urls) == set(urls) and len(live_urls) == len(urls) else "MISMATCH"
        except (ET.ParseError, ValueError):
            parity = "BAD_SITEMAP_XML"
    counts = {status: sum(p["status"] == status for p in pages)
              for status in sorted({p["status"] for p in pages})}
    return {
        "source": "Live HTTP probe versus locally generated public sitemap; NOT Google Search Console",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "git_sha": os.environ.get("GITHUB_SHA"),
        "expected_sitemap_urls": len(urls),
        "live_sitemap_urls": live_count,
        "sitemap_parity": parity,
        "live_sitemap_error": live_sitemap.get("error"),
        "statuses": counts,
        "google_indexed_count": None,
        "gsc_impressions": None,
        "gsc_clicks": None,
        "pages": pages,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("public"))
    parser.add_argument("--report", type=Path, default=Path("live-indexability-baseline.json"))
    parser.add_argument("--csv", type=Path, default=Path("live-indexability-baseline.csv"))
    parser.add_argument("--strict", action="store_true",
                        help="Nonzero exit on live problems; default is informational to avoid transient release failures")
    args = parser.parse_args()
    data = audit(args.root)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    with args.csv.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=(
            "url", "status", "http_status", "final_url", "canonical", "noindex", "details"))
        writer.writeheader()
        writer.writerows(data["pages"])
    print(json.dumps({key: data[key] for key in
                      ("expected_sitemap_urls", "live_sitemap_urls", "sitemap_parity", "statuses")}, indent=2))
    print("NOT_GSC: indexed_count, impressions and clicks remain unmeasured.")
    passed = data["statuses"].get("PASS", 0) == data["expected_sitemap_urls"]
    return 1 if args.strict and (not passed or data["sitemap_parity"] != "MATCH") else 0


if __name__ == "__main__":
    raise SystemExit(main())
