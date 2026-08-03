#!/usr/bin/env python3
from __future__ import annotations

from datetime import datetime
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
PYTHON_DIR = ROOT / 'python'
RECOMMENDATION = PYTHON_DIR / 'recommendation_engine.py'
SHOPPING_BRAIN = PYTHON_DIR / 'shopping_brain.py'


def backup(path: Path) -> Path:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    destination = path.with_name(f'{path.stem}_before_match_v1_{stamp}{path.suffix}')
    shutil.copy2(path, destination)
    return destination


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f'{label}: expected 1 match, found {count}')
    return text.replace(old, new, 1)


def write_recommendation_engine() -> None:
    backup_path = backup(RECOMMENDATION)
    content = """#!/usr/bin/env python3

from __future__ import annotations

from typing import Any


def _clean(value: Any) -> str:
    return str(value or '').strip()


def _has_list_values(value: Any) -> bool:
    return isinstance(value, list) and any(_clean(item) for item in value)


def explain_product(product: dict, intent: dict) -> list[str]:
    reasons: list[str] = []

    title = _clean(product.get('title')).lower()
    category = _clean(product.get('category')).lower()
    brand = _clean(product.get('brand')).lower()
    price = product.get('price')
    taxonomy = product.get('taxonomy', {})

    if not isinstance(taxonomy, dict):
        taxonomy = {}

    query_category = _clean(intent.get('category')).lower()
    if query_category and (
        query_category in category
        or query_category in title
        or query_category in _clean(taxonomy.get('shopping_category')).lower()
    ):
        reasons.append('Category matched')

    for query_brand in intent.get('brands', []):
        normalized_brand = _clean(query_brand).lower()
        if normalized_brand and (
            normalized_brand in brand or normalized_brand in title
        ):
            reasons.append(f'Brand matched: {query_brand}')

    taxonomy_features = {
        _clean(item).lower()
        for item in taxonomy.get('features', [])
        if _clean(item)
    }

    for feature in intent.get('features', []):
        normalized_feature = _clean(feature).lower()
        if normalized_feature and (
            normalized_feature in title or normalized_feature in taxonomy_features
        ):
            reasons.append(f'Feature matched: {feature}')

    budget = intent.get('budget_max')
    if budget is not None:
        if price in (None, ''):
            reasons.append('Current price is not verified')
        else:
            try:
                if float(price) <= float(budget):
                    reasons.append('Within stated budget')
                else:
                    reasons.append('Above stated budget')
            except (TypeError, ValueError):
                reasons.append('Current price could not be validated')

    return reasons


def calculate_data_confidence(product: dict) -> int:
    taxonomy = product.get('taxonomy', {})
    knowledge = product.get('product_knowledge', {})

    if not isinstance(taxonomy, dict):
        taxonomy = {}
    if not isinstance(knowledge, dict):
        knowledge = {}

    checks = [
        (bool(_clean(product.get('title'))), 10),
        (bool(_clean(product.get('brand'))), 10),
        (bool(_clean(product.get('link'))), 10),
        (bool(_clean(product.get('asin'))), 10),
        (bool(_clean(product.get('image'))), 10),
        (product.get('price') not in (None, ''), 15),
        (bool(_clean(taxonomy.get('product_type'))), 10),
        (bool(taxonomy.get('confidence')), 5),
        (_has_list_values(knowledge.get('features')), 10),
        (
            _has_list_values(knowledge.get('best_for'))
            or _has_list_values(knowledge.get('limitations')),
            10,
        ),
    ]

    return min(100, sum(weight for passed, weight in checks if passed))


def build_requirement_assessment(product: dict) -> dict:
    try:
        raw_score = int(round(float(product.get('score', 0))))
    except (TypeError, ValueError):
        raw_score = 0

    requirement_match = max(0, min(100, raw_score))
    data_confidence = calculate_data_confidence(product)

    if requirement_match >= 85 and data_confidence >= 70:
        confidence_label = 'high'
    elif requirement_match >= 65 and data_confidence >= 40:
        confidence_label = 'medium'
    else:
        confidence_label = 'low'

    matched = [
        reason
        for reason in product.get('reasons', [])
        if reason
        and 'not verified' not in reason.lower()
        and 'unavailable' not in reason.lower()
        and 'could not' not in reason.lower()
        and 'no matching reason' not in reason.lower()
    ]

    unverified: list[str] = []
    if product.get('price') in (None, ''):
        unverified.append('Current price')
    if not _clean(product.get('image')):
        unverified.append('Product image')

    knowledge = product.get('product_knowledge', {})
    if not isinstance(knowledge, dict):
        knowledge = {}
    if not _has_list_values(knowledge.get('features')):
        unverified.append('Detailed verified product knowledge')
    if not _clean(product.get('asin')):
        unverified.append('Marketplace product identity')

    return {
        'requirement_match_percent': requirement_match,
        'data_confidence_percent': data_confidence,
        'recommendation_confidence': confidence_label,
        'matched_requirements': matched,
        'unverified_requirements': unverified,
    }
"""
    RECOMMENDATION.write_text(content, encoding='utf-8', newline='\n')
    print(f'Updated: {RECOMMENDATION}')
    print(f'Backup : {backup_path}')


def patch_shopping_brain() -> None:
    backup_path = backup(SHOPPING_BRAIN)
    text = SHOPPING_BRAIN.read_text(encoding='utf-8-sig')

    text = replace_once(
        text,
        'from recommendation_engine import explain_product',
        'from recommendation_engine import build_requirement_assessment, explain_product',
        'recommendation import',
    )

    text = replace_once(
        text,
        '''        ranked_product["price_info"] = analyze_price(\n            ranked_product,\n            intent,\n        )\n\n        matches.append(ranked_product)\n''',
        '''        ranked_product["price_info"] = analyze_price(\n            ranked_product,\n            intent,\n        )\n\n        ranked_product["requirement_assessment"] = (\n            build_requirement_assessment(ranked_product)\n        )\n\n        matches.append(ranked_product)\n''',
        'assessment insertion',
    )

    text = replace_once(
        text,
        '''        response["matches"].append(\n            {\n                "id": product.get("id"),\n''',
        '''        assessment = product.get(\n            "requirement_assessment",\n            {},\n        )\n\n        response["matches"].append(\n            {\n                "id": product.get("id"),\n''',
        'response assessment local',
    )

    text = replace_once(
        text,
        '''                "score": product.get("score"),\n                "reasons": product.get("reasons", []),\n''',
        '''                "score": product.get("score"),\n                "requirement_match_percent": assessment.get(\n                    "requirement_match_percent",\n                    0,\n                ),\n                "data_confidence_percent": assessment.get(\n                    "data_confidence_percent",\n                    0,\n                ),\n                "recommendation_confidence": assessment.get(\n                    "recommendation_confidence",\n                    "low",\n                ),\n                "ai_top_suggestion": len(response["matches"]) == 0,\n                "matched_requirements": assessment.get(\n                    "matched_requirements",\n                    [],\n                ),\n                "unverified_requirements": assessment.get(\n                    "unverified_requirements",\n                    [],\n                ),\n                "reasons": product.get("reasons", []),\n''',
        'JSON assessment fields',
    )

    text = replace_once(
        text,
        '''        print("Score      :", product.get("score"))\n        print(\n            "Product type:",\n''',
        '''        assessment = product.get(\n            "requirement_assessment",\n            {},\n        )\n\n        if index == 1:\n            print("AI Suggestion: Top match for your current requirement")\n\n        print("Score      :", product.get("score"))\n        print(\n            "Requirement match:",\n            f"{assessment.get('requirement_match_percent', 0)}%",\n        )\n        print(\n            "Data confidence  :",\n            f"{assessment.get('data_confidence_percent', 0)}%",\n        )\n        print(\n            "AI confidence    :",\n            str(assessment.get("recommendation_confidence", "low")).title(),\n        )\n        print(\n            "Product type:",\n''',
        'terminal assessment output',
    )

    SHOPPING_BRAIN.write_text(text, encoding='utf-8', newline='\n')
    print(f'Updated: {SHOPPING_BRAIN}')
    print(f'Backup : {backup_path}')


def main() -> int:
    for required in (RECOMMENDATION, SHOPPING_BRAIN):
        if not required.exists():
            print(f'ERROR: Missing {required}')
            return 1

    try:
        write_recommendation_engine()
        patch_shopping_brain()
    except Exception as exc:
        print(f'ERROR: {exc}')
        return 1

    print('PASS: Requirement Match v1 applied')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
