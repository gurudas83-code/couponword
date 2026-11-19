#!/usr/bin/env python3
"""Deterministic 232-model research price-evidence classification, NO API calls.

Never promote third-party observations into live offers, buy buttons or ranking.
"""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
WIDTH = 5000
SAFE_RETAILERS = {"amazon", "flipkart", "croma"}
SAFE_HOSTS = {"amazon": "www.amazon.in", "flipkart": "www.flipkart.com", "croma": "www.croma.com"}


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def positive_historical_observations(configurations: list[dict], model_key: str) -> list[dict]:
    results = []
    is_apple = model_key.startswith("apple|")
    for config in configurations:
        storage = config.get("storage_gb")
        ram = config.get("ram_gb")
        # Never transfer the price across unknown storage or RAM configurations.
        if type(storage) is not int or storage <= 0 or (
            not is_apple and (type(ram) is not int or ram <= 0)
        ):
            continue
        if config.get("purchase_eligible") is not False:
            continue
        for offer in config.get("offers") or []:
            price = offer.get("price")
            if offer.get("retailer") not in SAFE_RETAILERS or (
                type(price) not in (int, float) or price <= 0
                or offer.get("availability") != "in_stock"
                or not offer.get("observed_at")
            ):
                continue
            parsed = urlsplit(str(offer.get("product_url") or ""))
            if parsed.scheme != "https" or parsed.hostname != SAFE_HOSTS[offer["retailer"]]:
                continue
            try:
                datetime.fromisoformat(offer["observed_at"].replace("Z", "+00:00"))
            except ValueError:
                continue
            results.append({
                "reference_price_inr": price,
                "ram_gb": ram,
                "storage_gb": storage,
                "color": config.get("color"),
                "retailer": offer["retailer"],
                "observed_at": offer["observed_at"],
                "pincode": config.get("pincode"),
                "retailer_product_id": offer.get("retailer_product_id"),
                "url": offer["product_url"],
                "purchase_eligible": False,
                "ranking_weight": 0,
            })
    # A model may have several variants. The lowest observation belongs only to
    # its exact recorded configuration, not all variants of the same model.
    return sorted(results, key=lambda row: (row["reference_price_inr"], row["observed_at"]))


def build(root: Path = ROOT) -> dict:
    catalogue = load_json(root / "data/mobile_research_catalogue.json")
    workbook = load_json(root / "data/mobile_workbook_research.json")
    observation_file = load_json(root / "data/retailer_price_observations.json")
    records = catalogue["model_cards"]
    entries = workbook["models"]
    by_key = {record["model_key"]: record for record in entries}
    if len(records) != 232 or len(by_key) != 232 or len(entries) != 232:
        raise ValueError("232-model evidence reconciliation failed")
    keys = [record["model_key"] for record in records]
    if len(set(keys)) != len(keys) or set(by_key) != set(keys):
        raise ValueError("Workbook and core catalogue model keys differ")
    if workbook.get("mode") != "DATED_RESEARCH_NOT_LIVE_OFFERS":
        raise ValueError("Unexpected workbook mode")
    if observation_file.get("mode") != "ATTRIBUTED_API_PRICE_OBSERVATIONS":
        raise ValueError("Unexpected third-party observation mode")

    classified = []
    status_counts = Counter()
    for card in records:
        key = card["model_key"]
        source = by_key[key]
        ref = source.get("research_budget_reference")
        candidates = positive_historical_observations(observation_file.get("models", {}).get(key, []), key)
        base = {
            "model_key": key,
            "brand": card.get("brand"),
            "model": card.get("model"),
            "catalogue_status": card.get("status"),
            "ranking_weight": 0,
            "live_price_verified": False,
            "buy_eligible": False,
            "price_purpose": "historical_research_only",
        }
        if ref is not None:
            if (
                not isinstance(ref, dict) or type(ref.get("reference_price_inr")) not in (int, float)
                or ref["reference_price_inr"] <= 0 or ref.get("live_offer") is not False
                or ref.get("ranking_weight") != 0
            ):
                raise ValueError("Unsafe historical workbook reference " + key)
            evidence = {
                "status": "WORKBOOK_DATED_REFERENCE",
                "price_reference_inr": ref["reference_price_inr"],
                "recorded_variant": {"ram_gb": ref.get("ram_gb"), "storage_gb": ref.get("storage_gb")},
                "source_date": workbook.get("research_as_of"),
                "source": ref.get("retailer"),
                "source_url": ref.get("source_url"),
            }
        elif candidates:
            selected = candidates[0]
            evidence = {
                "status": "API_HISTORICAL_VARIANT_OBSERVATION",
                "price_reference_inr": selected["reference_price_inr"],
                "recorded_variant": {"ram_gb": selected["ram_gb"], "storage_gb": selected["storage_gb"], "color": selected["color"]},
                "source_date": selected["observed_at"],
                "source": selected["retailer"],
                "source_url": selected["url"],
                "pincode": selected["pincode"],
                "historical_positive_variants": len(candidates),
            }
        elif key in observation_file.get("models", {}):
            evidence = {"status": "API_ONLY_NO_POSITIVE_IN_STOCK_PRICE", "price_reference_inr": None}
        else:
            evidence = {"status": "NOT_IN_SAVED_API_OBSERVATIONS", "price_reference_inr": None}
        record = {**base, **evidence}
        amount = evidence["price_reference_inr"]
        record["band_floor_inr"] = int(amount // WIDTH) * WIDTH if amount is not None else None
        record["band_ceiling_exclusive_inr"] = record["band_floor_inr"] + WIDTH if amount is not None else None
        classified.append(record)
        status_counts[record["status"]] += 1

    if len(classified) != 232 or sum(status_counts.values()) != 232:
        raise AssertionError("Model total changed")
    bins = []
    for floor in range(0, 200000, WIDTH):
        bucket = [row for row in classified if row["band_floor_inr"] == floor]
        bins.append({
            "floor_inr": floor, "ceiling_exclusive_inr": floor + WIDTH,
            "workbook_count": sum(row["status"] == "WORKBOOK_DATED_REFERENCE" for row in bucket),
            "api_historical_count": sum(row["status"] == "API_HISTORICAL_VARIANT_OBSERVATION" for row in bucket),
            "total_with_some_dated_price_evidence": len(bucket),
        })
    return {
        "schema_version": 1,
        "mode": "OFFLINE_RESEARCH_EVIDENCE_TRIAGE_NOT_LIVE_OFFERS",
        "classification_policy": "One model, one historical recorded variant; model price is NOT the price of other variants.",
        "source_files": ["data/mobile_research_catalogue.json", "data/mobile_workbook_research.json", "data/retailer_price_observations.json"],
        "source_dates": {"workbook": workbook.get("research_as_of"), "api_snapshot": observation_file.get("generated_at")},
        "summary": {
            "total_models": len(classified), "statuses": dict(status_counts),
            "with_any_dated_price_evidence": sum(row["price_reference_inr"] is not None for row in classified),
            "still_missing_positive_price_evidence": sum(row["price_reference_inr"] is None for row in classified),
            "price_beyond_200k": sum(row["band_floor_inr"] is not None and row["band_floor_inr"] >= 200000 for row in classified),
        },
        "budget_bands": bins,
        "model_rows": classified,
        "verification_queue": [
            {"model_key": row["model_key"], "status": row["status"], "brand": row["brand"], "model": row["model"]}
            for row in classified if row["price_reference_inr"] is None
        ],
    }



def export_review_files(report: dict, output_dir: Path) -> dict:
    """Write per-model inventory, strict ₹5k tiers and the complete 103-model queue.

    Derived exclusively from the existing offline evidence engine; never calls
    or charges an API, changes the shopping gate or creates an affiliate offer.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    rows = report["model_rows"]
    queue = report["verification_queue"]
    fields = [
        "model_key", "brand", "model", "status", "catalogue_status",
        "price_reference_inr", "band_floor_inr", "band_ceiling_exclusive_inr",
        "source_date", "source", "source_url", "ram_gb", "storage_gb", "color",
        "live_price_verified", "buy_eligible", "next_action",
    ]
    def flatten(item):
        variant = item.get("recorded_variant") or {}
        status = item["status"]
        action = {
            "WORKBOOK_DATED_REFERENCE": "Recheck exact SKU, current India price and availability; existing amount is historical",
            "API_HISTORICAL_VARIANT_OBSERVATION": "Recheck 17-Nov exact variant, current source and pincode before allowing into live budget filter",
            "API_ONLY_NO_POSITIVE_IN_STOCK_PRICE": "Resolve missing price, no-stock or unconfirmed RAM/storage; no substitute price",
            "NOT_IN_SAVED_API_OBSERVATIONS": "Source-review India exact model and variant; obtain allowed retailer listing without guessing",
        }[status]
        return {
            **{field: item.get(field) for field in fields if field not in {"ram_gb", "storage_gb", "color", "next_action"}},
            "ram_gb": variant.get("ram_gb"),
            "storage_gb": variant.get("storage_gb"),
            "color": variant.get("color"),
            "next_action": action,
        }
    for name, items in (
        ("all-232-mobile-price-evidence.csv", rows),
        ("103-mobile-price-verification-queue.csv",
         [next(row for row in rows if row["model_key"] == task["model_key"]) for task in queue]),
    ):
        with (output_dir / name).open("w", encoding="utf-8", newline="") as fp:
            writer = csv.DictWriter(fp, fieldnames=fields)
            writer.writeheader()
            writer.writerows(flatten(item) for item in items)
    sums = report["summary"]
    lines = [
        "# Coupon World: price-evidence classification of all 232 core phones",
        "",
        "> **Historical research only.** No amount is a current verified checkout price;",
        "> saved third-party observations do not authorize Buy buttons or ranking changes.",
        "",
        f'- Total core models: **{sums["total_models"]}**',
        f'- Existing workbook dated references: **{sums["statuses"]["WORKBOOK_DATED_REFERENCE"]}**',
        f'- Additional saved API historical observations: **{sums["statuses"]["API_HISTORICAL_VARIANT_OBSERVATION"]}**',
        f'- No eligible positive quote in saved API: **{sums["statuses"]["API_ONLY_NO_POSITIVE_IN_STOCK_PRICE"]}**',
        f'- No saved API observations: **{sums["statuses"]["NOT_IN_SAVED_API_OBSERVATIONS"]}**',
        f'- Total having some dated price evidence: **{sums["with_any_dated_price_evidence"]}**',
        f'- Still missing usable positive price evidence: **{sums["still_missing_positive_price_evidence"]}**',
        "",
        "One recorded model/variant belongs to one ₹5,000 audit band. Other RAM,",
        "storage and colours of the *same model* may fall into other price bands.",
        "This report does not change the source-backed public budget filter.",
        "",
        "| Historical ₹5k price band | Workbook | Saved API | Total |",
        "|---|---:|---:|---:|",
    ]
    for b in report["budget_bands"]:
        low, hi = b["floor_inr"], b["ceiling_exclusive_inr"]
        if low > 100000 and b["total_with_some_dated_price_evidence"] == 0:
            continue
        lines.append(f'| ₹{low:,} to below ₹{hi:,} | {b["workbook_count"]} | {b["api_historical_count"]} | {b["total_with_some_dated_price_evidence"]} |')
    lines.extend([
        "",
        "## Remaining 103 models",
        "",
        "The accompanying CSV identifies each missing model and the next",
        "verification action. It does **not** claim a new API request was made.",
        "",
        "API snapshots can be stale; default observation pincode is 110001.",
        "Retailer links, availability and pricing require independent re-verification.",
        "All public price eligibility and ranking gates remain unchanged.",
    ])
    (output_dir / "232-mobile-price-coverage.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return {"model_rows": len(rows), "verification_queue": len(queue), "files": [
        "all-232-mobile-price-evidence.csv", "103-mobile-price-verification-queue.csv",
        "232-mobile-price-coverage.md",
    ]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=Path("price-evidence-232.json"))
    parser.add_argument("--report-dir", type=Path, default=None)
    args = parser.parse_args()
    report = build(args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.report_dir:
        export_review_files(report, args.report_dir)
    print(json.dumps({"summary": report["summary"], "bands_with_evidence": [x for x in report["budget_bands"] if x["total_with_some_dated_price_evidence"]]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
