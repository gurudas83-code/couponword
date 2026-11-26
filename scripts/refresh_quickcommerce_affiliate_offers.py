#!/usr/bin/env python3
"""Refresh the approved India Top-30 offer store from QuickCommerce.

This is the one paid price-watch path. It makes exactly one bounded Flipkart
search per approved Top-30 model, validates the returned SKU, and derives the
physical RAM/storage/colour variant from that same listing. Verified results
are published even when an individual model has no current exact listing;
that model is reported as a refresh failure and is omitted rather than given
an invented or stale price.

The QuickCommerce deeplink is a retailer buying destination. The compatibility
``affiliate_url`` field is populated for the existing offer contract, but the
metadata deliberately does not claim that the provider deeplink carries a
commission or that a purchase will succeed.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

ROOT = Path(__file__).resolve().parents[1]
for import_path in (ROOT, ROOT / "python"):
    if str(import_path) not in sys.path:
        sys.path.insert(0, str(import_path))

from quickcommerce_flipkart_adapter import (  # noqa: E402
    QuickCommerceFlipkartConnector,
    _positive_price,
    _tokens,
)
from retailer_publication_gate import evaluate_offer  # noqa: E402
from scripts.quickcommerce_catalogue_audit import (  # noqa: E402
    listing_candidate,
    load_targets,
    query_for,
)


SOURCE = "quickcommerce_authorized_api"
DEFAULT_STORE = ROOT / "data" / "retailer_offers.json"
DEFAULT_TOP30 = ROOT / "data" / "top30_research_pilot_20261113.json"
TOP30_COUNT = 30
PID_PATTERN = re.compile(r"[A-Z0-9]{12,24}")
RAM_PATTERN = re.compile(r"\b(\d{1,3})\s*GB\s*RAM\b", re.I)
STORAGE_PATTERN = re.compile(r"\b(\d{1,4})\s*(GB|TB)\b", re.I)
UNSAFE_LISTING = re.compile(r"renewed|refurbished|pre.?owned|open.?box|virtual|extended\s+ram", re.I)


def load_top30_model_keys(path: Path = DEFAULT_TOP30) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("selected_models", []) if isinstance(payload, dict) else []
    keys = [
        re.sub(r"\s+", " ", str(row.get("model_key", "")).strip().casefold())
        for row in rows
        if isinstance(row, dict) and str(row.get("model_key", "")).strip()
    ]
    if len(rows) != TOP30_COUNT or len(keys) != TOP30_COUNT or len(set(keys)) != TOP30_COUNT:
        raise ValueError("approved Top-30 model worklist must contain 30 unique model keys")
    return keys


def load_top30_targets(top30_path: Path = DEFAULT_TOP30) -> list[dict]:
    approved = load_top30_model_keys(top30_path)
    by_key = {row["audit_id"]: row for row in load_targets("mobiles")}
    missing = [key for key in approved if key not in by_key]
    if missing:
        raise ValueError("Top-30 model cards missing from the 232-card catalogue: " + ",".join(missing))
    return [by_key[key] for key in approved]


def _listing_id(item: dict) -> str:
    return str(item.get("id") or item.get("item_id") or "").strip()


def _listing_url(item: dict) -> str:
    return str(item.get("deeplink") or "").strip()


def _positive_finite(value: object) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number > 0 else None


def _storage_values(title: str) -> list[int]:
    values = []
    for match in STORAGE_PATTERN.finditer(title):
        # A title's "8 GB RAM" token is not physical storage.
        if re.match(r"\s*RAM\b", title[match.end():], re.I):
            continue
        number, unit = match.groups()
        values.append(int(number) * (1024 if unit.upper() == "TB" else 1))
    return values


def _variant_from_listing(item: dict) -> dict[str, object] | None:
    """Extract one exact physical configuration from the returned listing."""
    title = str(item.get("name") or "").strip()
    quantity = str(item.get("quantity") or "").strip()
    combined = title + " " + quantity
    if not title or UNSAFE_LISTING.search(combined):
        return None

    ram_values = [int(value) for value in RAM_PATTERN.findall(combined)]
    if not ram_values:
        # Some provider listings expose the handset memory as a bare single
        # GB token in quantity (for example `8 GB`) rather than `8 GB RAM`.
        # Treat only one 1–32 GB quantity value as RAM; storage remains bound
        # to the product title and ambiguous values still fail closed.
        quantity_values = [int(value) for value in re.findall(r"\b(\d{1,2})\s*GB\b", quantity, re.I)]
        if len(set(quantity_values)) == 1:
            ram_values = quantity_values
    if len(set(ram_values)) != 1 or not 1 <= ram_values[0] <= 32:
        return None
    storage_values = _storage_values(title)
    if len(set(storage_values)) != 1 or storage_values[0] < 32:
        return None
    ram_gb, storage_gb = ram_values[0], storage_values[0]

    color = ""
    memory_group = None
    for match in re.finditer(r"\(([^()]*)\)", title):
        if re.search(r"\b\d{1,4}\s*(?:GB|TB)\b", match.group(1), re.I):
            memory_group = match.group(1)
    if memory_group:
        color = re.sub(r"\b\d{1,4}\s*(?:GB|TB)\b", "", memory_group, flags=re.I)
        color = re.sub(r"\s*,\s*$", "", color).strip(" ,")
    if not color:
        # A SKU ID still prevents a customer from confusing two capacity
        # listings when the provider does not expose colour text.
        color = "Colour not stated"

    return {
        "ram_gb": ram_gb,
        "storage_gb": storage_gb,
        "color": color,
        "variant": f"{ram_gb}GB/{storage_gb}GB · {color}",
    }


def _valid_exact_item(item: object, row: dict) -> bool:
    if not isinstance(item, dict) or not listing_candidate(item, row):
        return False
    pid = _listing_id(item)
    url = urlsplit(_listing_url(item))
    if (
        not PID_PATTERN.fullmatch(pid)
        or url.scheme != "https"
        or url.hostname not in {"flipkart.com", "www.flipkart.com"}
        or url.username
        or url.password
        or url.port not in {None, 443}
        or "/p/" not in url.path
        or parse_qs(url.query).get("pid") != [pid]
        or str(item.get("currency") or "") != "INR"
        or type(item.get("available")) is not bool
        or _variant_from_listing(item) is None
    ):
        return False
    available = item["available"]
    return not available or _positive_finite(item.get("offer_price")) is not None


def select_exact_listing(payload: dict, row: dict) -> tuple[dict, dict[str, object]]:
    if not isinstance(payload, dict) or payload.get("status") != "success":
        raise ValueError("QuickCommerce search did not succeed")
    data = payload.get("data") or {}
    if data.get("platform") != "Flipkart" or not isinstance(data.get("products"), list):
        raise ValueError("Unexpected QuickCommerce response schema/platform")
    matches = [item for item in data["products"] if _valid_exact_item(item, row)]
    if not matches:
        raise ValueError("no exact current Flipkart listing for " + row["audit_id"])
    # Keep provider order stable. Prefer the first available exact SKU so an
    # out-of-stock result never hides another currently buyable SKU; do not
    # sort by price and do not silently mix RAM/storage/colour variants.
    item = next((candidate for candidate in matches if candidate["available"]), matches[0])
    variant = _variant_from_listing(item)
    if variant is None:  # guarded above; keep the failure explicit for callers
        raise ValueError("exact listing variant could not be derived")
    return item, variant


def build_offer(item: dict, variant: dict[str, object], row: dict, *, observed_at: str, pincode: str, request_id: str) -> dict:
    pid = _listing_id(item)
    product_url = _listing_url(item)
    available = item["available"] is True
    price = _positive_price(item.get("offer_price")) if available else None
    checked_at = str(observed_at or "").strip()
    if not checked_at:
        raise ValueError("live QuickCommerce response did not include an observation timestamp")
    offer = {
        "model_key": row["audit_id"],
        "product_id": row["audit_id"],
        "retailer": "flipkart",
        "retailer_product_id": pid,
        "brand": row["brand"],
        "model": row["model"],
        "variant": variant["variant"],
        "title": str(item.get("name") or "").strip(),
        "price": price,
        "mrp": _positive_price(item.get("mrp")),
        "currency": "INR",
        "availability": "in_stock" if available else "out_of_stock",
        "product_url": product_url,
        # Compatibility field for the existing buying-link contract. The
        # metadata makes the attribution limitation explicit.
        "affiliate_url": product_url,
        "source": SOURCE,
        "source_type": SOURCE,
        "verification_status": "VERIFIED",
        "confidence": 0.92,
        "checked_at": checked_at,
        "observed_at": checked_at,
        "last_checked": checked_at,
        "metadata": {
            "source_type": SOURCE,
            "publication_authorized": True,
            "link_type": "quickcommerce_provider_deeplink",
            "affiliate_attribution": "not_asserted",
            "identity_match_method": "strict_model_brand_variant_pid",
            "provider": "QuickCommerce API",
            "provider_platform": "Flipkart",
            "provider_request_id": request_id,
            "provider_query": query_for(row),
            "pincode": pincode,
            "ram_gb": variant["ram_gb"],
            "storage_gb": variant["storage_gb"],
            "color": variant["color"],
            "evidence_observed_at": checked_at,
        },
    }
    return offer


def refresh_targets(targets: list[dict], connector, *, delay_seconds: float = 1.0, now: datetime | None = None) -> dict:
    if len(targets) != TOP30_COUNT:
        raise ValueError("the paid price-watch batch must contain exactly 30 targets")
    if delay_seconds < 0:
        raise ValueError("delay_seconds cannot be negative")
    now = now or datetime.now(timezone.utc)
    offers = []
    failures = []
    seen_keys = set()
    for index, row in enumerate(targets):
        key = str(row.get("audit_id") or "").strip().casefold()
        if not key or key in seen_keys:
            raise ValueError("duplicate or missing Top-30 target: " + (key or "unknown"))
        seen_keys.add(key)
        try:
            payload, observed = connector.search(query_for(row))
            item, variant = select_exact_listing(payload, row)
            offer = build_offer(
                item,
                variant,
                row,
                observed_at=observed,
                pincode=connector.pincode,
                request_id=str(payload.get("request_id") or ""),
            )
            ok, reason = evaluate_offer(offer, now=now, max_age_hours=6)
            if not ok:
                raise ValueError(f"publication gate rejected selected listing ({reason})")
            offers.append(offer)
        except Exception as error:
            failures.append({
                "model_key": key,
                "error": str(error),
                "error_type": type(error).__name__,
            })
        if delay_seconds and index + 1 < len(targets):
            time.sleep(delay_seconds)
    if not offers:
        reason = failures[0]["error"] if failures else "no verified offers returned"
        raise ValueError("Top-30 refresh produced no publishable offers: " + reason)
    refreshed_at = max(str(offer["checked_at"]) for offer in offers)
    return {
        "version": 2,
        "watch": "india_top30_mobile_price_watch",
        "provider": SOURCE,
        "model_count": TOP30_COUNT,
        "offer_count": len(offers),
        "refresh_failures": failures,
        "refreshed_at_utc": refreshed_at,
        "offers": offers,
    }


def write_store(payload: dict, path: Path = DEFAULT_STORE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
            temporary = Path(handle.name)
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def merge_with_previous_store(payload: dict, path: Path) -> dict:
    """Keep the last verified offer when today's exact lookup is unavailable.

    A failed lookup must never erase a previously verified price. Fresh offers
    replace the same model, while unrelated legacy/retailer rows remain in the
    store. Freshness gates still decide whether a retained row may be shown as
    a current offer; this merge only preserves the audit/history record.
    """
    if not path.is_file():
        payload["retained_previous_offer_count"] = 0
        return payload
    try:
        previous = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        payload["retained_previous_offer_count"] = 0
        return payload
    if not isinstance(previous, dict) or not isinstance(previous.get("offers"), list):
        payload["retained_previous_offer_count"] = 0
        return payload

    fresh = [offer for offer in payload.get("offers", []) if isinstance(offer, dict)]
    fresh_keys = {
        str(offer.get("model_key") or offer.get("product_id") or "").strip().casefold()
        for offer in fresh
    }
    retained = []
    for offer in previous["offers"]:
        if not isinstance(offer, dict):
            continue
        key = str(offer.get("model_key") or offer.get("product_id") or "").strip().casefold()
        if key and key not in fresh_keys:
            retained.append(offer)
    payload["offers"] = fresh + retained
    payload["offer_count"] = len(payload["offers"])
    payload["retained_previous_offer_count"] = len(retained)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pincode", default="110001")
    parser.add_argument("--delay-seconds", type=float, default=1.0)
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--top30", type=Path, default=DEFAULT_TOP30)
    args = parser.parse_args()
    if not os.environ.get("QUICKCOMMERCE_API_KEY"):
        raise SystemExit("QUICKCOMMERCE_API_KEY is required; no offer data changed")
    targets = load_top30_targets(args.top30)
    connector = QuickCommerceFlipkartConnector(pincode=args.pincode)
    payload = refresh_targets(targets, connector, delay_seconds=args.delay_seconds)
    payload = merge_with_previous_store(payload, args.store)
    write_store(payload, args.store)
    print(json.dumps({
        "status": "UPDATED",
        "watch": payload["watch"],
        "model_count": payload["model_count"],
        "offer_count": payload["offer_count"],
        "retained_previous_offer_count": payload["retained_previous_offer_count"],
        "refresh_failures": payload["refresh_failures"],
        "refreshed_at_utc": payload["refreshed_at_utc"],
    }))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())



