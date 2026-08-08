import copy
import json
import sys
from pathlib import Path

sys.path.insert(0, "python")
import official_spec_extractor as ose

PRODUCT_ID = "11"

data = json.load(
    open("data/official_specs.json", encoding="utf-8")
)

product = next(
    x for x in data["products"]
    if str(x.get("product_id")) == PRODUCT_ID
)

test = copy.deepcopy(product)

result_files = sorted(
    Path("data/vision_results").glob(
        f"product_{PRODUCT_ID}_media_*.json"
    )
)

combined = {
    "provider": "gemini",
    "results": []
}

raw_claims = 0

for path in result_files:
    payload = json.loads(
        path.read_text(encoding="utf-8")
    )

    results = payload.get("results", [])

    combined["results"].extend(results)

    for result in results:
        raw_claims += len(
            result.get("claims", [])
        )

print("RESULT FILES:", len(result_files))
print("RAW CLAIMS:", raw_claims)

test = ose.import_vision_result_payload(
    test,
    combined
)

test = ose.validate_vision_claims(test)

m = test.get("media_evidence", {})

print()
print("IMPORT STATUS:", m.get("vision_import_status"))
print("IMPORTED RESULTS:", m.get("vision_imported_results"))
print("IMPORTED CLAIMS:", m.get("vision_imported_claims"))

print()
print("VALIDATION:", m.get("vision_validation_status"))
print("REVIEW READY:", m.get("vision_review_ready_claims"))
print("REJECTED:", m.get("vision_rejected_claims"))
print("DUPLICATES:", m.get("vision_duplicate_claims"))
print("CONFLICTS:", m.get("vision_conflicting_claims"))

print()
print("=" * 90)

for item in m.get("vision_evidence_queue", []):
    claims = item.get("claims", [])

    print(
        item.get("evidence_id"),
        "|",
        item.get("claim_status"),
        "| CLAIMS:",
        len(claims)
    )

    for claim in claims:
        print(
            "  ",
            claim.get("claim_type"),
            "|",
            claim.get("english_text"),
            "| CONF:",
            claim.get("confidence"),
            "| STATUS:",
            claim.get("evidence_status")
        )

    print()
