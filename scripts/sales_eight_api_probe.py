#!/usr/bin/env python3
"""One-time, capped QuickCommerce research check of missing sales-report phones.

Uses the existing model-identity and evidence audit. Never promotes API data to
public prices, stock, images or quality rankings. No retries, schedules or
unbounded queries. The eight-key list is source-pinned and separately validated.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

from python.india_missing_eight_pages import import_eight
from scripts import quickcommerce_catalogue_audit as audit
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

MAX_CALLS = 2
OUT = ROOT / "private_observations" / "sales_eight_api_probe.json"


def approved_targets() -> list[dict]:
    payload = import_eight()
    cards = payload["model_cards"]
    if len(cards) != 8 or payload["mode"] != "EIGHT_SOURCE_REVIEWED_MARKET_ADDITIONS_NO_LIVE_OFFERS":
        raise ValueError("Market intake was not reviewed")
    targets = [
        {"audit_id": card["model_key"], "category": "mobiles",
         "brand": card["brand"], "model": card["model"], "photo": None}
        for card in cards
    ]
    if len({row["audit_id"] for row in targets}) != 8:
        raise ValueError("Duplicate market model in API scope")
    return targets


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-calls", type=int, default=0)
    args = parser.parse_args()
    if not 0 <= args.max_calls <= MAX_CALLS:
        parser.error("Capped one-time request limit is 0..2")
    if args.max_calls and not os.environ.get("QUICKCOMMERCE_API_KEY"):
        print(json.dumps({"status": "SKIPPED_API_KEY_NOT_CONFIGURED", "attempts": 0}))
        return 0
    targets = approved_targets()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    def save(report):
        OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    report = audit.run(targets, QuickCommerceFlipkartConnector(), max_calls=args.max_calls,
                       delay_seconds=1.0, checkpoint=save)
    print(json.dumps({
        "status": "PRIVATE_RESEARCH_ONLY", "calls_attempted": report["calls_attempted"],
        "candidate_statuses": report["status_counts"],
        "stopped_reason": report["stopped_reason"],
        "public_file_changes": 0, "photo_rights_granted": False,
    }, ensure_ascii=False))
    return 1 if report["stopped_reason"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
