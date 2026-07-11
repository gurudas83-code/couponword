#!/usr/bin/env python3
"""Coupon World AI OS - Product Pipeline v0.3 with Amazon data provider."""

import argparse
import re
from typing import Any
from urllib.parse import urlparse

from amazon_data_provider import get_default_provider
from product_engine import (
    COUPONS_FILE, clean_text, create_backup, detect_brand,
    generate_description, load_json, save_json,
)

AFFILIATE_TAG = "guru0906-21"
SUPPORTED_HOSTS = {"amazon.in", "www.amazon.in"}
ASIN_PATTERNS = (
    re.compile(r"/dp/([A-Z0-9]{10})(?:[/?]|$)", re.I),
    re.compile(r"/gp/product/([A-Z0-9]{10})(?:[/?]|$)", re.I),
    re.compile(r"/gp/aw/d/([A-Z0-9]{10})(?:[/?]|$)", re.I),
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Safely import one Amazon India product.")
    parser.add_argument("url", nargs="?", default="", help="Full Amazon India product URL")
    parser.add_argument("--title", default="", help="Verified product title; required with --write")
    parser.add_argument("--category", default="", help="Known product category")
    parser.add_argument("--write", action="store_true", help="Write product to coupons.json")
    return parser.parse_args()


def validate_url(url: str) -> str:
    url = clean_text(url)
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("URL must start with http:// or https://.")
    host = (parsed.hostname or "").casefold()
    if host not in SUPPORTED_HOSTS:
        raise ValueError(f"Unsupported host: {host or 'missing host'}. Use amazon.in.")
    return url


def extract_asin(url: str) -> str:
    path = urlparse(url).path
    for pattern in ASIN_PATTERNS:
        match = pattern.search(path)
        if match:
            return match.group(1).upper()
    raise ValueError("Could not extract a 10-character ASIN from the Amazon URL.")


def build_affiliate_url(asin: str) -> str:
    return f"https://www.amazon.in/dp/{asin}?tag={AFFILIATE_TAG}"


def existing_asin(product: dict[str, Any]) -> str:
    asin = clean_text(product.get("asin")).upper()
    if re.fullmatch(r"[A-Z0-9]{10}", asin):
        return asin
    link = clean_text(product.get("link"))
    if link:
        try:
            return extract_asin(link)
        except ValueError:
            pass
    return ""


def find_duplicate(products: list[dict[str, Any]], asin: str) -> dict[str, Any] | None:
    for product in products:
        if existing_asin(product) == asin:
            return product
    return None


def next_product_id(products: list[dict[str, Any]]) -> int:
    ids = []
    for product in products:
        value = product.get("id")
        if value is None:
            value = product.get("sl_no")
        try:
            ids.append(int(value))
        except (TypeError, ValueError):
            pass
    return max(ids, default=0) + 1


def build_record(products, asin, affiliate_url, title, category):
    provider = get_default_provider()
    data = provider.get_product(
        asin,
        title=clean_text(title),
        category=clean_text(category),
    )

    brand = clean_text(data.brand) or detect_brand(data.title)

    product = {
        "id": next_product_id(products),
        "asin": data.asin,
        "store": "Amazon IN",
        "title": clean_text(data.title),
        "brand": brand,
        "category": clean_text(data.category),
        "price": clean_text(data.price),
        "mrp": clean_text(data.mrp),
        "save": "",
        "discount": clean_text(data.discount),
        "image": clean_text(data.image),
        "link": affiliate_url,
        "description": "",
        "data_source": data.source,
    }

    if product["title"]:
        product["description"] = generate_description(product, brand)

    return product


def print_preview(product):
    print("\n" + "=" * 60)
    print("COUPON WORLD PRODUCT PIPELINE - PREVIEW")
    print("=" * 60)
    print(f"ID            : {product['id']}")
    print(f"ASIN          : {product['asin']}")
    print(f"Title         : {product['title'] or '[NOT PROVIDED]'}")
    print(f"Brand         : {product['brand'] or '[UNKNOWN]'}")
    print(f"Category      : {product['category'] or '[NOT PROVIDED]'}")
    print(f"Data source   : {product.get('data_source', 'manual')}")
    print(f"Affiliate URL : {product['link']}")
    print(f"Price         : {product['price'] or '[NOT FETCHED]'}")
    print(f"Image         : {product['image'] or '[NOT FETCHED]'}")
    print("=" * 60)


def collect_interactive_input(args: argparse.Namespace) -> argparse.Namespace:
    if args.url:
        return args

    print("\nCOUPON WORLD INTERACTIVE PRODUCT IMPORTER")
    print("=" * 48)
    args.url = input("Paste Amazon URL: ").strip()
    args.title = input("Enter verified product title: ").strip()
    args.category = input("Enter category (optional): ").strip()
    return args


def confirm_write() -> bool:
    answer = input("\nWrite this product to coupons.json? [y/N]: ").strip().casefold()
    return answer in {"y", "yes"}


def main() -> int:
    args = collect_interactive_input(parse_arguments())
    try:
        url = validate_url(args.url)
        asin = extract_asin(url)
        affiliate_url = build_affiliate_url(asin)
        products = load_json(COUPONS_FILE)

        duplicate = find_duplicate(products, asin)
        if duplicate:
            print("\nDUPLICATE PRODUCT FOUND")
            print(f"Product ID       : {duplicate.get('id') or duplicate.get('sl_no') or 'UNKNOWN'}")
            print(f"ASIN             : {asin}")
            print(f"Title            : {clean_text(duplicate.get('title')) or '[NO TITLE]'}")
            print("Database changed : NO")
            return 2

        product = build_record(products, asin, affiliate_url, args.title, args.category)
        print_preview(product)

        if not args.write:
            if args.url and product["title"] and confirm_write():
                args.write = True
            else:
                print("\nDRY RUN: coupons.json was not changed.")
                if not product["title"]:
                    print("NEXT: provide a verified title before writing.")
                return 0

        if not product["title"]:
            raise ValueError("--write requires a real --title; the pipeline will not invent one.")

        backup_file = create_backup(COUPONS_FILE)
        products.append(product)
        save_json(COUPONS_FILE, products)
        print("\nPRODUCT IMPORTED")
        print(f"Backup created   : {backup_file.relative_to(COUPONS_FILE.parent)}")
        print(f"Products after   : {len(products)}")
        print(f"New product ID   : {product['id']}")
        print("Database changed : YES")
        return 0
    except (FileNotFoundError, ValueError) as error:
        print(f"\nERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
