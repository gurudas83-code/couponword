"""Resolve reviewed retailer product destinations for the phone catalogue.

This module only admits product-page URLs that already have an exact identity
record in the repository's retailer registry.  A retailer search URL is never
rewritten into a guessed product URL.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from typing import Any


AMAZON_TAG = "guru07cc-21"
MOBILE_CATEGORIES = {"mobile", "mobiles", "phone", "phones"}


def _read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return default


def _norm(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").casefold()).split())


def affiliate_url(url: str, retailer: str) -> str:
    parsed = urlsplit(url)
    if retailer != "amazon" or parsed.hostname not in {"amazon.in", "www.amazon.in"}:
        return url
    query = [(key, value) for key, value in parse_qsl(parsed.query, keep_blank_values=True) if key != "tag"]
    query.append(("tag", AMAZON_TAG))
    return urlunsplit(parsed._replace(query=urlencode(query)))


def _direct_product_url(value: Any, retailer: str) -> str:
    """Return a safe direct product page or an empty string."""
    value = str(value or "").strip()
    parsed = urlsplit(value)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.port not in {None, 443}:
        return ""
    host = (parsed.hostname or "").casefold()
    if retailer == "amazon":
        if host not in {"amazon.in", "www.amazon.in"}:
            return ""
        match = re.match(r"^/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)", parsed.path, re.I)
        if not match:
            return ""
        clean = urlunsplit(parsed._replace(path=f"/dp/{match.group(1).upper()}", fragment=""))
        return affiliate_url(clean, retailer)
    if retailer == "flipkart":
        if host not in {"flipkart.com", "www.flipkart.com"} or "/p/" not in parsed.path.lower():
            return ""
        return urlunsplit(parsed._replace(fragment=""))
    return ""


def _identity_from_coupon(coupon: dict[str, Any], model_keys: set[str]) -> str:
    brand = _norm(coupon.get("brand"))
    title = _norm(coupon.get("title"))
    if not brand or not title:
        return ""
    candidates = []
    for key in model_keys:
        card_brand, separator, card_model = key.partition("|")
        if not separator or _norm(card_brand) != brand or not card_model:
            continue
        if f" {card_model} " in f" {title} ":
            candidates.append(key)
    # A direct registry row is safe only when the coupon title maps to one
    # model identity. Duplicate colour/capacity coupons still map to the same
    # model card and are merged later by retailer URL.
    return sorted(candidates, key=len, reverse=True)[0] if candidates else ""


def load_registry_direct_links(root: Path, model_keys: set[str]) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Load direct links from the reviewed registry, keyed by model identity."""
    registry = _read_json(root / "data/retailer_product_registry.json", {}).get("products") or {}
    coupons = _read_json(root / "coupons.json", [])
    if not isinstance(registry, dict) or not isinstance(coupons, list):
        return {}

    result: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for coupon in coupons:
        if not isinstance(coupon, dict) or _norm(coupon.get("category")) not in MOBILE_CATEGORIES:
            continue
        identity_key = _identity_from_coupon(coupon, model_keys)
        if not identity_key:
            continue
        brand, _, model = identity_key.partition("|")
        product_record = registry.get(f"cw-mobile-{coupon.get('id')}")
        if not isinstance(product_record, dict):
            continue
        for retailer, raw in product_record.items():
            if retailer not in {"amazon", "flipkart"} or not isinstance(raw, dict):
                continue
            url = _direct_product_url(raw.get("product_url"), retailer)
            if not url:
                continue
            row = {
                "retailer": retailer,
                "url": url,
                "affiliate_url": url if retailer == "amazon" else "",
                "retailer_product_id": str(raw.get("retailer_product_id") or "").strip(),
                "variant": str(coupon.get("title") or "").strip(),
                "source": str(raw.get("source") or "retailer_product_registry"),
                "source_type": "retailer_product_registry",
                "confidence": raw.get("confidence"),
                "price": None,
                "availability": "",
                "checked_at": "",
                "exact_identity_verified": True,
                "direct_product": True,
                "identity_source": "reviewed_retailer_product_registry",
            }
            bucket = result.setdefault((_norm(brand), _norm(model)), [])
            if not any(item["retailer"] == retailer and item["url"] == url for item in bucket):
                bucket.append(row)

    for identity in result:
        result[identity].sort(key=lambda item: (item["retailer"], item["variant"], item["url"]))
    return result
