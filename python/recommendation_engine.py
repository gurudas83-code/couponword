#!/usr/bin/env python3

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
