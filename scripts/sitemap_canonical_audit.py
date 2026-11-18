#!/usr/bin/env python3
"""Reconcile the generated public sitemap with real indexable HTML pages.

Do not mistake this for a Google indexing report. This operates on the
generated static artifact, not the checked-in historical source sitemap.
"""
from __future__ import annotations

from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
from xml.etree import ElementTree as ET

HOST = "coupon-world.in"
SITE = "https://" + HOST
NS = "http://www.sitemaps.org/schemas/sitemap/0.9"


class PageMetadata(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.canonicals = []
        self.robots = []
        self.redirect = False

    def handle_starttag(self, tag, attrs):
        attributes = {str(k).lower(): (v or "") for k, v in attrs}
        if tag == "link" and "canonical" in attributes.get("rel", "").lower().split():
            self.canonicals.append(attributes.get("href", "").strip())
        if tag == "meta":
            if attributes.get("name", "").lower() in ("robots", "googlebot"):
                self.robots.append(attributes.get("content", "").lower())
            if attributes.get("http-equiv", "").lower() == "refresh":
                self.redirect = True


def public_page(root: Path, url: str) -> Path:
    parsed = urlsplit(url)
    if (parsed.scheme != "https" or parsed.netloc != HOST
            or parsed.query or parsed.fragment or not parsed.path.startswith("/")):
        raise ValueError("Noncanonical sitemap URL: " + url)
    path = unquote(parsed.path)
    parts = path.split("/")
    if any(part in (".", "..") for part in parts):
        raise ValueError("Unsafe sitemap URL: " + url)
    relative = path.lstrip("/")
    target = root / relative
    if not relative or path.endswith("/"):
        target = target / "index.html"
    root = root.resolve()
    target = target.resolve()
    if not target.is_relative_to(root):
        raise ValueError("Sitemap path outside public root: " + url)
    return target


def inspect_url(root: Path, url: str) -> str:
    page = public_page(root, url)
    if not page.is_file():
        return "MISSING_PAGE"
    info = PageMetadata()
    info.feed(page.read_text(encoding="utf-8"))
    if any("noindex" in value.split(",") or "noindex" in value.replace(" ", "").split(",")
           for value in info.robots):
        return "NOINDEX"
    if info.redirect:
        return "META_REDIRECT"
    if len(info.canonicals) != 1:
        return "MISSING_OR_MULTIPLE_CANONICALS"
    if info.canonicals[0] != url:
        return "ALTERNATE_CANONICAL"
    return "OK"


def _entries(root: Path):
    path = root / "sitemap.xml"
    tree = ET.parse(path)
    outer = tree.getroot()
    if outer.tag != "{" + NS + "}urlset":
        raise ValueError("Not a sitemap urlset")
    entries = []
    for node in outer.findall("{" + NS + "}url"):
        loc = node.find("{" + NS + "}loc")
        if loc is None or not loc.text:
            raise ValueError("Empty sitemap loc")
        entries.append((node, loc.text.strip()))
    if len({url for _, url in entries}) != len(entries):
        raise ValueError("Duplicate sitemap URLs")
    return path, tree, outer, entries


def validate(root: Path) -> dict:
    _, _, _, entries = _entries(root)
    bad = [(url, inspect_url(root, url)) for _, url in entries
           if inspect_url(root, url) != "OK"]
    return {"count": len(entries), "problems": bad}


def reconcile(root: Path) -> dict:
    """Remove stale source-sitemap URLs, never alter the HTML destinations."""
    root = root.resolve()
    path, tree, outer, entries = _entries(root)
    reasons = Counter()
    samples = []
    for node, url in entries:
        result = inspect_url(root, url)
        if result != "OK":
            outer.remove(node)
            reasons[result] += 1
            if len(samples) < 24:
                samples.append({"url": url, "reason": result})
    remaining = [n.text for n in outer.iter("{" + NS + "}loc") if n.text]
    priority = [SITE + route for route in ("/", "/phones/", "/compare/", "/hi/compare/")]
    if any(url not in remaining for url in priority):
        raise ValueError("A priority discovery page is not indexable in the sitemap")
    if not remaining:
        raise ValueError("Sitemap would be empty")
    tree.write(path, encoding="utf-8", xml_declaration=True)
    return {
        "mode": "GENERATED_SITEMAP_TECHNICAL_CLEANUP_NOT_GSC",
        "retained": len(remaining),
        "removed": sum(reasons.values()),
        "reasons": dict(reasons),
        "samples": samples,
        "google_indexed_page_count": None,
    }
