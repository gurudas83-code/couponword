#!/usr/bin/env python3
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

from google import genai
from google.genai import types

sys.path.insert(0, "python")
import official_spec_extractor as ose

PRODUCT_ID = "11"
MODEL = "gemini-3.6-flash"

ALLOWED_CATEGORIES = [
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
]

with open("data/official_specs.json", encoding="utf-8") as f:
    data = json.load(f)

product = next(
    x for x in data["products"]
    if str(x.get("product_id")) == PRODUCT_ID
)

test = copy.deepcopy(product)

combined = {
    "provider": "gemini",
    "results": [],
}

for path in sorted(
    Path("data/vision_results").glob(
        f"product_{PRODUCT_ID}_media_*.json"
    )
):
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )
    combined["results"].extend(
        payload.get("results", [])
    )

test = ose.import_vision_result_payload(
    test,
    combined,
)
test = ose.validate_vision_claims(test)

claims = []
media = test.get("media_evidence", {})

for item in media.get("vision_evidence_queue", []):
    evidence_id = str(item.get("evidence_id") or "")

    for claim in item.get("claims", []):
        if claim.get("evidence_status") != "review_ready":
            continue

        claims.append({
            "claim_id": claim.get("claim_id"),
            "evidence_id": evidence_id,
            "claim_type": claim.get("claim_type"),
            "english_text": claim.get("english_text"),
            "value": claim.get("value"),
            "unit": claim.get("unit"),
            "confidence": claim.get("confidence"),
            "source_language": claim.get("source_language"),
        })

taxonomy_text = ", ".join(ALLOWED_CATEGORIES)

prompt = f"""
You are a UNIVERSAL product-fact semantic consolidator.

Input: validated factual claims for one product from official evidence.

Your output must work across many product categories and must NOT contain
product-specific hard-coded rules.

ALLOWED FACT CATEGORIES:
{taxonomy_text}

STRICT SEMANTIC RULES:

1. Group claims only when they represent the same underlying fact.
2. Preserve all meaningful qualifiers and operators:
   <, <=, >, >=, up to, over, more than, approximately, test conditions,
   modes, per-unit scope, standalone scope, total scope, with-case scope.
3. Never convert a bounded or qualified measurement into an exact value.
4. Preserve compound facts in structured_value.
5. Preserve additive values as arrays.
6. Compatible relational facts are not conflicts.
7. Genuine contradictions must be marked conflict_status="conflict".
8. Do not invent missing facts.
9. Keep all evidence_ids and source_claim_ids.
10. Canonical keys must be generic, machine-friendly and brand/model independent.
11. Separate codecs, certifications, technologies, interfaces and features.
12. Source images remain evidence only.

MANDATORY TAXONOMY RULES:

- Product/model/name identity facts -> fact_category = "identity".
- Physical operating/transmission range facts measured in mm/cm/m/km -> "distance".
- Physical object/component sizes, lengths, widths, heights, diameters or thicknesses -> "dimension".
- Material composition, purity or material-property percentages -> "material_property".
- Playback/charging/runtime measured in time -> "duration".
- Signal/input/output delay measured in ms -> "latency".
- Battery/storage capacities -> "capacity".
- Counts of devices/microphones/languages/items -> "count".
- Bluetooth/software/protocol revision numbers -> "version".
- SBC/AAC/LHDC/etc. -> "codec".
- Hi-Res or other certification labels -> "certification".
- IP ratings and similar protection grades -> "rating".
- Colors/finishes/options -> "variant".
- Connector/port standards -> "interface".
- Algorithms, driver systems and named technical mechanisms -> "technology".
- Boolean capability/integration/support -> "feature".

UNIT-CATEGORY CONSISTENCY:
- m, cm, mm, km describing operating/transmission range -> distance.
- mm/cm describing component size/diameter/thickness -> dimension.
- ms used for latency -> latency.
- hours/minutes/seconds for playback/charging/runtime -> duration.
- mAh/Wh/kWh -> capacity.
- percentage describing material purity/composition -> material_property.

SOURCE OPERATOR FIDELITY:
- Preserve the semantic operator actually stated by the source.
- "up to 55 dB" -> operator "up to"; DO NOT rewrite it as "<=".
- "up to 58 hours" -> operator "up to"; DO NOT rewrite it as "<=".
- "<=10m" -> operator "<="; DO NOT rewrite it as "up to".
- "over 30 languages" -> preserve "over" or ">" consistently with the source meaning.
- Never infer an operator from the numeric value alone.
- If consolidated evidence uses different wording but equivalent meaning, prefer the
  most explicit operator from the strongest direct evidence and retain source qualifiers.

Before returning JSON, internally check every fact against taxonomy,
unit-category consistency, source-operator fidelity and evidence provenance,
and correct any mismatch.

Return JSON only:

{{
  "schema_version": "1.3",
  "product_name": "",
  "input_claim_count": 0,
  "canonical_fact_count": 0,
  "facts": [
    {{
      "canonical_key": "",
      "fact_category": "",
      "normalized_summary": "",
      "value": null,
      "unit": "",
      "operator": "",
      "qualifier": "",
      "values": [],
      "structured_value": {{}},
      "confidence": 0,
      "evidence_ids": [],
      "source_claim_ids": [],
      "conflict_status": "none",
      "requires_review": false
    }}
  ]
}}
"""

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY")
)

input_payload = json.dumps(
    {
        "product_name": product.get("search_name"),
        "claims": claims,
    },
    ensure_ascii=False,
)

response = client.models.generate_content(
    model=MODEL,
    contents=[
        prompt,
        "\nINPUT CLAIMS:\n",
        input_payload,
    ],
    config=types.GenerateContentConfig(
        temperature=0.1,
        response_mime_type="application/json",
    ),
)

result = json.loads(response.text)

out = Path(
    f"data/semantic_results/product_{PRODUCT_ID}_semantic_v1_3.json"
)
out.parent.mkdir(parents=True, exist_ok=True)

out.write_text(
    json.dumps(
        result,
        indent=2,
        ensure_ascii=False,
    ) + "\n",
    encoding="utf-8",
)

print("INPUT CLAIMS:", len(claims))
print("CANONICAL FACTS:", result.get("canonical_fact_count"))
print("SCHEMA:", result.get("schema_version"))
print("SAVED:", out)
print()

for i, fact in enumerate(result.get("facts", []), 1):
    print(
        i,
        "|", fact.get("canonical_key"),
        "| CAT:", fact.get("fact_category"),
        "| VALUE:", fact.get("value"),
        fact.get("unit"),
        "| OP:", fact.get("operator"),
        "| QUAL:", fact.get("qualifier"),
        "| VALUES:", fact.get("values"),
        "| STRUCTURED:", fact.get("structured_value"),
        "| EVIDENCE:", fact.get("evidence_ids"),
        "| REVIEW:", fact.get("requires_review"),
    )

print()
print("UNIVERSAL SEMANTIC CONSOLIDATOR v1.3 DRY RUN COMPLETE")
