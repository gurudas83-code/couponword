#!/usr/bin/env python3
"""
Coupon World Product Knowledge Builder v1.0

Creates review-ready knowledge drafts for products that do not yet
have approved product knowledge.

It never invents specifications or overwrites approved knowledge.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
PRODUCT_DB = ROOT / "coupons.json"
KNOWLEDGE_DB = ROOT / "data" / "product_knowledge.json"
REVIEW_DB = ROOT / "data" / "knowledge_review.json"
RESEARCH_RESULTS_DB = ROOT / "data" / "research_results.json"
OFFICIAL_SPECS_DB = ROOT / "data" / "official_specs.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError(f"{path.name} must use UTF-8 encoding") from error
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{path.name} contains invalid JSON: {error}"
        ) from error


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            payload,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def normalize_text(value: Any) -> str:
    return re.sub(
        r"\s+",
        " ",
        str(value or "").strip().lower(),
    )


def get_product_id(product: dict[str, Any], position: int) -> str:
    product_id = (
        product.get("id")
        or product.get("product_id")
        or product.get("sl_no")
        or product.get("asin")
        or position
    )

    return str(product_id)


def get_brand(product: dict[str, Any]) -> str:
    brand = str(product.get("brand") or "").strip()

    if brand:
        return brand

    title = str(product.get("title") or "").strip()

    known_brands = (
        "boAt",
        "Samsung",
        "Sony",
        "Apple",
        "OnePlus",
        "Realme",
        "Redmi",
        "Xiaomi",
        "JBL",
        "Noise",
        "Boult",
        "Philips",
        "Puma",
        "Adidas",
        "Nike",
        "Lenovo",
        "HP",
        "Dell",
        "Asus",
        "Acer",
    )

    title_lower = title.lower()

    for known_brand in known_brands:
        if known_brand.lower() in title_lower:
            return known_brand

    return ""


def load_products() -> list[dict[str, Any]]:
    products = load_json(PRODUCT_DB, [])

    if not isinstance(products, list):
        raise ValueError("coupons.json must contain a JSON list")

    return [
        product
        for product in products
        if isinstance(product, dict)
    ]


def load_approved_knowledge() -> list[dict[str, Any]]:
    payload = load_json(KNOWLEDGE_DB, {"products": []})

    if not isinstance(payload, dict):
        return []

    products = payload.get("products", [])

    if not isinstance(products, list):
        return []

    return [
        product
        for product in products
        if isinstance(product, dict)
    ]


def load_existing_drafts() -> list[dict[str, Any]]:
    payload = load_json(REVIEW_DB, {"products": []})

    if not isinstance(payload, dict):
        return []

    products = payload.get("products", [])

    if not isinstance(products, list):
        return []

    return [
        product
        for product in products
        if isinstance(product, dict)
    ]

def load_research_results() -> dict[str, dict[str, Any]]:
    payload = load_json(
        RESEARCH_RESULTS_DB,
        {"products": []},
    )

    if not isinstance(payload, dict):
        return {}

    products = payload.get("products", [])

    if not isinstance(products, list):
        return {}

    index: dict[str, dict[str, Any]] = {}

    for product in products:
        if not isinstance(product, dict):
            continue

        product_id = product.get("product_id")

        if product_id not in (None, ""):
            index[str(product_id)] = product

    return index


def load_official_specs() -> dict[str, dict[str, Any]]:
    """Load extracted official specifications and index them by product_id."""
    payload = load_json(
        OFFICIAL_SPECS_DB,
        {"products": []},
    )

    if not isinstance(payload, dict):
        return {}

    products = payload.get("products", [])

    if not isinstance(products, list):
        return {}

    index: dict[str, dict[str, Any]] = {}

    for product in products:
        if not isinstance(product, dict):
            continue

        product_id = product.get("product_id")

        if product_id not in (None, ""):
            index[str(product_id)] = product

    return index

def merge_research_into_draft(
    draft: dict[str, Any],
    research_result: dict[str, Any] | None,
) -> dict[str, Any]:
    if not research_result:
        return draft

    merged = draft.copy()

    research = dict(merged.get("research", {}))

    official_url = str(
        research_result.get("official_url") or ""
    ).strip()

    status = str(
        research_result.get("status") or ""
    ).strip()

    verified = research_result.get("verified") is True

    research["official_product_url"] = official_url
    research["source_checked"] = bool(official_url)
    research["resolver_status"] = status
    research["resolver_verified"] = verified
    research["match_score"] = research_result.get(
        "match_score"
    )
    research["checked_on"] = datetime.now(
        timezone.utc
    ).isoformat()

    merged["research"] = research

    if verified:
        merged["status"] = "source_verified"
    elif official_url:
        merged["status"] = "source_review_required"

    return merged


def merge_official_specs_into_draft(
    draft: dict[str, Any],
    extracted: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Merge extractor output into a review draft without auto-approving it.

    Existing human-entered fields such as features, best_for, limitations,
    and review notes are preserved. Extracted evidence is kept separately
    until a reviewer approves it.
    """
    if not extracted:
        return draft

    merged = draft.copy()
    research = dict(merged.get("research", {}))

    fetch_status = str(extracted.get("fetch_status") or "").strip()
    page_score = extracted.get("page_identity_score")
    review_payload = extracted.get("review", {})
    extractor_status = (
        str(review_payload.get("status") or "").strip()
        if isinstance(review_payload, dict)
        else ""
    )
    extractor_reason = (
        str(review_payload.get("reason") or "").strip()
        if isinstance(review_payload, dict)
        else ""
    )

    evidence_summary = extracted.get("evidence_summary", {})
    specifications = extracted.get("specifications", {})
    official_features = extracted.get("features", [])
    meta = extracted.get("meta", {})

    if not isinstance(evidence_summary, dict):
        evidence_summary = {}

    if not isinstance(specifications, dict):
        specifications = {}

    if not isinstance(official_features, list):
        official_features = []

    if not isinstance(meta, dict):
        meta = {}

    research["spec_extraction"] = {
        "fetch_status": fetch_status,
        "http_status": extracted.get("http_status"),
        "page_identity_score": page_score,
        "extractor_status": extractor_status,
        "extractor_reason": extractor_reason,
        "source_host": extracted.get("source_host"),
        "extracted_at": extracted.get("extracted_at"),
        "evidence_summary": evidence_summary,
    }

    canonical_url = str(meta.get("canonical_url") or "").strip()

    if canonical_url:
        research["canonical_product_url"] = canonical_url

    merged["research"] = research
    merged["official_specifications"] = specifications
    merged["official_features"] = official_features
    merged["official_page_meta"] = meta

    specification_confidences = [
        int(record.get("confidence") or 0)
        for record in specifications.values()
        if isinstance(record, dict)
    ]

    average_spec_confidence = (
        round(
            sum(specification_confidences)
            / len(specification_confidences)
        )
        if specification_confidences
        else 0
    )

    try:
        numeric_page_score = float(page_score or 0)
    except (TypeError, ValueError):
        numeric_page_score = 0.0

    confidence_score = round(
        (numeric_page_score * 70)
        + (average_spec_confidence * 0.30)
    )
    confidence_score = max(0, min(confidence_score, 95))

    if extractor_status == "candidate_ready":
        merged["status"] = "knowledge_review_ready"
        confidence_level = "high" if confidence_score >= 75 else "medium"
        confidence_reason = (
            "Official page identity and extracted evidence are ready "
            "for human review"
        )
    elif fetch_status == "success":
        merged["status"] = "knowledge_review_required"
        confidence_level = "medium" if confidence_score >= 50 else "low"
        confidence_reason = (
            "Official-page evidence was extracted but requires "
            "manual verification"
        )
    elif fetch_status in {"error", "rejected", "skipped"}:
        confidence_level = "low"
        confidence_reason = (
            extractor_reason
            or "Official specification extraction was not successful"
        )
    else:
        confidence_level = "unverified"
        confidence_reason = (
            "Official specification extraction has not been completed"
        )

    merged["confidence"] = {
        "score": confidence_score,
        "level": confidence_level,
        "reason": confidence_reason,
    }

    return merged


def build_approved_indexes(
    approved_products: list[dict[str, Any]],
) -> tuple[set[str], set[str]]:
    approved_ids: set[str] = set()
    approved_titles: set[str] = set()

    for product in approved_products:
        product_id = product.get("product_id")

        if product_id not in (None, ""):
            approved_ids.add(str(product_id))

        title = normalize_text(product.get("title"))

        if title:
            approved_titles.add(title)

    return approved_ids, approved_titles


def build_draft_index(
    drafts: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    index: dict[str, dict[str, Any]] = {}

    for draft in drafts:
        product_id = draft.get("product_id")

        if product_id not in (None, ""):
            index[str(product_id)] = draft

    return index


def create_draft(
    product: dict[str, Any],
    position: int,
) -> dict[str, Any]:
    product_id = get_product_id(product, position)
    title = str(product.get("title") or "").strip()
    category = str(product.get("category") or "").strip()
    brand = get_brand(product)

    return {
        "product_id": product_id,
        "asin": str(product.get("asin") or "").strip(),
        "title": title,
        "brand": brand,
        "category": category,
        "status": "draft",
        "research": {
            "official_product_url": "",
            "official_brand_url": "",
            "retailer_url": str(product.get("link") or "").strip(),
            "source_checked": False,
            "checked_on": "",
        },
        "features": [],
        "best_for": [],
        "limitations": [],
        "confidence": {
            "score": 0,
            "level": "unverified",
            "reason": "Official product information has not yet been verified",
        },
        "review": {
            "approved": False,
            "reviewed_by": "",
            "reviewed_on": "",
            "notes": "",
        },
    }


def prepare_drafts() -> int:
    products = load_products()
    approved = load_approved_knowledge()
    existing_drafts = load_existing_drafts()
    research_index = load_research_results()
    official_specs_index = load_official_specs()

    approved_ids, approved_titles = build_approved_indexes(approved)
    draft_index = build_draft_index(existing_drafts)

    created = 0
    skipped_approved = 0
    preserved_drafts = 0

    final_drafts: list[dict[str, Any]] = []

    for position, product in enumerate(products, start=1):
        if product.get("active") is False:
            continue

        product_id = get_product_id(product, position)
        title_key = normalize_text(product.get("title"))

        if (
            product_id in approved_ids
            or title_key in approved_titles
        ):
            skipped_approved += 1
            continue

        if product_id in draft_index:

            existing = draft_index[product_id]

            merged = merge_research_into_draft(
                existing,
                research_index.get(product_id),
            )

            merged = merge_official_specs_into_draft(
                merged,
                official_specs_index.get(product_id),
            )

            final_drafts.append(merged)

            preserved_drafts += 1

            continue

        draft = create_draft(product, position)

        draft = merge_research_into_draft(
            draft,
            research_index.get(product_id),
        )

        draft = merge_official_specs_into_draft(
            draft,
            official_specs_index.get(product_id),
        )

        final_drafts.append(draft)

        created += 1

    payload = {
        "schema_version": "2.0",
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "instructions": [
            "Use official manufacturer sources wherever possible.",
            "Do not add specifications based only on assumptions.",
            "Set review.approved to true only after verification.",
            "Approved drafts can later be promoted to product_knowledge.json.",
            "Official specifications remain review-only until explicitly approved.",
        ],
        "summary": {
            "products_in_database": len(products),
            "approved_knowledge": len(approved),
            "drafts_created_now": created,
            "existing_drafts_preserved": preserved_drafts,
            "approved_products_skipped": skipped_approved,
            "total_pending_drafts": len(final_drafts),
            "drafts_with_official_specs": sum(
                1
                for draft in final_drafts
                if draft.get("official_specifications")
            ),
            "knowledge_review_ready": sum(
                1
                for draft in final_drafts
                if draft.get("status") == "knowledge_review_ready"
            ),
        },
        "products": final_drafts,
    }

    save_json(REVIEW_DB, payload)

    print("\n" + "=" * 64)
    print("COUPON WORLD PRODUCT KNOWLEDGE BUILDER")
    print("=" * 64)
    print("Products in database      :", len(products))
    print("Approved knowledge        :", len(approved))
    print("New drafts created        :", created)
    print("Existing drafts preserved :", preserved_drafts)
    print("Approved products skipped :", skipped_approved)
    print("Total pending drafts      :", len(final_drafts))
    print(
        "Drafts with official specs:",
        sum(
            1
            for draft in final_drafts
            if draft.get("official_specifications")
        ),
    )
    print(
        "Knowledge review ready    :",
        sum(
            1
            for draft in final_drafts
            if draft.get("status") == "knowledge_review_ready"
        ),
    )
    print("Review file               :", REVIEW_DB)
    print("=" * 64)

    return 0


def show_status() -> int:
    products = load_products()
    approved = load_approved_knowledge()
    drafts = load_existing_drafts()

    approved_drafts = sum(
        1
        for draft in drafts
        if draft.get("review", {}).get("approved") is True
    )

    print("\n" + "=" * 64)
    print("PRODUCT KNOWLEDGE STATUS")
    print("=" * 64)
    print("Products               :", len(products))
    print("Published knowledge     :", len(approved))
    print("Drafts awaiting review  :", len(drafts))
    print("Drafts marked approved  :", approved_drafts)
    print("=" * 64)

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build Product Knowledge review drafts"
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=("prepare", "status"),
        default="prepare",
        help="prepare drafts or show current status",
    )

    args = parser.parse_args()

    try:
        if args.command == "status":
            return show_status()

        return prepare_drafts()

    except (OSError, ValueError) as error:
        print(f"ERROR: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())