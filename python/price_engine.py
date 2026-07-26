#!/usr/bin/env python3
"""
Coupon World AI OS
Price Engine v0.1

Purpose:
- Read product price safely
- Normalize price values
- Check budget match
- Calculate discount when MRP is available
- Return price intelligence
"""

from __future__ import annotations

import re


def normalize_price(value: object) -> float | None:
    if value in (None, ""):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    text = str(value).strip()

    if not text:
        return None

    text = text.replace(",", "")
    text = text.replace("₹", "")
    text = re.sub(r"[^\d.]", "", text)

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def calculate_discount(
    price: float | None,
    mrp: float | None,
) -> float | None:
    if price is None or mrp is None:
        return None

    if mrp <= 0 or price > mrp:
        return None

    discount = ((mrp - price) / mrp) * 100

    return round(discount, 2)


def check_budget(
    price: float | None,
    budget_min: int | None,
    budget_max: int | None,
) -> bool | None:
    if price is None:
        return None

    if budget_min is not None and price < budget_min:
        return False

    if budget_max is not None and price > budget_max:
        return False

    return True


def analyze_price(product: dict, intent: dict) -> dict:
    price = normalize_price(product.get("price"))
    mrp = normalize_price(product.get("mrp"))

    budget_min = intent.get("budget_min")
    budget_max = intent.get("budget_max")

    return {
        "price": price,
        "mrp": mrp,
        "discount_percent": calculate_discount(price, mrp),
        "within_budget": check_budget(
            price,
            budget_min,
            budget_max,
        ),
        "price_available": price is not None,
    }


if __name__ == "__main__":
    sample_product = {
        "title": "boAt Airdopes 311 Pro TWS Earbuds",
        "price": "₹1,799",
        "mrp": "₹4,990",
    }

    sample_intent = {
        "budget_min": None,
        "budget_max": 2000,
    }

    print(analyze_price(sample_product, sample_intent))