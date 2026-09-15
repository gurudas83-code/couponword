#!/usr/bin/env python3

"""Build Coupon World's deterministic 1,000-query mobile coverage corpus."""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PRIORITY_FILE = ROOT / "data" / "mobile_universe_priority_126.json"
OUTPUT_FILE = ROOT / "data" / "mobile_query_corpus_1000.json"
BUDGETS = [8000, 10000, 12000, 15000, 18000, 20000, 25000, 30000, 40000, 50000]
QUERY_BRAND_ALIASES = {"xiaomi/redmi": "Redmi"}


def load_priority_products(path: Path) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    products = payload.get("products")
    if not isinstance(products, list) or len(products) != 126:
        raise ValueError("priority universe must contain exactly 126 products")
    return [item for item in products if isinstance(item, dict)]


def first_ten_brands(products: list[dict]) -> list[tuple[str, str]]:
    selected: list[tuple[str, str]] = []
    seen: set[str] = set()
    for item in sorted(products, key=lambda row: int(row.get("priority") or 9999)):
        source_brand = str(item.get("brand") or "").strip()
        brand = QUERY_BRAND_ALIASES.get(source_brand.casefold(), source_brand)
        model = str(item.get("model") or "").strip()
        key = brand.casefold()
        if brand and model and key not in seen:
            selected.append((brand, model))
            seen.add(key)
        if len(selected) == 10:
            return selected
    raise ValueError("priority universe does not contain ten usable brands")


def query_variants(brand: str, model: str, budget: int) -> list[dict]:
    short_budget = f"{budget // 1000}k"
    return [
        {"query": f"best {brand} phone under {budget}", "tags": ["brand", "budget", "english"]},
        {"query": f"{brand} 5G mobile {short_budget} ke andar", "tags": ["brand", "budget", "5g", "hinglish"]},
        {"query": f"{brand} 8/128 phone below {budget}", "tags": ["brand", "budget", "ram", "storage"]},
        {"query": f"camera priority {brand} phone under {budget}", "tags": ["brand", "budget", "camera"]},
        {"query": f"battery pe compromise nahi {brand} mobile under {budget}", "tags": ["brand", "budget", "battery", "hinglish"]},
        {"query": f"gaming ke liye {brand} phone {short_budget} tak", "tags": ["brand", "budget", "gaming", "hinglish"]},
        {"query": f"student ke liye {brand} mobile under {budget}", "tags": ["brand", "budget", "student", "hinglish"]},
        {"query": f"{brand} nahi chahiye phone under {budget}", "tags": ["avoid_brand", "budget", "hinglish"]},
        {"query": f"12GB 256GB {brand} smartphone under {budget}", "tags": ["brand", "budget", "ram", "storage"]},
        {"query": f"exact model {model} phone under {budget}", "tags": ["exact_model", "named_model", "budget"]},
    ]


def build(products: list[dict]) -> dict:
    records: list[dict] = []
    for brand, model in first_ten_brands(products):
        for budget in BUDGETS:
            for item in query_variants(brand, model, budget):
                records.append({
                    "query": item["query"],
                    "tags": item["tags"],
                    "brand_context": brand,
                    "model_context": model,
                    "budget_context": budget,
                })

    if len(records) != 1000 or len({x["query"] for x in records}) != 1000:
        raise ValueError("corpus must contain exactly 1,000 unique queries")

    random.Random(20260915).shuffle(records)
    boundaries = (("train", 0, 800), ("validation", 800, 900), ("test", 900, 1000))
    splits = {}
    sequence = 1
    for split, start, end in boundaries:
        rows = []
        for item in records[start:end]:
            rows.append({"id": f"MQ{sequence:04d}", **item})
            sequence += 1
        splits[split] = rows

    return {
        "schema_version": "1.0",
        "category": "smartphone",
        "market": "IN",
        "purpose": "intent coverage and regression benchmarking; not model training data",
        "seed": 20260915,
        "counts": {"total": 1000, "train": 800, "validation": 100, "test": 100},
        "splits": splits,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--priority", type=Path, default=PRIORITY_FILE)
    parser.add_argument("--output", type=Path, default=OUTPUT_FILE)
    args = parser.parse_args()
    payload = build(load_priority_products(args.priority))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    print("MOBILE QUERY CORPUS: PASS")
    print("Output     :", args.output)
    print("Total      :", payload["counts"]["total"])
    print("Train      :", payload["counts"]["train"])
    print("Validation :", payload["counts"]["validation"])
    print("Test       :", payload["counts"]["test"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
