#!/usr/bin/env python3

from __future__ import annotations

import json
from pathlib import Path

from canonical_product import CanonicalProduct
from retailer_product_registry import register_retailer_product


ROOT = Path(__file__).resolve().parent.parent
PILOT_FILE = ROOT / "data" / "pilot_products.json"
OUTPUT_FILE = ROOT / "data" / "pilot_canonical_products.json"


def load_manifest():
    return json.loads(
        PILOT_FILE.read_text(encoding="utf-8-sig")
    )


def build_product(item):
    asin = str(item.get("amazon_asin") or "").strip()

    identifiers = {}

    if asin:
        identifiers["amazon_asin"] = asin

    return CanonicalProduct(
        product_id=str(item["product_id"]).strip(),
        title=str(item["title"]).strip(),
        brand=str(item["brand"]).strip(),
        model=str(item["model"]).strip(),
        variant=str(item.get("variant") or "").strip(),
        category=str(item.get("category") or "").strip(),
        identifiers=identifiers,
        attributes=dict(item.get("attributes") or {}),
        source_product_id=str(item.get("catalog_id") or "").strip(),
        source="pilot_manifest",
        confidence=0.95,
    )


def main():
    manifest = load_manifest()

    products = []

    for item in manifest.get("products", []):
        product = build_product(item)

        products.append(product.to_dict())

        asin = product.identifiers.get("amazon_asin")

        if asin:
            register_retailer_product(
                product_id=product.product_id,
                retailer="amazon",
                retailer_product_id=asin,
                product_url=f"https://www.amazon.in/dp/{asin}",
                confidence=0.95,
                source="pilot_manifest_verified_identity",
            )

        print()
        print("REGISTERED")
        print("Product :", product.product_id)
        print("Brand   :", product.brand)
        print("Model   :", product.model)
        print("Variant :", product.variant or "-")
        print("ASIN    :", asin or "-")

    OUTPUT_FILE.write_text(
        json.dumps(
            {
                "version": 1,
                "products": products,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("=" * 70)
    print("PILOT CANONICAL BUILD COMPLETE")
    print("=" * 70)
    print("Products :", len(products))
    print("Output   :", OUTPUT_FILE)


if __name__ == "__main__":
    main()
