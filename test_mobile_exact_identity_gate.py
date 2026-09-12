import sys

sys.path.insert(0, "python")

from mobile_exact_identity_gate import classify_mobile_identity_reuse


CASES = [
    {
        "name": "apple_17e_256_missing_ram",
        "expected_text": "Apple iPhone 17e 8GB RAM 256GB Storage",
        "expected_brand": "Apple",
        "candidate_title": "Apple iPhone 17e 256 GB (Black) – 15.40 cm (6.1″) Super Retina XDR Display, A19 Chip, All-Day Battery Life, 48MP Fusion Camera, 256GB Starting Storage",
        "candidate_url": "https://www.amazon.in/dp/B0GQVL6STN",
        "want": "NEEDS_EVIDENCE",
    },
    {
        "name": "apple_17e_512_missing_ram",
        "expected_text": "Apple iPhone 17e 8GB RAM 512GB Storage",
        "expected_brand": "Apple",
        "candidate_title": "Apple iPhone 17e 512GB",
        "candidate_url": "https://www.amazon.in/dp/B0GQVHNX7R",
        "want": "NEEDS_EVIDENCE",
    },
    {
        "name": "nothing_3a_vs_3a_lite",
        "expected_text": "Nothing Phone 3a 8GB RAM 128GB Storage",
        "expected_brand": "Nothing",
        "candidate_title": "Nothing Phone (3a) Lite (White, 128 GB, 8 GB RAM)",
        "candidate_url": "https://www.amazon.in/dp/B0G47YZJH6",
        "want": "HARD_REJECT",
    },
    {
        "name": "redmi_note_15_vs_explicit_5g",
        "expected_text": "Redmi Note 15 8GB RAM 128GB Storage",
        "expected_brand": "Redmi",
        "candidate_title": "REDMI Note 15 5G (Glacier Blue, 8GB RAM, 128GB Storage)",
        "candidate_url": "https://www.amazon.in/dp/B0G5G7LCJQ",
        "want": "NEEDS_EVIDENCE",
    },
    {
        "name": "nothing_phone_3_exact_12_256",
        "expected_text": "Nothing Phone 3 12GB RAM 256GB Storage",
        "expected_brand": "Nothing",
        "candidate_title": "Nothing Phone (3) (Black, 12GB RAM, 256GB Storage)",
        "candidate_url": "https://www.amazon.in/dp/B0F7R6V1LM",
        "want": "AUTO_REUSE",
    },
    {
        "name": "ram_conflict",
        "expected_text": "Nothing Phone 3 12GB RAM 256GB Storage",
        "expected_brand": "Nothing",
        "candidate_title": "Nothing Phone (3) (Black, 8GB RAM, 256GB Storage)",
        "candidate_url": "",
        "want": "HARD_REJECT",
    },
    {
        "name": "storage_conflict",
        "expected_text": "Nothing Phone 3 12GB RAM 256GB Storage",
        "expected_brand": "Nothing",
        "candidate_title": "Nothing Phone (3) (Black, 12GB RAM, 512GB Storage)",
        "candidate_url": "",
        "want": "HARD_REJECT",
    },
]


failed = []

for case in CASES:
    result = classify_mobile_identity_reuse(
        expected_text=case["expected_text"],
        candidate_title=case["candidate_title"],
        candidate_url=case["candidate_url"],
        expected_brand=case["expected_brand"],
    )

    status = result["status"]
    print(case["name"], "=>", status, "|", result["reason"])

    if status != case["want"]:
        failed.append(
            f'{case["name"]}: expected {case["want"]}, got {status}'
        )


if failed:
    print()
    print("FAIL")
    for item in failed:
        print("-", item)
    raise SystemExit(1)


print()
print("PASS:", len(CASES), "mobile exact-identity gate cases")
