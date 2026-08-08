#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

PRODUCT_ID = "11"

src = Path(
    f"data/semantic_results/product_{PRODUCT_ID}_semantic_v1_3.json"
)

data = json.loads(src.read_text(encoding="utf-8"))
facts = data.get("facts", [])

ALLOWED_CATEGORIES = {
    "identity",
    "count",
    "distance",
    "duration",
    "latency",
    "capacity",
    "rating",
    "version",
    "codec",
    "certification",
    "technology",
    "feature",
    "interface",
    "variant",
    "dimension",
    "weight",
    "power",
    "performance",
    "compatibility",
    "material_property",
    "other",
}

DISTANCE_UNITS = {"mm", "cm", "m", "km"}
TIME_UNITS = {
    "ms", "s", "sec", "second", "seconds",
    "min", "minute", "minutes",
    "h", "hr", "hrs", "hour", "hours",
}
CAPACITY_UNITS = {"mah", "wh", "kwh"}
COUNT_UNITS = {"devices", "microphones", "languages"}

issues = []

for index, fact in enumerate(facts, 1):
    key = str(fact.get("canonical_key") or "").lower()
    category = str(fact.get("fact_category") or "").lower()
    value = fact.get("value")
    unit = str(fact.get("unit") or "").lower().strip()
    operator = str(fact.get("operator") or "").lower().strip()
    qualifier = str(fact.get("qualifier") or "").lower().strip()
    structured = fact.get("structured_value")
    evidence_ids = fact.get("evidence_ids")
    source_claim_ids = fact.get("source_claim_ids")
    conflict_status = str(fact.get("conflict_status") or "").lower()

    reasons = []

    if category not in ALLOWED_CATEGORIES:
        reasons.append(
            f"unsupported fact_category '{category}'"
        )

    if not key:
        reasons.append("canonical_key is empty")

    if not isinstance(evidence_ids, list) or not evidence_ids:
        reasons.append("fact has no supporting evidence_ids")

    if not isinstance(source_claim_ids, list) or not source_claim_ids:
        reasons.append("fact has no source_claim_ids")

    if structured is None:
        reasons.append("structured_value must be an object, not null")
    elif not isinstance(structured, dict):
        reasons.append("structured_value must be an object")

    if (
        key in {"product_name", "model_name"}
        or "identity" in key
    ) and category != "identity":
        reasons.append(
            f"identity fact should be category identity, not {category}"
        )

    if (
        any(token in key for token in ["range", "distance"])
        and unit in DISTANCE_UNITS
        and category != "distance"
    ):
        reasons.append(
            f"range/distance fact should be distance, not {category}"
        )

    if (
        any(token in key for token in ["diameter", "width", "height", "length", "thickness", "size"])
        and unit in {"mm", "cm", "m"}
        and category not in {"dimension", "distance"}
    ):
        reasons.append(
            f"physical size fact should be dimension/distance, not {category}"
        )

    if "driver" in key and unit in {"mm", "cm"} and category != "dimension":
        reasons.append(
            f"driver physical size should be dimension, not {category}"
        )

    if unit == "ms" and "latency" in key and category != "latency":
        reasons.append(
            f"latency measured in ms should be latency, not {category}"
        )

    if (
        unit in {"hour", "hours", "hr", "hrs"}
        and any(token in key for token in ["playback", "charging", "runtime", "duration"])
        and category != "duration"
    ):
        reasons.append(
            f"time-based runtime fact should be duration, not {category}"
        )

    if unit in CAPACITY_UNITS and category != "capacity":
        reasons.append(
            f"capacity unit {unit} should use category capacity"
        )

    if unit in COUNT_UNITS and category != "count":
        reasons.append(
            f"count unit {unit} should use category count"
        )

    if "codec" in key and category != "codec":
        reasons.append(
            f"codec fact should be codec, not {category}"
        )

    if "certification" in key and category != "certification":
        reasons.append(
            f"certification fact should be certification, not {category}"
        )

    if "purity" in key and unit == "%" and category != "material_property":
        reasons.append(
            f"purity percentage should be material_property, not {category}"
        )

    if operator not in {
        "", "<", "<=", ">", ">=", "up to",
        "over", "more than", "approximately",
    }:
        reasons.append(
            f"unsupported operator '{operator}'"
        )

    if key == "noise_cancellation_depth" and operator != "up to":
        reasons.append(
            "noise cancellation source meaning should preserve 'up to'"
        )

    if "playback" in key and value is not None and operator != "up to":
        reasons.append(
            "playback maximum claim should preserve 'up to'"
        )

    if "bluetooth" in key and "range" in key and operator != "<=":
        reasons.append(
            "Bluetooth range source explicitly used <= and should preserve it"
        )

    if conflict_status not in {"none", "conflict", ""}:
        reasons.append(
            f"unexpected conflict_status '{conflict_status}'"
        )

    if reasons:
        issues.append({
            "index": index,
            "key": fact.get("canonical_key"),
            "category": fact.get("fact_category"),
            "value": value,
            "unit": fact.get("unit"),
            "operator": fact.get("operator"),
            "reasons": reasons,
        })

print("SCHEMA VERSION:", data.get("schema_version"))
print("FACTS CHECKED:", len(facts))
print("ISSUES FOUND:", len(issues))
print()

for issue in issues:
    print("=" * 90)
    print("KEY:", issue["key"])
    print("CATEGORY:", issue["category"])
    print("VALUE:", issue["value"], issue["unit"])
    print("OPERATOR:", issue["operator"])
    for reason in issue["reasons"]:
        print("ISSUE:", reason)

print()

if issues:
    print("RESULT: FAIL")
else:
    print("RESULT: PASS")

print("UNIVERSAL SEMANTIC SCHEMA VALIDATOR v3 COMPLETE")
