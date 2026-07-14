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
import subprocess
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



def run_command(command: list[str]) -> int:
    print()
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
    )

    return result.returncode


def validate_build_source() -> int:
    print_section("BUILD SOURCE VALIDATION")

    try:
        products = load_products()
    except (
        FileNotFoundError,
        ValueError,
        json.JSONDecodeError,
    ) as exc:
        print(f"FAIL: {exc}")
        return 1

    identities: list[str] = []
    links: list[str] = []
    failures: list[str] = []

    for index, product in enumerate(products, start=1):
        identity = product_identity(product, index)
        identities.append(identity)

        title = product.get("title")
        category = product.get("category")
        link = product_link(product)

        if not title:
            failures.append(
                f"Product {identity} missing title"
            )

        if not category:
            failures.append(
                f"Product {identity} missing category"
            )

        if not link:
            failures.append(
                f"Product {identity} missing link"
            )
            continue

        links.append(link)

        tag = parse_qs(
            urlparse(link).query
        ).get("tag", [None])[0]

        if tag != CORRECT_AFFILIATE_TAG:
            failures.append(
                f"Product {identity} has invalid affiliate tag"
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

    if duplicate_ids:
        failures.append(
            "Duplicate product IDs: "
            + ", ".join(duplicate_ids)
        )

    if duplicate_links:
        failures.append(
            f"Duplicate product links found: {len(duplicate_links)}"
        )

    print("Products loaded          :", len(products))
    print("Duplicate IDs            :", len(duplicate_ids))
    print("Duplicate links          :", len(duplicate_links))

    if failures:
        print()
        for failure in failures:
            print("FAIL:", failure)

        print_section("BUILD SOURCE STATUS: FAIL")
        return 1

    print_section("BUILD SOURCE STATUS: PASS")
    return 0


def build_command() -> int:
    print_section("COUPON WORLD CONTROL CENTER — BUILD")

    if validate_build_source() != 0:
        print("BUILD ABORTED: source validation failed")
        return 1

    print_section("STEP 1 — BUILD PRODUCT PAGES")

    code = run_command(
        [
            sys.executable,
            "python/build_product_pages.py",
            "--write",
            "--clean",
        ]
    )

    if code != 0:
        print("BUILD FAILED: product page generation failed")
        return code

    print_section("STEP 2 — BUILD SITEMAP")

    code = run_command(
        [
            sys.executable,
            "python/build_sitemap.py",
        ]
    )

    if code != 0:
        print("BUILD FAILED: sitemap generation failed")
        return code

    print_section("STEP 3 — POST-BUILD CHECK")

    code = check_command()

    if code != 0:
        print_section("BUILD STATUS: FAIL")
        print("Generated site failed final validation.")
        return code

    print_section("BUILD STATUS: PASS")
    print("Product pages and sitemap rebuilt successfully.")
    print("Final site validation passed.")
    return 0




def intake_products(
    input_file: str,
    output_csv: str = "data/products_import.csv",
) -> int:
    print_section("COUPON WORLD CONTROL CENTER — INTAKE")

    input_path = Path(input_file)
    if not input_path.is_absolute():
        input_path = ROOT / input_path

    output_path = Path(output_csv)
    if not output_path.is_absolute():
        output_path = ROOT / output_path

    if not input_path.exists():
        print(f"FAIL: Product URL file not found: {input_path}")
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)

    return run_command(
        [
            sys.executable,
            "python/batch_product_importer.py",
            "prepare",
            str(input_path),
            str(output_path),
        ]
    )


def import_products(csv_file: str, write: bool = False) -> int:
    print_section("COUPON WORLD CONTROL CENTER — IMPORT")

    csv_path = Path(csv_file)

    if not csv_path.is_absolute():
        csv_path = ROOT / csv_path

    if not csv_path.exists():
        print(f"FAIL: CSV file not found: {csv_path}")
        return 1

    command = [
        sys.executable,
        "python/import_products.py",
        str(csv_path),
    ]

    command.append("--write" if write else "--preview")

    return run_command(command)



def run_workflow(
    input_file: str = "",
    output_csv: str = "data/products_import.csv",
) -> int:
    print_section("COUPON WORLD MASTER WORKFLOW")

    print("Mode        : SAFE")
    print("Auto-write  : NO")
    print("Auto-push   : NO")
    print("Discovery   : External source required")

    print_section("STEP 1 — FOUNDATION CHECK")

    check_code = check_command()

    if check_code != 0:
        print_section("MASTER WORKFLOW STATUS: FAIL")
        print("Foundation check failed. Workflow stopped.")
        return check_code

    if input_file:
        print_section("STEP 2 — PRODUCT INTAKE")

        intake_code = intake_products(
            input_file,
            output_csv,
        )

        if intake_code != 0:
            print_section("MASTER WORKFLOW STATUS: FAIL")
            print("Product intake failed. Workflow stopped.")
            return intake_code

        print_section("STEP 3 — IMPORT PREVIEW")

        import_code = import_products(
            output_csv,
            write=False,
        )

        if import_code != 0:
            print_section("MASTER WORKFLOW STATUS: REVIEW")
            print("Import preview requires review.")
            return import_code
    else:
        print_section("STEP 2 — PRODUCT INTAKE")
        print("SKIPPED: No input URL file supplied.")

    print_section("STEP 4 — CONTROLLED BUILD")

    build_code = build_command()

    if build_code != 0:
        print_section("MASTER WORKFLOW STATUS: FAIL")
        print("Controlled build failed.")
        return build_code

    print_section("MASTER WORKFLOW STATUS: PASS")
    print("Foundation             : PASS")
    print("Product intake         :", "PREVIEWED" if input_file else "SKIPPED")
    print("Database modification  : NO")
    print("Site build             : PASS")
    print("Git commit/push        : NOT PERFORMED")
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

    subparsers.add_parser(
        "build",
        help="Rebuild product pages and sitemap safely",
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run the safe Coupon World master workflow",
    )

    run_parser.add_argument(
        "--input",
        default="",
        help="Optional text file containing product URLs",
    )

    run_parser.add_argument(
        "--output",
        default="data/products_import.csv",
        help="Prepared CSV output path",
    )

    intake_parser = subparsers.add_parser(
        "intake",
        help="Prepare product import CSV from URL list",
    )

    intake_parser.add_argument(
        "input_file",
        help="Text file with one product URL per line",
    )

    intake_parser.add_argument(
        "--output",
        default="data/products_import.csv",
        help="Output CSV path",
    )

    import_parser = subparsers.add_parser(
        "import",
        help="Validate or import products from CSV",
    )

    import_parser.add_argument(
        "csv_file",
        help="CSV file containing products",
    )

    import_parser.add_argument(
        "--write",
        action="store_true",
        help="Write products and rebuild the site",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "check":
        return check_command()

    if args.command == "build":
        return build_command()

    if args.command == "run":
        return run_workflow(
            args.input,
            args.output,
        )

    if args.command == "intake":
        return intake_products(
            args.input_file,
            args.output,
        )

    if args.command == "import":
        return import_products(
            args.csv_file,
            args.write,
        )

    parser.error("Unknown command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
