#!/usr/bin/env python3
"""Refresh normalized, authorized affiliate offers from a configured feed.

The feed is intentionally provider-neutral.  A provider adapter must return
``{"offers": [...]}`` using the normalized fields already consumed by the
publication gate.  The existing store is never changed unless every row in
the feed passes the same fail-closed checks used for public offers.
"""
from __future__ import annotations

import argparse
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from retailer_publication_gate import evaluate_offer

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data" / "retailer_offers.json"
TOP30 = ROOT / "data" / "top30_research_pilot_20261113.json"


def load_top30_model_keys(path: Path = TOP30) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    rows = payload.get("selected_models", []) if isinstance(payload, dict) else []
    keys = {
        re.sub(r"\s+", " ", str(row.get("model_key", "")).strip().casefold())
        for row in rows
        if isinstance(row, dict) and str(row.get("model_key", "")).strip()
    }
    if len(rows) != 30 or len(keys) != 30:
        raise ValueError("approved Top-30 model worklist must contain 30 unique model keys")
    return keys


def offer_model_key(row: dict) -> str:
    explicit = row.get("model_key") or row.get("top30_model_key")
    if explicit:
        return re.sub(r"\s+", " ", str(explicit).strip().casefold())
    brand = re.sub(r"\s+", " ", str(row.get("brand", "")).strip().casefold())
    model = re.sub(r"\s+", " ", str(row.get("model", "")).strip().casefold())
    return f"{brand}|{model}" if brand and model else ""


def valid_affiliate_destination(value: object) -> bool:
    from urllib.parse import urlparse

    parsed = urlparse(str(value or "").strip())
    return parsed.scheme == "https" and bool(parsed.netloc) and parsed.path not in {"", "/"}


def fetch_feed(url: str, token: str = "") -> dict:
    headers = {"Accept": "application/json", "User-Agent": "CouponWorldAffiliateRefresh/1.0"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        if response.status != 200:
            raise RuntimeError(f"affiliate feed returned HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8"))
    if isinstance(payload, list):
        payload = {"offers": payload}
    if not isinstance(payload, dict) or not isinstance(payload.get("offers"), list):
        raise ValueError("affiliate feed must be a JSON object with an offers array")
    return payload


def validate_offers(
    rows: list[dict],
    now: datetime,
    max_age_hours: int,
    top30_keys: set[str] | None = None,
) -> list[dict]:
    if not rows:
        raise ValueError("affiliate feed contains no offers")
    top30_keys = top30_keys or load_top30_model_keys()
    checked: list[dict] = []
    rejected: list[str] = []
    seen_models: set[str] = set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            rejected.append(f"row_{index}:not_an_object")
            continue
        model_key = offer_model_key(row)
        if model_key not in top30_keys:
            rejected.append(f"row_{index}:model_not_in_approved_top30:{model_key or 'missing'}")
            continue
        ok, reason = evaluate_offer(row, now=now, max_age_hours=max_age_hours)
        if not ok:
            rejected.append(f"row_{index}:{reason}")
            continue
        availability = str(row.get("availability", "")).strip().casefold()
        if availability in {"available", "in_stock", "instock"} and not valid_affiliate_destination(row.get("affiliate_url")):
            rejected.append(f"row_{index}:missing_affiliate_destination")
            continue
        seen_models.add(model_key)
        checked.append(row)
    missing = sorted(top30_keys - seen_models)
    if missing:
        rejected.append("missing_top30_models:" + ",".join(missing))
    if rejected:
        raise ValueError("affiliate feed rejected: " + ", ".join(rejected[:8]))
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-url", default=os.environ.get("AFFILIATE_PRICE_FEED_URL", ""))
    parser.add_argument("--token", default=os.environ.get("AFFILIATE_PRICE_FEED_TOKEN", ""))
    parser.add_argument("--max-age-hours", type=int, default=6)
    parser.add_argument("--store", type=Path, default=STORE)
    parser.add_argument("--top30", type=Path, default=TOP30)
    args = parser.parse_args()
    if not args.feed_url:
        print("AFFILIATE_FEED_NOT_CONFIGURED: no public offer data changed")
        return 0
    now = datetime.now(timezone.utc)
    payload = fetch_feed(args.feed_url, args.token)
    top30_keys = load_top30_model_keys(args.top30)
    offers = validate_offers(payload["offers"], now, args.max_age_hours, top30_keys)
    refreshed_at = now.isoformat(timespec="seconds")
    output = {
        "version": 2,
        "watch": "india_top30_mobile_price_watch",
        "model_count": len(top30_keys),
        "offers": offers,
        "refreshed_at_utc": refreshed_at,
    }
    args.store.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "UPDATED", "watch": output["watch"], "model_count": len(top30_keys), "offer_rows": len(offers), "refreshed_at_utc": refreshed_at}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

