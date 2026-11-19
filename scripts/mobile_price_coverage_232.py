#!/usr/bin/env python3
"""Reconcile all 232 core phones with dated research and saved API observations.

No paid provider calls, no new offers, no ranking weights, no price publication.
A stored API observation is NOT a checkout-confirmed current price.
"""
from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
RETAILER_HOSTS = {"www.amazon.in", "www.flipkart.com", "www.croma.com"}
BASE = "DATED_RESEARCH_REFERENCE"
EXACT = "HISTORICAL_THIRD_PARTY_EXACT_VARIANT"
INCOMPLETE = "OBSERVATIONS_WITHOUT_ELIGIBLE_EXACT_PRICE"
ABSENT = "NO_SAVED_API_OBSERVATION"

def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def band(price: int | float) -> dict:
    lower = int(price // 5000) * 5000
    return {"lower_inr": lower, "upper_exclusive_inr": lower + 5000}

def eligible_observations(configurations: list[dict]) -> list[dict]:
    """Use only a saved exact-memory positive observation, never authorize purchase."""
    results = []
    for config in configurations:
        if config.get("comparison_eligible") is not True:
            continue
        if config.get("purchase_eligible") is not False:
            continue
        if config.get("pincode") != "110001":
            continue
        ram, storage = config.get("ram_gb"), config.get("storage_gb")
        if type(ram) is not int or type(storage) is not int or min(ram, storage) <= 0:
            continue
        for offer in config.get("offers") or []:
            url = str(offer.get("product_url") or "")
            parts = urlsplit(url)
            price = offer.get("price")
            try:
                datetime.fromisoformat(str(offer.get("observed_at") or ""))
                valid_date = True
            except ValueError:
                valid_date = False
            if (
                type(price) not in (int, float) or price <= 0
                or offer.get("availability") != "in_stock"
                or offer.get("currency") != "INR"
                or offer.get("retailer") not in {"amazon", "flipkart", "croma"}
                or parts.scheme != "https" or parts.hostname not in RETAILER_HOSTS
                or not valid_date
            ):
                continue
            results.append({
                "price_inr": price, "ram_gb": ram, "storage_gb": storage,
                "color": config.get("color"), "retailer": offer["retailer"],
                "observed_at": offer["observed_at"], "pincode": "110001",
                "source_url": url,
            })
    return sorted(results, key=lambda x: (
        x["price_inr"], x["ram_gb"], x["storage_gb"], str(x["color"]), x["retailer"]
    ))

def build(root: Path = ROOT) -> dict:
    source = read(root / "data/mobile_research_catalogue.json")
    workbook = read(root / "data/mobile_workbook_research.json")
    api = read(root / "data/retailer_price_observations.json")
    cards, records = source["model_cards"], workbook["models"]
    if len(cards) != 232 or len({c["model_key"] for c in cards}) != 232:
        raise ValueError("Expected exactly 232 unique core smartphone records")
    if workbook["mode"] != "DATED_RESEARCH_NOT_LIVE_OFFERS":
        raise ValueError("Workbook cannot be treated as live commerce")
    if api["mode"] != "ATTRIBUTED_API_PRICE_OBSERVATIONS" or api["source_type"] != "quickcommerce_third_party_research":
        raise ValueError("Saved API records must be third-party research observations")
    research = {x["model_key"]: x for x in records}
    if len(research) != 232 or set(research) != {c["model_key"] for c in cards}:
        raise ValueError("Workbook model identities do not exactly reconcile to core catalogue")
    models = []
    counters = {x: 0 for x in (BASE, EXACT, INCOMPLETE, ABSENT)}
    bands = {}
    for card in cards:
        key = card["model_key"]
        reference = research[key].get("research_budget_reference")
        configs = api["models"].get(key, [])
        observed = eligible_observations(configs)
        row = {
            "model_key": key, "brand": card["brand"], "model": card["model"],
            "status": None, "reference_price_inr": None, "reference_band": None,
            "reference_date": None, "source_type": None,
            "exact_ram_gb": None, "exact_storage_gb": None, "color": None,
            "observation_retailer": None, "snapshot_date": None,
            "saved_configurations": len(configs), "exact_positive_configurations": len(observed),
            "live_price_verified": False, "purchase_eligible": False,
            "next_action": None,
        }
        if reference is not None:
            price = reference.get("reference_price_inr")
            if type(price) not in (int, float) or price <= 0 or reference.get("live_offer") is not False:
                raise ValueError(f"Invalid dated research reference: {key}")
            row.update({
                "status": BASE, "reference_price_inr": price, "reference_band": band(price),
                "reference_date": workbook["research_as_of"], "source_type": "dated_workbook",
                "exact_ram_gb": reference.get("ram_gb"), "exact_storage_gb": reference.get("storage_gb"),
                "next_action": "Recheck exact variant and current retailer price; preserve dated reference until verified",
            })
        elif observed:
            best = observed[0]
            row.update({
                "status": EXACT, "reference_price_inr": best["price_inr"],
                "reference_band": band(best["price_inr"]),
                "reference_date": best["observed_at"],
                "source_type": "third_party_saved_api_snapshot",
                "exact_ram_gb": best["ram_gb"], "exact_storage_gb": best["storage_gb"],
                "color": best["color"], "observation_retailer": best["retailer"],
                "snapshot_date": api["generated_at"],
                "next_action": "Recheck source, exact SKU, current price, region and availability before live qualification",
            })
        elif configs:
            row.update({
                "status": INCOMPLETE, "snapshot_date": api["generated_at"],
                "next_action": "Resolve out-of-stock / missing amount / missing RAM or storage; verify exact model",
            })
        else:
            row.update({
                "status": ABSENT,
                "next_action": "Discover exact India variant and permitted retailer source without guessing price",
            })
        counters[row["status"]] += 1
        if row["reference_band"] is not None:
            label = f'{row["reference_band"]["lower_inr"]}-{row["reference_band"]["upper_exclusive_inr"]}'
            state = bands.setdefault(label, {"lower_inr": row["reference_band"]["lower_inr"],
                "upper_exclusive_inr": row["reference_band"]["upper_exclusive_inr"],
                "dated_workbook": 0, "historical_api": 0})
            state["dated_workbook" if row["status"] == BASE else "historical_api"] += 1
        models.append(row)
    models.sort(key=lambda x: x["model_key"])
    if sum(counters.values()) != 232:
        raise AssertionError("Coverage does not reconcile to 232")
    return {
        "schema_version": 1, "mode": "NON_LIVE_PRICE_EVIDENCE_COVERAGE",
        "notice": "Audit-only classification, not live prices, in-stock offers or buying eligibility. Old API prices are preliminary, not validated checkout prices. Each record has at most one illustrative minimum observed variant; other RAM/storage/color configurations may lie in a different range.",
        "source_dates": {"workbook": workbook["research_as_of"], "api_snapshot": api["generated_at"]},
        "counts": {"total": 232, **counters,
                   "has_any_dated_evidence": counters[BASE] + counters[EXACT],
                   "needs_reverification": 232 - counters[BASE],
                   "no_reference_workbook": 232 - counters[BASE]},
        "bands": sorted(bands.values(), key=lambda x: x["lower_inr"]),
        "models": models,
    }

def save(coverage: dict, folder: Path):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "mobile-price-coverage-232.json").write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    queue = [x for x in coverage["models"] if x["status"] != BASE]
    with (folder / "mobile-price-backfill-146.csv").open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=[
            "model_key", "brand", "model", "status", "reference_price_inr",
            "reference_date", "exact_ram_gb", "exact_storage_gb", "color",
            "observation_retailer", "saved_configurations",
            "exact_positive_configurations", "next_action",
        ])
        writer.writeheader()
        for row in queue:
            writer.writerow({k: row.get(k) for k in writer.fieldnames})
    totals = coverage["counts"]
    lines = [
        "# Coupon World — 232-phone evidence coverage",
        "",
        "Evidence audit only. No price here is a confirmed current checkout offer.",
        "",
        f'* Core catalogue: **{totals["total"]}**',
        f'* Dated workbook reference: **{totals[BASE]}**',
        f'* Additional saved exact-variant API observations: **{totals[EXACT]}**',
        f'* Saved observations with no eligible exact positive quote: **{totals[INCOMPLETE]}**',
        f'* No saved API observation: **{totals[ABSENT]}**',
        f'* Remaining without an existing dated workbook reference: **{totals["no_reference_workbook"]}**',
        "",
        "| Price band | Workbook references | Additional historical API leads |",
        "|---|---:|---:|",
    ]
    for b in coverage["bands"]:
        lines.append(f'| ₹{b["lower_inr"]:,} to below ₹{b["upper_exclusive_inr"]:,} | {b["dated_workbook"]} | {b["historical_api"]} |')
    lines.extend([
        "",
        "An observed ₹ amount is not a live offer, guaranteed stock, official retail feed,"
        " advertising consent or authorization to activate a Buy button.",
        "The saved API snapshot uses Delhi test pincode 110001 and can be stale.",
        "Market-intake additions outside the frozen 232 identity catalogue are excluded.",
    ])
    (folder / "mobile-price-coverage-232.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=ROOT / "reports" / "generated" / "mobile-price-coverage")
    a = p.parse_args()
    c = build()
    save(c, a.out)
    print(json.dumps({"counts": c["counts"], "bands": c["bands"]}, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
