#!/usr/bin/env python3

"""
Coupon World Google Discovery Auditor v1

READ-ONLY:
- Does not modify website files
- Does not access Google Search Console
- Audits local generated site files only
"""

from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent.parent
SITE_HOST = "coupon-world.in"
SITE_URL = f"https://{SITE_HOST}"

ROBOTS_FILE = ROOT / "robots.txt"
SITEMAP_FILE = ROOT / "sitemap.xml"

HTML_FILES = [
    ROOT / "index.html",
    *sorted((ROOT / "products").glob("*/index.html")),
    *sorted((ROOT / "guides").rglob("index.html")),
    *sorted((ROOT / "seo").glob("*.html")),
]

HTML_FILES = [
    path
    for path in HTML_FILES
    if path.exists()
]


def clean(value: object) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or ""),
    ).strip()


def page_url(path: Path) -> str:
    relative = path.relative_to(ROOT)

    if relative.as_posix() == "index.html":
        return f"{SITE_URL}/"

    if relative.name == "index.html":
        relative = relative.parent

        return (
            f"{SITE_URL}/"
            f"{relative.as_posix().strip('/')}/"
        )

    return (
        f"{SITE_URL}/"
        f"{relative.as_posix()}"
    )


def extract_title(text: str) -> str:
    match = re.search(
        r"<title[^>]*>(.*?)</title>",
        text,
        flags=re.I | re.S,
    )

    return clean(match.group(1)) if match else ""


def extract_description(text: str) -> str:
    patterns = [
        (
            r'<meta[^>]+name=["\']description["\']'
            r'[^>]+content=["\'](.*?)["\']'
        ),
        (
            r'<meta[^>]+content=["\'](.*?)["\']'
            r'[^>]+name=["\']description["\']'
        ),
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.I | re.S,
        )

        if match:
            return clean(match.group(1))

    return ""


def extract_canonical(text: str) -> str:
    patterns = [
        (
            r'<link[^>]+rel=["\']canonical["\']'
            r'[^>]+href=["\']([^"\']+)["\']'
        ),
        (
            r'<link[^>]+href=["\']([^"\']+)["\']'
            r'[^>]+rel=["\']canonical["\']'
        ),
    ]

    for pattern in patterns:
        match = re.search(
            pattern,
            text,
            flags=re.I,
        )

        if match:
            return clean(match.group(1))

    return ""


def has_h1(text: str) -> bool:
    return bool(
        re.search(
            r"<h1\b[^>]*>.*?</h1>",
            text,
            flags=re.I | re.S,
        )
    )


def is_noindex(text: str) -> bool:
    return bool(
        re.search(
            r'<meta[^>]+name=["\']robots["\']'
            r'[^>]+content=["\'][^"\']*noindex',
            text,
            flags=re.I,
        )
    )


def has_schema(text: str) -> bool:
    return bool(
        re.search(
            r'<script[^>]+type=["\']application/ld\+json["\']',
            text,
            flags=re.I,
        )
    )


def has_disclosure(text: str) -> bool:
    return (
        "As an Amazon Associate I earn from qualifying purchases."
        in text
    )


def internal_href_to_url(
    current_path: Path,
    href: str,
) -> str:
    href = clean(href)

    if not href:
        return ""

    if href.startswith(
        (
            "#",
            "mailto:",
            "tel:",
            "javascript:",
            "data:",
        )
    ):
        return ""

    parsed = urlparse(href)
    path_part = parsed.path or ""

    ignored_extensions = {
        ".css",
        ".js",
        ".json",
        ".xml",
        ".txt",
        ".ico",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".avif",
        ".woff",
        ".woff2",
        ".ttf",
        ".map",
        ".pdf",
    }

    if Path(path_part).suffix.lower() in ignored_extensions:
        return ""

    if parsed.scheme in {"http", "https"}:
        if parsed.netloc != SITE_HOST:
            return ""

        if path_part in {"", "/"}:
            return f"{SITE_URL}/"

        return (
            f"{SITE_URL}/"
            f"{path_part.strip('/')}"
            + (
                "/"
                if path_part.endswith("/")
                else ""
            )
        )

    if href.startswith("/"):
        if path_part in {"", "/"}:
            return f"{SITE_URL}/"

        return (
            f"{SITE_URL}/"
            f"{path_part.strip('/')}"
            + (
                "/"
                if path_part.endswith("/")
                else ""
            )
        )

    current_dir = current_path.parent

    target = (
        current_dir / path_part
    ).resolve()

    root_resolved = ROOT.resolve()

    try:
        relative = target.relative_to(
            root_resolved
        )
    except ValueError:
        return ""

    if target == root_resolved:
        return f"{SITE_URL}/"

    if relative.name == "index.html":
        relative = relative.parent

        if relative.as_posix() in {"", "."}:
            return f"{SITE_URL}/"

        return (
            f"{SITE_URL}/"
            f"{relative.as_posix().strip('/')}/"
        )

    if target.is_dir():
        if relative.as_posix() in {"", "."}:
            return f"{SITE_URL}/"

        return (
            f"{SITE_URL}/"
            f"{relative.as_posix().strip('/')}/"
        )

    return (
        f"{SITE_URL}/"
        f"{relative.as_posix().strip('/')}"
    )


def load_sitemap() -> tuple[list[str], list[str]]:
    if not SITEMAP_FILE.exists():
        return [], ["sitemap.xml missing"]

    try:
        root = ET.parse(
            SITEMAP_FILE
        ).getroot()
    except ET.ParseError as exc:
        return [], [
            f"sitemap.xml invalid XML: {exc}"
        ]

    urls = [
        clean(node.text)
        for node in root.iter()
        if node.tag.endswith("loc")
        and clean(node.text)
    ]

    errors = []

    if len(urls) != len(set(urls)):
        errors.append(
            "Duplicate URLs found in sitemap"
        )

    for url in urls:
        parsed = urlparse(url)

        if parsed.scheme != "https":
            errors.append(
                f"Non-HTTPS sitemap URL: {url}"
            )

        if parsed.netloc != SITE_HOST:
            errors.append(
                f"Wrong sitemap host: {url}"
            )

    return urls, errors


def robots_audit() -> tuple[bool, list[str]]:
    if not ROBOTS_FILE.exists():
        return False, [
            "robots.txt missing"
        ]

    text = ROBOTS_FILE.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    findings = []

    if re.search(
        r"Disallow:\s*/\s*$",
        text,
        flags=re.I | re.M,
    ):
        findings.append(
            "robots.txt blocks the entire site"
        )

    sitemap_line = re.search(
        r"^\s*Sitemap:\s*(\S+)",
        text,
        flags=re.I | re.M,
    )

    if not sitemap_line:
        findings.append(
            "robots.txt has no Sitemap directive"
        )
    else:
        sitemap_url = sitemap_line.group(1)

        if sitemap_url != f"{SITE_URL}/sitemap.xml":
            findings.append(
                "robots.txt sitemap URL is unexpected: "
                f"{sitemap_url}"
            )

    return not findings, findings


def main() -> int:
    print("=" * 78)
    print("COUPON WORLD — GOOGLE DISCOVERY AUDIT")
    print("=" * 78)

    sitemap_urls, sitemap_errors = load_sitemap()
    sitemap_set = set(sitemap_urls)

    robots_pass, robots_findings = robots_audit()

    page_records = []
    titles = Counter()
    descriptions = Counter()

    expected_urls = set()
    outgoing_links: dict[str, set[str]] = {}

    for path in HTML_FILES:
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        url = page_url(path)
        expected_urls.add(url)

        title = extract_title(text)
        description = extract_description(text)
        canonical = extract_canonical(text)

        if title:
            titles[title] += 1

        if description:
            descriptions[description] += 1

        internal_links = set()

        for href in re.findall(
            r'href=["\']([^"\']+)["\']',
            text,
            flags=re.I,
        ):
            linked_url = internal_href_to_url(
                path,
                href,
            )

            if linked_url:
                internal_links.add(linked_url)

        outgoing_links[url] = internal_links

        page_records.append(
            {
                "path": path,
                "url": url,
                "title": title,
                "description": description,
                "canonical": canonical,
                "h1": has_h1(text),
                "noindex": is_noindex(text),
                "schema": has_schema(text),
                "disclosure": has_disclosure(text),
                "links": internal_links,
            }
        )

    duplicate_titles = {
        value: count
        for value, count in titles.items()
        if count > 1
    }

    duplicate_descriptions = {
        value: count
        for value, count in descriptions.items()
        if count > 1
    }

    missing_titles = [
        record
        for record in page_records
        if not record["title"]
    ]

    missing_descriptions = [
        record
        for record in page_records
        if not record["description"]
    ]

    missing_canonicals = [
        record
        for record in page_records
        if not record["canonical"]
    ]

    canonical_mismatches = [
        record
        for record in page_records
        if (
            record["canonical"]
            and record["canonical"] != record["url"]
        )
    ]

    missing_h1 = [
        record
        for record in page_records
        if not record["h1"]
    ]

    noindex_pages = [
        record
        for record in page_records
        if record["noindex"]
    ]

    missing_schema = [
        record
        for record in page_records
        if not record["schema"]
    ]

    missing_disclosure = [
        record
        for record in page_records
        if not record["disclosure"]
    ]

    missing_from_sitemap = sorted(
        expected_urls - sitemap_set
    )

    unknown_sitemap_urls = sorted(
        sitemap_set - expected_urls
    )

    incoming_counts = Counter()

    for source_url, links in outgoing_links.items():
        for target_url in links:
            if target_url in expected_urls:
                incoming_counts[target_url] += 1

    homepage_url = f"{SITE_URL}/"

    orphan_pages = sorted(
        url
        for url in expected_urls
        if (
            url != homepage_url
            and incoming_counts[url] == 0
        )
    )

    broken_internal_links = []

    for source_url, links in outgoing_links.items():
        for target_url in sorted(links):
            if target_url not in expected_urls:
                broken_internal_links.append(
                    (
                        source_url,
                        target_url,
                    )
                )

    print()
    print("SITE INVENTORY")
    print("-" * 78)
    print("HTML pages scanned        :", len(page_records))
    print("Expected indexable URLs   :", len(expected_urls))
    print("Sitemap URLs              :", len(sitemap_urls))

    print()
    print("ROBOTS AND SITEMAP")
    print("-" * 78)
    print(
        "robots.txt               :",
        "PASS" if robots_pass else "REVIEW",
    )
    print("Sitemap errors            :", len(sitemap_errors))
    print("Missing from sitemap      :", len(missing_from_sitemap))
    print("Unknown sitemap URLs      :", len(unknown_sitemap_urls))

    print()
    print("PAGE SEO")
    print("-" * 78)
    print("Missing titles            :", len(missing_titles))
    print("Missing descriptions      :", len(missing_descriptions))
    print("Missing canonicals        :", len(missing_canonicals))
    print("Canonical mismatches      :", len(canonical_mismatches))
    print("Missing H1                :", len(missing_h1))
    print("Duplicate titles          :", len(duplicate_titles))
    print("Duplicate descriptions    :", len(duplicate_descriptions))
    print("Noindex pages             :", len(noindex_pages))

    print()
    print("DISCOVERY STRUCTURE")
    print("-" * 78)
    print("Orphan pages              :", len(orphan_pages))
    print("Broken internal links     :", len(broken_internal_links))
    print("Pages missing schema      :", len(missing_schema))
    print("Pages missing disclosure  :", len(missing_disclosure))

    penalties = {
        "robots": 15 if not robots_pass else 0,
        "sitemap": min(
            20,
            (
                len(sitemap_errors)
                + len(missing_from_sitemap)
                + len(unknown_sitemap_urls)
            ) * 3,
        ),
        "metadata": min(
            20,
            (
                len(missing_titles)
                + len(missing_descriptions)
                + len(missing_canonicals)
                + len(missing_h1)
                + len(canonical_mismatches)
            ),
        ),
        "duplicates": min(
            10,
            len(duplicate_titles)
            + len(duplicate_descriptions),
        ),
        "links": min(
            20,
            len(orphan_pages)
            + len(broken_internal_links),
        ),
        "schema": min(
            10,
            len(missing_schema) // 10,
        ),
        "disclosure": min(
            5,
            len(missing_disclosure),
        ),
    }

    score = max(
        0,
        100 - sum(penalties.values()),
    )

    print()
    print("=" * 78)
    print("DISCOVERY SCORE")
    print("=" * 78)
    print(f"{score} / 100")

    review_items = []

    if not robots_pass:
        review_items.append(
            "Fix robots.txt before requesting indexing."
        )

    if sitemap_errors:
        review_items.append(
            "Fix sitemap formatting, HTTPS or host issues."
        )

    if missing_from_sitemap:
        review_items.append(
            "Add all intended indexable pages to sitemap."
        )

    if unknown_sitemap_urls:
        review_items.append(
            "Remove stale or unknown URLs from sitemap."
        )

    if canonical_mismatches:
        review_items.append(
            "Correct canonical URLs that do not match page URLs."
        )

    if broken_internal_links:
        review_items.append(
            "Fix broken internal links."
        )

    if orphan_pages:
        review_items.append(
            "Add internal links to orphan pages."
        )

    if missing_schema:
        review_items.append(
            "Add suitable structured data gradually to important pages."
        )

    if not review_items:
        review_items.append(
            "Technical discovery foundation is ready; verify deployment "
            "and submit the sitemap in search-engine webmaster tools."
        )

    print()
    print("NEXT ACTIONS")
    print("-" * 78)

    for number, item in enumerate(
        review_items,
        start=1,
    ):
        print(f"{number}. {item}")

    def show_records(
        heading: str,
        records: list[dict],
        limit: int = 10,
    ) -> None:
        if not records:
            return

        print()
        print(heading)
        print("-" * 78)

        for record in records[:limit]:
            print(record["path"])

    show_records(
        "CANONICAL MISMATCH SAMPLE",
        canonical_mismatches,
    )

    show_records(
        "MISSING SCHEMA SAMPLE",
        missing_schema,
    )

    if robots_findings:
        print()
        print("ROBOTS FINDINGS")
        print("-" * 78)

        for finding in robots_findings:
            print(finding)

    if sitemap_errors:
        print()
        print("SITEMAP FINDINGS")
        print("-" * 78)

        for finding in sitemap_errors[:15]:
            print(finding)

    if missing_from_sitemap:
        print()
        print("MISSING FROM SITEMAP")
        print("-" * 78)

        for url in missing_from_sitemap[:15]:
            print(url)

    if unknown_sitemap_urls:
        print()
        print("UNKNOWN SITEMAP URLS")
        print("-" * 78)

        for url in unknown_sitemap_urls[:15]:
            print(url)

    if orphan_pages:
        print()
        print("ORPHAN PAGE SAMPLE")
        print("-" * 78)

        for url in orphan_pages[:15]:
            print(url)

    if broken_internal_links:
        print()
        print("BROKEN INTERNAL LINK SAMPLE")
        print("-" * 78)

        for source, target in broken_internal_links[:15]:
            print(f"{source} -> {target}")

    critical_failures = (
        not robots_pass
        or bool(sitemap_errors)
        or bool(missing_from_sitemap)
        or bool(unknown_sitemap_urls)
        or bool(canonical_mismatches)
        or bool(broken_internal_links)
    )

    print()
    print("=" * 78)

    if critical_failures:
        print("DISCOVERY AUDIT STATUS: REVIEW")
    else:
        print("DISCOVERY AUDIT STATUS: PASS")

    print("FILES MODIFIED: NO")
    print("=" * 78)

    return 1 if critical_failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
