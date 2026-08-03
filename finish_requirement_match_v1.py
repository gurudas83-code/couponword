#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "python" / "shopping_brain.py"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly 1 match, found {count}")
    return text.replace(old, new, 1)


def main() -> int:
    if not TARGET.exists():
        print(f"ERROR: Missing {TARGET}")
        return 1

    text = TARGET.read_text(encoding="utf-8-sig")
    original = text

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = TARGET.with_name(
        f"shopping_brain_before_requirement_match_finish_{stamp}.py"
    )
    shutil.copy2(TARGET, backup)

    if "build_requirement_assessment" not in text:
        old = "from recommendation_engine import explain_product"
        new = (
            "from recommendation_engine import "
            "build_requirement_assessment, explain_product"
        )
        text = replace_once(text, old, new, "recommendation import")

    if 'ranked_product["requirement_assessment"]' not in text:
        old = '''        ranked_product["price_info"] = analyze_price(
            ranked_product,
            intent,
        )

        matches.append(ranked_product)
'''
        new = '''        ranked_product["price_info"] = analyze_price(
            ranked_product,
            intent,
        )

        ranked_product["requirement_assessment"] = (
            build_requirement_assessment(ranked_product)
        )

        matches.append(ranked_product)
'''
        text = replace_once(text, old, new, "assessment calculation")

    if '"requirement_match_percent"' not in text:
        old = '''        response["matches"].append(
            {
                "id": product.get("id"),
'''
        new = '''        assessment = product.get(
            "requirement_assessment",
            {},
        )

        response["matches"].append(
            {
                "id": product.get("id"),
'''
        text = replace_once(text, old, new, "response assessment local")

        old = '''                "score": product.get("score"),
                "reasons": product.get("reasons", []),
'''
        new = '''                "score": product.get("score"),
                "requirement_match_percent": assessment.get(
                    "requirement_match_percent",
                    0,
                ),
                "data_confidence_percent": assessment.get(
                    "data_confidence_percent",
                    0,
                ),
                "recommendation_confidence": assessment.get(
                    "recommendation_confidence",
                    "low",
                ),
                "ai_top_suggestion": len(response["matches"]) == 0,
                "matched_requirements": assessment.get(
                    "matched_requirements",
                    [],
                ),
                "unverified_requirements": assessment.get(
                    "unverified_requirements",
                    [],
                ),
                "reasons": product.get("reasons", []),
'''
        text = replace_once(text, old, new, "JSON assessment fields")

    if 'print("Requirement match:"' not in text:
        old = '''        print("Score      :", product.get("score", 0))

        taxonomy = product.get("taxonomy", {})
'''
        new = '''        assessment = product.get(
            "requirement_assessment",
            {},
        )

        if position == 1:
            print("AI Suggestion: Top match for your current requirement")

        print("Score      :", product.get("score", 0))
        print(
            "Requirement match:",
            f"{assessment.get('requirement_match_percent', 0)}%",
        )
        print(
            "Data confidence  :",
            f"{assessment.get('data_confidence_percent', 0)}%",
        )
        print(
            "AI confidence    :",
            str(
                assessment.get(
                    "recommendation_confidence",
                    "low",
                )
            ).title(),
        )

        taxonomy = product.get("taxonomy", {})
'''
        text = replace_once(text, old, new, "terminal assessment fields")

    if text == original:
        print("PASS: shopping_brain.py already contains Requirement Match v1")
        print(f"Backup: {backup}")
        return 0

    TARGET.write_text(text, encoding="utf-8", newline="\n")

    print("PASS: Requirement Match v1 integration completed")
    print(f"Backup: {backup}")
    print(f"Updated: {TARGET}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
