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
from datetime import datetime, timezone
from pathlib import Path
import sys
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))
from retailer_publication_gate import evaluate_offer

ROOT = Path(__file__).resolve().parents[1]
STORE = ROOT / "data" / "retailer_offers.json"


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


def validate_offers(rows: list[dict], now: datetime, max_age_hours: int) -> list[dict]:
    if not rows:
        raise ValueError("affiliate feed contains no offers")
    checked: list[dict] = []
    rejected: list[str] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            rejected.append(f"row_{index}:not_an_object")
            continue
        ok, reason = evaluate_offer(row, now=now, max_age_hours=max_age_hours)
        if not ok:
            rejected.append(f"row_{index}:{reason}")
            continue
        checked.append(row)
    if rejected:
        raise ValueError("affiliate feed rejected: " + ", ".join(rejected[:8]))
    return checked


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--feed-url", default=os.environ.get("AFFILIATE_PRICE_FEED_URL", ""))
    parser.add_argument("--token", default=os.environ.get("AFFILIATE_PRICE_FEED_TOKEN", ""))
    parser.add_argument("--max-age-hours", type=int, default=6)
    parser.add_argument("--store", type=Path, default=STORE)
    args = parser.parse_args()
    if not args.feed_url:
        print("AFFILIATE_FEED_NOT_CONFIGURED: no public offer data changed")
        return 0
    now = datetime.now(timezone.utc)
    payload = fetch_feed(args.feed_url, args.token)
    offers = validate_offers(payload["offers"], now, args.max_age_hours)
    output = {"version": 1, "offers": offers, "refreshed_at_utc": now.isoformat(timespec="seconds")}
    args.store.write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "UPDATED", "offer_rows": len(offers), "refreshed_at_utc": output["refreshed_at_utc"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

