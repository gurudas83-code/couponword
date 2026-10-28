"""Issue 11 isolated price-truth classification and audit helpers.

This module is deliberately independent of production storage and rendering.
It gives reports/tests one canonical vocabulary for distinguishing live prices
from historical or reference values without mutating catalogue data.
"""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Iterable


CURRENT_VERIFIED = "CURRENT_VERIFIED"
HISTORICAL_EXPIRED = "HISTORICAL_EXPIRED"
HISTORICAL_UNVERIFIED = "HISTORICAL_UNVERIFIED"
REFERENCE_PRICE = "REFERENCE_PRICE"
PRICE_UNAVAILABLE = "PRICE_UNAVAILABLE"

PRICE_TTL_SECONDS = 6 * 60 * 60
APPROVED_HOSTS = ("amazon.in", "flipkart.com", "croma.com", "reliancedigital.in")


def parse_aware_timestamp(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _positive_price(value: Any) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0
    except (TypeError, ValueError):
        return False


def _approved_url(value: Any) -> bool:
    text = str(value or "").lower()
    return text.startswith("https://") and any(host in text for host in APPROVED_HOSTS)


def classify_price_record(
    record: dict[str, Any] | None,
    *,
    now: datetime,
    ttl_seconds: int = PRICE_TTL_SECONDS,
) -> str:
    """Classify one price without changing the supplied record."""
    if not record:
        return PRICE_UNAVAILABLE
    if str(record.get("price_kind") or record.get("source_type") or "").lower() in {
        "reference",
        "mrp",
        "manufacturer_mrp",
        "list_price",
    }:
        return REFERENCE_PRICE
    if not _positive_price(record.get("price")):
        return HISTORICAL_UNVERIFIED
    required = (record.get("canonical_product_id"), record.get("retailer_product_id"), record.get("retailer"))
    observed = parse_aware_timestamp(record.get("evidence_observed_at") or record.get("observed_at") or record.get("last_checked"))
    if not all(str(value or "").strip() for value in required) or not _approved_url(record.get("product_url") or record.get("source_url")):
        return HISTORICAL_UNVERIFIED
    if str(record.get("availability") or "").lower() != "in_stock" or observed is None:
        return HISTORICAL_UNVERIFIED
    now_utc = now.astimezone(timezone.utc)
    age = (now_utc - observed).total_seconds()
    if age < 0:
        return HISTORICAL_UNVERIFIED
    if age <= ttl_seconds:
        return CURRENT_VERIFIED
    return HISTORICAL_EXPIRED


def classify_records(records: Iterable[dict[str, Any]], *, now: datetime) -> list[dict[str, Any]]:
    result = []
    for record in records:
        item = dict(record)
        item["price_status"] = classify_price_record(record, now=now)
        result.append(item)
    return result


def display_price(record: dict[str, Any] | None, *, now: datetime) -> str:
    status = classify_price_record(record, now=now)
    if status == CURRENT_VERIFIED:
        return f"₹{float(record['price']):,.0f}"
    if status == REFERENCE_PRICE:
        return f"Reference ₹{float(record['price']):,.0f}"
    return "Price unavailable"
