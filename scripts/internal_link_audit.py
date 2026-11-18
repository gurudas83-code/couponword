#!/usr/bin/env python3
"""Audit genuine homepage-to-page HTML link paths in the published Pages artifact.

Only <a href> navigation counts. A sitemap alone does not count as an internal
link, and this report is NOT Google Search Console indexing evidence.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from html.parser import HTMLParser
import json
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree as ET

SITE = "https://coupon-world.in"
HOST = "coupon-world.in"
PRIORITY = (
    "/seo/phones-under-10000.html",
    "/seo/phones-under-15000.html",
    "/seo/phones-under-20000.html",
    "/seo/camera-phone-buying-guide.html",
    "/seo/gaming-phone-buying-guide.html",
    "/seo/5g-phone-india-checklist.html",
    "/compare/",
    "/phones/",
    "/guides/phone-budget-guides/",
)


class AnchorLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        props = dict(attrs)
        if "nofollow" in str(props.get("rel") or "").lower().split():
            return
        href = props.get("href")
        if isinstance(href, str) and href.strip():
            self.hrefs.append(href.strip())


def route_for_file(root: Path, path: Path) -> str:
    relative = path.relative_to(root).as_posix()
    if relative == "index.html":
        return "/"
    if relative.endswith("/index.html"):
        return "/" + relative[:-len("index.html")]
    return "/" + relative


def page_routes(root: Path) -> dict[str, Path]:
    return {route_for_file(root, path): path
            for path in root.rglob("*.html") if path.is_file()}


def internal_links(route: str, page: Path) -> set[str]:
    parser = AnchorLinks()
    parser.feed(page.read_text(encoding="utf-8", errors="replace"))
    result = set()
    for href in parser.hrefs:
        try:
            parsed = urlsplit(urljoin(SITE + route, href))
        except ValueError:
            continue
        if parsed.scheme != "https" or parsed.hostname != HOST:
            continue
        target = unquote(parsed.path)
        if target.startswith("/"):
            result.add(target)
    return result


def audit(root: Path) -> dict:
    root = root.resolve()
    routes = page_routes(root)
    if "/" not in routes:
        raise ValueError("Homepage missing from artifact")
    target_urls = {
        (item.text or "").strip()
        for item in ET.parse(root / "sitemap.xml").getroot().iter()
        if item.tag.endswith("}loc")
    }
    sitemap_routes = set()
    for url in target_urls:
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != HOST:
            raise ValueError("Unexpected sitemap URL: " + url)
        sitemap_routes.add(unquote(parsed.path))
    graph = {route: internal_links(route, page) for route, page in routes.items()}
    depth = {"/": 0}
    queue = deque(["/"])
    while queue:
        current = queue.popleft()
        for dest in graph[current]:
            if dest in routes and dest not in depth:
                depth[dest] = depth[current] + 1
                queue.append(dest)
    missing_pages = sorted(sitemap_routes - set(routes))
    unreachable = sorted(sitemap_routes - set(depth))
    priority_depth = {route: depth.get(route) for route in PRIORITY}
    histogram = dict(sorted(Counter(depth[route] for route in sitemap_routes if route in depth).items()))
    return {
        "mode": "STATIC_HTML_DISCOVERY_PATHS_NOT_GOOGLE_INDEXING",
        "html_pages_in_artifact": len(routes),
        "sitemap_indexable_url_count": len(sitemap_routes),
        "sitemap_urls_reachable_from_home": len(sitemap_routes & set(depth)),
        "sitemap_urls_without_homepage_link_path": len(unreachable),
        "unreachable_urls": [SITE + route for route in unreachable],
        "missing_sitemap_html_pages": [SITE + route for route in missing_pages],
        "priority_guide_click_depth": priority_depth,
        "reachable_sitemap_depth_histogram": histogram,
        "google_indexed_count": None,
        "note": "Static HTML <a href> link reachability only. Google may still crawl, index, or decline URLs independently.",
    }


def verify_priority(report: dict) -> None:
    bad = {route: d for route, d in report["priority_guide_click_depth"].items()
           if d is None or d > 3}
    if bad:
        raise ValueError("Priority guides have no short HTML crawl path: " + repr(bad))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = audit(args.root)
    print(json.dumps({
        "sitemap_urls": result["sitemap_indexable_url_count"],
        "reachable_via_html": result["sitemap_urls_reachable_from_home"],
        "unreachable_count": result["sitemap_urls_without_homepage_link_path"],
        "sample_unreachable": result["unreachable_urls"][:30],
        "priority_depth": result["priority_guide_click_depth"],
    }, indent=2))
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    verify_priority(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
