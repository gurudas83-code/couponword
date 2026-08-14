#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
PYTHON_DIR = ROOT / "python"

if str(PYTHON_DIR) not in sys.path:
    sys.path.insert(0, str(PYTHON_DIR))

from official_spec_extractor import (
    build_vision_provider_config,
    vision_provider_analyze,
)

COUPONS_DB = ROOT / "coupons.json"
OFFICIAL_SPECS_DB = ROOT / "data" / "official_specs.json"
CACHE_DB = ROOT / "data" / "hero_image_cache.json"


def clean(value: Any) -> str:
    return str(value or "").strip()


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default

    return json.loads(
        path.read_text(encoding="utf-8-sig")
    )


def save_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        json.dumps(
            data,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def product_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("products", "coupons", "items"):
            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def official_spec_list(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        for key in ("products", "items", "results"):
            value = data.get(key)

            if isinstance(value, list):
                return value

    return []


def product_id(product: dict[str, Any]) -> str:
    return clean(
        product.get("id")
        or product.get("sl_no")
        or product.get("product_id")
        or product.get("asin")
    )


def is_old_amazon_widget(image: str) -> bool:
    text = clean(image).lower()

    return (
        "amazon-adsystem.com/widgets/" in text
        or "asinimage" in text
    )


def ranked_candidates(
    spec: dict[str, Any],
    top_k: int,
) -> list[dict[str, Any]]:

    media = spec.get("media_evidence", {})

    if not isinstance(media, dict):
        return []

    ranked = media.get("ranked_images", [])

    if not isinstance(ranked, list):
        return []

    candidates = [
        item
        for item in ranked
        if isinstance(item, dict)
        and clean(item.get("url"))
    ]

    official_url = clean(spec.get("official_url")).rstrip("/").lower()

    def shortlist_priority(item: dict[str, Any]) -> tuple:
        href = clean(item.get("href")).rstrip("/").lower()
        exact_href_match = bool(official_url and href == official_url)

        path_text = clean(item.get("path")).lower()

        if "html.meta.og:image:secure_url" in path_text:
            source_priority = 4
        elif "html.meta.og:image" in path_text:
            source_priority = 3
        elif "html.meta.twitter:image" in path_text:
            source_priority = 2
        else:
            source_priority = 1

        return (
            1 if exact_href_match else 0,
            source_priority,
            int(item.get("hero_score") or 0),
            int(item.get("rank_score") or 0),
            -float(item.get("square_distance") or 99),
        )

    candidates.sort(
        key=shortlist_priority,
        reverse=True,
    )

    return candidates[:top_k]

def classify_candidate(
    *,
    title: str,
    candidate: dict[str, Any],
    cache: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:

    url = clean(candidate.get("url"))

    cached = cache.get(url)

    if isinstance(cached, dict):
        classification = cached.get("hero_classification")

        if isinstance(classification, dict):
            return {
                "status": "cached",
                "hero_classification": classification,
            }

    result = vision_provider_analyze(
        {
            "product_name": title,
            "image_url": url,
        },
        config,
    )

    if result.get("status") == "success":
        cache[url] = {
            "hero_classification": result.get(
                "hero_classification",
                {},
            ),
        }

    return result


def resolve_product_image(
    *,
    product: dict[str, Any],
    spec: dict[str, Any],
    cache: dict[str, Any],
    config: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:

    title = clean(
        product.get("title")
        or spec.get("search_name")
        or spec.get("title")
    )

    candidates = ranked_candidates(
        spec,
        top_k=top_k,
    )

    checked: list[dict[str, Any]] = []

    for candidate in candidates:

        url = clean(candidate.get("url"))

        result = classify_candidate(
            title=title,
            candidate=candidate,
            cache=cache,
            config=config,
        )

        classification = result.get(
            "hero_classification",
            {},
        )

        # Do not burn additional AI calls when the provider quota
        # is exhausted. Preserve the first failure for diagnostics.
        provider_error = clean(result.get("error")).lower()

        if (
            result.get("status") == "provider_error"
            and (
                "429" in provider_error
                or "resource_exhausted" in provider_error
                or "quota exceeded" in provider_error
            )
        ):
            checked.append(
                {
                    "url": url,
                    "hero_score": candidate.get("hero_score"),
                    "rank_score": candidate.get("rank_score"),
                    "status": result.get("status"),
                    "error": result.get("error"),
                    "classification": classification,
                }
            )

            return {
                "status": "provider_quota_exhausted",
                "image": None,
                "checked": checked,
            }

        checked.append(
            {
                "url": url,
                "hero_score": candidate.get("hero_score"),
                "rank_score": candidate.get("rank_score"),
                "status": result.get("status"),
                "classification": classification,
            }
        )

        if (
            isinstance(classification, dict)
            and classification.get("hero_eligible") is True
        ):
            return {
                "status": "verified",
                "image": url,
                "candidate": candidate,
                "classification": classification,
                "checked": checked,
            }

    return {
        "status": "no_safe_hero",
        "image": None,
        "checked": checked,
    }


def main() -> int:

    parser = argparse.ArgumentParser(
        description=(
            "Coupon World verified official hero-image resolver"
        )
    )

    parser.add_argument(
        "--write",
        action="store_true",
        help="Write verified images into coupons.json",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of products to inspect",
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Maximum image candidates sent through hero gate",
    )

    parser.add_argument(
        "--product-id",
        action="append",
        default=[],
        help="Process only selected product ID; may repeat",
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Recheck products already carrying verified provenance",
    )

    args = parser.parse_args()

    coupons_data = load_json(
        COUPONS_DB,
        [],
    )

    specs_data = load_json(
        OFFICIAL_SPECS_DB,
        [],
    )

    cache = load_json(
        CACHE_DB,
        {},
    )

    if not isinstance(cache, dict):
        cache = {}

    products = product_list(coupons_data)
    specs = official_spec_list(specs_data)

    spec_index = {
        clean(item.get("product_id")): item
        for item in specs
        if isinstance(item, dict)
        and clean(item.get("product_id"))
    }

    selected_ids = {
        clean(value)
        for value in args.product_id
        if clean(value)
    }

    config = build_vision_provider_config(
        "gemini"
    )

    inspected = 0
    verified = 0
    unresolved = 0
    skipped = 0
    changed = 0

    print("=" * 78)
    print("COUPON WORLD VERIFIED IMAGE ENGINE v1")
    print("=" * 78)
    print(
        "MODE:",
        "WRITE" if args.write else "DRY RUN",
    )
    print(
        "PRODUCTS:",
        len(products),
    )
    print()

    for product in products:

        pid = product_id(product)

        if not pid:
            continue

        if selected_ids and pid not in selected_ids:
            continue

        provenance = product.get(
            "image_provenance",
            {},
        )

        if (
            not args.force
            and isinstance(provenance, dict)
            and provenance.get("verified") is True
            and clean(product.get("image"))
        ):
            skipped += 1
            continue

        spec = spec_index.get(pid)

        if not spec:
            skipped += 1
            continue

        if (
            args.limit is not None
            and inspected >= args.limit
        ):
            break

        inspected += 1

        print("-" * 78)
        print(
            pid,
            "|",
            clean(product.get("title"))[:100],
        )

        resolution = resolve_product_image(
            product=product,
            spec=spec,
            cache=cache,
            config=config,
            top_k=max(1, args.top_k),
        )

        if resolution.get("status") == "provider_quota_exhausted":
            unresolved += 1
            print("RESULT : PROVIDER QUOTA EXHAUSTED")
            print("ACTION : Correct candidate preserved; retry later")

            checked = resolution.get("checked", [])

            for index, attempt in enumerate(checked, 1):
                classification = attempt.get(
                    "classification",
                    {},
                )

                print(
                    f"  CANDIDATE {index}:",
                    classification.get("image_type"),
                    "| eligible=",
                    classification.get("hero_eligible"),
                    "| status=",
                    attempt.get("status"),
                )

                if attempt.get("error"):
                    print("    ERROR :", clean(attempt.get("error"))[:300])

            continue

        if resolution.get("status") != "verified":
            unresolved += 1
            print("RESULT : NO SAFE HERO")

            checked = resolution.get("checked", [])

            if not checked:
                print("REASON : No ranked image candidates available")

            for index, attempt in enumerate(checked, 1):
                classification = attempt.get(
                    "classification",
                    {},
                )

                print(
                    f"  CANDIDATE {index}:",
                    classification.get("image_type"),
                    "| eligible=",
                    classification.get("hero_eligible"),
                    "| prominence=",
                    classification.get("product_prominence"),
                    "| confidence=",
                    classification.get("hero_confidence"),
                )

                print(
                    "    ",
                    classification.get("reason")
                    or "No classifier reason",
                )

            continue

        verified += 1

        image = clean(
            resolution.get("image")
        )

        candidate = resolution.get(
            "candidate",
            {},
        )

        classification = resolution.get(
            "classification",
            {},
        )

        old_image = clean(
            product.get("image")
        )

        print("RESULT :", "VERIFIED HERO")
        print("IMAGE  :", image)
        print(
            "AI TYPE:",
            classification.get("image_type"),
        )
        print(
            "CONF   :",
            classification.get("hero_confidence"),
        )

        if (
            old_image == image
            and not is_old_amazon_widget(old_image)
        ):
            continue

        if args.write:

            product["image"] = image

            product["image_provenance"] = {
                "source_type": "official_product_page",
                "source_page": clean(
                    spec.get("official_url")
                ),
                "verified": True,
                "selection_method": (
                    "hero_score_plus_ai_gate_v1"
                ),
                "hero_score": candidate.get(
                    "hero_score"
                ),
                "rank_score": candidate.get(
                    "rank_score"
                ),
                "width": candidate.get("width"),
                "height": candidate.get("height"),
                "ai_image_type": classification.get(
                    "image_type"
                ),
                "ai_product_prominence": (
                    classification.get(
                        "product_prominence"
                    )
                ),
                "ai_confidence": classification.get(
                    "hero_confidence"
                ),
            }

            changed += 1

    # Classification cache is useful even during dry-run,
    # so the same images do not consume AI calls repeatedly.
    save_json(
        CACHE_DB,
        cache,
    )

    if args.write and changed:
        save_json(
            COUPONS_DB,
            coupons_data,
        )

    print()
    print("=" * 78)
    print("SUMMARY")
    print("=" * 78)
    print("INSPECTED :", inspected)
    print("VERIFIED  :", verified)
    print("UNRESOLVED:", unresolved)
    print("SKIPPED   :", skipped)
    print("CHANGED   :", changed)
    print(
        "DATABASE  :",
        "UPDATED" if args.write and changed else "UNCHANGED",
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
