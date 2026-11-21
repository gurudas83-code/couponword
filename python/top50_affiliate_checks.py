"""Opt-in official affiliate SKU checks for the historical-demand Top 50.

This is a provider adapter for the *existing* research/retailer evidence flow,
not a new recommendation engine or a live-offer admission route.
No request is made without explicit user-run --live, credentials and a
human-approved exact model+RAM/storage+retailer ID mapping.
"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urlencode
from urllib.request import Request, urlopen

AMAZON_TOKEN_URLS = {
    "3.1": "https://api.amazon.com/auth/o2/token",
    "3.2": "https://api.amazon.co.uk/auth/o2/token",
    "3.3": "https://api.amazon.co.jp/auth/o2/token",
}
AMAZON_GET_ITEMS_URL = "https://creatorsapi.amazon/catalog/v1/getItems"
FLIPKART_PRODUCT_URL = "https://affiliate-api.flipkart.net/affiliate/1.0/product.json"
PARTNER_TAG = "guru07cc-21"


def _post_json(url: str, data: dict, headers: dict | None = None) -> dict:
    request = Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    with urlopen(request, timeout=12) as response:
        return json.load(response)


def _get_json(url: str, headers: dict) -> dict:
    with urlopen(Request(url, headers=headers), timeout=12) as response:
        return json.load(response)


def _positive_inr(value: object) -> float | None:
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    return round(amount, 2) if 0 < amount < 10_000_000 and amount == amount else None


def configured(retailer: str) -> bool:
    if retailer == "amazon":
        return all(os.environ.get(key) for key in (
            "AMAZON_CREATORS_CREDENTIAL_ID",
            "AMAZON_CREATORS_CREDENTIAL_SECRET",
            "AMAZON_CREATORS_CREDENTIAL_VERSION",
        )) and os.environ.get("AMAZON_CREATORS_CREDENTIAL_VERSION") in AMAZON_TOKEN_URLS
    if retailer == "flipkart":
        return bool(os.environ.get("FLIPKART_AFFILIATE_ID") and os.environ.get("FLIPKART_AFFILIATE_TOKEN"))
    return False


def amazon_get_item(asin: str) -> dict:
    """Get only a reviewer-approved ASIN. Never admit into buyable offer store."""
    asin = asin.upper().strip()
    if not re.fullmatch(r"[A-Z0-9]{10}", asin):
        raise ValueError("Expected exact 10-character ASIN")
    if not configured("amazon"):
        return {"status": "NOT_CONFIGURED", "retailer": "amazon"}
    version = os.environ["AMAZON_CREATORS_CREDENTIAL_VERSION"]
    token = _post_json(AMAZON_TOKEN_URLS[version], {
        "grant_type": "client_credentials",
        "client_id": os.environ["AMAZON_CREATORS_CREDENTIAL_ID"],
        "client_secret": os.environ["AMAZON_CREATORS_CREDENTIAL_SECRET"],
        "scope": "creatorsapi::default",
    }).get("access_token")
    if not token:
        return {"status": "PROVIDER_AUTH_FAILURE", "retailer": "amazon"}
    payload = _post_json(AMAZON_GET_ITEMS_URL, {
        "itemIds": [asin],
        "itemIdType": "ASIN",
        "marketplace": "www.amazon.in",
        "partnerTag": os.environ.get("AMAZON_ASSOCIATES_TAG") or PARTNER_TAG,
        "resources": ["itemInfo.title", "offersV2.listings.price", "offersV2.listings.availability"],
    }, {"Authorization": "Bearer " + token, "x-marketplace": "www.amazon.in"})
    items = ((payload.get("itemResults") or {}).get("items") or [])
    matched = next((x for x in items if isinstance(x, dict) and x.get("asin") == asin), None)
    if not matched:
        return {"status": "PROVIDER_NO_EXACT_ASIN", "retailer": "amazon", "retailer_product_id": asin}
    listings = ((matched.get("offersV2") or {}).get("listings") or [])
    listing = next((x for x in listings if isinstance(x, dict)), {})
    price_field = listing.get("price") or {}
    if not isinstance(price_field, dict):
        price_field = {}
    money = price_field.get("money") or {}
    raw_price = money.get("amount") if isinstance(money, dict) else None
    # No explicit live stock proof: never infer it from an offer/price.
    availability = listing.get("availability")
    title = ((matched.get("itemInfo") or {}).get("title") or {}).get("displayValue")
    return {
        "status": "RAW_PROVIDER_OBSERVATION_PENDING_VARIANT_REVIEW",
        "retailer": "amazon", "retailer_product_id": asin, "provider_title": title,
        "observed_price_inr": _positive_inr(raw_price),
        "provider_availability": availability,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "publishable": False,
    }


def flipkart_get_product(product_id: str) -> dict:
    """Lookup exact reviewed Flipkart PID through documented affiliate API."""
    product_id = product_id.upper().strip()
    if not re.fullmatch(r"[A-Z0-9]{10,32}", product_id):
        raise ValueError("Invalid exact Flipkart product ID")
    if not configured("flipkart"):
        return {"status": "NOT_CONFIGURED", "retailer": "flipkart"}
    payload = _get_json(FLIPKART_PRODUCT_URL + "?" + urlencode({"id": product_id}), {
        "Fk-Affiliate-Id": os.environ["FLIPKART_AFFILIATE_ID"],
        "Fk-Affiliate-Token": os.environ["FLIPKART_AFFILIATE_TOKEN"],
    })
    base = payload.get("productBaseInfoV1") or {}
    if str(base.get("productId") or "").upper() != product_id:
        return {"status": "PROVIDER_NO_EXACT_PID", "retailer": "flipkart", "retailer_product_id": product_id}
    money = base.get("flipkartSellingPrice") or {}
    currency = money.get("currency") if isinstance(money, dict) else None
    raw_price = money.get("amount") if isinstance(money, dict) and currency == "INR" else None
    return {
        "status": "RAW_PROVIDER_OBSERVATION_PENDING_VARIANT_REVIEW",
        "retailer": "flipkart", "retailer_product_id": product_id,
        "provider_title": base.get("title"),
        "observed_price_inr": _positive_inr(raw_price),
        "provider_in_stock": base.get("inStock") if isinstance(base.get("inStock"), bool) else None,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "publishable": False,
    }
