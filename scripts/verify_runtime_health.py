#!/usr/bin/env python3
"""Read-only production API probe. Never treats a research result as a buyable offer."""
from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://couponword.onrender.com"
EXPECTED_SERVICE = "coupon-world-shopping-intelligence"


def get_json(url: str, attempts: int = 3, timeout: int = 65) -> tuple[dict, float]:
    last_error = None
    for attempt in range(attempts):
        began = time.monotonic()
        try:
            with urlopen(
                Request(url, headers={"User-Agent": "CouponWorldReadOnlyRuntimeAudit/1.0", "Accept": "application/json"}),
                timeout=timeout,
            ) as response:
                if response.status != 200:
                    raise ValueError("HTTP " + str(response.status))
                payload = json.loads(response.read(2_000_000))
                if not isinstance(payload, dict):
                    raise ValueError("Expected JSON object")
                return payload, round(time.monotonic() - began, 2)
        except (HTTPError, URLError, TimeoutError, ValueError, OSError) as exc:
            last_error = type(exc).__name__ + ": " + str(exc)[:200]
            if attempt + 1 < attempts:
                time.sleep(5)
    raise RuntimeError(f"API did not return valid JSON after {attempts} attempts: {last_error}")


def probe(base_url: str = BASE_URL) -> dict:
    base = base_url.rstrip("/")
    health, health_seconds = get_json(base + "/health")
    if health.get("status") != "ok" or health.get("service") != EXPECTED_SERVICE:
        raise ValueError("Backend health contract changed unexpectedly")
    query = "compare Samsung Galaxy A36 5G vs Samsung Galaxy A56 5G"
    comparison, comparison_seconds = get_json(
        base + "/api/recommend?" + urlencode({"q": query}), attempts=2
    )
    if comparison.get("request_route") != "research_comparison":
        raise ValueError("Existing safe comparison route was not selected: "
                         + str(comparison.get("request_route")))
    if comparison.get("candidate_pool_entered") is not False:
        raise ValueError("Research-only comparison unexpectedly entered commerce")
    evidence = comparison.get("research_comparison")
    if not isinstance(evidence, dict):
        raise ValueError("Safe comparison evidence not returned")
    commerce = evidence.get("commerce") or {}
    if commerce.get("purchase_cta_eligible"):
        raise ValueError("Research-only comparison incorrectly became buyable")
    return {
        "result": "PASS",
        "checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "backend": base,
        "revision": health.get("revision"),
        "health_latency_seconds": health_seconds,
        "safe_comparison_latency_seconds": comparison_seconds,
        "route": comparison["request_route"],
        "tested": ["GET /health", "GET /api/recommend (read-only research comparison)"],
        "not_tested": ["live merchant stock", "price refresh", "full merchant recommendation latency", "browser interactions"],
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--base", default=BASE_URL)
    args = p.parse_args()
    try:
        result = probe(args.base)
    except Exception as exc:
        print(json.dumps({"result": "FAIL", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
