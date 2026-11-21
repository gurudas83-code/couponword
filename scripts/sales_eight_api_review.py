#!/usr/bin/env python3
"""Review the private six-phone API response without publishing offers.

Use locally with: python scripts/sales_eight_api_review.py private_observations/sales_eight_api_probe.json
No network calls, no public catalogue writes, no API charges.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

EXPECTED = (
    "vivo|y31 5g", "samsung|galaxy a07 5g",
    "samsung|galaxy a17 5g", "vivo|y11 5g",
    "vivo|y21 5g", "redmi|redmi 15a 5g",
    "redmi|redmi a7",
)
# There are eight reviewed keys overall; this is the remaining-six batch.
REMAINING_SIX = (
    "samsung|galaxy a07 5g", "samsung|galaxy a17 5g",
    "vivo|y11 5g", "vivo|y21 5g",
    "redmi|redmi 15a 5g", "redmi|redmi a7",
)
ALL_EIGHT = ("oppo|a6x 5g", "vivo|y31 5g") + REMAINING_SIX


def review(report: dict) -> dict:
    if report.get("mode") != "PRIVATE_RESEARCH_OBSERVATIONS":
        raise ValueError("Unsupported private evidence format")
    records = report.get("records")
    if not isinstance(records, list) or not isinstance(report.get("calls_attempted"), int):
        raise ValueError("Invalid API evidence record")
    if report["calls_attempted"] < 0 or report["calls_attempted"] > 6:
        raise ValueError("Six-call API budget exceeded")
    seen = set()
    decisions = []
    for entry in records:
        if not isinstance(entry, dict):
            raise ValueError("Invalid record entry")
        key = entry.get("audit_id")
        if key not in REMAINING_SIX or key in seen:
            raise ValueError("Unexpected or duplicate API model: " + str(key))
        seen.add(key)
        candidates = entry.get("candidates", [])
        if not isinstance(candidates, list):
            raise ValueError("Invalid candidate list")
        for candidate in candidates:
            if not isinstance(candidate, dict):
                raise ValueError("Invalid candidate")
            if (candidate.get("publishable") is not False
                    or candidate.get("exact_canonical_variant_verified") is not False
                    or candidate.get("image_publish_eligible") is not False):
                raise ValueError("API candidate improperly promoted to a public offer")
        decisions.append({
            "model_key": key,
            "status": entry.get("status", "UNKNOWN"),
            "candidate_count": len(candidates),
            "next_action": (
                "REVIEW_EXACT_SKU_MANUALLY" if candidates else
                "VERIFY_OFFICIAL_MODEL_AND_RETAILER_SEARCH"
            ),
        })
    if len(seen) != 6:
        # Error-stop reports legitimately contain NOT_REQUESTED_AFTER_ERROR rows.
        raise ValueError("Missing records for: " + ", ".join(sorted(set(REMAINING_SIX) - seen)))
    return {
        "mode": "PRIVATE_API_REVIEW_NO_PUBLIC_PROMOTION",
        "models_in_scope": 6,
        "api_calls_attempted": report["calls_attempted"],
        "statuses": dict(Counter(item["status"] for item in decisions)),
        "candidate_count": sum(item["candidate_count"] for item in decisions),
        "canonical_models_imported": 0,
        "public_prices_published": 0,
        "verified_retailer_links_published": 0,
        "stopped_reason": report.get("stopped_reason"),
        "decisions": decisions,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_report", type=Path)
    args = parser.parse_args()
    path = args.private_report.resolve()
    root = Path(__file__).resolve().parents[1]
    if not path.is_relative_to((root / "private_observations").resolve()):
        parser.error("Input must be under private_observations/")
    result = review(json.loads(path.read_text(encoding="utf-8")))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
