#!/usr/bin/env python3

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS


ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from shopping_intelligence_pipeline import run_pipeline


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

    try:
        payload = run_pipeline(
            query=query,
            max_candidates=4,
            max_results=4,
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

    return jsonify(payload)


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=8000,
        debug=False,
    )

