#!/usr/bin/env python3
"""Benchmark the structured 1,000-query corpus against intent_engine."""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))
from intent_engine import parse_query

DEFAULT_CORPUS = ROOT / "data" / "mobile_query_corpus_1000.json"
DEFAULT_REPORT = ROOT / "data" / "mobile_query_benchmark_phase3_report.json"
MOBILE_CATEGORIES = {"mobile", "mobiles", "phone", "phones", "smartphone", "smartphones"}


def norm(value) -> str:
    return str(value or "").strip().casefold()


def load_rows(path: Path, split: str) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if isinstance(payload, list):
        return [{"id": row.get("id"), "query": row.get("q") or row.get("query"), "tags": []} for row in payload]
    splits = payload.get("splits") or {}
    if split == "all":
        return [row for name in ("train", "validation", "test") for row in splits.get(name, [])]
    return list(splits.get(split, []))


def evaluate(row: dict) -> dict:
    query = str(row.get("query") or "").strip()
    tags = set(row.get("tags") or [])
    intent = parse_query(query)
    failures: list[str] = []
    warnings: list[str] = []

    if norm(intent.get("category")) not in MOBILE_CATEGORIES:
        failures.append(f"mobile category not recognized: {intent.get('category')!r}")
    budget = row.get("budget_context")
    if budget is not None and intent.get("budget_max") != budget:
        failures.append(f"budget_max={intent.get('budget_max')!r}; expected={budget}")

    brand = norm(row.get("brand_context"))
    brands = {norm(x) for x in intent.get("brands", [])}
    avoid = {norm(x) for x in intent.get("avoid", [])}
    if "avoid_brand" in tags:
        if f"brand_{brand}" not in avoid:
            failures.append(f"avoided brand not captured: {brand}")
    elif "brand" in tags and brand not in brands:
        failures.append(f"brand not captured: {brand}")

    must_have = {norm(x) for x in intent.get("must_have", [])}
    if "5g" in tags and "5g" not in must_have:
        warnings.append("5g not represented in must_have")
    if "ram" in tags and not any("gb_ram" in x for x in must_have):
        warnings.append("RAM not represented in must_have")
    if "storage" in tags and not any("gb_storage" in x for x in must_have):
        warnings.append("storage not represented in must_have")
    # Exact candidate identity is enforced later by mobile_exact_identity_gate.
    # This intent-stage benchmark validates its category and budget context only.

    return {"id": row.get("id"), "query": query, "passed": not failures,
            "failures": failures, "warnings": warnings, "intent": intent}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus", type=Path, default=DEFAULT_CORPUS)
    parser.add_argument("--split", choices=("all", "train", "validation", "test"), default="all")
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    results = [evaluate(row) for row in load_rows(args.corpus, args.split)]
    passed = sum(item["passed"] for item in results)
    failure_types = Counter(reason.split(":", 1)[0] for item in results for reason in item["failures"])
    report = {
        "corpus": str(args.corpus), "split": args.split, "total": len(results),
        "passed": passed, "failed": len(results) - passed,
        "score_percent": round(100 * passed / max(len(results), 1), 2),
        "warning_count": sum(len(item["warnings"]) for item in results),
        "failure_types": dict(failure_types), "results": results,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print("COUPON WORLD - MOBILE QUERY BENCHMARK / PHASE D")
    for label, key in (("Split", "split"), ("Total", "total"), ("Passed", "passed"),
                       ("Failed", "failed"), ("Score %", "score_percent"),
                       ("Warnings", "warning_count")):
        print(f"{label:9}:", report[key])
    print("Report   :", args.report)
    if failure_types:
        print("Failure types:", dict(failure_types))
    return 1 if args.strict and report["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
