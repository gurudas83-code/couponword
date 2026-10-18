#!/usr/bin/env python3
"""Build a resumable, read-only mobile coverage queue from existing sources.

This coordinator reuses the existing stores and identity rules.  It creates
the master/gap/progress manifests but never invents Product DNA, canonical IDs,
prices or retailer offers.  Verification and admission remain the existing
official-evidence and canonical workflows.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
SEED_PATH = ROOT / "data" / "india_three_year_coverage.json"
PRIORITY_PATH = ROOT / "data" / "mobile_universe_priority_126.json"
SEED_COMPAT_PATH = ROOT / "data" / "mobile_universe_seed.json"
EVIDENCE_PATH = ROOT / "data" / "verified_product_evidence_cache.json"
DNA_PATH = ROOT / "data" / "mobile_intelligence_repository.json"
REGISTRY_PATH = ROOT / "data" / "retailer_product_registry.json"
OFFERS_PATH = ROOT / "data" / "retailer_offers.json"
MASTER_PATH = ROOT / "data" / "mobile_universe_2023_2026.json"
GAP_PATH = ROOT / "data" / "mobile_coverage_gap_2023_2026.json"
PROGRESS_PATH = ROOT / "data" / "mobile_coverage_progress.json"
BASELINE_PRIVATE_DNA_TOTAL = 9


def norm(value: Any) -> str:
    return " ".join(re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).split())


def iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def variant_key(ram: Any, storage: Any, text: Any = "") -> str:
    if ram not in (None, "") and storage not in (None, ""):
        return f"{int(ram)}gb/{int(storage)}gb"
    return norm(text) or "unknown"


def parse_variant(text: Any) -> tuple[int | None, int | None]:
    numbers = [int(x) for x in re.findall(r"\b(\d{1,4})\s*gb\b", str(text or ""), re.I)]
    ram = next((x for x in numbers if 1 <= x <= 32), None)
    storage = next((x for x in numbers if x >= 32), None)
    return ram, storage


def build_sources() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    priority = read_json(PRIORITY_PATH).get("products", [])
    coverage = read_json(SEED_PATH)
    launch_rows = coverage.get("verified_india_launch_inventory", [])
    compat_rows = read_json(SEED_COMPAT_PATH).get("products", [])
    evidence_payload = read_json(EVIDENCE_PATH)
    evidence_rows = evidence_payload.get("records", [])
    models: dict[str, dict[str, Any]] = {}

    def ensure_model(brand: Any, model: Any) -> dict[str, Any]:
        key = f"{norm(brand)}|{norm(model)}"
        return models.setdefault(key, {
            "model_key": key,
            "market": "IN",
            "brand": str(brand or "").strip(),
            "model": str(model or "").strip(),
            "generation": None,
            "launch_year": None,
            "launch_date": None,
            "manufacturer_model_id": None,
            "official_product_url": None,
            "india_launch_sources": [],
            "variants": [],
            "discovery_sources": [],
            "india_market_status": "UNVERIFIED_RESEARCH",
            "coverage_status": "RESEARCH_ONLY",
        })

    def add_variant(record: dict[str, Any], source_type: str) -> None:
        brand, model = record.get("brand"), record.get("model")
        if not brand or not model:
            return
        item = ensure_model(brand, model)
        ram = record.get("ram_gb")
        storage = record.get("storage_gb")
        if ram in (None, "") or storage in (None, ""):
            parsed_ram, parsed_storage = parse_variant(record.get("variant"))
            ram = ram if ram not in (None, "") else parsed_ram
            storage = storage if storage not in (None, "") else parsed_storage
        key = variant_key(ram, storage, record.get("variant"))
        if not any(v.get("variant_key") == key for v in item["variants"]):
            item["variants"].append({
                "variant_key": key,
                "ram_gb": ram,
                "storage_gb": storage,
                "variant_text": str(record.get("variant") or "").strip() or None,
                "manufacturer_sku": None,
                "identity_status": "EXACT_SEED_VARIANT" if ram and storage else "UNVERIFIED",
                "official_evidence_status": "PENDING",
                "source_type": source_type,
            })
        source_ref = str(record.get("source_reference") or record.get("discovery_source") or "").strip()
        if source_ref and source_ref not in item["discovery_sources"]:
            item["discovery_sources"].append(source_ref)

    for record in priority:
        if isinstance(record, dict):
            add_variant(record, "priority_research_seed")

    for record in compat_rows:
        if isinstance(record, dict):
            add_variant(record, "compatibility_seed")

    for record in launch_rows:
        if not isinstance(record, dict) or not record.get("brand") or not record.get("model"):
            continue
        item = ensure_model(record["brand"], record["model"])
        source_url = str(record.get("source_url") or "").strip()
        launch_date = str(record.get("india_launch") or "").strip()
        launch_year = launch_date[:4] if launch_date[:4].isdigit() else None
        evidence = {
            "india_launch": launch_date or None,
            "date_precision": record.get("date_precision"),
            "source_url": source_url or None,
            "source_type": record.get("source_type"),
            "observed_at": record.get("observed_at"),
            "inventory_status": record.get("inventory_status"),
        }
        if evidence not in item["india_launch_sources"]:
            item["india_launch_sources"].append(evidence)
        if launch_year and (item["launch_year"] is None or launch_year < str(item["launch_year"])):
            item["launch_year"] = int(launch_year)
        if launch_date and len(launch_date) >= 8 and item["launch_date"] is None:
            item["launch_date"] = launch_date
        if source_url and item["official_product_url"] is None:
            item["official_product_url"] = source_url
        item["india_market_status"] = "LAUNCH_EVIDENCE_VERIFIED"

    # Evidence rows are also discovery records.  Include them in the master
    # universe so a newly admitted DNA record cannot disappear from the gap
    # manifest simply because its original research seed used another alias.
    for record in evidence_rows:
        if not isinstance(record, dict):
            continue
        signature = record.get("variant_signature") if isinstance(record.get("variant_signature"), dict) else {}
        evidence_record = dict(record)
        evidence_record["ram_gb"] = signature.get("ram_gb")
        evidence_record["storage_gb"] = signature.get("storage_gb")
        evidence_record["variant"] = (
            f"{signature.get('ram_gb')}GB/{signature.get('storage_gb')}GB"
            if signature.get("ram_gb") and signature.get("storage_gb")
            else ""
        )
        evidence_record["source_reference"] = record.get("official_url")
        add_variant(evidence_record, "official_evidence_cache")
        item = ensure_model(record.get("brand"), record.get("model"))
        if item["official_product_url"] is None and record.get("official_url"):
            item["official_product_url"] = record.get("official_url")
        if item["india_market_status"] == "UNVERIFIED_RESEARCH":
            item["india_market_status"] = "OFFICIAL_EVIDENCE_ONLY"

    for item in models.values():
        if not item["variants"]:
            item["variants"].append({
                "variant_key": "unknown",
                "ram_gb": None,
                "storage_gb": None,
                "variant_text": None,
                "manufacturer_sku": None,
                "identity_status": "UNVERIFIED",
                "official_evidence_status": "PENDING",
                "source_type": "launch_evidence_only",
            })
    return models, read_json(EVIDENCE_PATH), read_json(DNA_PATH)


def exact_signature(record: dict[str, Any]) -> tuple[int | None, int | None]:
    sig = record.get("variant_signature")
    if isinstance(sig, dict):
        return sig.get("ram_gb"), sig.get("storage_gb")
    return parse_variant(record.get("search_name") or record.get("model"))


def text_value(value: Any) -> Any:
    if isinstance(value, dict):
        return value.get("value")
    return value


def evidence_product_id(brand: str, model: str, ram: int, storage: int) -> str:
    slug = re.sub(
        r"[^a-z0-9]+",
        "-",
        f"{brand}-{model}-{ram}gb-{storage}gb".lower(),
    ).strip("-")
    return f"dna-{slug}"


def admit_exact_evidence(*, execute: bool) -> list[dict[str, Any]]:
    """Admit only exact, resolver-verified official evidence rows.

    This is intentionally narrower than discovery: a current offer and a
    canonical shopping ID are not required for private DNA, but exact variant
    identity and a successful official source fetch are mandatory.
    """
    from mobile_intelligence_repository import load_repository, save_mobile_dna
    from mobile_product_dna import EvidenceValue, MobileProductDNA

    evidence_rows = read_json(EVIDENCE_PATH).get("records", [])
    existing = load_repository().get("products", {})
    existing_keys: set[tuple[str, str, int, int]] = set()
    for wrapper in existing.values():
        dna = wrapper.get("dna", {}) if isinstance(wrapper, dict) else {}
        brand = text_value(dna.get("brand"))
        model = text_value(dna.get("model"))
        ram = text_value(dna.get("ram_gb"))
        storage = text_value(dna.get("storage_gb"))
        if brand and model and ram not in (None, "") and storage not in (None, ""):
            existing_keys.add((norm(brand), norm(model), int(ram), int(storage)))

    results: list[dict[str, Any]] = []
    for index, row in enumerate(evidence_rows):
        if not isinstance(row, dict):
            continue
        ram_raw, storage_raw = exact_signature(row)
        brand = str(row.get("brand") or "").strip()
        model = str(row.get("model") or "").strip()
        source_url = str(row.get("official_url") or "").strip()
        base = {
            "record": str(row.get("asin") or source_url or f"evidence-{index}"),
            "brand": brand,
            "model": model,
            "ram_gb": ram_raw,
            "storage_gb": storage_raw,
            "source_url": source_url,
        }
        if ram_raw is None or storage_raw is None:
            continue
        ram, storage = int(ram_raw), int(storage_raw)
        if not brand or not model or not source_url.startswith("https://"):
            base.update(status="BLOCKED_MISSING_OFFICIAL_EVIDENCE", reason="missing exact identity or HTTPS official URL")
            results.append(base)
            continue
        if row.get("resolver_verified") is not True or str(row.get("fetch_status") or "").lower() != "success":
            base.update(status="BLOCKED_SOURCE_NOT_VERIFIED", reason="resolver/fetch verification is not successful")
            results.append(base)
            continue
        specs = row.get("specifications") if isinstance(row.get("specifications"), dict) else {}
        name_value = str(text_value(specs.get("name")) or "")
        declared_memory = re.search(r"\b(\d{1,2})\s*gb\s*(?:memory|ram)\b", name_value, re.I)
        if declared_memory and int(declared_memory.group(1)) != ram:
            base.update(status="BLOCKED_IDENTITY_CONFLICT", reason=f"official name declares {declared_memory.group(1)}GB while requested variant is {ram}GB")
            results.append(base)
            continue
        identity_key = (norm(brand), norm(model), ram, storage)
        if identity_key in existing_keys:
            base.update(status="DUPLICATE_REUSED", reason="exact variant already exists in private DNA")
            results.append(base)
            continue
        product_id = evidence_product_id(brand, model, ram, storage)
        def ev(value: Any) -> EvidenceValue:
            return EvidenceValue(
                value=value,
                source="official_product_evidence_cache",
                source_url=source_url,
                confidence="high",
                verified=True,
            )

        dna = MobileProductDNA(
            product_id=product_id,
            canonical_product_id=None,
            brand=ev(brand),
            model=ev(model),
            ram_gb=ev(ram),
            storage_gb=ev(storage),
            warnings=[
                "Private Product DNA admitted from exact official evidence.",
                "No canonical shopping ID or current retailer offer was asserted.",
            ],
        )
        processor = text_value(specs.get("processor") or specs.get("chipset"))
        if processor:
            dna.chipset = ev(processor)
        battery = text_value(specs.get("battery_capacity_mah"))
        battery_match = re.search(r"\b(\d{3,5})\s*mAh\b", str(battery or ""), re.I)
        if battery_match:
            dna.battery_mah = ev(int(battery_match.group(1)))
        os_value = text_value(specs.get("operating_system"))
        if os_value:
            dna.operating_system = ev(os_value)
        if not execute:
            base.update(status="READY_FOR_ADMISSION", product_id=product_id, reason="exact official evidence passed identity gates")
            results.append(base)
            continue
        saved, reason = save_mobile_dna(dna)
        if saved:
            existing_keys.add(identity_key)
            base.update(status="ADMITTED", product_id=product_id, reason=reason)
        else:
            base.update(status="ADMISSION_FAILED", product_id=product_id, reason=reason)
        results.append(base)
    return results


def build_manifests() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    from retailer_offer_store import find_fresh_verified_offer

    models, evidence_payload, dna_payload = build_sources()
    evidence_rows = evidence_payload.get("records", [])
    dna_rows = dna_payload.get("products", {})
    registry = read_json(REGISTRY_PATH).get("products", {})
    offers = read_json(OFFERS_PATH).get("offers", [])
    compat_rows = read_json(SEED_COMPAT_PATH).get("products", [])
    known_ids = {key for key in registry if str(key).startswith("cw-mobile-")}
    canonical_by_variant: dict[tuple[str, str, str], str] = {}
    for row in compat_rows:
        if isinstance(row, dict) and row.get("canonical_product_id"):
            canonical_by_variant[(norm(row.get("brand")), norm(row.get("model")), variant_key(row.get("ram_gb"), row.get("storage_gb"), row.get("variant")))] = row["canonical_product_id"]
    for row in offers:
        if not isinstance(row, dict) or not row.get("product_id"):
            continue
        canonical_by_variant[(norm(row.get("brand")), norm(row.get("model")), variant_key(*parse_variant(row.get("variant")), row.get("variant")))] = row["product_id"]

    dna_by_variant: dict[tuple[str, str, str], str] = {}
    for dna_id, wrapper in dna_rows.items():
        dna = wrapper.get("dna", {}) if isinstance(wrapper, dict) else {}
        brand = dna.get("brand", {}).get("value") if isinstance(dna.get("brand"), dict) else None
        model = dna.get("model", {}).get("value") if isinstance(dna.get("model"), dict) else None
        ram = dna.get("ram_gb", {}).get("value") if isinstance(dna.get("ram_gb"), dict) else None
        storage = dna.get("storage_gb", {}).get("value") if isinstance(dna.get("storage_gb"), dict) else None
        if brand and model:
            dna_by_variant[(norm(brand), norm(model), variant_key(ram, storage))] = dna_id

    evidence_by_variant: dict[tuple[str, str, str], list[str]] = {}
    evidence_by_model: dict[tuple[str, str], list[str]] = {}
    for index, row in enumerate(evidence_rows):
        if not isinstance(row, dict):
            continue
        brand, model = norm(row.get("brand")), norm(row.get("model"))
        if not brand or not model:
            continue
        record_id = str(row.get("asin") or row.get("official_url") or f"evidence-{index}")
        evidence_by_model.setdefault((brand, model), []).append(record_id)
        ram, storage = exact_signature(row)
        if ram is not None and storage is not None:
            evidence_by_variant.setdefault((brand, model, variant_key(ram, storage)), []).append(record_id)

    gaps: list[dict[str, Any]] = []
    for item in models.values():
        model_key = (norm(item["brand"]), norm(item["model"]))
        for variant in item["variants"]:
            vkey = variant["variant_key"]
            identity = (model_key[0], model_key[1], vkey)
            canonical_id = canonical_by_variant.get(identity)
            dna_id = dna_by_variant.get(identity)
            exact_evidence = evidence_by_variant.get(identity, [])
            model_evidence = evidence_by_model.get(model_key, [])
            if canonical_id and canonical_id in known_ids:
                status = "EXISTING_CANONICAL"
            elif dna_id:
                status = "EXISTING_PRIVATE_DNA"
            elif exact_evidence or model_evidence:
                status = "OFFICIAL_EVIDENCE_ONLY"
            else:
                status = "RESEARCH_ONLY"
            if canonical_id and not exact_evidence and not dna_id:
                blocker = "CANONICAL_MAPPING_GAP"
            elif dna_id:
                blocker = "CANONICAL_MAPPING_GAP"
            elif exact_evidence:
                blocker = "CANONICAL_MAPPING_GAP"
            elif model_evidence:
                blocker = "EXACT_VARIANT_IDENTITY_GAP"
            elif variant["ram_gb"] is None or variant["storage_gb"] is None:
                blocker = "EXACT_VARIANT_IDENTITY_GAP"
            else:
                blocker = "MISSING_OFFICIAL_EVIDENCE"
            offer_variant = (
                f"{variant['ram_gb']}GB/{variant['storage_gb']}GB"
                if variant["ram_gb"] is not None and variant["storage_gb"] is not None
                else str(variant.get("variant_text") or "")
            )
            fresh_offer = bool(
                canonical_id
                and find_fresh_verified_offer(
                    product_id=canonical_id,
                    brand=item["brand"],
                    model=item["model"],
                    variant=offer_variant,
                )
            )
            if status == "EXISTING_CANONICAL":
                action = "Verify a fresh exact in_stock offer before recommendation admission."
            elif status == "EXISTING_PRIVATE_DNA":
                action = "Resolve an existing canonical mapping; retain DNA without a buyable claim."
            elif status == "OFFICIAL_EVIDENCE_ONLY":
                action = "Run the existing identity/admission workflow; do not invent an ID."
            else:
                action = "Verify the exact India variant through the existing official-source pipeline."
            gaps.append({
                "model_key": item["model_key"],
                "brand": item["brand"],
                "model": item["model"],
                "variant_key": vkey,
                "ram_gb": variant["ram_gb"],
                "storage_gb": variant["storage_gb"],
                "present_in_backend": status != "RESEARCH_ONLY",
                "existing_canonical_id": canonical_id,
                "private_dna_id": dna_id,
                "official_evidence_record_ids": sorted(set(exact_evidence or model_evidence)),
                "official_evidence_exact": bool(exact_evidence),
                "current_fresh_offer": fresh_offer,
                "coverage_status": status,
                "blocker_code": blocker,
                "required_admission_action": action,
                "next_automated_recovery_action": "bounded_official_evidence_retry" if blocker == "MISSING_OFFICIAL_EVIDENCE" else "review_existing_pipeline_gate",
            })
            variant["official_evidence_status"] = "VERIFIED_EXACT" if exact_evidence else ("MODEL_ONLY" if model_evidence else "PENDING")

    master_models = sorted(models.values(), key=lambda row: (row["brand"].casefold(), row["model"].casefold()))
    master = {
        "schema_version": "1.0",
        "market": "IN",
        "category": "smartphone",
        "period_start": "2023-01-01",
        "period_end": "2026-10-18",
        "generated_at": iso_now(),
        "denominator_status": "COVERAGE_DENOMINATOR_UNVERIFIED",
        "scope": "Union of existing 126-candidate coverage, 187-entry priority discovery and saved manufacturer launch evidence; not a complete market census.",
        "sources": [
            str(SEED_PATH.relative_to(ROOT)),
            str(PRIORITY_PATH.relative_to(ROOT)),
            str(SEED_COMPAT_PATH.relative_to(ROOT)),
        ],
        "models": master_models,
        "counts": {
            "discovered_unique_models": len(master_models),
            "discovered_exact_variants": sum(1 for row in gaps if row["ram_gb"] is not None and row["storage_gb"] is not None),
            "launch_evidence_model_rows": sum(1 for row in master_models if row["india_launch_sources"]),
        },
    }
    gap = {
        "schema_version": "1.0",
        "generated_at": iso_now(),
        "scope": "Coverage gap generated from existing source-backed manifests and current durable stores. Unverified rows are not recommendation eligible.",
        "source_manifest": str(MASTER_PATH.relative_to(ROOT)),
        "known_canonical_mobile_ids": len(known_ids),
        "gaps": gaps,
        "counts": {
            "total_variant_rows": len(gaps),
            "existing_canonical_rows": sum(x["coverage_status"] == "EXISTING_CANONICAL" for x in gaps),
            "existing_private_dna_rows": sum(x["coverage_status"] == "EXISTING_PRIVATE_DNA" for x in gaps),
            "official_evidence_only_rows": sum(x["coverage_status"] == "OFFICIAL_EVIDENCE_ONLY" for x in gaps),
            "research_only_rows": sum(x["coverage_status"] == "RESEARCH_ONLY" for x in gaps),
            "fresh_in_stock_offer_rows": sum(x["current_fresh_offer"] for x in gaps),
        },
    }
    return master, gap, {"known_ids": known_ids, "gaps": gaps, "models": master_models}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the existing mobile coverage manifests with resumable checkpoints.")
    parser.add_argument("--market", default="IN")
    parser.add_argument("--start-year", type=int, default=2023)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--until-exhausted", action="store_true")
    parser.add_argument("--execute", action="store_true", help="admit exact resolver-verified official evidence into private DNA")
    parser.add_argument("--dry-run", action="store_true", help="show exact evidence admission candidates without writing")
    args = parser.parse_args()
    if args.market.upper() != "IN":
        raise SystemExit("Only the existing IN source manifests are supported.")
    if args.execute and args.dry_run:
        raise SystemExit("Choose either --execute or --dry-run, not both.")
    admission_results = admit_exact_evidence(execute=args.execute) if (args.execute or args.dry_run) else []
    master, gap, state = build_manifests()
    write_json(MASTER_PATH, master)
    write_json(GAP_PATH, gap)
    previous = read_json(PROGRESS_PATH) if args.resume and PROGRESS_PATH.exists() else {}
    total = len(gap["gaps"])
    cursor = total if args.until_exhausted else min(int(previous.get("cursor", 0)), total)
    progress = {
        "schema_version": "1.0",
        "generated_at": iso_now(),
        "market": args.market.upper(),
        "period": {"start_year": args.start_year, "end_year": args.end_year},
        "source_hashes": {str(path.relative_to(ROOT)): sha256(path) for path in [SEED_PATH, PRIORITY_PATH, SEED_COMPAT_PATH, EVIDENCE_PATH, DNA_PATH, REGISTRY_PATH, OFFERS_PATH]},
        "cursor": cursor,
        "queue_total": total,
        "queue_remaining": max(total - cursor, 0),
        "processing_mode": "manifest_and_existing_store_reconciliation",
        "status": "EXHAUSTED_MANIFEST_WITH_VERIFICATION_BLOCKERS" if cursor == total else "CHECKPOINTED",
        "admission_run": {
            "mode": "execute" if args.execute else ("dry_run" if args.dry_run else "reconcile_only"),
            "records_considered": len(admission_results),
            "admitted": sum(x["status"] == "ADMITTED" for x in admission_results),
            "ready_for_admission": sum(x["status"] == "READY_FOR_ADMISSION" for x in admission_results),
            "duplicates_reused": sum(x["status"] == "DUPLICATE_REUSED" for x in admission_results),
            "identity_conflicts": sum(x["status"] == "BLOCKED_IDENTITY_CONFLICT" for x in admission_results),
            "failed": sum(x["status"].endswith("FAILED") for x in admission_results),
            "results": admission_results,
        },
        "counts": {
            "discovered_unique_models": master["counts"]["discovered_unique_models"],
            "discovered_exact_variants": master["counts"]["discovered_exact_variants"],
            "existing_backend_models": len({x["model_key"] for x in gap["gaps"] if x["present_in_backend"]}),
            "missing_models_identified": len({x["model_key"] for x in gap["gaps"] if not x["present_in_backend"]}),
            "verified_exact_variants": sum(bool(x["private_dna_id"] or x["official_evidence_exact"]) for x in gap["gaps"]),
            "private_dna_total": len(read_json(DNA_PATH).get("products", {})),
            "canonical_mobile_ids": len(state["known_ids"]),
            "fresh_in_stock_offers": sum(x["current_fresh_offer"] for x in gap["gaps"]),
            "private_dna_total_before_execution": BASELINE_PRIVATE_DNA_TOTAL,
            "private_dna_total_after_execution": len(read_json(DNA_PATH).get("products", {})),
            "new_product_dna_admissions": max(
                0,
                len(read_json(DNA_PATH).get("products", {})) - BASELINE_PRIVATE_DNA_TOTAL,
            ),
            "blockers_still_open": sum(x["coverage_status"] == "RESEARCH_ONLY" for x in gap["gaps"]),
        },
        "resume_command": "py python/run_mobile_coverage.py --market IN --start-year 2023 --end-year 2026 --resume --until-exhausted",
        "note": "--execute admits only exact resolver-verified official evidence. Research-only rows remain pending until an authorized official source is verified.",
    }
    write_json(PROGRESS_PATH, progress)
    print(json.dumps({"master": master["counts"], "gap": gap["counts"], "progress": progress["counts"], "status": progress["status"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
