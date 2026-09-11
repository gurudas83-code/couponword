import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / "data" / "mobile_search_benchmark_e2e_report.json"

API_BASE = "http://127.0.0.1:8000/api/recommend?q="


TESTS = [
    {
        "id": "E001",
        "query": "best phone under 20000",
        "expect": {
            "budget_max": 20000,
            "min_discovered": 3,
        },
    },
    {
        "id": "E002",
        "query": "8/128 phone under 20k",
        "expect": {
            "budget_max": 20000,
            "must_have": ["8gb_ram", "128gb_storage"],
            "min_discovered": 3,
        },
    },
    {
        "id": "E003",
        "query": "8/128 5G phone under 20k",
        "expect": {
            "budget_max": 20000,
            "must_have": ["8gb_ram", "128gb_storage", "5g"],
            "min_discovered": 3,
        },
    },
    {
        "id": "E004",
        "query": "Samsung phone under 25000",
        "expect": {
            "budget_max": 25000,
            "brand": "Samsung",
            "min_discovered": 3,
        },
    },
    {
        "id": "E005",
        "query": "Samsung only phone under 30000",
        "expect": {
            "budget_max": 30000,
            "brand": "Samsung",
            "min_discovered": 3,
        },
    },
    {
        "id": "E006",
        "query": "Samsung nahi chahiye phone under 20000",
        "expect": {
            "budget_max": 20000,
            "avoid_brand": "Samsung",
            "min_discovered": 3,
        },
    },
    {
        "id": "E007",
        "query": "gaming phone under 30000",
        "expect": {
            "budget_max": 30000,
            "min_discovered": 3,
        },
    },
    {
        "id": "E008",
        "query": "best camera phone under 25000",
        "expect": {
            "budget_max": 25000,
            "min_discovered": 3,
        },
    },
    {
        "id": "E009",
        "query": "phone under 20000 battery pe compromise nahi",
        "expect": {
            "budget_max": 20000,
            "min_discovered": 3,
        },
    },
    {
        "id": "E010",
        "query": "Samsung",
        "expect": {
            "brand": "Samsung",
            "min_discovered": 3,
        },
    },
]


def fetch(query):
    url = API_BASE + urllib.parse.quote(query)

    started = time.perf_counter()

    with urllib.request.urlopen(url, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))

    elapsed = time.perf_counter() - started

    return data, elapsed


def norm(value):
    return str(value or "").strip().lower()


def extract_criterion(rec, name):
    for item in rec.get("criteria", []) or []:
        if norm(item.get("criterion")) == norm(name):
            return item
    return None


def evaluate(test, data, elapsed):
    expect = test["expect"]
    failures = []
    warnings = []

    intent = data.get("intent") or {}
    stage_counts = data.get("stage_counts") or {}
    recommendations = data.get("recommendations") or []
    diagnostics = data.get("fit_diagnostics") or []

    discovered = int(stage_counts.get("discovered") or 0)
    evidence_ready = int(stage_counts.get("evidence_ready") or 0)
    fit_scored = int(stage_counts.get("fit_scored") or 0)

    if discovered < expect.get("min_discovered", 0):
        failures.append(
            f"discovered only {discovered}, expected >= "
            f"{expect.get('min_discovered')}"
        )

    if expect.get("budget_max") is not None:
        if intent.get("budget_max") != expect["budget_max"]:
            failures.append(
                f"intent budget_max={intent.get('budget_max')}, "
                f"expected={expect['budget_max']}"
            )

    expected_must = {
        norm(x)
        for x in expect.get("must_have", [])
    }
    actual_must = {
        norm(x)
        for x in intent.get("must_have", [])
    }

    missing_must = expected_must - actual_must

    if missing_must:
        failures.append(
            f"missing intent must_have={sorted(missing_must)}"
        )

    expected_brand = norm(expect.get("brand"))

    if expected_brand:
        brands = {norm(x) for x in intent.get("brands", [])}

        if expected_brand not in brands:
            failures.append(
                f"intent brand missing: {expect.get('brand')}"
            )

    avoid_brand = norm(expect.get("avoid_brand"))

    if avoid_brand:
        avoid = {norm(x) for x in intent.get("avoid", [])}

        if f"brand_{avoid_brand}" not in avoid:
            failures.append(
                f"avoid brand missing: {expect.get('avoid_brand')}"
            )

    # ------------------------------------------------------------
    # Recommendation-level checks
    # ------------------------------------------------------------
    valid_price_count = 0
    valid_image_count = 0
    budget_compliant_count = 0
    brand_compliant_count = 0

    budget_max = intent.get("budget_max")

    for rec in recommendations:
        price = rec.get("price")

        if isinstance(price, (int, float)) and price > 0:
            valid_price_count += 1

            if budget_max is None or price <= budget_max:
                budget_compliant_count += 1

        if rec.get("image_url"):
            valid_image_count += 1

        if expected_brand:
            if norm(rec.get("brand")) == expected_brand:
                brand_compliant_count += 1

        if avoid_brand:
            if norm(rec.get("brand")) == avoid_brand:
                failures.append(
                    f"excluded brand returned: {rec.get('brand')}"
                )

    if recommendations and valid_price_count < len(recommendations):
        warnings.append(
            f"verified price missing on "
            f"{len(recommendations) - valid_price_count} recommendation(s)"
        )

    if recommendations and valid_image_count < len(recommendations):
        warnings.append(
            f"image missing on "
            f"{len(recommendations) - valid_image_count} recommendation(s)"
        )

    if budget_max is not None and recommendations:
        if budget_compliant_count < len(recommendations):
            failures.append(
                "one or more recommendations exceed budget"
            )

    if expected_brand and recommendations:
        if brand_compliant_count < len(recommendations):
            failures.append(
                "one or more recommendations violate requested brand"
            )

    # ------------------------------------------------------------
    # Target UX checks
    # ------------------------------------------------------------
    recommendation_count = len(recommendations)

    if recommendation_count == 0:
        failures.append(
            "no recommendation returned"
        )
    elif recommendation_count < 3:
        failures.append(
            f"Best-3 not achieved: only {recommendation_count}"
        )

    total_analysis_options = len(diagnostics)

    if total_analysis_options < 6:
        failures.append(
            f"5-6 comparison options not achieved: "
            f"only {total_analysis_options} scored options"
        )

    if evidence_ready < 3:
        warnings.append(
            f"low evidence-ready count: {evidence_ready}"
        )

    if fit_scored < 3:
        warnings.append(
            f"low fit-scored count: {fit_scored}"
        )

    if elapsed > 10:
        failures.append(
            f"response too slow: {elapsed:.2f}s > 10s"
        )
    elif elapsed > 5:
        warnings.append(
            f"response above preferred 5s: {elapsed:.2f}s"
        )

    top_fit = (
        recommendations[0].get("fit_percent")
        if recommendations
        else None
    )

    return {
        "id": test["id"],
        "query": test["query"],
        "passed": not failures,
        "failures": failures,
        "warnings": warnings,
        "elapsed_seconds": round(elapsed, 3),
        "status": data.get("status"),
        "discovered": discovered,
        "evidence_ready": evidence_ready,
        "fit_scored": fit_scored,
        "recommendation_count": recommendation_count,
        "comparison_option_count": total_analysis_options,
        "verified_price_count": valid_price_count,
        "image_count": valid_image_count,
        "top_fit_percent": top_fit,
        "recommendations": [
            {
                "rank": rec.get("rank"),
                "title": rec.get("title"),
                "brand": rec.get("brand"),
                "price": rec.get("price"),
                "fit_percent": rec.get("fit_percent"),
                "image_url": rec.get("image_url"),
            }
            for rec in recommendations
        ],
    }


def main():
    results = []

    print()
    print("=" * 110)
    print("COUPON WORLD - MOBILE SEARCH BENCHMARK / PHASE 2 END-TO-END")
    print("=" * 110)

    for test in TESTS:
        print()
        print("-" * 110)
        print(test["id"], "|", test["query"])

        try:
            data, elapsed = fetch(test["query"])
            result = evaluate(test, data, elapsed)

        except Exception as error:
            result = {
                "id": test["id"],
                "query": test["query"],
                "passed": False,
                "failures": [f"request failed: {error}"],
                "warnings": [],
                "elapsed_seconds": None,
                "status": "ERROR",
                "discovered": 0,
                "evidence_ready": 0,
                "fit_scored": 0,
                "recommendation_count": 0,
                "comparison_option_count": 0,
                "verified_price_count": 0,
                "image_count": 0,
                "top_fit_percent": None,
                "recommendations": [],
            }

        results.append(result)

        state = "PASS" if result["passed"] else "FAIL"

        print("RESULT          :", state)
        print("TIME            :", result["elapsed_seconds"])
        print("DISCOVERED      :", result["discovered"])
        print("EVIDENCE READY  :", result["evidence_ready"])
        print("FIT SCORED      :", result["fit_scored"])
        print("BEST RESULTS    :", result["recommendation_count"])
        print("COMPARE OPTIONS :", result["comparison_option_count"])
        print("IMAGES          :", result["image_count"])
        print("VERIFIED PRICES :", result["verified_price_count"])
        print("TOP FIT         :", result["top_fit_percent"])

        for failure in result["failures"]:
            print("  FAIL ->", failure)

        for warning in result["warnings"]:
            print("  WARN ->", warning)

        for rec in result["recommendations"]:
            print(
                "   ",
                f'#{rec["rank"]}',
                rec["title"],
                "|",
                rec["price"],
                "| fit",
                rec["fit_percent"],
            )

    passed = sum(1 for x in results if x["passed"])
    failed = len(results) - passed

    avg_time_values = [
        x["elapsed_seconds"]
        for x in results
        if isinstance(x["elapsed_seconds"], (int, float))
    ]

    avg_time = (
        round(sum(avg_time_values) / len(avg_time_values), 3)
        if avg_time_values
        else None
    )

    summary = {
        "total": len(results),
        "passed": passed,
        "failed": failed,
        "score_percent": round(
            100 * passed / max(len(results), 1),
            1,
        ),
        "average_response_seconds": avg_time,
        "best3_success_count": sum(
            1 for x in results
            if x["recommendation_count"] >= 3
        ),
        "six_option_success_count": sum(
            1 for x in results
            if x["comparison_option_count"] >= 6
        ),
        "results": results,
    }

    REPORT.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print()
    print("=" * 110)
    print("SUMMARY")
    print("=" * 110)
    print("TOTAL                 :", summary["total"])
    print("PASS                  :", summary["passed"])
    print("FAIL                  :", summary["failed"])
    print("SCORE                 :", summary["score_percent"], "%")
    print("AVG RESPONSE          :", summary["average_response_seconds"], "sec")
    print("BEST-3 SUCCESS        :", summary["best3_success_count"], "/", summary["total"])
    print("6-OPTION SUCCESS      :", summary["six_option_success_count"], "/", summary["total"])
    print("REPORT                :", REPORT)


if __name__ == "__main__":
    main()
