#!/usr/bin/env python3
"""One-time bounded read-only API discovery for 19 added India phone models.

QuickCommerce is an independent research API, not an authorized Flipkart
affiliate feed. Observations never become public live prices, stock or images.
No retries, schedules, silent provider fallback or unchecked bulk requests.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

from python.india_missing_eight_pages import import_eight
from python.india_recent_eight_import import build_recent
from scripts import quickcommerce_catalogue_audit as audit
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector

MAX_CALLS = 19
OUTPUT = ROOT / "private_observations" / "nineteen_new_mobile_api_probe.json"


def approved_targets() -> list[dict]:
    cards = import_eight()["model_cards"] + build_recent()["model_cards"]
    # Preserve the existing approved one-time cap: newly added Karbonn
    # identities are published research-only but are not silently probed.
    cards = [card for card in cards if card.get("api_probe_eligible", True)]
    core = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8"))
    core_keys = {x["model_key"] for x in core["model_cards"]}
    ids = [x["model_key"] for x in cards]
    if len(ids) != 19 or len(set(ids)) != 19 or core_keys.intersection(ids):
        raise ValueError("Only 19 distinct research-only models outside the frozen core")
    for card in cards:
        if (card["status"] != "RESEARCH_ONLY" or card["verified_retailer_links"]
                or card.get("photo") or card.get("price") is not None):
            raise ValueError("Unsafe importer record")
    return [{"audit_id": card["model_key"], "category": "mobiles",
             "brand": card["brand"], "model": card["model"], "photo": None}
            for card in cards]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-calls", type=int, default=0)
    args = parser.parse_args()
    if args.max_calls not in (0, MAX_CALLS):
        parser.error("Only dry-run or one explicitly approved cap of 19 may execute")
    targets = approved_targets()
    if not args.max_calls:
        print(json.dumps({"status": "DRY_RUN", "targets": len(targets),
                          "calls_attempted": 0, "public_price_publications": 0}))
        return 0
    if not os.environ.get("QUICKCOMMERCE_API_KEY"):
        print(json.dumps({"status": "API_SECRET_UNAVAILABLE", "targets": 19,
                          "calls_attempted": 0, "public_price_publications": 0}))
        return 0
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    def checkpoint(report):
        OUTPUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                          encoding="utf-8")
    report = audit.run(targets, QuickCommerceFlipkartConnector(), max_calls=MAX_CALLS,
                       delay_seconds=1.0, checkpoint=checkpoint)
    print(json.dumps({"status": "RESEARCH_API_PROBE_ONLY",
                      "requests": report["calls_attempted"],
                      "candidate_status_counts": report["status_counts"],
                      "stop_reason": report["stopped_reason"],
                      "published_prices": 0,
                      "published_photos": 0,
                      "publication_blocker": "Provider not authorized as an exact retailer price/official image feed"}))
    return 1 if report["stopped_reason"] else 0


if __name__ == "__main__":
    raise SystemExit(main())