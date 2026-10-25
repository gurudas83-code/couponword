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
import ipaddress
import re
import socket
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urljoin, urlparse, urlunparse

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

# Manufacturer stores are accepted only as first-party evidence sources.  The
# product-page path checks below prevent a generic support, news, or search
# page from becoming a price source.
ALLOWED_MANUFACTURER_HOSTS = (
    "oneplus.in",
    "samsung.com",
    "shop.vivo.com",
    "shop.lavamobiles.com",
)

REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/152.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-IN,en;q=0.9",
}

def clean(value: object) -> str:
    return " ".join(str(value or "").split())


def _amazon_live_offer_fetch_available(source_url: str) -> bool:
    """Allow Amazon page fetches only when its configured provider is live."""
    try:
        host = (_canonical_hostname(urlparse(clean(source_url)).hostname) or "")
    except Exception:
        host = ""
    if not (host == "amazon.in" or host.endswith(".amazon.in")):
        return True
    try:
        from amazon_data_provider import get_default_provider

        return bool(get_default_provider().api_available)
    except Exception:
        return False

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


def _frozen_offer_price_evidence(candidate: dict[str, Any]) -> dict[str, Any] | None:
    """Accept only the committed exact-ASIN offer used by offline replay."""
    if candidate.get("source") != "FROZEN_CATALOGUE_INTEGRATION":
        return None

    offer = candidate.get("frozen_offer")
    if not isinstance(offer, dict):
        return None

    candidate_asin = clean(candidate.get("asin")).upper()
    offer_asin = clean(offer.get("retailer_product_id")).upper()
    source_url = clean(offer.get("product_url"))
    parsed = urlparse(source_url)
    path_asin = clean((parsed.path or "").rstrip("/").rsplit("/", 1)[-1]).upper()
    try:
        price = float(offer.get("price"))
    except (TypeError, ValueError):
        return None

    if (
        not candidate_asin
        or candidate_asin != offer_asin
        or path_asin != offer_asin
        or parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "www.amazon.in"
        or offer.get("retailer") != "amazon"
        or offer.get("evidence_method") != "amazon_primary_buybox"
        or offer.get("availability") not in {"in_stock", "out_of_stock"}
        or price <= 0
        or not clean(offer.get("observed_at"))
        or not clean(offer.get("identity_evidence_url")).startswith("https://")
    ):
        return None

    return {
        "price": price,
        "currency": "INR",
        "verified": True,
        "status": "verified_from_frozen_offer_snapshot",
        "source_type": "amazon_primary_buybox",
        "source_url": source_url,
        "source_host": "www.amazon.in",
        "verified_at": clean(offer.get("observed_at")),
        "availability": offer.get("availability"),
        "reason": "Exact-ASIN offer from committed frozen evidence snapshot",
        "evidence_method": "amazon_primary_buybox",
        "snapshot_id": clean(offer.get("snapshot_id")),
        "identity_evidence_url": clean(offer.get("identity_evidence_url")),
    }

def extract_price_mentions(text: str) -> list[float]:
    values: list[object] = []

    for pattern in PRICE_PATTERNS:
        for match in pattern.finditer(clean(text)):
            values.append(match.group(1))

    return unique_prices(values)

def retailer_host_allowed(url: str) -> bool:
    try:
        host = _canonical_hostname(urlparse(url).hostname)
    except Exception:
        return False

    return any(
        host == allowed or host.endswith("." + allowed)
        for allowed in ALLOWED_RETAIL_HOSTS
    ) or manufacturer_product_url_allowed(url)

def manufacturer_product_url_allowed(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = _canonical_hostname(parsed.hostname)
        path = (parsed.path or "").lower().rstrip("/")
    except Exception:
        return False

    if not any(host == allowed or host.endswith("." + allowed)
               for allowed in ALLOWED_MANUFACTURER_HOSTS):
        return False

    if host.endswith("oneplus.in"):
        return path in {"/15", "/oneplus-15"} or path.startswith("/oneplus-15/")

    if host.endswith("samsung.com"):
        return path.startswith("/in/smartphones/") and "/buy" in path

    # First-party vivo store pages expose a selected SKU in the query.  Keep
    # that exact-SKU requirement so a generic product page cannot become a
    # current offer for an arbitrary RAM/storage variant.
    if host.endswith("shop.vivo.com"):
        sku_id = parse_qs(parsed.query).get("skuId", [""])[0]
        return bool(
            re.fullmatch(r"/in/product/\d+", path)
            and re.fullmatch(r"\d+", sku_id)
        )

    # Lava's first-party Shopify product pages identify the selected variant
    # with a numeric variant query.  A collection, search or support page is
    # never an offer source.
    if host.endswith("shop.lavamobiles.com"):
        variant_id = parse_qs(parsed.query).get("variant", [""])[0]
        return bool(
            re.fullmatch(r"/products/[a-z0-9][a-z0-9-]*", path)
            and re.fullmatch(r"\d+", variant_id)
        )

    return False


REDIRECT_STATUSES = {301, 302, 303, 307, 308}
MAX_SAFE_REDIRECTS = 5


def _canonical_hostname(host: object) -> str:
    """Return the ASCII, lower-case hostname used by the allow-list."""
    value = str(host or "").strip().rstrip(".").lower()
    if not value:
        return ""
    try:
        return value.encode("idna").decode("ascii")
    except (UnicodeError, AttributeError):
        return ""


def _public_dns_addresses(host: str, port: int) -> tuple[bool, str]:
    """Reject private, loopback and otherwise non-public DNS destinations."""
    try:
        records = socket.getaddrinfo(
            host,
            port,
            type=socket.SOCK_STREAM,
        )
    except (OSError, socket.gaierror):
        return False, "Retail source DNS resolution failed"

    addresses = {
        str(record[4][0]).split("%", 1)[0]
        for record in records
        if len(record) > 4 and record[4]
    }
    if not addresses:
        return False, "Retail source DNS returned no addresses"

    for address in addresses:
        try:
            parsed = ipaddress.ip_address(address)
        except ValueError:
            return False, "Retail source DNS returned an invalid address"
        if not parsed.is_global:
            return False, "Retail source resolves to a non-public network"

    return True, ""


def _safe_retailer_destination(url: str) -> tuple[bool, str]:
    """Validate a URL before any request is made to it."""
    try:
        parsed = urlparse(clean(url))
        host = _canonical_hostname(parsed.hostname)
        port = parsed.port
    except (ValueError, TypeError):
        return False, "Retail source URL is malformed"

    if parsed.scheme.lower() != "https":
        return False, "Retail source must use HTTPS"
    if not host or parsed.username or parsed.password or parsed.fragment:
        return False, "Retail source URL contains an unsafe destination"
    if port not in (None, 443):
        return False, "Retail source must use HTTPS port 443"

    canonical_url = urlunparse(
        (
            "https",
            host if port in (None, 443) else f"{host}:{port}",
            parsed.path,
            parsed.params,
            parsed.query,
            "",
        )
    )
    if not retailer_host_allowed(canonical_url):
        return False, "URL is not an approved retail price source"

    return _public_dns_addresses(host, port or 443)


def _get_with_safe_redirects(url: str) -> tuple[Any | None, str, str]:
    """Fetch an approved page while authorizing every redirect hop first."""
    current_url = clean(url)

    for _ in range(MAX_SAFE_REDIRECTS + 1):
        allowed, reason = _safe_retailer_destination(current_url)
        if not allowed:
            return None, current_url, f"REJECTED: {reason}"

        try:
            response = requests.get(
                current_url,
                headers=REQUEST_HEADERS,
                timeout=(4, 8),
                allow_redirects=False,
            )
        except requests.RequestException as error:
            return None, current_url, (
                f"Retail page fetch failed safely: "
                f"{type(error).__name__}: {error}"
            )

        response_url = str(getattr(response, "url", "") or current_url).strip()
        if response_url != current_url:
            response_allowed, response_reason = _safe_retailer_destination(
                response_url
            )
            if not response_allowed:
                return None, response_url, f"REJECTED: {response_reason}"

        if response.status_code not in REDIRECT_STATUSES:
            return response, response_url, ""

        location = str(
            getattr(response, "headers", {}).get("Location", "") or ""
        ).strip()
        if not location:
            return None, current_url, "REJECTED: Retail redirect omitted a destination"
        current_url = urljoin(response_url or current_url, location)

    return None, current_url, "REJECTED: Retail source exceeded the safe redirect limit"

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

def jsonld_availability(value: Any) -> list[str]:
    found: list[str] = []
    if isinstance(value, list):
        for item in value:
            found.extend(jsonld_availability(item))
        return found
    if not isinstance(value, dict):
        return found
    availability = clean(value.get("availability")).lower()
    if availability:
        if "instock" in availability or "in stock" in availability:
            found.append("in_stock")
        elif "outofstock" in availability or "out of stock" in availability:
            found.append("out_of_stock")
    for nested in value.values():
        if isinstance(nested, (dict, list)):
            found.extend(jsonld_availability(nested))
    return found

def fetch_structured_price(url: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "price": None,
        "prices_found": [],
        "availability": "unknown",
        "status": "unavailable",
        "reason": "No structured retailer price found",
        "http_status": None,
        "evidence_method": None,
    }

    allowed, reason = _safe_retailer_destination(url)
    if not allowed:
        result["status"] = "rejected"
        result["reason"] = reason
        return result

    response, final_url, fetch_reason = _get_with_safe_redirects(url)
    if response is None:
        rejected = fetch_reason.startswith("REJECTED:")
        result["status"] = "rejected" if rejected else "fetch_error"
        result["reason"] = fetch_reason.removeprefix("REJECTED: ").strip()
        return result

    result["http_status"] = response.status_code

    if response.status_code != 200:
        result["status"] = "fetch_error"
        result["reason"] = (
            f"Retail page returned HTTP {response.status_code}"
        )
        return result

    final_allowed, final_reason = _safe_retailer_destination(final_url)
    if not final_allowed:
        result["status"] = "rejected"
        result["reason"] = final_reason
        return result

    try:
        soup = BeautifulSoup(response.text, "lxml")
    except Exception:
        soup = BeautifulSoup(response.text, "html.parser")

    structured_values: list[object] = []
    structured_payloads: list[Any] = []

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

        structured_payloads.append(payload)
        structured_values.extend(jsonld_prices(payload))

    jsonld_found = unique_prices(structured_values)
    jsonld_stock = jsonld_availability(structured_payloads)
    if jsonld_stock and len(set(jsonld_stock)) == 1:
        result["availability"] = jsonld_stock[0]

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

        availability_nodes = soup.select(
            "#availability, "
            "#availabilityInsideBuyBox_feature_div"
        )

        availability_text = " ".join(
            node.get_text(" ", strip=True)
            for node in availability_nodes
        ).strip().lower()

        has_add_to_cart = bool(
            soup.select("#add-to-cart-button")
        )
        has_buy_now = bool(
            soup.select("#buy-now-button")
        )
        has_out_of_stock = bool(
            soup.select("#outOfStock")
        )

        if (
            "in stock" in availability_text
            and not has_out_of_stock
            and (has_add_to_cart or has_buy_now)
        ):
            result["availability"] = "in_stock"
        elif (
            has_out_of_stock
            or "currently unavailable" in availability_text
            or "out of stock" in availability_text
        ):
            result["availability"] = "out_of_stock"

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
    frozen = _frozen_offer_price_evidence(candidate)
    if frozen is not None:
        return frozen

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
        and search_price_method in {
    "amazon_exact_asin_search_card",
    "amazon_exact_asin_search_card_offer_text",
}
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
                "verified_at": datetime.now(timezone.utc).isoformat(),
                "availability": "unknown",
                "reason": (
                    "Exact Amazon ASIN-bound search-card price verified"
                ),
                "evidence_method": search_price_method,
            })

            # Keep the exact-ASIN search-card price as a safe fallback,
            # but continue to the exact retailer page. The page may
            # provide stronger buy-box price and availability evidence.
            # If page verification fails, the verified search-card
            # evidence already stored in result remains usable.

    # Second preference for visitor latency: reuse only a genuinely
    # recent verified price observation.
    #
    # This cache contains price evidence only. It does not establish
    # current stock/availability, so availability must remain unknown.
    if result.get("verified") is True:
        return result

    cached = get_recent_cached_price(source_url)

    if cached:
        result.update({
            "price": cached.get("price"),
            "verified": True,
            "availability": "unknown",
            "status": "verified_from_recent_cache",
            "verified_at": cached.get("verified_at"),
            "reason": (
                "Reused a recent verified retailer price observation; "
                "current availability was not re-verified"
            ),
            "evidence_method": "recent_verified_cache",
            "cached_evidence": cached,
        })

        return result

    if not _amazon_live_offer_fetch_available(source_url):
        result["status"] = "provider_unavailable"
        result["reason"] = (
            "Authorized Amazon provider is unavailable; current retailer "
            "page retrieval was skipped"
        )
        return result

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
                "availability": (
                    page_result.get("availability") or "unknown"
                ),
                "status": "verified_from_retail_page",
                "verified_at": datetime.now(timezone.utc).isoformat(),
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
            "verified_at": cached.get("verified_at"),
            "availability": "unknown",
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
