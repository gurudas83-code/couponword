import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "python"))

from intent_engine import parse_query


BENCHMARK = ROOT / "data" / "mobile_search_benchmark.json"


def contains_all(actual, expected):
    actual_norm = {str(x).lower() for x in (actual or [])}
    return all(str(x).lower() in actual_norm for x in expected)


def check_test(test):
    query = test["query"]
    expected = test.get("expected", {})
    intent = parse_query(query)

    failures = []

    for field in (
        "category",
        "budget_max",
        "budget_min",
        "user_profile",
    ):
        if field in expected:
            if intent.get(field) != expected[field]:
                failures.append(
                    f"{field}: expected={expected[field]!r}, "
                    f"actual={intent.get(field)!r}"
                )

    for field in (
        "must_have",
        "preferred",
        "avoid",
        "brands",
    ):
        if field in expected:
            if not contains_all(intent.get(field), expected[field]):
                failures.append(
                    f"{field}: expected contains {expected[field]!r}, "
                    f"actual={intent.get(field)!r}"
                )

    if "priority_high" in expected:
        dimension = expected["priority_high"]
        weights = intent.get("priority_weights") or {}

        if dimension not in weights:
            failures.append(
                f"priority dimension missing: {dimension}"
            )
        else:
            values = list(weights.values())

            if values and weights[dimension] < max(values):
                failures.append(
                    f"{dimension} not highest priority: "
                    f"{weights[dimension]}, max={max(values)}"
                )

    if "priority_relation" in expected:
        higher, lower = expected["priority_relation"]
        weights = intent.get("priority_weights") or {}

        high_value = weights.get(higher)
        low_value = weights.get(lower)

        if high_value is None or low_value is None:
            failures.append(
                f"priority relation unavailable: "
                f"{higher}={high_value}, {lower}={low_value}"
            )
        elif high_value <= low_value:
            failures.append(
                f"priority relation failed: "
                f"{higher}={high_value} <= {lower}={low_value}"
            )

    return {
        "id": test["id"],
        "query": query,
        "passed": not failures,
        "failures": failures,
        "intent": intent,
    }


def main():
    tests = json.loads(
        BENCHMARK.read_text(encoding="utf-8")
    )

    results = [check_test(test) for test in tests]

    passed = sum(1 for x in results if x["passed"])
    failed = len(results) - passed

    print()
    print("=" * 100)
    print("COUPON WORLD ? MOBILE SEARCH BENCHMARK / PHASE 1")
    print("=" * 100)
    print("TOTAL :", len(results))
    print("PASS  :", passed)
    print("FAIL  :", failed)
    print(
        "SCORE :",
        round(100 * passed / max(len(results), 1), 1),
        "%"
    )
    print()

    for result in results:
        status = "PASS" if result["passed"] else "FAIL"

        print(
            f'{status:4} | {result["id"]} | '
            f'{result["query"]}'
        )

        for failure in result["failures"]:
            print("       ->", failure)

    report_path = ROOT / "data" / "mobile_search_benchmark_report.json"

    report_path.write_text(
        json.dumps(
            {
                "total": len(results),
                "passed": passed,
                "failed": failed,
                "score_percent": round(
                    100 * passed / max(len(results), 1),
                    1,
                ),
                "results": results,
            },
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    print()
    print("REPORT:", report_path)


if __name__ == "__main__":
    main()
