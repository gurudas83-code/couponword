"""Single fail-closed purchase CTA eligibility contract for Issue 12."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any
from urllib.parse import urlparse


VERIFIED_BUYABLE = "VERIFIED_BUYABLE"
PRICE_EXPIRED = "PRICE_EXPIRED"
STOCK_UNKNOWN = "STOCK_UNKNOWN"
OUT_OF_STOCK = "OUT_OF_STOCK"
EXACT_VARIANT_UNVERIFIED = "EXACT_VARIANT_UNVERIFIED"
AUTHORIZED_OFFER_UNAVAILABLE = "AUTHORIZED_OFFER_UNAVAILABLE"
PROVIDER_ERROR = "PROVIDER_ERROR"

CTA_TTL_SECONDS = 6 * 60 * 60
RETAILER_HOSTS = {
    "amazon": {"amazon.in"},
    "flipkart": {"flipkart.com"},
    "croma": {"croma.com"},
}
AUTHORIZED_SOURCES = {
    "amazon_primary_buybox",
    "retailer_page_verified",
    "retailer_api_verified",
    "provider_verified",
}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _variant(value: Any) -> str:
    return "".join(ch for ch in _text(value).lower() if ch.isalnum())


def _timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(_text(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _valid_price(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def _valid_retailer_url(retailer: str, value: Any) -> bool:
    try:
        parsed = urlparse(_text(value))
    except ValueError:
        return False
    host = (parsed.hostname or "").lower()
    allowed = RETAILER_HOSTS.get(retailer, set())
    return parsed.scheme == "https" and any(
        host == domain or host.endswith("." + domain) for domain in allowed
    )


def evaluate_offer(
    offer: dict[str, Any] | None,
    *,
    product_id: str,
    variant: str,
    now: datetime,
    provider_error: bool = False,
) -> dict[str, Any]:
    """Return one authoritative, fail-closed decision for a purchase CTA."""
    if provider_error:
        return {"eligible": False, "status": PROVIDER_ERROR, "reason": "provider_error"}
    if not isinstance(offer, dict):
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "missing_offer"}

    offer_product = _text(offer.get("product_id") or offer.get("canonical_product_id"))
    if offer_product and offer_product != _text(product_id):
        return {"eligible": False, "status": EXACT_VARIANT_UNVERIFIED, "reason": "wrong_product"}
    if not _text(offer.get("retailer_product_id")) or not _text(offer.get("variant")):
        return {"eligible": False, "status": EXACT_VARIANT_UNVERIFIED, "reason": "missing_exact_listing_identity"}
    if _variant(offer.get("variant")) != _variant(variant):
        return {"eligible": False, "status": EXACT_VARIANT_UNVERIFIED, "reason": "wrong_ram_or_storage"}

    retailer = _text(offer.get("retailer")).lower().replace(" ", "_")
    source = _text(offer.get("source")).lower()
    if retailer not in RETAILER_HOSTS or source not in AUTHORIZED_SOURCES:
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "unauthorized_source"}
    if not _valid_retailer_url(retailer, offer.get("product_url")):
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "invalid_retailer_destination"}
    if not _valid_price(offer.get("price")):
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "invalid_price"}

    observed = _timestamp(
        offer.get("evidence_observed_at")
        or offer.get("observed_at")
        or offer.get("last_checked")
    )
    if observed is None:
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "missing_or_invalid_observation"}
    age = (now.astimezone(timezone.utc) - observed).total_seconds()
    if age < 0:
        return {"eligible": False, "status": AUTHORIZED_OFFER_UNAVAILABLE, "reason": "future_observation"}
    if age > CTA_TTL_SECONDS:
        return {"eligible": False, "status": PRICE_EXPIRED, "reason": "six_hour_ttl_expired", "age_seconds": age}

    availability = _text(offer.get("availability")).lower()
    if availability == "unknown":
        return {"eligible": False, "status": STOCK_UNKNOWN, "reason": "stock_not_verified"}
    if availability != "in_stock":
        return {"eligible": False, "status": OUT_OF_STOCK, "reason": "not_in_stock"}

    return {
        "eligible": True,
        "status": VERIFIED_BUYABLE,
        "reason": "exact_current_authorized_in_stock_offer",
        "age_seconds": age,
    }


def attach_cta_eligibility(
    offer: dict[str, Any] | None,
    *,
    product_id: str,
    variant: str,
    now: datetime,
) -> dict[str, Any] | None:
    if not isinstance(offer, dict):
        return None
    result = dict(offer)
    result["cta_eligibility"] = evaluate_offer(
        offer, product_id=product_id, variant=variant, now=now
    )
    return result
