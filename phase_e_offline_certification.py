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
import re
from unittest.mock import patch
import requests
import urllib.request
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
_DISCOVERY_CACHE: dict[str, Any] | None = None
_CATALOGUE_CANDIDATES: list[dict[str, Any]] | None = None
CATALOGUE_MODE = False

def frozen_catalogue_candidates() -> list[dict[str, Any]]:
    global _CATALOGUE_CANDIDATES
    if _CATALOGUE_CANDIDATES is not None:
        return _CATALOGUE_CANDIDATES
    registry = json.loads((ROOT / "data" / "retailer_product_registry.json").read_text(encoding="utf-8"))
    owned = set()
    for value in (registry.get("products") or {}).values():
        for retailer in (value or {}).values():
            if retailer.get("retailer_product_id"):
                owned.add(str(retailer["retailer_product_id"]).upper())
    catalogue = json.loads((ROOT / "coupons.json").read_text(encoding="utf-8-sig"))
    catalogue = catalogue if isinstance(catalogue, list) else catalogue.get("products", [])
    rows = []
    for item in catalogue:
        asin = str(item.get("asin") or "").upper()
        if asin not in owned or "mobile" not in str(item.get("category") or "").lower() and "phone" not in str(item.get("title") or "").lower():
            continue
        rows.append({
            "candidate_id": f"frozen-{asin}", "asin": asin,
            "title": item.get("title"), "source_title": item.get("title"),
            "brand": item.get("brand"), "source_url": item.get("link"),
            "market_source_url": item.get("link"), "source": "FROZEN_CATALOGUE_INTEGRATION",
        })
    _CATALOGUE_CANDIDATES = rows
    return rows


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def rows() -> list[dict[str, Any]]:
    payload = json.loads(CORPUS.read_text(encoding="utf-8"))
    splits = payload.get("splits") or {}
    return [item for split in ("train", "validation", "test") for item in splits.get(split, [])]


def discovery_for(query: str, intent: dict[str, Any], max_candidates: int, *, allow_compatible: bool = True) -> dict[str, Any] | None:
    # Candidate snapshots are sufficient to exercise the downstream identity,
    # evidence, eligibility, scoring and serialization path. Missing offer or
    # extractor records remain honest partial results; they must not prevent
    # the algorithm from executing.
    if CATALOGUE_MODE:
        candidates = frozen_catalogue_candidates()
        return ({"candidates": [dict(item) for item in candidates],
                 "candidate_count": len(candidates),
                 "snapshot_source_query": "FROZEN_CATALOGUE_INTEGRATION"}
                if candidates else None)
    if get_candidate_snapshot is None or not OFFLINE_FIXTURE_MANIFEST.exists():
        return None
    exact = get_candidate_snapshot(
        query=query,
        category=intent.get("category"),
        max_candidates=max_candidates,
    )
    if exact is not None:
        exact["snapshot_source_query"] = query
        return exact
    if not allow_compatible:
        return None

    # Reuse only a snapshot whose structured intent constraints are identical.
    # Lexical wording may differ, but budget, category, brand, variant and
    # preference constraints must match exactly.
    def signature(parsed: dict[str, Any]) -> tuple[Any, ...]:
        return (
            parsed.get("category"), parsed.get("budget_min"), parsed.get("budget_max"),
            tuple(sorted(parsed.get("brands") or [])),
            tuple(sorted(parsed.get("must_have") or [])),
            tuple(sorted(parsed.get("preferred") or [])),
            tuple(sorted(parsed.get("avoid") or [])),
        )

    global _DISCOVERY_CACHE
    if _DISCOVERY_CACHE is None:
        _DISCOVERY_CACHE = __import__("market_discovery").load_discovery_cache()
    cache = _DISCOVERY_CACHE
    prefix = f"__candidate_snapshot__::{intent.get('category')}::"
    for key in sorted(cache):
        if not key.startswith(prefix) or not key.endswith(f"::{max_candidates}"):
            continue
        snapshot_query = key[len(prefix):-len(f"::{max_candidates}")]
        snapshot_intent = parse_query(snapshot_query)
        if signature(snapshot_intent) != signature(intent):
            continue
        candidate = get_candidate_snapshot(
            query=snapshot_query,
            category=snapshot_intent.get("category"),
            max_candidates=max_candidates,
        )
        if candidate is not None:
            candidate["snapshot_source_query"] = snapshot_query
            return candidate
    # Catalogue-backed integration lane: this is a frozen candidate universe,
    # not a live discovery result. Query constraints remain enforced downstream.
    candidates = frozen_catalogue_candidates() if CATALOGUE_MODE else []
    if candidates:
        return {"candidates": [dict(item) for item in candidates],
                "candidate_count": len(candidates),
                "snapshot_source_query": "FROZEN_CATALOGUE_INTEGRATION"}
    return None


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
        tags = set(row.get("tags") or [])
        snapshot = discovery_for(
            query, intent, max_candidates,
            allow_compatible=not bool(tags & {"exact_model", "ram", "storage"}),
        )
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
            def blocked(*args, **kwargs):
                raise requests.ConnectionError("offline external source blocked")
            with patch.object(requests, "get", blocked), patch.object(urllib.request, "urlopen", blocked):
                payload = pipeline._run_pipeline_once(
                    query, max_candidates=max_candidates, max_results=3,
                    live_fast=True, _discovery=snapshot, _save_discovery_memory=False,
                    _allow_evidence_writes=CATALOGUE_MODE,
                )
            execution_class = (
                "EXECUTED_WITH_RESULTS" if payload.get("recommendations")
                else "EXECUTED_INCOMPLETE"
            )
            results.append({"id": row.get("id"), "query": query, "status": execution_class, "snapshot_source_query": snapshot.get("snapshot_source_query"), "semantic": semantic(payload), "rejection_summary": payload.get("failure_summary", [])})
        except Exception as error:
            results.append({"id": row.get("id"), "query": query, "status": "TECHNICAL_EXECUTION_FAILURE", "reason": f"offline pipeline dependency unavailable: {type(error).__name__}: {error}", "intent": intent})
        finally:
            pipeline.discover_market = original
    return results, quality_cases


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--max-candidates", type=int, default=15)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--query", action="append", default=[])
    parser.add_argument("--catalogue-mode", action="store_true")
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--checkpoint", type=Path, default=None)
    args = parser.parse_args()
    items = rows()
    if args.query:
        wanted = set(args.query)
        items = [item for item in items if str(item.get("query") or "") in wanted]
        present = {str(item.get("query") or "") for item in items}
        items.extend({"id": f"PILOT-{index:02d}", "query": query, "tags": ["pilot"]}
                     for index, query in enumerate(sorted(wanted - present), 1))
    if args.offset:
        items = items[max(0, args.offset):]
    if args.limit:
        items = items[:max(0, args.limit)]
    if args.catalogue_mode:
        # The lane is selected by making the frozen catalogue available only
        # for this invocation; captured-source mode remains the default.
        global _DISCOVERY_CACHE, CATALOGUE_MODE
        _DISCOVERY_CACHE = {}
        CATALOGUE_MODE = True
    first, quality_cases = run_once(items, args.max_candidates)
    second, _ = run_once(items, args.max_candidates)
    executed_statuses = {"EXECUTED_WITH_RESULTS", "EXECUTED_INCOMPLETE", "EXECUTED_UNSUPPORTED"}
    first_semantic = {x["id"]: x.get("semantic") for x in first if x.get("status") in executed_statuses}
    second_semantic = {x["id"]: x.get("semantic") for x in second if x.get("status") in executed_statuses}
    mismatches = [key for key in sorted(set(first_semantic) | set(second_semantic)) if first_semantic.get(key) != second_semantic.get(key)]
    output = {
        "schema_version": "phase_e_offline_certification.v1",
        "corpus": str(CORPUS), "corpus_sha256": sha256(CORPUS), "total": len(items),
        "freeze": {"catalogue_revision": pipeline.CATALOGUE_REVISION if pipeline is not None and hasattr(pipeline, "CATALOGUE_REVISION") else None, "max_candidates": args.max_candidates, "external_network": False, "pipeline_import_error": PIPELINE_IMPORT_ERROR},
        "run_1": first, "run_2": second,
        "counts": {"executed": len(first_semantic), "with_results": sum(x.get("status") == "EXECUTED_WITH_RESULTS" for x in first), "incomplete": sum(x.get("status") == "EXECUTED_INCOMPLETE" for x in first), "technical_failure": sum(x.get("status") == "TECHNICAL_EXECUTION_FAILURE" for x in first), "fixture_gap": sum(x.get("status") == "FIXTURE_GAP" for x in first), "deterministic_matches": len(first_semantic) - len(mismatches), "deterministic_mismatches": len(mismatches)},
        "mismatch_ids": mismatches,
        "quality_review_cases": quality_cases,
        "quality_review_status": "PROPOSED_NOT_INDEPENDENTLY_APPROVED",
    }
    if args.checkpoint:
        args.checkpoint.parent.mkdir(parents=True, exist_ok=True)
        previous = {}
        if args.checkpoint.exists():
            try:
                previous = json.loads(args.checkpoint.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                previous = {}
        batches = previous.get("batches") if isinstance(previous, dict) else []
        if not isinstance(batches, list):
            batches = []
        batches.append({"offset": args.offset, "limit": args.limit, "corpus_sha256": output["corpus_sha256"], "counts": output["counts"], "run_1": first, "run_2": second})
        args.checkpoint.write_text(json.dumps({"schema_version": output["schema_version"], "corpus_sha256": output["corpus_sha256"], "batches": batches}, indent=2, ensure_ascii=False), encoding="utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(output["counts"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
