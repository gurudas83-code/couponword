#!/usr/bin/env python3
"""Bounded six-hour Coupon World observation agent.

Reuses the existing QuickCommerce catalogue audit, model-identity gate and
retailer publication gate. Paid calls are capped at four per invocation.
This agent never modifies public catalogues, ranking, photos or offers.
Third-party API observations and images are private research evidence only.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "python"))

from scripts import quickcommerce_catalogue_audit as audit
from quickcommerce_flipkart_adapter import QuickCommerceFlipkartConnector
from retailer_publication_gate import evaluate_store

SLOT_SECONDS = 6 * 60 * 60
START = datetime(2026, 11, 17, tzinfo=timezone.utc)
HARD_CALL_CAP = 4
PRIVATE_DIR = ROOT / "private_observations"
DEFAULT_OUTPUT = PRIVATE_DIR / "six_hour_research_monitor.json"


def slot_index(now: datetime) -> int:
    """UTC six-hour slots; stable even when GitHub Actions runs late."""
    if now.tzinfo is None:
        raise ValueError("now must have a timezone")
    return max(0, int((now.astimezone(timezone.utc) - START).total_seconds() // SLOT_SECONDS))


def _rotate(rows: list[dict], count: int, slot: int) -> list[dict]:
    if not rows or count <= 0:
        return []
    return [rows[(slot * count + offset) % len(rows)]
            for offset in range(min(count, len(rows)))]


def select_targets(now: datetime, *, limit: int = HARD_CALL_CAP) -> list[dict]:
    """Three mobile queries plus one model-code-qualified TV/earbud query.

    Deliberately rotates instead of querying all 272 entries four times daily.
    Missing TV/earbud model codes are excluded to avoid paid ambiguous searches.
    """
    if not 0 <= limit <= HARD_CALL_CAP:
        raise ValueError("Per-run limit must be between 0 and 4")
    if limit == 0:
        return []
    slots = slot_index(now)
    mobile = audit.load_targets("mobiles")
    others = [row for row in audit.load_targets("all")
              if row["category"] in {"tvs", "earbuds"} and str(row.get("model_code") or "").strip()]
    secondary_calls = 1 if limit >= 2 and others else 0
    mobile_calls = limit - secondary_calls
    selected = _rotate(mobile, mobile_calls, slots)
    selected += _rotate(others, secondary_calls, slots)
    if len({row["audit_id"] for row in selected}) != len(selected):
        raise ValueError("Duplicate research target identity")
    return selected


def catalogue_health() -> dict:
    mobile = json.loads((ROOT / "data/mobile_research_catalogue.json").read_text(encoding="utf-8-sig"))
    other = json.loads((ROOT / "data/india_tv_earbuds_40_catalogue.json").read_text(encoding="utf-8-sig"))
    cards = mobile["model_cards"]
    photos = sum(card.get("image_status") == "VERIFIED_MATCH" and bool(card.get("photo")) for card in cards)
    source_models = sum(bool(card.get("source_urls")) for card in cards)
    evidence_fields = sum(
        sum(bool(field.get("source_url")) for field in (card.get("specifications") or {}).values()
            if isinstance(field, dict))
        for card in cards
    )
    counts = Counter("tvs" if row["category"] == "tvs" else "earbuds" for row in other["records"])
    return {
        "mobile_models": len(cards),
        "tv_models": counts["tvs"],
        "earbud_models": counts["earbuds"],
        "mobile_photos_with_existing_verified_references": photos,
        "mobile_photos_missing_or_unverified": len(cards) - photos,
        "mobile_models_with_recorded_source_urls": source_models,
        "specification_fields_with_recorded_source": evidence_fields,
        "specification_links_checked_live_by_this_agent": 0,
        "separate_spec_and_link_monitor": "mobile-integrity-6h.yml",
    }


def public_offer_health() -> dict:
    result = evaluate_store(ROOT / "data/retailer_offers.json", max_age_hours=6)
    return {
        "status": result["status"],
        "stored_offer_rows": result["stored_offer_rows"],
        "publishable_offer_rows_under_existing_gate": result["publishable_offer_rows"],
        "research_observations_promoted_to_offers": 0,
    }


def execute(*, now: datetime, live: bool, max_calls: int,
            connector=None, output: Path = DEFAULT_OUTPUT) -> dict:
    if not 0 <= max_calls <= HARD_CALL_CAP or (live and max_calls == 0):
        raise ValueError("Live mode requires 1..4 calls; offline mode permits 0..4")
    if not live and max_calls:
        raise ValueError("Offline mode cannot spend requests")
    output = output.resolve()
    if not output.is_relative_to(PRIVATE_DIR.resolve()):
        raise ValueError("Evidence output must stay inside private_observations")
    chosen = select_targets(now, limit=max_calls if live else HARD_CALL_CAP)
    report = {
        "schema_version": 1,
        "mode": "PRIVATE_API_RESEARCH" if live else "OFFLINE_READ_ONLY",
        "checked_at_utc": now.astimezone(timezone.utc).isoformat(),
        "slot": slot_index(now),
        "source": "quickcommerce_third_party_research",
        "pincode": getattr(connector, "pincode", "110001"),
        "selected_targets": [{"audit_id": row["audit_id"], "category": row["category"]} for row in chosen],
        "catalogue": catalogue_health(),
        "public_offers": public_offer_health(),
        "ranking_modified": False,
        "public_files_modified": False,
        "new_public_prices": 0,
        "new_public_stock_claims": 0,
        "new_public_images": 0,
        "publication_authorized": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    def save(research):
        report["provider_research"] = research
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    connector = connector or QuickCommerceFlipkartConnector()
    research = audit.run(chosen, connector, max_calls=max_calls if live else 0,
                         delay_seconds=1.0, checkpoint=save)
    report["provider_research"] = research
    save(research)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Permit up to four paid searches per run")
    parser.add_argument("--max-calls", type=int, default=0, help="Paid searches; default zero")
    parser.add_argument("--pincode", default="110001")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if args.live and not os.environ.get("QUICKCOMMERCE_API_KEY"):
        parser.error("QUICKCOMMERCE_API_KEY must be configured in GitHub Secrets")
    try:
        report = execute(now=datetime.now(timezone.utc), live=args.live,
                         max_calls=args.max_calls,
                         connector=QuickCommerceFlipkartConnector(pincode=args.pincode),
                         output=args.output)
    except (ValueError, OSError, KeyError) as error:
        parser.error(str(error))
    provider = report["provider_research"]
    status = {
        "mode": report["mode"],
        "calls_attempted": provider["calls_attempted"],
        "candidate_counts": provider.get("status_counts", {}),
        "stopped_reason": provider["stopped_reason"],
        "mobile_photos": report["catalogue"]["mobile_photos_with_existing_verified_references"],
        "public_price_updates": 0,
        "publishable": False,
    }
    print(json.dumps(status, sort_keys=True))
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as stream:
            stream.write("### Coupon World six-hour research monitor\n\n")
            stream.write(f"- Mode: {report['mode']}\n")
            stream.write(f"- Third-party search calls: {provider['calls_attempted']} / {HARD_CALL_CAP}\n")
            stream.write(f"- Existing verified photo references: {status['mobile_photos']} / {report['catalogue']['mobile_models']}\n")
            stream.write(f"- Model-candidate statuses: {provider.get('status_counts', {})}\n")
            stream.write(f"- Existing offer publication gate: {report['public_offers']['status']}\n")
            stream.write("- Public prices/images/rankings modified: **none**\n")
            stream.write("- Findings are location-specific, research-only; review exact variants and rights.\n")
    return 1 if provider["stopped_reason"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
