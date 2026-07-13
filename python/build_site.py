#!/usr/bin/env python3
"""
Coupon World Build Controller v1.0

Purpose:
- Validate coupons.json
- Run Product Engine health check
- Generate all product pages
- Generate sitemap.xml
- Verify generated page and sitemap counts
- Fail safely if any critical check fails

This script does not invent or fetch price, image, rating, review,
discount, availability, or urgency information.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"
COUPONS_FILE = ROOT / "coupons.json"
PRODUCTS_DIR = ROOT / "products"
SITEMAP_FILE = ROOT / "sitemap.xml"

AFFILIATE_TAG = "guru0906-21"
DIRECT_AMAZON_HOSTS = {
    "amazon.in",
    "www.amazon.in",
}

SHORT_AMAZON_HOSTS = {
    "amzn.in",
    "www.amzn.in",
    "amzn.to",
    "www.amzn.to",
}

SUPPORTED_AMAZON_HOSTS = DIRECT_AMAZON_HOSTS | SHORT_AMAZON_HOSTS


class BuildError(RuntimeError):
    """Raised when a critical build validation fails."""


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate and build the complete Coupon World static site."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Generate product pages and sitemap.xml.",
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Remove old generated product directories before rebuilding.",
    )
    return parser.parse_args()


def clean(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).strip().split())


def section(title: str) -> None:
    print("\n" + "=" * 64)
    print(title)
    print("=" * 64)


def run_command(command: list[str]) -> None:
    print("$", " ".join(command))

    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        raise BuildError(
            f"Command failed with exit code {result.returncode}: "
            + " ".join(command)
        )


def load_products() -> list[dict]:
    if not COUPONS_FILE.exists():
        raise BuildError(f"Missing product database: {COUPONS_FILE}")

    try:
        data = json.loads(COUPONS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise BuildError(
            f"Invalid coupons.json at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error

    if not isinstance(data, list):
        raise BuildError("coupons.json must contain a JSON list.")

    invalid_rows = [
        index
        for index, product in enumerate(data, start=1)
        if not isinstance(product, dict)
    ]

    if invalid_rows:
        raise BuildError(
            "Non-object product rows found at positions: "
            + ", ".join(map(str, invalid_rows[:10]))
        )

    return data


def product_identity(product: dict, fallback: int) -> str:
    return clean(
        product.get("id")
        or product.get("sl_no")
        or product.get("asin")
        or fallback
    )


def validate_products(products: list[dict]) -> dict[str, int]:
    errors: list[str] = []
    warnings: list[str] = []

    seen_ids: dict[str, int] = {}
    seen_asins: dict[str, int] = {}
    seen_links: dict[str, int] = {}

    active_count = 0
    inactive_count = 0
    missing_images = 0
    missing_prices = 0
    search_links = 0
    direct_links = 0

    for index, product in enumerate(products, start=1):
        identity = product_identity(product, index)
        title = clean(product.get("title"))
        link = clean(product.get("link"))
        asin = clean(product.get("asin")).upper()
        image = clean(product.get("image"))

        if product.get("active") is False:
            inactive_count += 1
        else:
            active_count += 1

        if not title:
            errors.append(f"Product {identity}: missing title")

        if not link:
            errors.append(f"Product {identity}: missing affiliate link")
        else:
            parsed = urlparse(link)
            host = (parsed.hostname or "").casefold()

            if host not in SUPPORTED_AMAZON_HOSTS:
                errors.append(
                    f"Product {identity}: unsupported link host "
                    f"{host or '[missing]'}"
                )
            elif host in DIRECT_AMAZON_HOSTS:
                query = parse_qs(parsed.query)
                tag = clean((query.get("tag") or [""])[0])

                if tag != AFFILIATE_TAG:
                    errors.append(
                        f"Product {identity}: affiliate tag is "
                        f"{tag or '[missing]'}, expected {AFFILIATE_TAG}"
                    )

                if parsed.path.rstrip("/") in {"", "/s"} or parsed.path == "/s":
                    search_links += 1
                elif "/dp/" in parsed.path or "/gp/product/" in parsed.path:
                    direct_links += 1
            else:
                warnings.append(
                    f"Product {identity}: Amazon short link host {host}; "
                    "affiliate tag cannot be verified without resolving the link."
                )
                direct_links += 1

            normalized_link = link.casefold()
            if normalized_link in seen_links:
                errors.append(
                    f"Product {identity}: duplicate link also used by "
                    f"product {seen_links[normalized_link]}"
                )
            else:
                seen_links[normalized_link] = index

        raw_id = clean(product.get("id") or product.get("sl_no"))
        if raw_id:
            normalized_id = raw_id.casefold()
            if normalized_id in seen_ids:
                errors.append(
                    f"Product {identity}: duplicate ID also used at "
                    f"row {seen_ids[normalized_id]}"
                )
            else:
                seen_ids[normalized_id] = index

        if asin:
            if len(asin) != 10 or not asin.isalnum():
                errors.append(f"Product {identity}: malformed ASIN {asin}")
            elif asin in seen_asins:
                errors.append(
                    f"Product {identity}: duplicate ASIN also used at "
                    f"row {seen_asins[asin]}"
                )
            else:
                seen_asins[asin] = index

        if not image:
            missing_images += 1

        if product.get("price") in (None, ""):
            missing_prices += 1

    if missing_images:
        warnings.append(
            f"{missing_images} products have no image "
            "(warning only; PA-API is not connected)."
        )

    if missing_prices:
        warnings.append(
            f"{missing_prices} products have no verified price "
            "(warning only; no price will be invented)."
        )

    for warning in warnings:
        print("WARNING:", warning)

    if errors:
        print("\nCRITICAL VALIDATION ERRORS:")
        for error in errors[:25]:
            print(" -", error)

        if len(errors) > 25:
            print(f" - ...and {len(errors) - 25} more errors")

        raise BuildError(
            f"Product validation failed with {len(errors)} critical error(s)."
        )

    return {
        "total": len(products),
        "active": active_count,
        "inactive": inactive_count,
        "missing_images": missing_images,
        "missing_prices": missing_prices,
        "search_links": search_links,
        "direct_links": direct_links,
    }


def count_generated_pages() -> int:
    if not PRODUCTS_DIR.exists():
        return 0

    return sum(
        1
        for page in PRODUCTS_DIR.glob("*/index.html")
        if page.is_file()
    )


def count_sitemap_urls() -> int:
    if not SITEMAP_FILE.exists():
        raise BuildError("sitemap.xml was not generated.")

    try:
        tree = ET.parse(SITEMAP_FILE)
    except ET.ParseError as error:
        raise BuildError(f"Invalid sitemap.xml: {error}") from error

    root = tree.getroot()
    namespace = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    return len(root.findall("sm:url", namespace))


def main() -> int:
    args = parse_arguments()

    try:
        section("1. PRODUCT DATABASE VALIDATION")
        products = load_products()
        stats = validate_products(products)

        print(f"Products          : {stats['total']}")
        print(f"Active products   : {stats['active']}")
        print(f"Inactive products : {stats['inactive']}")
        print(f"Direct links      : {stats['direct_links']}")
        print(f"Search links      : {stats['search_links']}")
        print("Critical errors   : 0")

        section("2. PRODUCT ENGINE HEALTH CHECK")
        run_command(
            [
                sys.executable,
                str(PYTHON_DIR / "product_engine.py"),
                "--preview-limit",
                "5",
            ]
        )

        if not args.write:
            section("DRY RUN COMPLETE")
            print("Database changed      : NO")
            print("Product pages changed : NO")
            print("Sitemap changed       : NO")
            print("\nRun this to build the site:")
            print("python python/build_site.py --write --clean")
            return 0

        section("3. PRODUCT PAGE GENERATION")
        page_command = [
            sys.executable,
            str(PYTHON_DIR / "build_product_pages.py"),
            "--write",
        ]

        if args.clean:
            page_command.append("--clean")

        run_command(page_command)

        section("4. SITEMAP GENERATION")
        run_command(
            [
                sys.executable,
                str(PYTHON_DIR / "build_sitemap.py"),
            ]
        )

        section("5. BUILD VERIFICATION")
        generated_pages = count_generated_pages()
        sitemap_urls = count_sitemap_urls()

        expected_pages = stats["total"]
        expected_sitemap_urls = stats["active"] + 1

        print(f"Expected product pages : {expected_pages}")
        print(f"Generated pages        : {generated_pages}")
        print(f"Expected sitemap URLs  : {expected_sitemap_urls}")
        print(f"Actual sitemap URLs    : {sitemap_urls}")

        if generated_pages != expected_pages:
            raise BuildError(
                f"Generated page count mismatch: expected {expected_pages}, "
                f"found {generated_pages}."
            )

        if sitemap_urls != expected_sitemap_urls:
            raise BuildError(
                f"Sitemap URL count mismatch: expected "
                f"{expected_sitemap_urls}, found {sitemap_urls}."
            )

        section("COUPON WORLD BUILD REPORT")
        print(f"Products             : {stats['total']}")
        print(f"Active products      : {stats['active']}")
        print(f"Inactive products    : {stats['inactive']}")
        print(f"Pages generated      : {generated_pages}")
        print(f"Sitemap URLs         : {sitemap_urls}")
        print(f"Missing images       : {stats['missing_images']} (warning)")
        print(f"Missing prices       : {stats['missing_prices']} (warning)")
        print("Affiliate tag errors : 0")
        print("Duplicate errors     : 0")
        print("\nBUILD STATUS         : PASS")

        return 0

    except (BuildError, OSError) as error:
        section("COUPON WORLD BUILD FAILED")
        print("ERROR:", error)
        print("\nBUILD STATUS : FAIL")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
