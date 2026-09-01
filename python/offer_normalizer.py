#!/usr/bin/env python3

from __future__ import annotations

import re
from typing import Any

from retailer_contract import (
    RetailerOffer,
    normalize_availability,
    normalize_retailer_name,
)


def normalize_price(value: Any) -> float | None:
    """Convert retailer price formats such as ₹19,999 or 19999 to float."""
    if value is None:
        return None

    if isinstance(value, (int, float)):
        price = float(value)
        return price if price > 0 else None

    text = str(value).strip()
    if not text:
        return None

    text = text.replace(",", "")
    match = re.search(r"\d+(?:\.\d+)?", text)

    if not match:
        return None

    price = float(match.group())
    return price if price > 0 else None


def normalize_offer(
    retailer: str,
    raw: dict[str, Any],
) -> RetailerOffer:
    """Convert retailer-specific raw data into Coupon World RetailerOffer."""

    retailer_name = normalize_retailer_name(retailer)

    return RetailerOffer(
        retailer=retailer_name,

        product_id=str(
            raw.get("product_id")
            or raw.get("canonical_product_id")
            or ""
        ).strip(),

        retailer_product_id=str(
            raw.get("retailer_product_id")
            or raw.get("asin")
            or raw.get("fsn")
            or raw.get("sku")
            or ""
        ).strip(),

        brand=str(raw.get("brand") or "").strip(),
        model=str(raw.get("model") or "").strip(),

        variant=str(
            raw.get("variant")
            or raw.get("configuration")
            or ""
        ).strip(),

        title=str(
            raw.get("title")
            or raw.get("name")
            or ""
        ).strip(),

        price=normalize_price(
            raw.get("price")
            or raw.get("selling_price")
            or raw.get("current_price")
        ),

        mrp=normalize_price(
            raw.get("mrp")
            or raw.get("list_price")
        ),

        currency=str(
            raw.get("currency") or "INR"
        ).upper(),

        availability=normalize_availability(
            raw.get("availability")
            or raw.get("stock")
            or raw.get("status")
            or ""
        ),

        product_url=str(
            raw.get("product_url")
            or raw.get("url")
            or raw.get("link")
            or ""
        ).strip(),

        affiliate_url=str(
            raw.get("affiliate_url")
            or ""
        ).strip(),

        source=str(
            raw.get("source")
            or "unknown"
        ).strip(),

        confidence=float(
            raw.get("confidence") or 0.0
        ),

        metadata={
            "raw_retailer": retailer,
        },
    )


if __name__ == "__main__":

    amazon_raw = {
        "asin": "B0TEST123",
        "title": "Samsung Galaxy Test 8GB 128GB",
        "brand": "Samsung",
        "model": "Galaxy Test",
        "variant": "8GB/128GB",
        "price": "₹19,999",
        "mrp": "₹22,999",
        "availability": "In Stock",
        "url": "https://www.amazon.in/example",
        "source": "manual",
        "confidence": 0.95,
    }

    flipkart_raw = {
        "fsn": "MOBTEST456",
        "name": "Samsung Galaxy Test 8 GB 128 GB",
        "brand": "Samsung",
        "model": "Galaxy Test",
        "configuration": "8GB/128GB",
        "selling_price": "18,999",
        "list_price": "22,999",
        "stock": "Available",
        "link": "https://www.flipkart.com/example",
        "source": "manual",
        "confidence": 0.93,
    }

    amazon_offer = normalize_offer("Amazon", amazon_raw)
    flipkart_offer = normalize_offer("Flipkart", flipkart_raw)

    print("\nAMAZON NORMALIZED")
    print(amazon_offer.to_dict())

    print("\nFLIPKART NORMALIZED")
    print(flipkart_offer.to_dict())
