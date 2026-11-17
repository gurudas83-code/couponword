"""Isolated QuickCommerce Flipkart observation adapter (research only).

This deliberately does not change the default retailer manager or write offers.
QuickCommerce is a third-party provider, NOT Flipkart's authorized affiliate feed.
Its observations must never be promoted to public prices by this adapter.
"""
from __future__ import annotations

import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, urlopen

from offer_normalizer import normalize_offer

BASE_URL = "https://api.quickcommerceapi.com"
SOURCE = "quickcommerce_third_party_research"
MODEL_TOKEN = re.compile(r"[^a-z0-9]+")
RAM_TOKEN = re.compile(r"\b(\d{1,3})\s*GB\s*RAM\b", re.I)
STORAGE_TOKEN = re.compile(r"\b(\d{1,4})\s*(GB|TB)\b", re.I)


def _tokens(value):
    return " ".join(MODEL_TOKEN.sub(" ", str(value).lower()).split())


def _listing_model_name(title):
    """Remove trailing memory/color groups, preserving model names like Phone (3a)."""
    text = str(title).strip()
    while True:
        model = re.sub(r"\s*\([^()]*\b\d+\s*(?:GB|TB)\b[^()]*\)\s*$", "", text, flags=re.I).strip()
        if model == text:
            return text
        text = model


def _memory(variant):
    text = str(variant).replace(" ", "")
    match = re.search(r"(\d{1,3})GB/(\d{1,4})(GB|TB)", text, re.I)
    if not match:
        raise ValueError("Exact variant must be formatted as 8GB/128GB")
    storage = int(match.group(2)) * (1024 if match.group(3).upper() == "TB" else 1)
    return int(match.group(1)), storage


def _valid_listing(item, product):
    if not isinstance(item, dict):
        return False
    brand = _tokens(product.brand)
    model = _tokens(product.model)
    name = _tokens(_listing_model_name(item.get("name", "")))
    # Enforce the full model phrase, rather than matching 'A56' to 'A56 Plus'.
    if not brand or not model or name != brand + " " + model:
        return False
    if _tokens(item.get("brand", "")) != brand:
        return False
    try:
        ram, storage = _memory(product.variant)
    except ValueError:
        return False
    ram_match = RAM_TOKEN.search(str(item.get("quantity") or ""))
    storage_matches = STORAGE_TOKEN.findall(str(item.get("name") or ""))
    storage_values = [int(n) * (1024 if u.upper() == "TB" else 1) for n, u in storage_matches]
    if ram_match is None or int(ram_match.group(1)) != ram or storage not in storage_values:
        return False
    expected_color = str((product.attributes or {}).get("color") or "").strip()
    if expected_color:
        # Color must be stated explicitly and match; do not silently swap colors.
        parenthesized = re.search(r"\(([^,()]+),", str(item.get("name") or ""))
        if not parenthesized or _tokens(parenthesized.group(1)) != _tokens(expected_color):
            return False
    pid = str(item.get("id") or item.get("item_id") or "").strip()
    url = str(item.get("deeplink") or "").strip()
    parsed = urlsplit(url)
    domain = parsed.hostname or ""
    if (not re.fullmatch(r"[A-Z0-9]{12,24}", pid)
            or domain not in {"www.flipkart.com", "flipkart.com"}
            or parsed.scheme != "https"
            or parse_qs(parsed.query).get("pid", [""])[0] != pid):
        return False
    return True


def _positive_price(value):
    if isinstance(value, bool):
        return None
    try:
        price = float(value)
        return price if math.isfinite(price) and price > 0 else None
    except (TypeError, ValueError):
        return None


def normalize_search_response(payload, product, observed_at=""):
    """Return a research RetailerOffer; fail closed for ambiguous/missing evidence."""
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("QuickCommerce search did not succeed")
    data = payload.get("data") or {}
    if data.get("platform") != "Flipkart" or not isinstance(data.get("products"), list):
        raise ValueError("Unexpected QuickCommerce response schema/platform")
    matched = [x for x in data["products"] if _valid_listing(x, product)]
    if not matched:
        return None
    # Stable matching: if color unspecified, choose the first matching listing,
    # not the cheapest offer or the API's retailer search rank for recommendation.
    item = matched[0]
    available = item.get("available")
    if not isinstance(available, bool):
        return None
    price = _positive_price(item.get("offer_price"))
    if available and price is None:
        return None
    raw = {
        "product_id": product.product_id,
        "retailer_product_id": item["id"],
        "brand": product.brand,
        "model": product.model,
        "variant": product.variant,
        "title": item["name"],
        "price": price if available else None,
        "mrp": _positive_price(item.get("mrp")),
        "currency": str(item.get("currency") or "INR"),
        "availability": "in_stock" if available else "out_of_stock",
        "product_url": item["deeplink"],
        "source": SOURCE,
        "confidence": 0.0,  # not an official/independently verified source
        "observed_at": observed_at,
        "metadata": {
            "source_type": SOURCE,
            "publication_authorized": False,
            "identity_match_method": "strict_model_ram_storage_color_pid",
            "provider_request_id": str(payload.get("request_id") or ""),
            "provider_result_count": data.get("total_results"),
            "provider_platform": "Flipkart",
            "evidence_observed_at": observed_at,
        },
    }
    if raw["currency"] != "INR":
        raise ValueError("Unexpected currency for Flipkart India")
    return normalize_offer("flipkart", raw)


class QuickCommerceFlipkartConnector:
    """Opt-in connector for dry-run/explicit research; not in default manager."""
    name = "flipkart"
    live_data_available = False  # never claim authorized/publishable live offers

    def __init__(self, *, lat=28.6315, lon=77.2167, pincode="110001", fixture=None, api_key=None, opener=urlopen):
        self.lat, self.lon = float(lat), float(lon)
        self.pincode = str(pincode).strip()
        if not re.fullmatch(r"[1-9][0-9]{5}", self.pincode):
            raise ValueError("Valid 6-digit Indian pincode required")
        self.fixture = fixture
        self.api_key = api_key
        self.opener = opener

    def get_offer(self, product):
        payload, observed = self.search(f"{product.brand} {product.model} {product.variant}")
        return normalize_search_response(payload, product, observed_at=observed)

    def search(self, query):
        """One bounded provider search; caller must validate identity before use."""
        return self.fetch_observation("search", "Flipkart", q=query)

    def fetch_observation(self, endpoint, platform, **parameters):
        """Reuse private transport for attributed comparison data, not affiliate offers."""
        if platform not in {"Amazon", "Flipkart", "Croma"}:
            raise ValueError("Unsupported comparison platform")
        if endpoint not in {"search", "item"} or (platform == "Croma" and endpoint != "item"):
            raise ValueError("Unsupported comparison endpoint")
        if set(parameters) != ({"q"} if endpoint == "search" else {"item_id"}):
            raise ValueError("Unexpected comparison parameters")
        if self.fixture is not None:
            payload = self.fixture
            observed = ""  # fixtures are historical samples, never fresh evidence
        else:
            key = self.api_key or os.environ.get("QUICKCOMMERCE_API_KEY")
            if not key:
                raise RuntimeError("Set QUICKCOMMERCE_API_KEY privately for a live request")
            params = urlencode({**parameters, "lat": self.lat, "lon": self.lon,
                                "platform": platform, "pincode": self.pincode})
            request = Request(BASE_URL + "/v1/" + endpoint + "?" + params,
                              headers={"X-API-Key": key, "Accept": "application/json"})
            with self.opener(request, timeout=15) as response:
                payload = json.load(response)
            observed = datetime.now(timezone.utc).isoformat()
        return payload, observed


def dry_run(fixture_path, product):
    payload = json.loads(Path(fixture_path).read_text(encoding="utf-8"))
    offer = QuickCommerceFlipkartConnector(fixture=payload).get_offer(product)
    if offer is None:
        return {"status": "NO_EXACT_MATCH", "publishable": False}
    return {
        "status": "RESEARCH_ONLY",
        "product_id": offer.product_id,
        "retailer_product_id": offer.retailer_product_id,
        "price_observation": offer.price,
        "mrp_observation": offer.mrp,
        "availability_observation": offer.availability,
        "source": offer.source,
        "publishable": False,
    }

