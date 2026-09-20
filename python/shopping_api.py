#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from intent_engine import parse_query
from shopping_intelligence_pipeline import run_pipeline


MOBILE_UNIVERSE_FILE = (
    ROOT / "data" / "mobile_universe_priority_126.json"
)


def _normalise_route_text(value: str) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").casefold().strip(),
    )


def _load_mobile_brand_aliases() -> set[str]:
    """
    Derive mobile-brand scope from the existing mobile universe.

    Do not globally redefine a brand such as Samsung as smartphone;
    this scope is used only for an otherwise category-less bare-brand
    request on the current mobile recommendation endpoint.
    """
    try:
        payload = json.loads(
            MOBILE_UNIVERSE_FILE.read_text(encoding="utf-8")
        )
    except Exception:
        return set()

    aliases: set[str] = set()

    for product in payload.get("products") or []:
        if not isinstance(product, dict):
            continue

        brand = str(product.get("brand") or "").strip()

        for part in re.split(r"[/|,]", brand):
            normalised = _normalise_route_text(part)

            if normalised:
                aliases.add(normalised)

    return aliases


MOBILE_BRAND_ALIASES = _load_mobile_brand_aliases()


def mobile_scoped_query(query: str) -> str:
    """
    Scope only a bare known-mobile-brand query.

    Examples:
      Samsung             -> Samsung smartphone
      OnePlus             -> OnePlus smartphone
      Samsung TV          -> unchanged
      Samsung refrigerator-> unchanged
      Samsung phone ...   -> unchanged (already categorised)
    """
    intent = parse_query(query)

    if intent.get("category"):
        return query

    if str(intent.get("intent") or "") != "brand_search":
        return query

    brands = [
        str(value).strip()
        for value in (intent.get("brands") or [])
        if str(value).strip()
    ]

    if len(brands) != 1:
        return query

    brand_key = _normalise_route_text(brands[0])
    query_key = _normalise_route_text(query)

    if brand_key not in MOBILE_BRAND_ALIASES:
        return query

    if query_key != brand_key:
        return query

    return f"{query} smartphone"


app = Flask(__name__)

# Development only.
# Production CORS will later be restricted to coupon-world.in.
CORS(app)


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "coupon-world-shopping-intelligence",
        }
    )


@app.get("/api/recommend")
def recommend():
    query = str(request.args.get("q") or "").strip()

    if not query:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "Missing shopping query",
                }
            ),
            400,
        )

    if len(query) > 300:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "Shopping query is too long",
                }
            ),
            400,
        )

    pipeline_query = mobile_scoped_query(query)

    try:
        payload = run_pipeline(
            query=pipeline_query,
            # Mobile benchmark target:
            # enough discovery depth for Best-3 plus additional
            # comparison choices without immediately paying the
            # latency cost of the full 15-candidate pool.
            max_candidates=8,
            max_results=6,
            live_fast=True,
        )
    except Exception as error:
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "Shopping intelligence pipeline failed",
                    "detail": str(error),
                }
            ),
            500,
        )

    # Preserve exactly what the shopper typed even when the
    # current mobile endpoint supplied an internal catalog scope.
    if pipeline_query != query:
        payload["query"] = query

    return jsonify(payload)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False,
    )

