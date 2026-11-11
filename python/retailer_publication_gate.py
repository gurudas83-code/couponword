#!/usr/bin/env python3
"""Fail-closed publication gate for retailer offers.

This module deliberately does not fetch prices. It only admits offers that an
authorized connector has already verified, with an exact identity, a current
timestamp, a usable product URL, and an explicit availability state.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_STORE = ROOT / "data" / "retailer_offers.json"
DEFAULT_MAX_AGE_HOURS = 6
AUTHORIZED_SOURCES = {"amazon_creators_api", "amazon_pa_api", "flipkart_affiliate_feed", "croma_authorized_feed"}
VALID_AVAILABILITY = {"available", "in_stock", "instock", "unavailable", "out_of_stock", "outofstock"}


def _parse_time(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _is_https_product_url(value: object) -> bool:
    parsed = urlparse(str(value or "").strip())
    if parsed.scheme != "https" or not parsed.netloc or parsed.path in {"", "/"} or parsed.query:
        return False
    path = parsed.path.lower().rstrip("/")
    return not any(token in path for token in ("/search", "/s", "/q/", "/category", "/browse"))


def evaluate_offer(record: dict, *, now: datetime, max_age_hours: int) -> tuple[bool, str]:
    if str(record.get("verification_status", "")).upper() != "VERIFIED":
        return False, "verification_status_not_verified"
    if str(record.get("source_type", "")).strip() not in AUTHORIZED_SOURCES:
        return False, "source_not_authorized"
    if not str(record.get("retailer_product_id", "")).strip():
        return False, "missing_retailer_product_id"
    if not _is_https_product_url(record.get("product_url")):
        return False, "missing_exact_product_url"
    if str(record.get("availability", "")).lower() not in VALID_AVAILABILITY:
        return False, "availability_unknown"
    checked = _parse_time(record.get("checked_at"))
    if checked is None:
        return False, "missing_checked_at"
    if checked > now + timedelta(minutes=5):
        return False, "checked_at_in_future"
    if now - checked > timedelta(hours=max_age_hours):
        return False, "offer_stale"
    if str(record.get("availability", "")).lower() in {"available", "in_stock", "instock"}:
        try:
            if float(record.get("price")) <= 0:
                return False, "available_offer_missing_price"
        except (TypeError, ValueError):
            return False, "available_offer_missing_price"
    return True, "eligible"


def evaluate_store(path: Path = DEFAULT_STORE, *, now: datetime | None = None, max_age_hours: int = DEFAULT_MAX_AGE_HOURS) -> dict:
    now = now or datetime.now(timezone.utc)
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    records = payload.get("offers", []) if isinstance(payload, dict) else []
    eligible = []
    rejected = []
    for record in records:
        ok, reason = evaluate_offer(record, now=now, max_age_hours=max_age_hours)
        if ok:
            eligible.append(record)
        else:
            rejected.append({"product_id": record.get("product_id", ""), "retailer": record.get("retailer", ""), "reason": reason})
    return {
        "checked_at_utc": now.isoformat(timespec="seconds"),
        "max_age_hours": max_age_hours,
        "stored_offer_rows": len(records),
        "publishable_offer_rows": len(eligible),
        "status": "READY" if eligible else "BLOCKED_NO_FRESH_VERIFIED_OFFERS",
        "rejected": rejected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--store", type=Path, default=DEFAULT_STORE)
    parser.add_argument("--max-age-hours", type=int, default=DEFAULT_MAX_AGE_HOURS)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()
    report = evaluate_store(args.store, max_age_hours=args.max_age_hours)
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "READY" or not args.strict else 1


if __name__ == "__main__":
    raise SystemExit(main())
