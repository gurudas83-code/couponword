#!/usr/bin/env python3
"""Evidence-safe A-to-Z release readiness: audit only, never a price importer.

Joins the 232-model built catalogue, 232-row offline price evidence audit,
historical third-party API observations and 623 unanswered-query diagnostics.
Does NOT declare any saved price fresh or change public recommendation gates.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scripts.build_price_evidence_coverage import build as build_price_coverage

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def build(root=ROOT, *, as_of=None):
    as_of = as_of or datetime.now(timezone.utc)
    if as_of.tzinfo is None:
        raise ValueError("as_of must be timezone-aware")
    as_of = as_of.astimezone(timezone.utc)
    public = read(root / "public/data/mobile_research_catalogue.json")
    raw = read(root / "data/mobile_research_catalogue.json")
    saved = read(root / "data/retailer_price_observations.json")
    query_audit = read(root / "data/mobile_623_evidence_audit_20261121.json")
    coverage = build_price_coverage(root)
    cards = public["model_cards"]
    if len(cards) != 232 or len(set(c["model_key"] for c in cards)) != 232:
        raise ValueError("Published 232-model registry incomplete or duplicated")
    by_price = {row["model_key"]: row for row in coverage["model_rows"]}
    by_raw = {row["model_key"]: row for row in raw["model_cards"]}
    if set(by_price) != set(by_raw) or set(by_raw) != {c["model_key"] for c in cards}:
        raise ValueError("Model key mismatch between published, source and price audit")
    if sum(query_audit["counts"].values()) != 623 or len(query_audit["rows"]) != 623:
        raise ValueError("Unanswered query audit no longer reconciles")
    saved_models = saved.get("models", {})
    freshness = timedelta(hours=float(saved.get("freshness_hours", 6)))
    if freshness <= timedelta(0):
        raise ValueError("Invalid observation freshness")
    rows = []
    all_status = Counter()
    for c in cards:
        key = c["model_key"]
        old = by_price[key]
        original = by_raw[key]
        historical = saved_models.get(key, [])
        observed = [offer for conf in historical for offer in conf.get("offers", [])]
        latest = None
        fresh = 0
        for offer in observed:
            raw_time = offer.get("observed_at")
            try:
                stamp = datetime.fromisoformat(str(raw_time).replace("Z", "+00:00"))
                if stamp.tzinfo is None:
                    continue
                stamp = stamp.astimezone(timezone.utc)
            except (ValueError, TypeError):
                continue
            if latest is None or stamp > latest:
                latest = stamp
            if as_of - freshness <= stamp <= as_of:
                fresh += 1
        fields = sum(
            1 for spec in (c.get("specifications") or {}).values()
            if isinstance(spec, dict) and spec.get("value") is not None
            and str(spec.get("source_url") or "").startswith("https://")
        )
        photo = c.get("photo") or {}
        image_verified = c.get("image_status") == "VERIFIED_MATCH" and bool(photo.get("url"))
        # Historical third-party observations cannot become affiliate offers.
        # An observed price does not prove availability for today's checkout.
        missing = []
        if c.get("status") != "OFFICIAL_VERIFIED" or fields < 2:
            missing.append("MANUFACTURER_SPEC_OR_IDENTITY_REVIEW")
        if not image_verified:
            missing.append("LICENSED_EXACT_MODEL_PHOTO")
        if old["price_reference_inr"] is None:
            missing.append("NO_POSITIVE_HISTORICAL_PRICE_EVIDENCE")
        missing.append("CURRENT_AUTHORIZED_EXACT_SKU_OFFER")
        if not c.get("verified_india_variants"):
            missing.append("OFFICIAL_INDIA_RAM_STORAGE_VARIANT_REVIEW")
        row = {
            "model_key": key, "brand": c.get("brand"), "model": c.get("model"),
            "research_status": c.get("status"), "source_spec_fields": fields,
            "exact_photo_verified": image_verified,
            "exact_india_variants": len(c.get("verified_india_variants") or []),
            "historical_price_status": old["status"],
            "historical_price_inr": old["price_reference_inr"],
            "historical_price_source_date": old.get("source_date"),
            "api_observation_variants": len(historical),
            "api_observation_offers": len(observed),
            "latest_api_observation_at": latest.isoformat() if latest else None,
            "saved_observations_inside_freshness_window": fresh,
            "authorized_current_offer_verified": False,
            "missing_gates": missing,
        }
        rows.append(row)
        all_status.update([c.get("status", "UNKNOWN")])
    image_missing = [r for r in rows if not r["exact_photo_verified"]]
    maker_missing = [r for r in rows if "MANUFACTURER_SPEC_OR_IDENTITY_REVIEW" in r["missing_gates"]]
    sku_missing = [r for r in rows if "OFFICIAL_INDIA_RAM_STORAGE_VARIANT_REVIEW" in r["missing_gates"]]
    price_missing = [r for r in rows if r["historical_price_inr"] is None]
    return {
        "schema_version": 1,
        "mode": "OFFLINE_RELEASE_READINESS_NOT_LIVE_PRICES",
        "as_of_utc": as_of.isoformat(),
        "policy": "Research records and attributed API observations do not prove buy eligibility. No live price/stock claims are produced.",
        "totals": {
            "core_models": len(rows),
            "research_statuses": dict(all_status),
            "with_source_linked_spec_fields": sum(r["source_spec_fields"] > 0 for r in rows),
            "official_verified_with_2_source_fields": sum(
                r["research_status"] == "OFFICIAL_VERIFIED" and r["source_spec_fields"] >= 2 for r in rows
            ),
            "exact_licensed_photo_verified": len(rows) - len(image_missing),
            "photo_review_remaining": len(image_missing),
            "manufacturer_or_identity_review_remaining": len(maker_missing),
            "exact_india_variant_review_remaining": len(sku_missing),
            "historical_price_evidence": len(rows) - len(price_missing),
            "historical_price_missing": len(price_missing),
            "api_observed_phone_models": sum(r["api_observation_variants"] > 0 for r in rows),
            "non_phone_observation_ids": len(set(saved_models) - {r["model_key"] for r in rows}),
            "api_observed_offer_rows_for_phones": sum(r["api_observation_offers"] for r in rows),
            "observations_currently_inside_6h_window": sum(r["saved_observations_inside_freshness_window"] for r in rows),
            "authorized_live_checkout_prices_verified_by_this_audit": 0,
            "previous_query_gaps": query_audit["counts"],
            "previous_incomplete_queries": len(query_audit["rows"]),
        },
        "coverage_by_historical_5k_band": coverage["budget_bands"],
        "work_queues": {
            "price_missing": [r["model_key"] for r in price_missing],
            "image_missing": [r["model_key"] for r in image_missing],
            "manufacturer_review": [r["model_key"] for r in maker_missing],
            "india_variant_missing": [r["model_key"] for r in sku_missing],
        },
        "models": rows,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=Path("mobile-readiness-232.json"))
    args = parser.parse_args()
    report = build(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("MOBILE_A_TO_Z_READINESS " + json.dumps(report["totals"], ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
