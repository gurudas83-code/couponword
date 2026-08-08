#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import requests
from google import genai
from google.genai import types

MODEL = "gemini-3.6-flash"
DB = Path("data/official_specs.json")
OUT_DIR = Path("data/vision_results")


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def result_provenance_matches(
    payload: dict,
    evidence_id: str,
    image_url: str,
    official_page: str,
) -> bool:
    if not isinstance(payload, dict):
        return False

    results = payload.get("results", [])
    if not isinstance(results, list) or not results:
        return False

    result = results[0]
    if not isinstance(result, dict):
        return False

    return (
        str(result.get("evidence_id") or "") == evidence_id
        and str(result.get("source_image") or "") == image_url
        and str(result.get("official_page") or "") == official_page
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run provenance-safe Gemini vision extraction"
    )
    parser.add_argument(
        "--product-id",
        required=True,
        help="Product ID from data/official_specs.json",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even when matching provenance already exists",
    )
    args = parser.parse_args()

    data = load_json(DB, {})
    products = data.get("products", [])

    product = next(
        (
            x for x in products
            if str(x.get("product_id")) == str(args.product_id)
        ),
        None,
    )

    if not isinstance(product, dict):
        print("ERROR: product not found:", args.product_id)
        return 1

    queue = (
        product.get("media_evidence", {})
        .get("vision_evidence_queue", [])
    )

    if not isinstance(queue, list):
        queue = []

    official_page = str(
        product.get("official_url")
        or product.get("source_url")
        or ""
    )

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set")
        return 1

    client = genai.Client(api_key=api_key)

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("PRODUCT:", product.get("search_name"))
    print("OFFICIAL PAGE:", official_page)
    print("QUEUE:", len(queue))
    print()

    processed = 0
    skipped = 0
    stale = 0
    failed = 0

    for index, item in enumerate(queue, 1):
        evidence_id = str(item.get("evidence_id") or "")
        image_url = str(item.get("image_url") or "")

        print(f"[{index}/{len(queue)}]", evidence_id)

        if not evidence_id or not image_url:
            print("SKIP: missing evidence id or image url")
            skipped += 1
            continue

        out_file = OUT_DIR / (
            f"product_{args.product_id}_{evidence_id}.json"
        )

        if out_file.exists() and not args.force:
            try:
                existing = load_json(out_file, {})
            except Exception:
                existing = {}

            if result_provenance_matches(
                existing,
                evidence_id,
                image_url,
                official_page,
            ):
                print("SKIP: matching provenance already exists")
                skipped += 1
                continue

            print("STALE: provenance missing or changed; regenerating")
            stale += 1

        try:
            image_response = requests.get(
                image_url,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=40,
            )
            image_response.raise_for_status()

            image_bytes = image_response.content
            image_sha256 = hashlib.sha256(
                image_bytes
            ).hexdigest()

            prompt = f"""
Analyze this official manufacturer image.

Expected product:
{product.get("search_name")}

Return only factual product evidence visible in the image.

Rules:
- Detect the source language.
- Translate factual product claims into concise English.
- Preserve numerical values, units, and qualifiers.
- Do not infer specifications that are not visible.
- Ignore decorative marketing language unless it contains a factual feature.
- Set product_identity_supported to true only when the image itself provides
  reasonable support for the expected product.
- Confidence must be an integer from 0 to 100.

Return JSON exactly in this shape:

{{
  "provider": "gemini",
  "results": [
    {{
      "evidence_id": "{evidence_id}",
      "provider": "gemini",
      "source_language": "",
      "raw_text": "",
      "claims": [
        {{
          "claim_type": "",
          "original_text": "",
          "english_text": "",
          "value": null,
          "unit": "",
          "confidence": 0,
          "product_identity_supported": false
        }}
      ]
    }}
  ]
}}
"""

            response = client.models.generate_content(
                model=MODEL,
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type=image_response.headers.get(
                            "content-type",
                            "image/jpeg",
                        ),
                    ),
                    prompt,
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type="application/json",
                ),
            )

            payload = json.loads(response.text)

            results = payload.get("results", [])
            if not isinstance(results, list) or not results:
                raise ValueError("provider returned no results")

            result = results[0]
            if not isinstance(result, dict):
                raise ValueError("provider result is not an object")

            # Enforce trusted provenance locally instead of trusting model output.
            result["evidence_id"] = evidence_id
            result["provider"] = "gemini"
            result["source_image"] = image_url
            result["official_page"] = official_page
            result["image_sha256"] = image_sha256
            result["provenance_schema_version"] = "1.0"

            payload["provider"] = "gemini"

            out_file.write_text(
                json.dumps(
                    payload,
                    indent=2,
                    ensure_ascii=False,
                ) + "\n",
                encoding="utf-8",
            )

            claims = result.get("claims", [])
            if not isinstance(claims, list):
                claims = []

            print(
                "PASS:",
                len(claims),
                "claim(s)",
                "| SHA256:",
                image_sha256[:12],
            )
            processed += 1

        except Exception as error:
            print(
                "ERROR:",
                type(error).__name__,
                str(error)[:300],
            )
            failed += 1

        time.sleep(1.5)

    print()
    print("BATCH COMPLETE")
    print("Processed :", processed)
    print("Skipped   :", skipped)
    print("Stale     :", stale)
    print("Failed    :", failed)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
