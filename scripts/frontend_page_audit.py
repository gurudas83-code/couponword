#!/usr/bin/env python3
"""Read-only, per-page audit of the EXACT generated public HTML artifact.

This is a static evidence report, not a browser render, legal opinion,
Google Search Console status or guarantee that a page is indexed.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from xml.etree import ElementTree as ET

SITE = "https://coupon-world.in"
NS = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title_parts = []
        self.in_title = False
        self.in_suppressed = 0
        self.description = []
        self.canonical = []
        self.robots = []
        self.refresh = False
        self.h1 = 0
        self.main = 0
        self.images = []
        self.anchors = []
        self.text_parts = []
        self.structured_blocks = 0

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        line = self.getpos()[0]
        if tag in ("script", "style"):
            self.in_suppressed += 1
        if tag == "title":
            self.in_title = True
        if tag == "h1":
            self.h1 += 1
        if tag == "main":
            self.main += 1
        if tag == "meta":
            if (props.get("name") or "").lower() == "description":
                self.description.append((props.get("content") or "", line))
            if (props.get("name") or "").lower() in ("robots", "googlebot"):
                self.robots.append((props.get("content") or "", line))
            if (props.get("http-equiv") or "").lower() == "refresh":
                self.refresh = True
        if tag == "link" and "canonical" in (props.get("rel") or "").lower().split():
            self.canonical.append((props.get("href") or "", line))
        if tag == "img":
            self.images.append({"line": line, "src": props.get("src"),
                                "has_alt_attribute": "alt" in props})
        if tag == "a":
            self.anchors.append({"line": line, "href": props.get("href") or "",
                                 "target": props.get("target") or "",
                                 "rel": (props.get("rel") or "").lower()})
        if tag == "script" and (props.get("type") or "").lower() == "application/ld+json":
            self.structured_blocks += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style") and self.in_suppressed:
            self.in_suppressed -= 1
        if tag == "title":
            self.in_title = False

    def handle_data(self, text):
        if self.in_title:
            self.title_parts.append(text)
        if not self.in_suppressed and not self.in_title:
            self.text_parts.append(text)


def public_path(rel):
    if rel == "index.html":
        return "/"
    if rel.endswith("/index.html"):
        return "/" + rel[:-len("index.html")]
    return "/" + rel


def issue(level, code, message, line=None):
    return {"severity": level, "code": code, "message": message, "line": line}


def examine(file, root, indexed_urls):
    rel = file.relative_to(root).as_posix()
    route = public_path(rel)
    url = SITE + route
    parser = PageParser()
    try:
        parser.feed(file.read_text(encoding="utf-8"))
        parser.close()
    except (OSError, UnicodeError, ValueError) as exc:
        return {"path": rel, "url": url, "issues": [issue("error", "HTML_PARSE", str(exc))]}
    text = " ".join(parser.text_parts)
    words = len(text.split())
    title = " ".join(" ".join(parser.title_parts).split())
    robots = ",".join(x[0].lower().replace(" ", "") for x in parser.robots)
    noindex = "noindex" in robots
    special = rel in ("404.html", "google54faf165096b5622.html")
    eligible = not special and not noindex and not parser.refresh
    problems = []
    if eligible:
        if not title:
            problems.append(issue("error", "TITLE_MISSING", "Indexable page has no title"))
        if len(parser.description) != 1 or not parser.description[0][0].strip():
            problems.append(issue("error", "DESCRIPTION_MISSING_OR_MULTIPLE",
                                  "Indexable page needs exactly one nonempty meta description"))
        if len(parser.canonical) != 1:
            problems.append(issue("error", "CANONICAL_MISSING_OR_MULTIPLE",
                                  "Expected exactly one canonical link"))
        elif parser.canonical[0][0] != url:
            problems.append(issue("error", "CANONICAL_NOT_SELF", "Canonical does not equal page URL",
                                  parser.canonical[0][1]))
        if parser.h1 != 1:
            problems.append(issue("warning", "H1_COUNT", "Expected one clear main H1; found " + str(parser.h1)))
        if parser.main < 1:
            problems.append(issue("warning", "MAIN_LANDMARK", "No HTML main landmark"))
        if words < 120:
            problems.append(issue("review", "SHORT_VISIBLE_CONTENT",
                                  "Fewer than 120 text words; manually review usefulness, not an automatic penalty"))
        if url not in indexed_urls:
            problems.append(issue("warning", "INDEXABLE_NOT_IN_SITEMAP",
                                  "Indexable HTML URL not present in generated sitemap"))
    if url in indexed_urls and (noindex or parser.refresh):
        problems.append(issue("error", "SITEMAP_INDEX_CONFLICT",
                              "Noindex or redirect page is included in the indexable sitemap"))
    if parser.refresh and not noindex:
        problems.append(issue("review", "META_REFRESH_REVIEW",
                              "Redirect-like meta refresh: verify intended canonical and legacy routing"))
    for image in parser.images:
        if not image["has_alt_attribute"]:
            problems.append(issue("warning", "IMAGE_MISSING_ALT",
                                  "Image lacks alt attribute (decorative image may use alt empty)",
                                  image["line"]))
    for anchor in parser.anchors:
        href = anchor["href"].strip()
        if href.lower().startswith(("javascript:", "data:")):
            problems.append(issue("error", "UNSAFE_LINK_SCHEME", "Unsafe href scheme", anchor["line"]))
        if anchor["target"] == "_blank" and not {"noopener", "noreferrer"}.issubset(set(anchor["rel"].split())):
            problems.append(issue("warning", "EXTERNAL_TAB_REL", "Target blank needs rel noopener noreferrer",
                                  anchor["line"]))
        parsed = urlsplit(href)
        if parsed.scheme == "https" and parsed.hostname in ("amazon.in", "www.amazon.in"):
            if not parse_qs(parsed.query).get("tag"):
                problems.append(issue("warning", "AMAZON_TAG_MISSING", "Amazon outbound link has no tag",
                                      anchor["line"]))
            if "sponsored" not in anchor["rel"].split():
                problems.append(issue("warning", "AMAZON_SPONSORED_REL", "Amazon affiliate link needs sponsored rel",
                                      anchor["line"]))
    return {"path": rel, "url": url, "indexable_candidate": eligible,
            "in_generated_sitemap": url in indexed_urls, "robots": robots,
            "title": title, "meta_description": parser.description[0][0] if parser.description else None,
            "canonical": parser.canonical[0][0] if len(parser.canonical) == 1 else None,
            "h1_count": parser.h1, "main_landmarks": parser.main,
            "visible_word_count": words, "images": len(parser.images),
            "anchors": len(parser.anchors), "jsonld_blocks": parser.structured_blocks,
            "issues": problems}


def audit(root: Path):
    sitemap = root / "sitemap.xml"
    indexed = set()
    for node in ET.parse(sitemap).getroot().iter(NS + "loc"):
        if node.text:
            indexed.add(node.text.strip())
    pages = [examine(file, root, indexed) for file in sorted(root.rglob("*.html"))]
    titles = defaultdict(list)
    for page in pages:
        if page.get("indexable_candidate") and page.get("title"):
            titles[page["title"].casefold()].append(page)
    for duplicates in titles.values():
        if len(duplicates) > 1:
            for page in duplicates:
                page["issues"].append(issue("review", "DUPLICATE_TITLE",
                                            "Same title is shared by " + str(len(duplicates)) + " indexable candidates"))
    counts = Counter(problem["severity"] for page in pages for problem in page["issues"])
    return {"source": "generated public HTML only; not GSC indexing or visual browser certification",
            "pages_scanned": len(pages), "indexable_candidates": sum(bool(p.get("indexable_candidate")) for p in pages),
            "sitemap_entries": len(indexed), "issue_count": sum(counts.values()),
            "issues_by_severity": dict(counts), "pages": pages}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("public"))
    parser.add_argument("--out", type=Path, default=Path("frontend-page-audit.json"))
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error("generated public directory does not exist")
    result = audit(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("A-to-Z generated HTML audit:",
          result["pages_scanned"], "pages;",
          result["sitemap_entries"], "sitemap URLs;",
          result["issue_count"], "review findings")
    for page in result["pages"]:
        # Surface all warnings and review requests in CI, not just fatal errors.
        # A review finding is an inspection prompt, NOT evidence of a Google
        # penalty, manual action or indexed-status report.
        findings = [item for item in page["issues"] if item["severity"] in ("error", "warning", "review")]
        if findings:
            print("PAGE_AUDIT_FINDING", page["path"], [(item["severity"], item["code"], item["line"]) for item in findings])
    return 0  # report-only until findings are adjudicated; existing release gates remain fail-closed


if __name__ == "__main__":
    raise SystemExit(main())
