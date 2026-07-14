#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

AFFILIATE_TAG = "guru0906-21"

OUTPUT_FIELDS = [
    "title",
    "category",
    "link",
    "store",
    "discount",
    "code",
    "expiry",
    "badge",
    "price",
    "mrp",
    "save",
    "priceText",
    "linkType",
    "asin",
    "image",
    "description",
]


def clean(value: object) -> str:
    return str(value or "").strip()


def add_affiliate_tag(url: str) -> str:
    url = clean(url)

    if not url:
        return ""

    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()

    if host not in {
        "amazon.in",
        "www.amazon.in",
        "amzn.in",
        "www.amzn.in",
    }:
        return url

    query = parse_qs(parsed.query, keep_blank_values=True)
    query["tag"] = [AFFILIATE_TAG]

    return urlunparse(
        parsed._replace(
            query=urlencode(query, doseq=True)
        )
    )


def normalize_price(value: object) -> str:
    text = clean(value)

    if not text:
        return ""

    text = (
        text.replace("₹", "")
        .replace(",", "")
        .strip()
    )

    try:
        number = float(text)
    except ValueError:
        return ""

    if number <= 0:
        return ""

    return str(int(number)) if number.is_integer() else str(number)


def detect_link_type(url: str) -> str:
    lowered = clean(url).lower()

    if any(token in lowered for token in ("/dp/", "/gp/product/", "amzn.in/d/")):
        return "product"

    if "/s?" in lowered or "?k=" in lowered:
        return "search"

    return ""


def normalize_row(row: dict[str, str]) -> dict[str, str]:
    title = clean(
        row.get("title")
        or row.get("product_name")
        or row.get("name")
    )

    category = clean(
        row.get("category")
        or row.get("product_category")
    )

    link = add_affiliate_tag(
        row.get("link")
        or row.get("url")
        or row.get("product_url")
        or row.get("affiliate_url")
        or ""
    )

    price = normalize_price(
        row.get("price")
        or row.get("current_price")
        or row.get("sale_price")
    )

    mrp = normalize_price(
        row.get("mrp")
        or row.get("original_price")
        or row.get("list_price")
    )

    return {
        "title": title,
        "category": category,
        "link": link,
        "store": clean(row.get("store")) or "Online Store",
        "discount": clean(row.get("discount")) or "Check Deal",
        "code": clean(row.get("code")) or "No code",
        "expiry": clean(row.get("expiry")),
        "badge": clean(row.get("badge")),
        "price": price,
        "mrp": mrp,
        "save": normalize_price(row.get("save")),
        "priceText": clean(row.get("priceText")),
        "linkType": clean(row.get("linkType")) or detect_link_type(link),
        "asin": clean(row.get("asin")).upper(),
        "image": clean(
            row.get("image")
            or row.get("image_url")
        ),
        "description": clean(row.get("description")),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Convert an approved product feed to Coupon World CSV format"
    )

    parser.add_argument("input_csv")
    parser.add_argument("output_csv")
    args = parser.parse_args()

    input_path = Path(args.input_csv)
    output_path = Path(args.output_csv)

    if not input_path.exists():
        print(f"FAIL: Input file not found: {input_path}")
        return 1

    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)

        if not reader.fieldnames:
            print("FAIL: Input CSV header missing")
            return 1

        rows = [
            normalize_row(row)
            for row in reader
        ]

    valid = [
        row
        for row in rows
        if row["title"] and row["category"] and row["link"]
    ]

    rejected = len(rows) - len(valid)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=OUTPUT_FIELDS,
        )

        writer.writeheader()
        writer.writerows(valid)

    print("=" * 68)
    print("COUPON WORLD PRODUCT SOURCE ADAPTER")
    print("=" * 68)
    print("Input rows     :", len(rows))
    print("Accepted rows  :", len(valid))
    print("Rejected rows  :", rejected)
    print("Output file    :", output_path)
    print("Database change: NO")
    print("ADAPTER STATUS : PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
