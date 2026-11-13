#!/usr/bin/env python3
"""Read-only regression checks for research UI and evidence policy.

Run from any directory: python scripts/research_quality_gate.py
These tests intentionally do not modify data, offers, prices, or images.
"""
from pathlib import Path
import json
import re
import sys

root = Path(__file__).resolve().parents[1]
errors = []
def check(condition, message):
    if not condition:
        errors.append(message)

js_path = root / "mobile-research-preview.js"
data_path = root / "data/mobile_research_catalogue.json"
policy_path = root / "docs/EDITORIAL_EVIDENCE_POLICY.md"
check(js_path.is_file(), "Missing research UI")
check(data_path.is_file(), "Missing research catalogue")
check(policy_path.is_file(), "Missing evidence policy")
if js_path.is_file():
    js = js_path.read_text(encoding="utf-8")
    for marker in (
        "function researchConstraints(", "function researchRowsFor(",
        "function groupResearchMatches(", "function renderSelectedComparison(",
        "function verifiedRecommendationBridge(", "function searchResearch(",
        "Not confirmed", "data-research-compare-clear",
    ):
        check(marker in js, "Missing UI behavior: " + marker)
    check("source_url" in js, "Missing evidence source references")
    check("comparisonSelection.length" in js, "Missing comparison selection limits")
    check("research_budget_reference" in js, "Missing budget reference gating")
    check("no performance winner" in js.lower() or "performance winner" in js.lower(),
          "Missing performance claim disclosure")
if data_path.is_file():
    try:
        data = json.loads(data_path.read_text(encoding="utf-8"))
        check(isinstance(data, (list, dict)), "Catalogue must be JSON array/object")
        check(len(data) > 0, "Catalogue must not be empty")
        print("Catalogue top-level entries:", len(data))
    except (ValueError, UnicodeError) as exc:
        errors.append("Invalid catalogue JSON: " + str(exc))
print("\n".join("ERROR: " + e for e in errors))
print("PASS" if not errors else "FAIL")
sys.exit(bool(errors))
