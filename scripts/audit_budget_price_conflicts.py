#!/usr/bin/env python3
"""Offline diagnostic: historical workbook vs saved third-party price bands.

Does not call the provider, assert a current price, authorize buying, or
change the price gate. The comparison is model+RAM+storage only: colour,
retailer and seller may differ, so band differences are review flags.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

from scripts.build_price_evidence_coverage import (
    ROOT, WIDTH, load_json, positive_historical_observations,
)


def generate(root: Path = ROOT) -> dict:
    workbook = load_json(root / "data/mobile_workbook_research.json")
    observations = load_json(root / "data/retailer_price_observations.json")
    catalogue = load_json(root / "data/mobile_research_catalogue.json")
    if len(catalogue["model_cards"]) != 232 or len(workbook["models"]) != 232:
        raise ValueError("Expected the 232-model core research catalogue")
    if workbook["mode"] != "DATED_RESEARCH_NOT_LIVE_OFFERS":
        raise ValueError("Unexpected historical workbook source")
    if observations["mode"] != "ATTRIBUTED_API_PRICE_OBSERVATIONS":
        raise ValueError("Unexpected historical third-party observation source")
    by_key = {card["model_key"] for card in catalogue["model_cards"]}
    if by_key != {row["model_key"] for row in workbook["models"]}:
        raise ValueError("Model identity mismatch")
    rows = []
    statuses = Counter()
    for row in workbook["models"]:
        reference = row.get("research_budget_reference")
        if not reference:
            continue
        key = row["model_key"]
        refprice = reference["reference_price_inr"]
        if type(refprice) not in (int, float) or refprice <= 0:
            raise ValueError("Invalid dated workbook amount")
        ref_storage = reference.get("storage_gb")
        ref_ram = reference.get("ram_gb")
        candidates = positive_historical_observations(
            observations.get("models", {}).get(key, []), key
        )
        same_memory = [
            offer for offer in candidates
            if offer["storage_gb"] == ref_storage
            and offer["ram_gb"] == ref_ram
        ]
        basis = min(same_memory, key=lambda offer: offer["reference_price_inr"]) if same_memory else None
        old_band = int(refprice // WIDTH) * WIDTH
        new_price = basis["reference_price_inr"] if basis else None
        new_band = int(new_price // WIDTH) * WIDTH if new_price is not None else None
        status = (
            "NO_COMPARABLE_SAVED_MEMORY" if basis is None else
            "DIFFERENT_5000_BAND" if old_band != new_band else
            "DIFFERENT_AMOUNT_SAME_BAND" if refprice != new_price else
            "SAME_AMOUNT"
        )
        statuses[status] += 1
        rows.append({
            "model_key": key,
            "status": status,
            "workbook_price_inr": refprice,
            "workbook_band_lower_inr": old_band,
            "workbook_storage_gb": ref_storage,
            "workbook_ram_gb": ref_ram,
            "workbook_checked_at": reference.get("checked_at"),
            "saved_price_inr": new_price,
            "saved_band_lower_inr": new_band,
            "saved_retailer": basis["retailer"] if basis else None,
            "saved_ram_gb": basis["ram_gb"] if basis else None,
            "saved_storage_gb": basis["storage_gb"] if basis else None,
            "saved_colour": basis["color"] if basis else None,
            "saved_observed_at": basis["observed_at"] if basis else None,
            "delta_inr": new_price - refprice if new_price is not None else None,
            "needs_price_reverification": status == "DIFFERENT_5000_BAND",
            "publish_as_current": False,
        })
    statuses = dict(statuses)
    if len(rows) != 86:
        raise ValueError("Workbook priced model count changed; inspect before releasing")
    compared = len(rows) - statuses.get("NO_COMPARABLE_SAVED_MEMORY", 0)
    return {
        "schema_version": 1,
        "mode": "HISTORICAL_BUDGET_BAND_CONFLICT_AUDIT_ONLY",
        "notice": "Historical 3-Nov workbook versus 17-Nov saved third-party API observations, matched only on model+RAM+storage. Different retailer, seller, colour, promotions or date may explain differences. Neither amount is current or checkout-verified. Do not automatically move models, activate Buy CTAs, or change ranking.",
        "workbook_as_of": workbook.get("research_as_of"),
        "saved_api_generated_at": observations.get("generated_at"),
        "models_in_core_catalogue": len(by_key),
        "dated_workbook_models": len(rows),
        "same_memory_comparisons": compared,
        "status_counts": statuses,
        "rows": sorted(rows, key=lambda x: (0 if x["status"] == "DIFFERENT_5000_BAND" else 1, x["model_key"])),
    }


def write(audit: dict, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# Coupon World — Budget Filter / Saved-Price Conflict Audit",
        "",
        "> Audit only. Never promote these historical amounts into live-price or purchase eligibility.",
        "",
        f'- Core models: **{audit["models_in_core_catalogue"]}**',
        f'- With 3-Nov research references: **{audit["dated_workbook_models"]}**',
        f'- Same RAM/storage comparables in saved 17-Nov snapshot: **{audit["same_memory_comparisons"]}**',
        f'- Different ₹5,000 bands: **{audit["status_counts"].get("DIFFERENT_5000_BAND", 0)}**',
        f'- Different prices within same band: **{audit["status_counts"].get("DIFFERENT_AMOUNT_SAME_BAND", 0)}**',
        f'- Same amount: **{audit["status_counts"].get("SAME_AMOUNT", 0)}**',
        f'- No comparable saved memory: **{audit["status_counts"].get("NO_COMPARABLE_SAVED_MEMORY", 0)}**',
        "",
        "## Models needing current exact-offer verification",
        "",
        "| Model key | Earlier reference | Saved API observation | Previous band | Saved band |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in audit["rows"]:
        if row["status"] != "DIFFERENT_5000_BAND":
            continue
        md.append(
            f'| {row["model_key"]} | ₹{row["workbook_price_inr"]:,.0f} | '
            f'₹{row["saved_price_inr"]:,.0f} | ₹{row["workbook_band_lower_inr"]:,.0f} | '
            f'₹{row["saved_band_lower_inr"]:,.0f} |'
        )
    md += [
        "",
        "Model/RAM/storage are matched but colours, sellers, retailer platforms,",
        "stock and checking dates may differ. These are discrepancy flags, not",
        "proof that either snapshot was wrong or that the latest amount is valid now.",
        "",
        "P0: Do not claim dated reference matches are currently within budget.",
        "P1: Current-price filtering needs fresh allowed retailer offers and exact SKU matching.",
        "P2: Keep backend band upper bound exclusive to match static quick chips.",
        "P3: Distinguish saved stale prices from fresh prices and do not imply that opening",
        "a saved-price panel bills a live API call.",
    ]
    path.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("price-band-conflicts.json"))
    args = parser.parse_args()
    audit = generate()
    write(audit, args.out)
    print(json.dumps({"compared": audit["same_memory_comparisons"], "statuses": audit["status_counts"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
