"""P0 India identity and exact-variant gate for the existing 232-phone research lane.

Fail closed. Official India RAM/storage evidence is NOT a live retailer offer.
The historical third-party observation file is never used to certify purchase.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_HOSTS = {
    "in.nothing.tech", "www.oppo.com", "www.oneplus.in",
    "shop.vivo.com", "www.samsung.com", "news.samsung.com",
    "www.mi.com", "www.realme.com", "buy.realme.com", "www.motorola.in",
}
RETAILER_HOSTS = {
    "amazon": {"www.amazon.in", "amazon.in"},
    "flipkart": {"www.flipkart.com", "flipkart.com"},
    "croma": {"www.croma.com", "croma.com"},
}


def _read(root, name):
    return json.loads((root / name).read_text(encoding="utf-8-sig"))


def _same_model_key(brand, model):
    def norm(value):
        return " ".join(re.findall(r"[a-z0-9]+", str(value).casefold()))
    return norm(brand) + "|" + norm(model)


def _official(url):
    parts = urlsplit(str(url))
    return parts.scheme == "https" and parts.hostname in OFFICIAL_HOSTS


def _pair(item):
    ram, storage = item.get("ram_gb"), item.get("storage_gb")
    if type(ram) is not int or type(storage) is not int or not 1 <= ram <= 32 or not 32 <= storage <= 2048:
        raise ValueError("India variant missing physical RAM/storage")
    return (ram, storage)


def enrich_public_catalogue(catalogue: dict, root: Path = ROOT) -> dict:
    """Attach only separately supported India market identities to all 232 cards."""
    cards = catalogue.get("model_cards") or []
    by_key = {c["model_key"]: c for c in cards}
    if len(cards) != 232 or len(by_key) != 232:
        raise ValueError("Cannot enrich a non-232 or duplicate catalogue")
    approved = _read(root, "data/mobile_india_variant_sources.json")
    manual = _read(root, "data/mobile_p0_india_variant_evidence_20261121.json")
    frozen = _read(root, "data/mobile_research_preview.json")["products"]
    if manual.get("mode") != "MANUFACTURER_INDIA_VARIANT_EVIDENCE_ONLY_NOT_CURRENT_STOCK_OR_OFFER":
        raise ValueError("Unexpected P0 identity ledger")
    if set(approved) - set(by_key) or set(x["model_key"] for x in manual["records"]) - set(by_key):
        raise ValueError("Unknown model in India evidence")
    if len(manual["records"]) != len({x["model_key"] for x in manual["records"]}):
        raise ValueError("Duplicate identity in P0 ledger")
    variants_by_key = {}
    for key, items in approved.items():
        for row in items:
            if not _official(row.get("source_url")):
                raise ValueError("Unapproved official India variant source for " + key)
            variants_by_key.setdefault(key, {})[_pair(row)] = {
                "ram_gb": row["ram_gb"], "storage_gb": row["storage_gb"],
                "source_url": row["source_url"], "evidence_kind": "APPROVED_MANUFACTURER_INDIA_VARIANT"
            }
    for row in frozen:
        if row.get("region") != "IN" or row.get("manufacturer_spec_status") != "VERIFIED":
            continue
        key = _same_model_key(row["brand"], row["model"])
        if key not in by_key:
            raise ValueError("Frozen variant lacks core model " + key)
        source = row.get("official_source")
        if not _official(source):
            raise ValueError("Frozen variant does not cite maker India source " + key)
        pair = _pair(row)
        variants_by_key.setdefault(key, {}).setdefault(pair, {
            "ram_gb": row["ram_gb"], "storage_gb": row["storage_gb"],
            "source_url": source, "evidence_kind": "FROZEN_MANUFACTURER_VERIFIED_INDIA_VARIANT"
        })
    for record in manual["records"]:
        key = record["model_key"]
        if record.get("manufacturer", "").casefold() != str(by_key[key]["brand"]).casefold():
            raise ValueError("Manual India manufacturer does not match model key: " + key)
        if not _official(record.get("india_model_url")):
            raise ValueError("Invalid official India model URL: " + key)
        if not record.get("variants"):
            raise ValueError("Identity record must contain sourced exact variants: " + key)
        pairs = set()
        for row in record["variants"]:
            pair = _pair(row)
            if pair in pairs or not _official(row.get("source_url")):
                raise ValueError("Duplicate or unapproved maker India SKU: " + key)
            pairs.add(pair)
            variants_by_key.setdefault(key, {})[pair] = {
                "ram_gb": row["ram_gb"], "storage_gb": row["storage_gb"],
                "source_url": row["source_url"],
                "evidence_kind": "MANUALLY_REVIEWED_OFFICIAL_INDIA_VARIANT",
                "reviewed_on": manual["reviewed_on"],
            }
    for key, card in by_key.items():
        variant_rows = list(variants_by_key.get(key, {}).values())
        variant_rows.sort(key=lambda item: (item["ram_gb"], item["storage_gb"]))
        card["india_identity_evidence"] = {
            "status": "INDIA_EXACT_VARIANT_DOCUMENTED" if variant_rows else "INDIA_IDENTITY_OR_VARIANT_UNCONFIRMED",
            "verified_variants": variant_rows,
            "current_stock_verified": False,
            "current_price_verified": False,
            "purchase_eligible": False,
            "disclaimer": "Manufacturer India variant identity only; checkout price, India-wide stock, pincode and delivery unverified."
        }
    return catalogue


def top30_report(catalogue: dict, root: Path = ROOT) -> dict:
    """Thirty *research priorities*, annotated with exact, non-live evidence."""
    selected = _read(root, "data/top30_research_pilot_20261113.json")["selected_models"]
    observation = _read(root, "data/retailer_price_observations.json")
    by_key = {c["model_key"]: c for c in catalogue["model_cards"]}
    if len(selected) != 30 or len({x["model_key"] for x in selected}) != 30:
        raise ValueError("Top30 priority ledger not exactly thirty distinct models")
    results = []
    for priority in selected:
        key = priority["model_key"]
        card = by_key[key]
        reviewed = (card.get("india_identity_evidence") or {}).get("verified_variants") or []
        matches = []
        for v in reviewed:
            for conf in observation.get("models", {}).get(key, []):
                if conf.get("ram_gb") != v["ram_gb"] or conf.get("storage_gb") != v["storage_gb"]:
                    continue
                for offer in conf.get("offers", []):
                    retailer = str(offer.get("retailer") or "").lower()
                    parts = urlsplit(str(offer.get("product_url") or ""))
                    if parts.scheme != "https" or parts.hostname not in RETAILER_HOSTS.get(retailer, set()):
                        continue
                    if not offer.get("retailer_product_id") or not offer.get("observed_at") or type(offer.get("price")) not in (int, float):
                        continue
                    matches.append({
                        "ram_gb": v["ram_gb"], "storage_gb": v["storage_gb"],
                        "retailer": retailer, "retailer_product_id": offer["retailer_product_id"],
                        "observed_price_inr": offer["price"],
                        "observed_at": offer["observed_at"], "source_url": offer["product_url"],
                        "observation_scope": "HISTORICAL_THIRD_PARTY_NOT_AUTHORIZED_OFFER",
                        "purchase_eligible": False
                    })
        ref = card.get("research_budget_reference")
        pair = (ref.get("ram_gb"), ref.get("storage_gb")) if isinstance(ref, dict) else None
        matching_ref = bool(pair and pair in {(v["ram_gb"], v["storage_gb"]) for v in reviewed})
        amount = ref.get("reference_price_inr") if matching_ref else None
        in_range = type(amount) in (int, float) and 10000 <= amount < 30000
        results.append({
            "priority_index": priority["priority_index"], "model_key": key,
            "model": str(card["brand"]) + " " + str(card["model"]),
            "india_model_status": card["india_identity_evidence"]["status"],
            "india_source_verified_variants": reviewed,
            "historical_retailer_evidence_matching_india_variant": matches,
            "has_exact_historical_retailer_observation": bool(matches),
            "exact_variant_historical_budget_reference": amount,
            "historical_reference_in_10k_to_30k": in_range,
            "current_india_stock_verified": False,
            "current_authorized_offer_verified": False,
            "buying_recommendation_eligible": False,
            "blockers": ([] if reviewed else ["INDIA_MODEL_AND_EXACT_VARIANT_PENDING"]) +
                        ([] if matches else ["EXACT_RETAILER_SKU_OBSERVATION_PENDING"]) +
                        ["FRESH_AUTHORIZED_STOCK_AND_PRICE_PENDING"],
        })
    return {
        "mode": "P0_TOP30_RESEARCH_PRIORITIES_NOT_30_VERIFIED_BUYING_OPTIONS",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "research_priorities": len(results),
            "maker_india_variant_confirmed_models": sum(bool(x["india_source_verified_variants"]) for x in results),
            "with_exact_variant_historical_retailer_evidence": sum(x["has_exact_historical_retailer_observation"] for x in results),
            "with_matching_10k_to_30k_dated_reference": sum(x["historical_reference_in_10k_to_30k"] for x in results),
            "live_authorized_buying_candidates": 0
        },
        "models": results
    }


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--out", type=Path, default=Path("p0-india-identity-top30.json"))
    args = parser.parse_args()
    catalogue = _read(args.root, "public/data/mobile_research_catalogue.json")
    if any("india_identity_evidence" not in x for x in catalogue["model_cards"]):
        raise ValueError("Public catalogue has not passed India identity enrichment")
    report = top30_report(catalogue, args.root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("P0_INDIA_TOP30 " + json.dumps(report["counts"], sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
