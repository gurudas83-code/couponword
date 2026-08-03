#!/usr/bin/env python3

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent.parent
REVIEW_DB = ROOT / "data" / "knowledge_review.json"
KNOWLEDGE_DB = ROOT / "data" / "product_knowledge.json"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    return json.loads(path.read_text(encoding="utf-8-sig"))


def save_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def backup(path: Path) -> Path | None:
    if not path.exists():
        return None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    destination = path.with_name(
        f"{path.stem}_before_publish_{stamp}{path.suffix}"
    )

    shutil.copy2(path, destination)
    return destination


def normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def publish() -> int:
    review_payload = load_json(
        REVIEW_DB,
        {"products": []},
    )

    knowledge_payload = load_json(
        KNOWLEDGE_DB,
        {"products": []},
    )

    drafts = review_payload.get("products", [])
    published = knowledge_payload.get("products", [])

    if not isinstance(drafts, list):
        print("ERROR: knowledge_review.json products must be a list")
        return 1

    if not isinstance(published, list):
        print("ERROR: product_knowledge.json products must be a list")
        return 1

    approved = [
        draft
        for draft in drafts
        if isinstance(draft, dict)
        and draft.get("review", {}).get("approved") is True
    ]

    if not approved:
        print("No approved knowledge drafts found.")
        return 0

    knowledge_backup = backup(KNOWLEDGE_DB)
    review_backup = backup(REVIEW_DB)

    published_by_id = {
        str(item.get("product_id")): item
        for item in published
        if isinstance(item, dict)
        and item.get("product_id") not in (None, "")
    }

    published_titles = {
        normalize(item.get("title")): str(item.get("product_id"))
        for item in published
        if isinstance(item, dict)
        and normalize(item.get("title"))
    }

    promoted_ids: set[str] = set()

    for draft in approved:
        product_id = str(draft.get("product_id") or "").strip()
        title = str(draft.get("title") or "").strip()

        if not product_id or not title:
            print("SKIP: Approved draft missing product_id or title")
            continue

        record = {
            "product_id": product_id,
            "asin": str(draft.get("asin") or "").strip(),
            "title": title,
            "brand": str(draft.get("brand") or "").strip(),
            "category": str(draft.get("category") or "").strip(),
            "features": draft.get("features", []),
            "best_for": draft.get("best_for", []),
            "limitations": draft.get("limitations", []),
            "confidence": draft.get("confidence", {}),
            "official_product_url": (
                draft.get("research", {}).get(
                    "official_product_url",
                    "",
                )
            ),
            "published_on": datetime.now(
                timezone.utc
            ).isoformat(),
        }

        old_id = published_titles.get(normalize(title))

        if old_id and old_id != product_id:
            published_by_id.pop(old_id, None)

        published_by_id[product_id] = record
        promoted_ids.add(product_id)

    final_published = list(published_by_id.values())

    remaining_drafts = [
        draft
        for draft in drafts
        if str(draft.get("product_id")) not in promoted_ids
    ]

    knowledge_payload["products"] = final_published
    knowledge_payload["updated_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    review_payload["products"] = remaining_drafts

    summary = review_payload.get("summary", {})

    if isinstance(summary, dict):
        summary["total_pending_drafts"] = len(remaining_drafts)

    save_json(KNOWLEDGE_DB, knowledge_payload)
    save_json(REVIEW_DB, review_payload)

    print("=" * 64)
    print("PRODUCT KNOWLEDGE PUBLISHER")
    print("=" * 64)
    print("Approved drafts found :", len(approved))
    print("Records published     :", len(promoted_ids))
    print("Total published       :", len(final_published))
    print("Remaining drafts      :", len(remaining_drafts))
    print("Knowledge backup      :", knowledge_backup)
    print("Review backup         :", review_backup)
    print("STATUS                : PASS")

    return 0


if __name__ == "__main__":
    raise SystemExit(publish())