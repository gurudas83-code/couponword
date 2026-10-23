#!/usr/bin/env python3

from __future__ import annotations

import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from retailer_contract import RetailerOffer
from product_evidence_store import variant_signature_from_text
from retail_price_evidence import CACHE_MAX_AGE_SECONDS, retailer_host_allowed


ROOT = Path(__file__).resolve().parent.parent
OFFERS_DB = ROOT / "data" / "retailer_offers.json"


def load_offer_database() -> dict[str, Any]:
    if not OFFERS_DB.exists():
        return {
            "version": 1,
            "offers": [],
        }

    return json.loads(
        OFFERS_DB.read_text(encoding="utf-8-sig")
    )


def save_offer_database(data: dict[str, Any]) -> None:
    OFFERS_DB.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(
        data,
        indent=2,
        ensure_ascii=False,
    )

    # Replace the authoritative file only after a complete, flushed JSON
    # document exists.  This keeps a process interruption from leaving a
    # truncated offer store that the API cannot parse after restart.
    temporary_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=OFFERS_DB.parent,
            prefix=f".{OFFERS_DB.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
            temporary_path = handle.name
        os.replace(temporary_path, OFFERS_DB)
        temporary_path = None
    finally:
        if temporary_path:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


def add_verified_offer(
    offer: RetailerOffer,
) -> None:

    if not offer.product_id:
        raise ValueError(
            "Canonical product_id is required."
        )

    if not offer.retailer:
        raise ValueError(
            "Retailer name is required."
        )

    if not offer.retailer_product_id:
        raise ValueError(
            "Retailer product identifier is required."
        )

    data = load_offer_database()

    offers = data.setdefault("offers", [])

    key = (
        offer.product_id,
        offer.retailer,
        offer.retailer_product_id,
    )

    new_record = offer.to_dict()

    for index, existing in enumerate(offers):
        existing_key = (
            existing.get("product_id"),
            existing.get("retailer"),
            existing.get("retailer_product_id"),
        )

        if existing_key == key:
            offers[index] = new_record
            save_offer_database(data)
            return

    offers.append(new_record)
    save_offer_database(data)


def find_fresh_verified_offer(
    *,
    product_id: str,
    brand: str = "",
    model: str = "",
    variant: str = "",
    now: datetime | None = None,
    require_in_stock: bool = True,
) -> dict[str, Any] | None:
    """Return one exact, recent offer from the authoritative offer store.

    This is a read-only bridge for recommendation eligibility.  It accepts
    only an exact canonical product/variant, an approved product URL, a
    positive price, and an observation within the normal six-hour freshness
    window.  First-party selected-SKU URLs are additionally bound to the
    stored retailer product identifier.
    """
    product_id = str(product_id or "").strip()
    expected_brand = str(brand or "").strip().casefold()
    expected_model = " ".join(str(model or "").split()).casefold()
    expected_variant = variant_signature_from_text(variant)
    if not product_id:
        return None

    current_time = now or datetime.now(timezone.utc)
    for record in load_offer_database().get("offers", []):
        if not isinstance(record, dict) or str(record.get("product_id") or "").strip() != product_id:
            continue

        if expected_brand and str(record.get("brand") or "").strip().casefold() != expected_brand:
            continue
        if expected_model and " ".join(str(record.get("model") or "").split()).casefold() != expected_model:
            continue
        if expected_variant and variant_signature_from_text(record.get("variant")) != expected_variant:
            continue

        if require_in_stock and str(record.get("availability") or "").strip().casefold() != "in_stock":
            continue

        try:
            price = float(record.get("price"))
        except (TypeError, ValueError):
            continue
        if not math.isfinite(price) or price <= 0:
            continue

        metadata = record.get("metadata") if isinstance(record.get("metadata"), dict) else {}
        source_url = str(metadata.get("evidence_source_url") or record.get("product_url") or "").strip()
        if not source_url or not retailer_host_allowed(source_url):
            continue

        retailer = str(record.get("retailer") or "").strip().lower()
        retailer_product_id = str(record.get("retailer_product_id") or "").strip()
        parsed = urlparse(source_url)
        if retailer == "vivo":
            selected_sku = parse_qs(parsed.query).get("skuId", [""])[0]
            if not selected_sku or selected_sku.casefold() != retailer_product_id.casefold():
                continue

        observed_text = str(metadata.get("evidence_observed_at") or record.get("last_checked") or "").strip()
        try:
            observed = datetime.fromisoformat(observed_text.replace("Z", "+00:00"))
            if observed.tzinfo is None:
                continue
            observed = observed.astimezone(timezone.utc)
            age_seconds = (current_time.astimezone(timezone.utc) - observed).total_seconds()
        except (TypeError, ValueError):
            continue
        if age_seconds < 0 or age_seconds > CACHE_MAX_AGE_SECONDS:
            continue

        result = dict(record)
        result["price"] = price
        result["verified_at"] = observed.isoformat()
        result["source_url"] = source_url
        result["age_seconds"] = round(age_seconds)
        result["evidence_method"] = str(
            metadata.get("evidence_source_type") or record.get("source") or "stored_verified_offer"
        ).strip()
        return result

    return None


if __name__ == "__main__":
    data = load_offer_database()

    print("\nCOUPON WORLD RETAILER OFFER STORE")
    print("Database :", OFFERS_DB)
    print("Version  :", data.get("version"))
    print("Offers   :", len(data.get("offers", [])))
