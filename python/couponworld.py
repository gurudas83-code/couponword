#!/usr/bin/env python3

"""
Coupon World Control Center v1

Current command:
    python python/couponworld.py check

Purpose:
- Validate coupons.json
- Verify product/page/sitemap counts
- Verify affiliate tags
- Detect duplicate products and links
- Detect missing required fields
- Detect stale or missing generated product pages
- Detect unwanted public-facing retailer wording
- Return PASS or FAIL with proper exit code

READ-ONLY:
This script does not modify the website.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parent.parent
COUPONS_FILE = ROOT / "coupons.json"
PRODUCTS_DIR = ROOT / "products"
SITEMAP_FILE = ROOT / "sitemap.xml"

CORRECT_AFFILIATE_TAG = "guru0906-21"
WRONG_AFFILIATE_TAGS = {"guru07cc-21"}

# Preserve previously published URLs when titles change.
LEGACY_PRODUCT_PATHS = {
    "17": "amazon-in-fashion-fest-17",
}

PUBLIC_FILES = [
    ROOT / "index.html",
    ROOT / "app.js",
    ROOT / "validator.html",
    ROOT / "global_coupon_website.html",
    ROOT / "templates" / "seo-template.html",
]

PUBLIC_DIRS = [
    ROOT / "products",
    ROOT / "seo",
]

UNWANTED_PUBLIC_TERMS = [
    "Amazon India",
    "Amazon IN",
    "View on Amazon",
    "Check latest price on Amazon",
    "Check price on Amazon",
    "latest Amazon deals",
]

LINK_KEYS = (
    "link",
    "url",
    "affiliate_link",
    "affiliate_url",
    "product_url",
)


def slugify(value: object, max_length: int = 70) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:max_length].rstrip("-")


def load_products() -> list[dict]:
    if not COUPONS_FILE.exists():
        raise FileNotFoundError("coupons.json not found")

    data = json.loads(COUPONS_FILE.read_text(encoding="utf-8"))

    if not isinstance(data, list):
        raise ValueError("coupons.json must contain a JSON list")

    invalid_rows = [
        index
        for index, item in enumerate(data, start=1)
        if not isinstance(item, dict)
    ]

    if invalid_rows:
        raise ValueError(
            "Non-object product rows found at positions: "
            + ", ".join(map(str, invalid_rows))
        )

    return data


def product_identity(product: dict, index: int) -> str:
    return str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or f"row-{index}"
    )


def product_link(product: dict) -> str:
    for key in LINK_KEYS:
        value = product.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    return ""


def page_directory(product: dict) -> Path:
    identity = str(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or ""
    )

    legacy_path = LEGACY_PRODUCT_PATHS.get(identity)

    if legacy_path:
        return PRODUCTS_DIR / legacy_path

    title_slug = slugify(product.get("title"))
    suffix = (
        product.get("asin")
        or product.get("id")
        or product.get("sl_no")
    )

    return PRODUCTS_DIR / f"{title_slug}-{slugify(suffix)}"


def sitemap_urls() -> list[str]:
    if not SITEMAP_FILE.exists():
        return []

    root = ET.parse(SITEMAP_FILE).getroot()

    return [
        node.text.strip()
        for node in root.iter()
        if node.tag.endswith("loc") and node.text
    ]


def public_files() -> list[Path]:
    found: list[Path] = []
    seen: set[Path] = set()

    for path in PUBLIC_FILES:
        if path.exists() and path.is_file():
            resolved = path.resolve()
            if resolved not in seen:
                found.append(path)
                seen.add(resolved)

    for directory in PUBLIC_DIRS:
        if not directory.exists():
            continue

        for path in sorted(directory.rglob("*")):
            if not path.is_file():
                continue

            if path.suffix.lower() not in {".html", ".js", ".json"}:
                continue

            resolved = path.resolve()

            if resolved not in seen:
                found.append(path)
                seen.add(resolved)

    return found


def print_section(title: str) -> None:
    print()
    print("=" * 68)
    print(title)
    print("=" * 68)


def check_command() -> int:
    failures: list[str] = []
    warnings: list[str] = []

    print_section("COUPON WORLD CONTROL CENTER — CHECK")

    try:
        products = load_products()
        print("PASS: coupons.json valid")
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}")
        return 1

    identities: list[str] = []
    links: list[str] = []

    missing_titles: list[str] = []
    missing_categories: list[str] = []
    missing_links: list[str] = []

    correct_tags: list[str] = []
    wrong_tags: list[tuple[str, str]] = []
    missing_tags: list[str] = []

    expected_pages: set[str] = set()

    for index, product in enumerate(products, start=1):
        identity = product_identity(product, index)
        identities.append(identity)

        title = product.get("title")
        category = product.get("category")
        link = product_link(product)

        if not title:
            missing_titles.append(identity)

        if not category:
            missing_categories.append(identity)

        if not link:
            missing_links.append(identity)
        else:
            links.append(link)

            tag = parse_qs(
                urlparse(link).query
            ).get("tag", [None])[0]

            if tag == CORRECT_AFFILIATE_TAG:
                correct_tags.append(identity)
            elif tag:
                wrong_tags.append((identity, tag))
            else:
                missing_tags.append(identity)

        expected_pages.add(
            str(page_directory(product).relative_to(ROOT))
        )

    duplicate_ids = [
        value
        for value, count in Counter(identities).items()
        if count > 1
    ]

    duplicate_links = [
        value
        for value, count in Counter(links).items()
        if count > 1
    ]

    actual_page_dirs = {
        str(path.parent.relative_to(ROOT))
        for path in PRODUCTS_DIR.rglob("index.html")
    } if PRODUCTS_DIR.exists() else set()

    missing_page_dirs = sorted(expected_pages - actual_page_dirs)
    stale_page_dirs = sorted(actual_page_dirs - expected_pages)

    urls = sitemap_urls()

    public_findings: list[tuple[str, int, str]] = []

    for path in public_files():
        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for line_number, line in enumerate(
            text.splitlines(),
            start=1,
        ):
            lowered = line.lower()

            for term in UNWANTED_PUBLIC_TERMS:
                if term.lower() in lowered:
                    public_findings.append(
                        (
                            str(path.relative_to(ROOT)),
                            line_number,
                            term,
                        )
                    )
                    break

    print(f"Products                 : {len(products)}")
    print(f"Product pages            : {len(actual_page_dirs)}")
    print(f"Sitemap URLs             : {len(urls)}")
    print(f"Correct affiliate tags   : {len(correct_tags)}")
    print(f"Wrong affiliate tags     : {len(wrong_tags)}")
    print(f"Missing affiliate tags   : {len(missing_tags)}")
    print(f"Duplicate IDs            : {len(duplicate_ids)}")
    print(f"Duplicate links          : {len(duplicate_links)}")
    print(f"Missing titles           : {len(missing_titles)}")
    print(f"Missing categories       : {len(missing_categories)}")
    print(f"Missing links            : {len(missing_links)}")
    print(f"Missing product pages    : {len(missing_page_dirs)}")
    print(f"Stale product pages      : {len(stale_page_dirs)}")
    print(f"Public wording findings  : {len(public_findings)}")

    expected_sitemap_count = len(products) + 1

    if len(actual_page_dirs) != len(products):
        failures.append(
            "Product page count does not match product count"
        )

    if len(urls) != expected_sitemap_count:
        failures.append(
            f"Sitemap should contain {expected_sitemap_count} URLs"
        )

    if wrong_tags:
        failures.append("Wrong affiliate tags found")

    if missing_tags:
        failures.append("Missing affiliate tags found")

    if duplicate_ids:
        failures.append("Duplicate product IDs found")

    if duplicate_links:
        failures.append("Duplicate product links found")

    if missing_titles:
        failures.append("Products missing titles")

    if missing_categories:
        failures.append("Products missing categories")

    if missing_links:
        failures.append("Products missing links")

    if missing_page_dirs:
        failures.append("Expected product pages are missing")

    if stale_page_dirs:
        failures.append("Stale product pages found")

    if public_findings:
        failures.append(
            "Unwanted public-facing retailer wording found"
        )

    wrong_tag_files: list[str] = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if ".git" in path.parts:
            continue

        # Do not report the checker’s own blocked-tag definitions.
        if path.resolve() == Path(__file__).resolve():
            continue

        if any(
            folder in path.parts
            for folder in (
                ".branding_backups",
                ".compliance_backups",
            )
        ):
            continue

        if path.suffix.lower() not in {
            ".py",
            ".json",
            ".html",
            ".js",
            ".md",
            ".txt",
        }:
            continue

        text = path.read_text(
            encoding="utf-8",
            errors="ignore",
        )

        for wrong_tag in WRONG_AFFILIATE_TAGS:
            if wrong_tag in text:
                wrong_tag_files.append(
                    str(path.relative_to(ROOT))
                )

    if wrong_tag_files:
        failures.append(
            "Old wrong affiliate tag still exists in repository"
        )

    if failures:
        print_section("FAILURES")

        for item in failures:
            print("FAIL:", item)

        if wrong_tags:
            print()
            print("Wrong product tags:")
            for identity, tag in wrong_tags:
                print(f"  {identity}: {tag}")

        if missing_tags:
            print()
            print("Missing product tags:")
            for identity in missing_tags:
                print(f"  {identity}")

        if missing_page_dirs:
            print()
            print("Missing pages:")
            for path in missing_page_dirs[:20]:
                print(f"  {path}")

        if stale_page_dirs:
            print()
            print("Stale pages:")
            for path in stale_page_dirs[:20]:
                print(f"  {path}")

        if public_findings:
            print()
            print("Public wording findings:")
            for file_name, line_number, term in public_findings:
                print(
                    f"  {file_name}:{line_number}: {term}"
                )

        if wrong_tag_files:
            print()
            print("Files containing old wrong tag:")
            for file_name in sorted(set(wrong_tag_files)):
                print(f"  {file_name}")

        print_section("SITE STATUS: FAIL")
        return 1

    if warnings:
        print_section("WARNINGS")
        for item in warnings:
            print("WARNING:", item)

    print_section("SITE STATUS: PASS")
    print("Safe to continue with the next controlled step.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Coupon World Control Center"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "check",
        help="Run read-only foundation checks",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        return check_command()

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
