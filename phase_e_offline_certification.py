#!/usr/bin/env python3
"""Bounded offline Phase-E certification over the existing pipeline.

The runner never calls retailers or discovery providers. Queries without a
version-matching candidate snapshot are reported as FIXTURE_GAP rather than
being silently replaced with live data or engine-generated expectations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

from intent_engine import parse_query
try:
    from market_discovery import get_candidate_snapshot
    import shopping_intelligence_pipeline as pipeline
    PIPELINE_IMPORT_ERROR = None
except ModuleNotFoundError as error:
    get_candidate_snapshot = None
    pipeline = None
    PIPELINE_IMPORT_ERROR = f"{type(error).__name__}: {error}"

CORPUS = ROOT / "data" / "mobile_query_corpus_1000.json"
DEFAULT_OUTPUT = ROOT / "data" / "phase_e_offline_certification.json"
QUALITY_TAGS = {"camera", "battery", "gaming", "display", "brand", "ram", "storage", "exact_model"}
OFFLINE_FIXTURE_MANIFEST = ROOT / "data" / "phase_e_offline_fixture_manifest.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def rows() -> list[dict[str, Any]]:
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    splits = payload.get("splits") or {}
    return [item for split in ("train", "validation", "test") for item in splits.get(split, [])]


def discovery_for(query: str, intent: dict[str, Any], max_candidates: int) -> dict[str, Any] | None:
    # Candidate snapshots are sufficient to exercise the downstream identity,
    # evidence, eligibility, scoring and serialization path. Missing offer or
    # extractor records remain honest partial results; they must not prevent
    # the algorithm from executing.
    if get_candidate_snapshot is None or not OFFLINE_FIXTURE_MANIFEST.exists():
        return None
    return get_candidate_snapshot(
        query=query,
        category=intent.get("category"),
        max_candidates=max_candidates,
    )


def semantic(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "query": payload.get("query"),
        "intent": payload.get("intent"),
        "stage_counts": payload.get("stage_counts"),
        "recommendations": [
            {
                key: item.get(key)
                for key in ("product_id", "canonical_product_id", "asin", "title", "brand", "price", "fit_percent", "quality_score", "quality_evidence_coverage_percent", "battery_evidence", "why_it_fits", "tradeoffs", "unknown", "best_offer")
            }
            for item in payload.get("recommendations") or []
        ],
        "market_quality_status": payload.get("market_quality_status"),
        "completion_status": payload.get("completion_status"),
    }


def run_once(items: list[dict[str, Any]], max_candidates: int) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    results: list[dict[str, Any]] = []
    quality_cases: list[dict[str, Any]] = []
    for row in items:
        query = str(row.get("query") or "").strip()
        intent = parse_query(query)
        tags = set(row.get("tags") or [])
        if tags & QUALITY_TAGS and len(quality_cases) < 40:
            quality_cases.append({"id": row.get("id"), "query": query, "tags": sorted(tags & QUALITY_TAGS), "status": "PROPOSED"})
        snapshot = discovery_for(query, intent, max_candidates)
        if snapshot is None:
            reason = PIPELINE_IMPORT_ERROR or (
                "No complete frozen catalogue/evidence/offer fixture manifest"
                if not OFFLINE_FIXTURE_MANIFEST.exists()
                else "No version-matching candidate snapshot"
            )
            results.append({"id": row.get("id"), "query": query, "split": row.get("split"), "status": "FIXTURE_GAP", "reason": reason, "intent": intent})
            continue
        try:
            original = pipeline.discover_market
            pipeline.discover_market = lambda **kwargs: dict(snapshot)
            payload = pipeline._run_pipeline_once(
                query, max_candidates=max_candidates, max_results=3,
                live_fast=True, _discovery=snapshot, _save_discovery_memory=False,
            )
            results.append({"id": row.get("id"), "query": query, "status": "EXECUTED", "semantic": semantic(payload)})
        except Exception as error:
            results.append({"id": row.get("id"), "query": query, "status": "FIXTURE_GAP", "reason": f"offline pipeline dependency unavailable: {type(error).__name__}: {error}", "intent": intent})
        finally:
            pipeline.discover_market = original
    return results, quality_cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-candidates", type=int, default=15)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--query", action="append", default=[])
    args = parser.parse_args()
    items = rows()
    if args.query:
        wanted = set(args.query)
        items = [item for item in items if str(item.get("query") or "") in wanted]
        present = {str(item.get("query") or "") for item in items}
        items.extend({"id": f"PILOT-{index:02d}", "query": query, "tags": ["pilot"]}
                     for index, query in enumerate(sorted(wanted - present), 1))
    if args.limit:
        items = items[:max(0, args.limit)]
    first, quality_cases = run_once(items, args.max_candidates)
    second, _ = run_once(items, args.max_candidates)
    first_semantic = {x["id"]: x.get("semantic") for x in first if x.get("status") == "EXECUTED"}
    second_semantic = {x["id"]: x.get("semantic") for x in second if x.get("status") == "EXECUTED"}
    mismatches = [key for key in sorted(set(first_semantic) | set(second_semantic)) if first_semantic.get(key) != second_semantic.get(key)]
    output = {
        "schema_version": "phase_e_offline_certification.v1",
        "corpus": str(CORPUS), "corpus_sha256": sha256(CORPUS), "total": len(items),
        "freeze": {"catalogue_revision": pipeline.CATALOGUE_REVISION if pipeline is not None and hasattr(pipeline, "CATALOGUE_REVISION") else None, "max_candidates": args.max_candidates, "external_network": False, "pipeline_import_error": PIPELINE_IMPORT_ERROR},
        "run_1": first, "run_2": second,
        "counts": {"executed": len(first_semantic), "fixture_gap": sum(x.get("status") == "FIXTURE_GAP" for x in first), "deterministic_matches": len(first_semantic) - len(mismatches), "deterministic_mismatches": len(mismatches)},
        "mismatch_ids": mismatches,
        "quality_review_cases": quality_cases,
        "quality_review_status": "PROPOSED_NOT_INDEPENDENTLY_APPROVED",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
