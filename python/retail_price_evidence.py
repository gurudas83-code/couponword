#!/usr/bin/env python3
"""
Coupon World AI OS
Retail Price Evidence v1.2

Trust model:
1. Exact structured price from exact retailer product page.
2. Recent cached price that was previously verified from structured evidence.
3. Otherwise UNKNOWN.

Discovery snippets remain hints only and never independently satisfy
a hard budget constraint when they contain mixed commerce content.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import requests
from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = ROOT / "data" / "retail_price_cache.json"

# A cached price may satisfy the hard-budget check only while recent.
CACHE_MAX_AGE_SECONDS = 6 * 60 * 60


PRICE_PATTERNS = [
    re.compile(r"₹\s*([\d,]+(?:\.\d{1,2})?)"),
    re.compile(r"\bRs\.?\s*([\d,]+(?:\.\d{1,2})?)", re.I),
    re.compile(r"\bINR\s*([\d,]+(?:\.\d{1,2})?)", re.I),
]

ALLOWED_RETAIL_HOSTS = (
    "amazon.in",
    "flipkart.com",
    "croma.com",
    "reliancedigital.in",
    "vijaysales.com",
)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 Chrome/131 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}


def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def normalize_url(url: str) -> str:
    url = clean(url)

    try:
        parsed = urlparse(url)

        return urlunparse(
            (
                parsed.scheme.lower(),
                parsed.netloc.lower(),
                parsed.path.rstrip("/"),
                "",
                "",
                "",
            )
        )
    except Exception:
        return url


def normalize_amount(value: object) -> float | None:
    text = clean(value).replace(",", "")

    text = (
        text.replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .strip()
    )

    try:
        amount = float(text)
    except (TypeError, ValueError):
        return None

    if amount < 50 or amount > 1000000:
        return None

    return amount


def unique_prices(values: list[object]) -> list[float]:
    found: list[float] = []

    for value in values:
        amount = normalize_amount(value)

        if amount is not None and amount not in found:
            found.append(amount)

    return found


def extract_price_mentions(text: str) -> list[float]:
    values: list[object] = []

    for pattern in PRICE_PATTERNS:
        for match in pattern.finditer(clean(text)):
            values.append(match.group(1))

    return unique_prices(values)


def retailer_host_allowed(url: str) -> bool:
    try:
        host = (urlparse(url).hostname or "").lower()
    except Exception:
        return False

    return any(
        host == allowed or host.endswith("." + allowed)
        for allowed in ALLOWED_RETAIL_HOSTS
    )


def load_cache() -> dict[str, Any]:
    if not CACHE_PATH.exists():
        return {}

    try:
        payload = json.loads(
            CACHE_PATH.read_text(encoding="utf-8-sig")
        )
    except Exception:
        return {}

    return payload if isinstance(payload, dict) else {}


def save_cache(cache: dict[str, Any]) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)

    temp = CACHE_PATH.with_suffix(".tmp")

    temp.write_text(
        json.dumps(
            cache,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    temp.replace(CACHE_PATH)


def cache_verified_price(
    *,
    url: str,
    price: float,
    source_host: str,
    evidence_method: str,
) -> None:
    key = normalize_url(url)

    if not key:
        return

    cache = load_cache()

    cache[key] = {
        "price": price,
        "currency": "INR",
        "verified": True,
        "source_url": url,
        "source_host": source_host,
        "evidence_method": evidence_method,
        "verified_at": utc_now_iso(),
    }

    try:
        save_cache(cache)
    except OSError:
        # Cache failure must never break shopping intelligence.
        pass


def get_recent_cached_price(url: str) -> dict[str, Any] | None:
    key = normalize_url(url)

    if not key:
        return None

    record = load_cache().get(key)

    if not isinstance(record, dict):
        return None

    if record.get("verified") is not True:
        return None

    price = normalize_amount(record.get("price"))

    if price is None:
        return None

    verified_at = clean(record.get("verified_at"))

    if not verified_at:
        return None

    try:
        timestamp = datetime.fromisoformat(
            verified_at.replace("Z", "+00:00")
        )

        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)

        age_seconds = (
            datetime.now(timezone.utc) - timestamp
        ).total_seconds()
    except Exception:
        return None

    if age_seconds < 0 or age_seconds > CACHE_MAX_AGE_SECONDS:
        return None

    result = dict(record)
    result["age_seconds"] = round(age_seconds)
    result["cache_key"] = key

    return result


def jsonld_prices(value: Any) -> list[object]:
    prices: list[object] = []

    if isinstance(value, list):
        for item in value:
            prices.extend(jsonld_prices(item))
        return prices

    if not isinstance(value, dict):
        return prices

    item_type = value.get("@type")

    if isinstance(item_type, list):
        types = {str(x).lower() for x in item_type}
    else:
        types = {str(item_type or "").lower()}

    if "product" in types:
        offers = value.get("offers")

        if isinstance(offers, dict):
            for key in ("price", "lowPrice"):
                if offers.get(key) not in (None, ""):
                    prices.append(offers.get(key))

        elif isinstance(offers, list):
            for offer in offers:
                if not isinstance(offer, dict):
                    continue

                for key in ("price", "lowPrice"):
                    if offer.get(key) not in (None, ""):
                        prices.append(offer.get(key))

    if "offer" in types:
        for key in ("price", "lowPrice"):
            if value.get(key) not in (None, ""):
                prices.append(value.get(key))

    for nested in value.values():
        if isinstance(nested, (dict, list)):
            prices.extend(jsonld_prices(nested))

    return prices


def fetch_structured_price(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "price": None,
        "prices_found": [],
        "status": "unavailable",
        "reason": "No structured retailer price found",
        "http_status": None,
        "evidence_method": None,
    }

    if not retailer_host_allowed(url):
        result["status"] = "rejected"
        result["reason"] = "URL is not an approved retail price source"
        return result

    try:
        response = requests.get(
            url,
            headers=REQUEST_HEADERS,
            timeout=(4, 8),
            allow_redirects=True,
        )
    except requests.RequestException as error:
        result["status"] = "fetch_error"
        result["reason"] = (
            f"Retail page fetch failed safely: "
            f"{type(error).__name__}: {error}"
        )
        return result

    result["http_status"] = response.status_code

    if response.status_code != 200:
        result["status"] = "fetch_error"
        result["reason"] = (
            f"Retail page returned HTTP {response.status_code}"
        )
        return result

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception:
        soup = BeautifulSoup(response.text, "html.parser")

    structured_values: list[object] = []

    for script in soup.find_all(
        "script",
        attrs={"type": "application/ld+json"},
    ):
        raw = script.string or script.get_text(" ", strip=True)

        if not raw:
            continue

        try:
            payload = json.loads(raw)
        except Exception:
            continue

        structured_values.extend(jsonld_prices(payload))

    jsonld_found = unique_prices(structured_values)

    if len(jsonld_found) == 1:
        result.update({
            "price": jsonld_found[0],
            "prices_found": jsonld_found,
            "status": "verified",
            "reason": "Exact retailer Product/Offer JSON-LD price found",
            "evidence_method": "json_ld_offer",
        })
        return result

    if len(jsonld_found) > 1:
        result.update({
            "prices_found": jsonld_found,
            "status": "ambiguous",
            "reason": "Multiple structured JSON-LD prices found",
            "evidence_method": "json_ld_offer",
        })
        return result

    # Amazon India does not consistently expose Product/Offer JSON-LD
    # or generic price metadata. On an exact /dp/ ASIN page, use only
    # high-confidence primary buy-box containers.
    #
    # Do NOT use generic ".a-price-whole" or page-wide price text here:
    # those can include MRP, EMI, accessories and related products.
    host = urlparse(response.url).netloc.lower()

    if host == "amazon.in" or host.endswith(".amazon.in"):
        amazon_values: list[object] = []

        # Current Amazon India markup exposes the primary payable
        # amount directly in .priceToPay. Do not scan generic
        # .a-price-whole elements because those also contain MRP,
        # related products, accessories and other non-buy-box prices.
        amazon_selectors = (
            ".priceToPay",
            "#corePriceDisplay_desktop_feature_div .priceToPay",
            "#apex_desktop .priceToPay",
        )

        for selector in amazon_selectors:
            for tag in soup.select(selector):
                text_value = tag.get_text(" ", strip=True)

                # Extract INR amount only from this trusted buy-box
                # container rather than treating its whole text as
                # a numeric value.
                amazon_values.extend(
                    extract_price_mentions(text_value)
                )

        amazon_found = unique_prices(amazon_values)

        if len(amazon_found) == 1:
            result.update({
                "price": amazon_found[0],
                "prices_found": amazon_found,
                "status": "verified",
                "reason": (
                    "Exact Amazon primary buy-box price found"
                ),
                "evidence_method": "amazon_primary_buybox",
            })
            return result

        if len(amazon_found) > 1:
            result.update({
                "prices_found": amazon_found,
                "status": "ambiguous",
                "reason": (
                    "Multiple Amazon primary buy-box prices found"
                ),
                "evidence_method": "amazon_primary_buybox",
            })
            return result

    meta_values: list[object] = []

    meta_selectors = (
        ("property", "product:price:amount"),
        ("property", "og:price:amount"),
        ("name", "price"),
        ("itemprop", "price"),
    )

    for attribute, value in meta_selectors:
        for tag in soup.find_all(attrs={attribute: value}):
            candidate = (
                tag.get("content")
                or tag.get("value")
                or tag.get_text(" ", strip=True)
            )

            if candidate not in (None, ""):
                meta_values.append(candidate)

    meta_found = unique_prices(meta_values)

    if len(meta_found) == 1:
        result.update({
            "price": meta_found[0],
            "prices_found": meta_found,
            "status": "verified",
            "reason": "Exact retailer structured price metadata found",
            "evidence_method": "structured_meta",
        })
        return result

    if len(meta_found) > 1:
        result.update({
            "prices_found": meta_found,
            "status": "ambiguous",
            "reason": "Multiple structured metadata prices found",
            "evidence_method": "structured_meta",
        })

    return result


def build_price_evidence(candidate: dict[str, Any]) -> dict[str, Any]:
    source_url = clean(candidate.get("source_url"))
    source_host = clean(candidate.get("source_host"))
    snippet = clean(candidate.get("snippet"))

    discovery_mentions = extract_price_mentions(snippet)

    result: dict[str, Any] = {
        "price": None,
        "currency": "INR",
        "verified": False,
        "status": "unavailable",
        "source_type": "retailer_price_evidence",
        "source_url": source_url,
        "source_host": source_host,
        "price_mentions": discovery_mentions,
        "reason": "No usable verified price evidence found",
        "evidence_method": None,
    }

    # First preference: exact-ASIN Amazon search-card evidence already
    # captured during live discovery. Accept it only when identity binding
    # is exact and explicit.
    candidate_asin = clean(candidate.get("asin")).upper()
    search_price_text = clean(candidate.get("search_price_text"))
    search_price_method = clean(
        candidate.get("search_price_evidence_method")
    )

    try:
        source_path = urlparse(source_url).path
    except Exception:
        source_path = ""

    url_asin_match = re.search(
        r"/(?:dp|gp/product)/([A-Z0-9]{10})(?:/|$)",
        source_path,
        re.I,
    )

    url_asin = (
        clean(url_asin_match.group(1)).upper()
        if url_asin_match
        else ""
    )

    if (
        candidate_asin
        and url_asin
        and candidate_asin == url_asin
        and search_price_text
        and search_price_method == "amazon_exact_asin_search_card"
        and "amazon.in" in source_host.lower()
    ):
        search_card_price = normalize_amount(search_price_text)

        if search_card_price is not None:
            cache_verified_price(
                url=source_url,
                price=search_card_price,
                source_host=source_host,
                evidence_method=search_price_method,
            )

            result.update({
                "price": search_card_price,
                "verified": True,
                "status": "verified_from_exact_asin_search_card",
                "reason": (
                    "Exact Amazon ASIN-bound search-card price verified"
                ),
                "evidence_method": search_price_method,
            })

            return result

    # Second preference: current structured retailer evidence.
    page_result = fetch_structured_price(source_url)

    result["page_evidence"] = page_result

    if page_result.get("status") == "verified":
        price = normalize_amount(page_result.get("price"))

        if price is not None:
            method = clean(page_result.get("evidence_method"))

            cache_verified_price(
                url=source_url,
                price=price,
                source_host=source_host,
                evidence_method=method,
            )

            result.update({
                "price": price,
                "verified": True,
                "status": "verified_from_retail_page",
                "reason": page_result.get("reason"),
                "evidence_method": method,
            })

            return result

    # If live retailer fetch is blocked or temporarily incomplete,
    # a recently verified structured observation may be reused.
    cached = get_recent_cached_price(source_url)

    if cached:
        result.update({
            "price": cached.get("price"),
            "verified": True,
            "status": "verified_from_recent_cache",
            "reason": (
                "Live retailer price was unavailable; reused a "
                "recent structured price verification"
            ),
            "evidence_method": "recent_verified_cache",
            "cached_evidence": cached,
        })

        return result

    # Discovery snippets are diagnostic hints only.
    if discovery_mentions:
        result["status"] = "ambiguous"
        result["reason"] = (
            "Retail discovery contains price mentions but no current "
            "or recent structured price verification is available"
        )
    else:
        result["status"] = (
            page_result.get("status") or "unavailable"
        )
        result["reason"] = (
            page_result.get("reason")
            or result["reason"]
        )

    return result


if __name__ == "__main__":
    print("Retail Price Evidence v1.2")
    print("Cache:", CACHE_PATH)
    print("Freshness seconds:", CACHE_MAX_AGE_SECONDS)
