"""Check the existing Phase E API twice per query from the repository root.

Runs the same Flask endpoint as the site, without publishing or committing.
"""

import sys
import time
from pathlib import Path


root = Path.cwd()
if not (root / "python/shopping_api.py").exists():
    raise SystemExit("Run from the couponword-integration repository directory")
sys.path.insert(0, str(root / "python"))

from shopping_api import app  # noqa: E402


cases = (
    ("mobile under 10000", 10000, None),
    ("mobile under 15000", 15000, None),
    ("best phone under 20000", 20000, None),
    ("Samsung phone under 20000", 20000, "samsung"),
)

failures = []
with app.test_client() as client:
    for query, budget, required_brand in cases:
        runs = []
        for repeat in (1, 2):
            start = time.monotonic()
            response = client.get("/api/recommend", query_string={"q": query})
            data = response.get_json(silent=True) or {}
            picks = data.get("recommendations") or []
            stages = data.get("stage_counts") or {}
            print(f"\n{query} | run {repeat} | HTTP {response.status_code} | "
                  f"{data.get('status')} | {time.monotonic() - start:.1f}s")
            print("stages:", {key: stages.get(key) for key in (
                "discovered", "identity_verified", "official_verified",
                "qualifying_unique_models", "recommendations_returned",
            )})
            print("snapshot:", data.get("candidate_snapshot"))
            for pick in picks:
                print("pick:", pick.get("asin"), pick.get("brand"),
                      pick.get("title"), pick.get("fit_percent"),
                      pick.get("price"), "official:", pick.get("official_source") or "none")
            if response.status_code != 200:
                failures.append((query, "API error", data.get("error")))
            if len(picks) > 3:
                failures.append((query, "more than 3 results", len(picks)))
            if len({pick.get("asin") for pick in picks}) != len(picks):
                failures.append((query, "duplicate ASIN", repeat))
            for pick in picks:
                try:
                    price = float(pick.get("price"))
                    fit = int(pick.get("fit_percent"))
                except (ValueError, TypeError):
                    failures.append((query, "missing price or fit", pick.get("asin")))
                    continue
                if price > budget or fit < 50:
                    failures.append((query, "out of budget or below 50 Fit", pick.get("asin")))
                if required_brand and required_brand not in str(pick.get("brand") or "").casefold():
                    failures.append((query, "wrong brand", pick.get("asin")))
            runs.append((response.status_code, data.get("status"), [
                (pick.get("asin"), pick.get("fit_percent"), pick.get("price"))
                for pick in picks
            ]))
        if runs[0] != runs[1]:
            failures.append((query, "repeat response changed", runs))
        if len(runs[1][2]) < 3:
            failures.append((query, "fewer than 3 eligible phones", len(runs[1][2])))

print("\nPHASE E LOCAL GATE:", "PASS" if not failures else "INCOMPLETE")
for failure in failures:
    print("CHECK:", *failure)
print("No commit, push or deploy performed by this gate.")
raise SystemExit(1 if failures else 0)
