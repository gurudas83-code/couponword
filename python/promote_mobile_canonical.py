#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

import requests
from bs4 import BeautifulSoup

from amazon_exact_image_recovery import HEADERS
from mobile_exact_identity_gate import (
    AUTO_REUSE,
    classify_mobile_identity_reuse,
)
from retailer_product_registry import load_registry


ROOT = Path(__file__).resolve().parents[1]
COUPONS_FILE = ROOT / "coupons.json"
REGISTRY_FILE = ROOT / "data" / "retailer_product_registry.json"


def clean(value) -> str:
    return str(value or "").strip()


def load_products() -> list[dict]:
    data = json.loads(
        COUPONS_FILE.read_text(encoding="utf-8-sig")
    )

    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        products = data.get("products", [])
        if isinstance(products, list):
            return products

    raise SystemExit("BLOCKED: unsupported coupons.json structure")


def url_asin(url: str) -> str:
    match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:[/?]|$)",
        clean(url),
        flags=re.IGNORECASE,
    )
    return match.group(1).upper() if match else ""


def fetch_amazon_identity(
    asin: str,
    expected_title: str,
    expected_brand: str,
) -> dict:
    url = f"https://www.amazon.in/dp/{asin}"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=(5, 18),
        allow_redirects=True,
    )

    if response.status_code != 200:
        raise SystemExit(
            f"BLOCKED: Amazon HTTP {response.status_code}"
        )

    soup = BeautifulSoup(response.text, "lxml")

    node = soup.find(id="productTitle")

    page_title = (
        node.get_text(" ", strip=True)
        if node
        else (
            soup.title.get_text(" ", strip=True)
            if soup.title
            else ""
        )
    )

    asin_node = (
        soup.find("input", id="ASIN")
        or soup.find(
            "input",
            attrs={"name": "ASIN"},
        )
    )

    page_asin = (
        clean(asin_node.get("value")).upper()
        if asin_node
        else ""
    )

    final_url_asin = url_asin(response.url)

    if final_url_asin != asin:
        raise SystemExit(
            "BLOCKED: final Amazon URL ASIN mismatch "
            f"({final_url_asin!r} != {asin!r})"
        )

    if page_asin != asin:
        raise SystemExit(
            "BLOCKED: Amazon page ASIN mismatch "
            f"({page_asin!r} != {asin!r})"
        )

    gate = classify_mobile_identity_reuse(
        expected_text=expected_title,
        candidate_title=page_title,
        candidate_url=response.url,
        expected_brand=expected_brand,
    )

    if gate.get("status") != AUTO_REUSE:
        raise SystemExit(
            "BLOCKED: strict mobile identity gate returned "
            f"{gate.get('status')}: {gate.get('reason')}"
        )

    return {
        "http_status": response.status_code,
        "final_url": response.url,
        "page_asin": page_asin,
        "page_title": page_title,
        "strict_status": gate.get("status"),
        "strict_reason": gate.get("reason"),
        "resolver_decision": gate.get("resolver_decision"),
        "resolver_score": gate.get("resolver_score"),
    }


def find_asin_owners(
    registry: dict,
    asin: str,
) -> list[str]:
    owners: list[str] = []

    for product_id, retailers in (
        registry.get("products", {}).items()
    ):
        if not isinstance(retailers, dict):
            continue

        amazon = retailers.get("amazon")

        if not isinstance(amazon, dict):
            continue

        registered = clean(
            amazon.get("retailer_product_id")
        ).upper()

        if registered == asin:
            owners.append(str(product_id))

    return owners


def main() -> int:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--source-id",
        required=True,
    )
    parser.add_argument(
        "--asin",
        required=True,
    )
    parser.add_argument(
        "--write",
        action="store_true",
    )

    args = parser.parse_args()

    source_id = clean(args.source_id)
    asin = clean(args.asin).upper()

    if not source_id.isdigit():
        raise SystemExit(
            "BLOCKED: durable source ID must be numeric"
        )

    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise SystemExit(
            "BLOCKED: invalid Amazon ASIN"
        )

    canonical_id = f"cw-mobile-{source_id}"

    products = load_products()

    matches = [
        row
        for row in products
        if clean(row.get("id")) == source_id
    ]

    if len(matches) != 1:
        raise SystemExit(
            "BLOCKED: durable catalog ID must resolve "
            f"to exactly one row; found {len(matches)}"
        )

    product = matches[0]

    title = clean(product.get("title"))
    brand = clean(product.get("brand"))
    category = clean(product.get("category"))
    source_asin = clean(product.get("asin")).upper()

    if category.casefold() != "mobiles":
        raise SystemExit(
            f"BLOCKED: source row is not Mobiles ({category!r})"
        )

    if source_asin != asin:
        raise SystemExit(
            "BLOCKED: durable source row ASIN mismatch "
            f"({source_asin!r} != {asin!r})"
        )

    if not title or not brand:
        raise SystemExit(
            "BLOCKED: source row missing title or brand"
        )

    registry = load_registry()
    registry_products = registry.get("products", {})

    if canonical_id in registry_products:
        raise SystemExit(
            f"BLOCKED: canonical ID already exists: {canonical_id}"
        )

    owners = find_asin_owners(
        registry,
        asin,
    )

    if owners:
        raise SystemExit(
            "BLOCKED: Amazon ASIN already belongs to "
            + ", ".join(owners)
        )

    live = fetch_amazon_identity(
        asin=asin,
        expected_title=title,
        expected_brand=brand,
    )

    record = {
        "retailer_product_id": asin,
        "product_url": f"https://www.amazon.in/dp/{asin}",
        "confidence": 0.99,
        "source": (
            "live-amazon-exact-page+"
            "mobile-exact-identity-gate-v1"
        ),
    }

    print("=" * 78)
    print("COUPON WORLD MOBILE CANONICAL PROMOTION")
    print("=" * 78)
    print("MODE          :", "WRITE" if args.write else "DRY RUN")
    print("SOURCE ID     :", source_id)
    print("CANONICAL ID  :", canonical_id)
    print("TITLE         :", title)
    print("BRAND         :", brand)
    print("ASIN          :", asin)
    print("HTTP          :", live["http_status"])
    print("PAGE ASIN     :", live["page_asin"])
    print("PAGE TITLE    :", live["page_title"])
    print("STRICT STATUS :", live["strict_status"])
    print("STRICT REASON :", live["strict_reason"])
    print(
        "BASE RESOLVER :",
        live["resolver_decision"],
        live["resolver_score"],
    )
    print("ASIN OWNERS   :", owners)
    print()
    print(
        "PLANNED RECORD:",
        json.dumps(
            {
                canonical_id: {
                    "amazon": record,
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    if not args.write:
        print()
        print("DATABASE      : UNCHANGED")
        print("RESULT        : READY_FOR_WRITE")
        return 0

    registry.setdefault(
        "products",
        {},
    )[canonical_id] = {
        "amazon": record,
    }

    temp_file = REGISTRY_FILE.with_name(
        REGISTRY_FILE.name + ".tmp"
    )

    temp_file.write_text(
        json.dumps(
            registry,
            ensure_ascii=False,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )

    os.replace(
        temp_file,
        REGISTRY_FILE,
    )

    print()
    print("DATABASE      : UPDATED")
    print("RESULT        : PROMOTED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
