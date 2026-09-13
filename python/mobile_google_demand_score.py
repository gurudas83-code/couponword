#!/usr/bin/env python3

"""
Coupon World - Mobile Google Demand Scorer v1

Purpose:
- Join Google Keyword Planner historical metrics to Coupon World's
  126-mobile keyword research map.
- Produce demand-ranked mobile research priorities.
- Never treat Google search demand as product Fit.
- Never invent missing search-volume metrics.
- Never modify the stable mobile universe source file.

Google Demand Score is a research/enrichment priority signal, NOT sales units
and NOT a recommendation score.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent

DEFAULT_KEYWORDS = (
    ROOT / "data" / "mobile_google_demand_keywords_126.csv"
)

DEFAULT_OUTPUT = (
    ROOT / "data" / "mobile_google_demand_ranked_126.json"
)

KEYWORD_TYPE_WEIGHTS = {
    "model": 1.00,
    "variant": 0.90,
    "price": 0.70,
    "buy": 0.70,
}

KEYWORD_COLUMN_ALIASES = (
    "keyword",
    "keywords",
    "search term",
    "search_term",
)

AVG_MONTHLY_SEARCH_ALIASES = (
    "avg. monthly searches",
    "avg monthly searches",
    "average monthly searches",
    "avg_monthly_searches",
)

COMPETITION_ALIASES = (
    "competition",
    "competition (indexed value)",
    "competition_index",
)


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def normalize_keyword(value: Any) -> str:
    return clean(value).casefold()


def parse_number(value: Any) -> float | None:
    text = clean(value)

    if not text:
        return None

    text = text.replace(",", "")

    try:
        return float(text)
    except ValueError:
        return None


def find_column(
    fieldnames: list[str],
    aliases: tuple[str, ...],
) -> str | None:
    mapping = {
        clean(name).casefold(): name
        for name in fieldnames
        if clean(name)
    }

    for alias in aliases:
        match = mapping.get(alias.casefold())
        if match:
            return match

    return None


def load_keyword_map(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Keyword map not found: {path}"
        )

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as handle:
        rows = list(csv.DictReader(handle))

    required = {
        "priority",
        "brand",
        "model",
        "variant",
        "keyword_type",
        "keyword",
    }

    if not rows:
        raise ValueError("Keyword map is empty")

    missing = required - set(rows[0].keys())

    if missing:
        raise ValueError(
            "Keyword map missing columns: "
            + ", ".join(sorted(missing))
        )

    return rows


def load_google_metrics(
    path: Path,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(
            f"Google metrics CSV not found: {path}"
        )

    raw = path.read_bytes()

    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        encoding = "utf-16"
    else:
        encoding = "utf-8-sig"

    report_text = raw.decode(encoding)
    lines = report_text.splitlines()

    header_index = next(
        (
            index
            for index, line in enumerate(lines)
            if "keyword" in line.casefold()
            and "avg. monthly searches" in line.casefold()
        ),
        None,
    )

    if header_index is None:
        raise ValueError(
            "Could not locate Google Keyword Planner header"
        )

    header_line = lines[header_index]
    delimiter = "\t" if "\t" in header_line else ","

    reader = csv.DictReader(
        io.StringIO(
            "\n".join(lines[header_index:])
        ),
        delimiter=delimiter,
    )

    fieldnames = list(reader.fieldnames or [])

    keyword_column = find_column(
        fieldnames,
        KEYWORD_COLUMN_ALIASES,
    )

    search_column = find_column(
        fieldnames,
        AVG_MONTHLY_SEARCH_ALIASES,
    )

    competition_column = find_column(
        fieldnames,
        COMPETITION_ALIASES,
    )

    if not keyword_column:
        raise ValueError(
            "Could not find keyword column in Google CSV"
        )

    if not search_column:
        raise ValueError(
            "Could not find Avg. monthly searches column "
            "in Google CSV"
        )

    metrics: dict[str, dict[str, Any]] = {}

    for row in reader:
        keyword = normalize_keyword(
            row.get(keyword_column)
        )

        if not keyword:
            continue

        searches = parse_number(
            row.get(search_column)
        )

        # Blank Google metrics stay unknown.
        # Never manufacture zero demand.
        if searches is None:
            continue

        metrics[keyword] = {
            "avg_monthly_searches": searches,
            "competition": (
                clean(row.get(competition_column))
                if competition_column
                else None
            ),
        }

    metadata: dict[str, Any] = {
        "keyword_column": keyword_column,
        "search_column": search_column,
        "competition_column": (
            competition_column or ""
        ),
        "encoding": encoding,
        "delimiter": (
            "tab"
            if delimiter == "\t"
            else "comma"
        ),
        "header_row": header_index + 1,
        "report_title": (
            clean(lines[0])
            if header_index >= 1
            else ""
        ),
        "period": (
            clean(lines[1])
            if header_index >= 2
            else ""
        ),
        "metric_keyword_count": len(metrics),
    }

    return metrics, metadata

def build_product_demand(
    keyword_rows: list[dict[str, Any]],
    metrics: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    products: dict[
        tuple[str, str, str, str],
        dict[str, Any],
    ] = {}

    for row in keyword_rows:
        product_key = (
            clean(row.get("priority")),
            clean(row.get("brand")),
            clean(row.get("model")),
            clean(row.get("variant")),
        )

        product = products.setdefault(
            product_key,
            {
                "priority": (
                    int(row["priority"])
                    if clean(row.get("priority")).isdigit()
                    else None
                ),
                "brand": clean(row.get("brand")),
                "model": clean(row.get("model")),
                "variant": clean(row.get("variant")),
                "matched_keywords": [],
                "missing_keywords": [],
                "model_avg_monthly_searches": None,
                "supporting_keyword_count": 0,
            },
        )

        keyword = clean(row.get("keyword"))
        keyword_type = clean(
            row.get("keyword_type")
        ).lower()

        metric = metrics.get(
            normalize_keyword(keyword)
        )

        if not metric:
            product["missing_keywords"].append(
                {
                    "keyword_type": keyword_type,
                    "keyword": keyword,
                }
            )
            continue

        searches = float(
            metric["avg_monthly_searches"]
        )

        product["matched_keywords"].append(
            {
                "keyword_type": keyword_type,
                "keyword": keyword,
                "avg_monthly_searches": searches,
                "competition": metric.get(
                    "competition"
                ),
            }
        )

        if keyword_type == "model":
            product["model_avg_monthly_searches"] = searches
        else:
            product["supporting_keyword_count"] += 1

    records = list(products.values())

    observed_model_volumes = [
        float(item["model_avg_monthly_searches"])
        for item in records
        if item["model_avg_monthly_searches"] is not None
    ]

    max_model_volume = max(
        observed_model_volumes,
        default=0.0,
    )

    denominator = (
        math.log1p(max_model_volume)
        if max_model_volume > 0
        else 0.0
    )

    def demand_tier(
        volume: float | None,
    ) -> str:
        if volume is None:
            return "unknown"
        if volume >= 5_000_000:
            return "exceptional"
        if volume >= 500_000:
            return "very_high"
        if volume >= 50_000:
            return "high"
        if volume >= 5_000:
            return "medium"
        if volume >= 500:
            return "low"
        if volume >= 50:
            return "very_low"
        if volume > 0:
            return "minimal"
        return "reported_zero"

    for item in records:
        volume = item[
            "model_avg_monthly_searches"
        ]

        item["matched_keyword_count"] = len(
            item["matched_keywords"]
        )

        item["missing_keyword_count"] = len(
            item["missing_keywords"]
        )

        item["google_demand_tier"] = demand_tier(
            volume
        )

        if volume is None:
            item["google_demand_score"] = None
        elif volume <= 0 or denominator <= 0:
            item["google_demand_score"] = 0.0
        else:
            item["google_demand_score"] = round(
                math.log1p(float(volume))
                / denominator
                * 100.0,
                2,
            )

    distinct_volumes = sorted(
        {
            float(item["model_avg_monthly_searches"])
            for item in records
            if item["model_avg_monthly_searches"]
            is not None
        },
        reverse=True,
    )

    dense_rank = {
        volume: rank
        for rank, volume in enumerate(
            distinct_volumes,
            start=1,
        )
    }

    for item in records:
        volume = item[
            "model_avg_monthly_searches"
        ]

        item["google_demand_rank"] = (
            dense_rank.get(float(volume))
            if volume is not None
            else None
        )

    records.sort(
        key=lambda item: (
            item["model_avg_monthly_searches"]
            is not None,
            (
                float(
                    item[
                        "model_avg_monthly_searches"
                    ]
                )
                if item[
                    "model_avg_monthly_searches"
                ] is not None
                else -1.0
            ),
            -(
                int(item["priority"])
                if item["priority"] is not None
                else 10**9
            ),
        ),
        reverse=True,
    )

    return records

def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Rank Coupon World mobile research priority "
            "using real Google Keyword Planner metrics"
        )
    )

    parser.add_argument(
        "--metrics",
        required=True,
        help=(
            "Google Keyword Planner historical metrics CSV"
        ),
    )

    parser.add_argument(
        "--keywords",
        default=str(DEFAULT_KEYWORDS),
    )

    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
    )

    args = parser.parse_args()

    keyword_path = Path(args.keywords)
    metrics_path = Path(args.metrics)
    output_path = Path(args.output)

    keyword_rows = load_keyword_map(
        keyword_path
    )

    metrics, columns = load_google_metrics(
        metrics_path
    )

    ranked = build_product_demand(
        keyword_rows,
        metrics,
    )

    matched_products = sum(
        1
        for item in ranked
        if item["matched_keyword_count"] > 0
    )

    payload = {
        "schema_version": "1.0",
        "signal": "google_search_demand",
        "market": "IN",
        "category": "smartphone",
        "score_policy": (
            "Research/enrichment priority only. "
            "Not sales units and not recommendation Fit."
        ),
        "source": {
            "type": (
                "google_keyword_planner_historical_metrics"
            ),
            "metrics_file": str(metrics_path),
            "keyword_map_file": str(keyword_path),
            "detected_columns": columns,
        },
        "product_count": len(ranked),
        "products_with_google_metrics": matched_products,
        "products_without_google_metrics": (
            len(ranked) - matched_products
        ),
        "products": ranked,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    print("GOOGLE DEMAND SCORE: PASS")
    print("PRODUCTS:", len(ranked))
    print(
        "WITH GOOGLE METRICS:",
        matched_products,
    )
    print(
        "WITHOUT GOOGLE METRICS:",
        len(ranked) - matched_products,
    )
    print("OUTPUT:", output_path)

    print()
    print("TOP 10:")

    for item in ranked[:10]:
        print(
            f"{item['google_demand_rank']:>3}. "
            f"{item['brand']} {item['model']} "
            f"{item['variant']} | "
            f"score={item['google_demand_score']} | "
            f"model_volume="
            f"{item['model_avg_monthly_searches']} | "
            f"tier={item['google_demand_tier']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
