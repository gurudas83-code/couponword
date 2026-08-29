#!/usr/bin/env python3

from __future__ import annotations

import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PUBLIC_FILE = ROOT / "data" / "multi_retailer_public.json"


def load_multi_retailer_products():
    if not PUBLIC_FILE.exists():
        return {}

    try:
        data = json.loads(
            PUBLIC_FILE.read_text(encoding="utf-8-sig")
        )
    except (OSError, json.JSONDecodeError):
        return {}

    result = {}

    for product in data.get("products", []):
        product_id = str(product.get("product_id") or "").strip()

        if product_id:
            result[product_id] = product

    return result


def couponworld_product_id(product):
    raw_id = str(
        product.get("id")
        or product.get("sl_no")
        or ""
    ).strip()

    category = str(
        product.get("category") or ""
    ).strip().lower()

    if category in {"mobile", "mobiles", "smartphone", "smartphones"}:
        prefix = "mobile"
    elif "audio" in category:
        prefix = "audio"
    elif "musical" in category:
        prefix = "keyboard"
    elif "electronic" in category:
        title = str(product.get("title") or "").lower()

        if "telescope" in title:
            prefix = "telescope"
        elif "buds" in title or "earbuds" in title:
            prefix = "audio"
        else:
            prefix = "product"
    else:
        prefix = "product"

    return f"cw-{prefix}-{raw_id}" if raw_id else ""


def format_price(value):
    try:
        value = float(value)
    except (TypeError, ValueError):
        return "Price unavailable"

    if value <= 0:
        return "Price unavailable"

    return f"₹{value:,.0f}"


def availability_label(value):
    value = str(value or "").strip().lower()

    if value == "in_stock":
        return "In stock"

    if value == "out_of_stock":
        return "Out of stock"

    return "Availability not verified"


def retailer_name(value):
    value = str(value or "").strip()

    return value.title() if value else "Retailer"


def render_multi_retailer_section(product, multi_products):
    product_id = couponworld_product_id(product)

    multi = multi_products.get(product_id)

    if not multi:
        return ""

    offers = multi.get("offers") or []

    if not offers:
        return ""

    best = multi.get("best_offer") or {}
    best_retailer = str(
        best.get("retailer") or ""
    ).strip().lower()

    cards = []

    for offer in offers:
        retailer = str(
            offer.get("retailer") or ""
        ).strip().lower()

        price = format_price(
            offer.get("price")
        )

        availability = availability_label(
            offer.get("availability")
        )

        freshness = str(
            offer.get("freshness") or ""
        ).strip().lower()

        url = str(
            offer.get("affiliate_url")
            or offer.get("product_url")
            or ""
        ).strip()

        is_best = (
            best_retailer
            and retailer == best_retailer
        )

        badges = []

        if is_best:
            badges.append(
                '<span class="offer-best">'
                'Best verified offer'
                '</span>'
            )

        if freshness == "fresh":
            badges.append(
                '<span class="offer-fresh">'
                'Price checked recently'
                '</span>'
            )

        button = ""

        if url:
            button = (
                f'<a class="offer-cta" '
                f'href="{html.escape(url)}" '
                'target="_blank" '
                'rel="nofollow sponsored noopener">'
                f'View on {html.escape(retailer_name(retailer))}'
                '</a>'
            )

        cards.append(
            '<div class="retailer-offer">'
            '<div class="offer-top">'
            f'<strong>{html.escape(retailer_name(retailer))}</strong>'
            f'{"".join(badges)}'
            '</div>'
            f'<div class="offer-price">{html.escape(price)}</div>'
            f'<div class="offer-availability">{html.escape(availability)}</div>'
            f'{button}'
            '</div>'
        )

    return (
        '<section class="multi-retailer">'
        '<div class="multi-retailer-heading">'
        '<div>'
        '<h2>Compare retailer offers</h2>'
        '<p>Prices and availability are based on recently verified evidence.</p>'
        '</div>'
        '</div>'
        '<div class="retailer-offer-grid">'
        + "".join(cards)
        + '</div>'
        '<div class="multi-retailer-note">'
        'Final price and availability are confirmed on the retailer website.'
        '</div>'
        '</section>'
    )


MULTI_RETAILER_CSS = """
.multi-retailer-heading h2{margin:0 0 6px}
.multi-retailer-heading p{margin:0;color:#68707d}
.retailer-offer-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16px;margin-top:20px}
.retailer-offer{border:1px solid #e5e7eb;border-radius:16px;padding:18px;display:grid;gap:10px}
.offer-top{display:flex;align-items:center;flex-wrap:wrap;gap:8px}
.offer-price{font-size:27px;font-weight:900}
.offer-availability{color:#68707d;font-weight:700}
.offer-best{font-size:12px;font-weight:800;background:#ecfdf3;color:#067647;padding:5px 8px;border-radius:999px}
.offer-fresh{font-size:12px;font-weight:800;background:#eef4ff;color:#3538cd;padding:5px 8px;border-radius:999px}
.offer-cta{display:inline-flex;width:max-content;padding:10px 14px;border-radius:10px;background:#111827;color:#fff;text-decoration:none;font-weight:800}
.multi-retailer-note{font-size:13px;color:#68707d;margin-top:14px}
@media(max-width:760px){.retailer-offer-grid{grid-template-columns:1fr}}
"""

