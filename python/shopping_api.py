#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from api_contract import apply_response_contract
from intent_engine import parse_query

# Keep the health endpoint import-light.  The recommendation pipeline loads
# retailer/evidence adapters and can take several seconds on a cold Render
# instance, so importing it at module startup made a health probe look dead.
# Tests may still patch ``shopping_api.run_pipeline``; the lazy loader only
# fills it when the recommendation route is actually used.
run_pipeline = None


def _load_pipeline():
    global run_pipeline
    if run_pipeline is None:
        from shopping_intelligence_pipeline import run_pipeline as pipeline

        run_pipeline = pipeline
    return run_pipeline


MOBILE_UNIVERSE_FILE = (
    ROOT / "data" / "mobile_universe_priority_126.json"
)
RESEARCH_PREVIEW_FILE = ROOT / "data" / "mobile_research_preview.json"


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


def _load_public_research_preview() -> dict:
    try:
        payload = json.loads(RESEARCH_PREVIEW_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if payload.get("mode") != "PUBLIC_TECHNICAL_RESEARCH_PREVIEW":
        return {}
    products = payload.get("products")
    if not isinstance(products, list) or len(products) != 10:
        return {}
    if len({item.get("canonical_product_id") for item in products}) != len(products):
        return {}
    return payload


def _comparison_models(query: str) -> list[str]:
    normalized = _normalise_route_text(query)
    if "compare" not in normalized and " vs " not in f" {normalized} ":
        return []
    # Keep this route deliberately narrow: it reuses the frozen P13.1O
    # dataset for named Samsung A36/A56 comparisons and never broadens the
    # shopping candidate pool or invents a comparison engine.
    if "a36" in normalized and "a56" in normalized and "galaxy" in normalized:
        return ["Galaxy A36 5G", "Galaxy A56 5G"]
    return []


def _research_comparison(query: str, intent: dict) -> dict | None:
    models = _comparison_models(query)
    if not models:
        return None
    payload = _load_public_research_preview()
    products = payload.get("products") or []
    model_rows = []
    for model in models:
        rows = [
            row for row in products
            if row.get("brand") == "Samsung" and row.get("model") == model
        ]
        if not rows:
            return None
        base = rows[0]
        model_rows.append({
            "brand": base.get("brand"),
            "model": base.get("model"),
            "manufacturer_spec_status": base.get("manufacturer_spec_status"),
            "technical_lane": base.get("technical_lane"),
            "official_source": base.get("official_source"),
            "specifications": base.get("specifications") or {},
            "battery_evidence": base.get("battery_evidence") or {},
            "camera_evidence": base.get("camera_evidence") or {},
            "variants": [
                {
                    "canonical_product_id": row.get("canonical_product_id"),
                    "ram_gb": row.get("ram_gb"),
                    "storage_gb": row.get("storage_gb"),
                }
                for row in rows
            ],
        })
    return {
        "status": "RESEARCH_REFERENCE_ONLY",
        "query": query,
        "intent": intent,
        "models": model_rows,
        "source_dataset": "P13.1O_PUBLIC_TECHNICAL_RESEARCH_PREVIEW",
        "commerce": {
            "price": None,
            "stock": None,
            "purchase_cta_eligible": False,
            "publication_eligible": False,
        },
    }


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

# The public frontend is the only browser client for this read-only endpoint.
# Keep same-origin requests working while avoiding a wildcard CORS policy.
CORS(
    app,
    resources={
        r"/api/*": {
            # Keep the production origin explicit and permit only the two
            # exact loopback origins used by the approved local E2E harness.
            # This is not a wildcard and does not grant credentialed access.
            "origins": [
                "https://coupon-world.in",
                "http://127.0.0.1:4173",
                "http://localhost:4173",
            ],
            "methods": ["GET"],
            "allow_headers": [],
            "supports_credentials": False,
        }
    },
)


@app.get("/health")
def health():
    # Render supplies the deployed revision. Never infer it from a local checkout.
    revision = os.environ.get("RENDER_GIT_COMMIT", "").strip()
    if not re.fullmatch(r"[0-9a-fA-F]{40}", revision):
        revision = None
    return jsonify(
        {
            "status": "ok",
            "service": "coupon-world-shopping-intelligence",
            "revision": revision,
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

    parsed_intent = parse_query(query)
    research_comparison = _research_comparison(query, parsed_intent)
    if research_comparison is not None:
        # Comparison research is intentionally served from the existing
        # frozen P13.1O dataset. It never calls discovery, ranking or retailer
        # offer code, so strict shopping gates remain unchanged.
        output = apply_response_contract(
            {
                "query": query,
                "intent": parsed_intent,
                "recommendations": [],
                "result_status": "RESEARCH_REFERENCE_ONLY",
                "status": "RESEARCH_REFERENCE_ONLY",
                "completion_status": "PASS",
                "completion_reason": "Evidence-backed comparison served from the public research preview.",
                "exact_model_scope": {
                    "active": True,
                    "model_tokens": ["a36", "a56"],
                    "numeric_brand_pairs": [],
                },
                "stage_counts": {
                    "discovered": 0,
                    "identity_prepared": 0,
                    "identity_verified": 0,
                    "official_verified": 2,
                    "evidence_ready": 2,
                    "fit_scored": 0,
                    "qualifying_50_plus": 0,
                    "qualifying_unique_models": 0,
                    "recommendations_returned": 0,
                },
                "research_comparison": research_comparison,
                "market_data_status": "CURRENT_OFFERS_UNAVAILABLE",
            },
            requested_query=query,
        )
        output["request_route"] = "research_comparison"
        output["candidate_pool_entered"] = False
        output["hard_gate_rejections"] = []
        output["response_reason"] = "RESEARCH_COMPARISON"
        return jsonify(output)

    try:
        payload = _load_pipeline()(
            query=pipeline_query,
            # Mobile benchmark target:
            # enough discovery depth for Best-3 plus additional
            # comparison choices without immediately paying the
            # latency cost of the full 15-candidate pool.
            max_candidates=15,
            max_results=3,
            live_fast=True,
        )
    except Exception:
        app.logger.exception("Shopping intelligence pipeline failed")
        return (
            jsonify(
                {
                    "status": "error",
                    "error": "Shopping intelligence pipeline failed",
                }
            ),
            500,
        )

    # Preserve exactly what the shopper typed even when the
    # current mobile endpoint supplied an internal catalog scope.
    if pipeline_query != query:
        payload["query"] = query

    output = apply_response_contract(payload, requested_query=query)
    output["request_route"] = "shopping_candidate_pool"
    output["candidate_pool_entered"] = True
    gate_rejections = output.get("failures") or []
    if (
        not output.get("recommendations")
        and output.get("market_data_status") == "CURRENT_OFFERS_UNAVAILABLE"
    ):
        gate_rejections = [
            {
                "code": "NO_CURRENT_VERIFIED_OFFER",
                "stage": "commerce_gate",
                "reason": "No current in-stock retailer offer passed the existing price, identity and freshness gates.",
            }
        ] + gate_rejections
    output["hard_gate_rejections"] = gate_rejections
    output["response_reason"] = (
        "NO_CURRENT_VERIFIED_OFFER"
        if gate_rejections and gate_rejections[0].get("code") == "NO_CURRENT_VERIFIED_OFFER"
        else None
    )
    return jsonify(output)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", "8000")),
        debug=False,
    )

