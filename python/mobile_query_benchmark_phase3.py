from pathlib import Path
import json
import sys

sys.path.insert(0, "python")

from intent_engine import parse_query

source = Path("data/mobile_query_benchmark_phase3.json")
queries = json.loads(source.read_text(encoding="utf-8"))

results = []

print("=" * 110)
print("COUPON WORLD - MOBILE QUERY BENCHMARK / PHASE 3")
print("=" * 110)

for item in queries:
    q = item["q"]
    intent = parse_query(q)

    result = {
        "id": item["id"],
        "query": q,
        "category": intent.get("category"),
        "budget_min": intent.get("budget_min"),
        "budget_max": intent.get("budget_max"),
        "hard_constraints": intent.get("hard_constraints"),
        "must_have": intent.get("must_have"),
        "preferred": intent.get("preferred"),
        "avoid": intent.get("avoid"),
        "brands": intent.get("brands"),
        "user_profile": intent.get("user_profile"),
        "use_case": intent.get("use_case"),
        "priority_weights": intent.get("priority_weights"),
    }

    results.append(result)

    print()
    print("-" * 110)
    print(item["id"], "|", q)
    print("CATEGORY :", result["category"])
    print("BUDGET   :", result["budget_min"], "-", result["budget_max"])
    print("HARD     :", result["hard_constraints"])
    print("MUST     :", result["must_have"])
    print("PREFERRED:", result["preferred"])
    print("AVOID    :", result["avoid"])
    print("BRANDS   :", result["brands"])
    print("PROFILE  :", result["user_profile"])
    print("USE CASE :", result["use_case"])

report = Path("data/mobile_query_benchmark_phase3_report.json")
report.write_text(
    json.dumps(results, indent=2, ensure_ascii=False),
    encoding="utf-8"
)

print()
print("=" * 110)
print("TOTAL :", len(results))
print("REPORT:", report.resolve())
