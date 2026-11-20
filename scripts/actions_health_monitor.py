#!/usr/bin/env python3
"""Read-only GitHub Actions health audit and single-issue incident tracking.

Only completed MAIN-branch push/schedule/manual runs are considered.
Pull-request failures are intentionally ignored: failed development iterations
must not be confused with production incidents. Never rerun paid API workflows.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API = "https://api.github.com"
ISSUE_TITLE = "[CI Watchdog] Coupon World main workflow failures"
WORKFLOWS = {
    "public-pages-artifact.yml": ("GitHub Pages release", None),
    "static-seo-quality.yml": ("Static SEO on main", None),
    "research-quality.yml": ("Research quality", 72),
    "mobile-integrity-6h.yml": ("Mobile integrity", 30),
    "amazon-catalog-sync.yml": ("Retailer source monitor", 30),
    "six-hour-research-monitor.yml": ("Bounded research monitor", 30),
}
FAILURES = {"failure", "timed_out", "startup_failure", "action_required"}


def github_api(path: str, token: str, method: str = "GET", payload=None):
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required for Actions health inspection")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = Request(
        API + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "CouponWorldCIWatchdog/1.0",
            **({"Content-Type": "application/json"} if body is not None else {}),
        },
    )
    try:
        with urlopen(request, timeout=25) as response:
            result = response.read(4_000_000)
            return json.loads(result) if result else {}
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError("GitHub API could not complete " + method + " " + path.split("?")[0]) from exc


def latest_main_result(label: str, runs: list[dict], now: datetime,
                       max_age_hours: int | None = None) -> dict:
    eligible = [
        row for row in runs
        if row.get("head_branch") == "main"
        and row.get("event") in {"push", "schedule", "workflow_dispatch"}
        and row.get("status") == "completed"
    ]
    if not eligible:
        return {"workflow": label, "result": "UNKNOWN", "reason": "No completed main run"}
    # GitHub normally returns newest first; sort explicitly for testability.
    selected = max(eligible, key=lambda row: (row.get("created_at") or "", row.get("run_attempt") or 0))
    conclusion = selected.get("conclusion") or "unknown"
    when = selected.get("created_at") or ""
    age_hours = None
    try:
        age_hours = round(max(0, (now - datetime.fromisoformat(
            when.replace("Z", "+00:00")
        )).total_seconds()) / 3600, 2)
    except (ValueError, TypeError):
        pass

    if conclusion in FAILURES:
        result = "FAIL"
    elif conclusion == "success":
        result = "PASS"
    else:
        result = "UNKNOWN"
    if result == "PASS" and max_age_hours is not None and (
        age_hours is None or age_hours > max_age_hours
    ):
        result = "STALE"
    return {
        "workflow": label, "result": result, "conclusion": conclusion,
        "run_id": selected.get("id"), "url": selected.get("html_url"),
        "created_at": when, "age_hours": age_hours,
    }


def collect(repo: str, token: str, now: datetime) -> dict:
    items = []
    for workflow, (label, age_limit) in WORKFLOWS.items():
        # Narrow by main branch AND verify event/branch again in Python.
        payload = github_api(
            "/repos/" + repo + "/actions/workflows/" + workflow +
            "/runs?branch=main&per_page=15", token
        )
        runs = payload.get("workflow_runs")
        if not isinstance(runs, list):
            raise RuntimeError("Invalid GitHub run response for " + workflow)
        items.append(latest_main_result(label, runs, now, age_limit))
    alerts = [item for item in items if item["result"] in {"FAIL", "STALE"}]
    unknown = [item for item in items if item["result"] == "UNKNOWN"]
    return {
        "schema_version": 1, "repository": repo,
        "checked_at_utc": now.isoformat(timespec="seconds"),
        "status": "ALERT" if alerts else ("INCOMPLETE" if unknown else "PASS"),
        "checks": items, "alerts": alerts,
        "meaning": "Latest completed main-branch CI, not a guarantee of future success.",
    }


def issue_body(report: dict) -> str:
    rows = [
        "Automatically created by read-only CI monitoring; no paid API calls or reruns.",
        "",
        "**Scope:** Latest completed runs of main-branch workflows only. "
        "Historical and in-progress pull-request failures are excluded.",
        "",
        "| Workflow | Status | Evidence |",
        "|---|---|---|",
    ]
    for item in report["checks"]:
        url = item.get("url")
        link = "[Run " + str(item.get("run_id")) + "](" + url + ")" if url else "Not observed"
        rows.append("| " + item["workflow"] + " | " + item["result"] + " | " + link + " |")
    rows += [
        "", "**Checked (UTC):** " + report["checked_at_utc"],
        "", "Fix the failing job or external dependency. The monitor closes this issue "
        "only when all tracked latest main runs are confirmed healthy.",
    ]
    return "\n".join(rows)


def sync_issue(report: dict, repo: str, token: str) -> str:
    issues = github_api("/repos/" + repo + "/issues?state=open&per_page=100", token)
    if not isinstance(issues, list):
        raise RuntimeError("Unable to list existing CI incidents")
    matching = [i for i in issues if i.get("title") == ISSUE_TITLE and "pull_request" not in i]
    existing = matching[0] if matching else None
    if report["status"] == "ALERT":
        body = issue_body(report)
        if existing:
            github_api("/repos/" + repo + "/issues/" + str(existing["number"]),
                       token, "PATCH", {"body": body})
            return "Updated existing failure issue"
        github_api("/repos/" + repo + "/issues", token, "POST",
                   {"title": ISSUE_TITLE, "body": body})
        return "Created failure issue"
    if report["status"] == "PASS" and existing:
        github_api("/repos/" + repo + "/issues/" + str(existing["number"]),
                   token, "PATCH", {"state": "closed",
                                    "state_reason": "completed",
                                    "body": issue_body(report)})
        return "Closed recovered failure issue"
    return "No issue mutation: " + report["status"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report", type=Path, default=Path("actions-health.json"))
    parser.add_argument("--notify", action="store_true")
    args = parser.parse_args(argv)
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    token = os.environ.get("GITHUB_TOKEN", "")
    if "/" not in repo:
        raise SystemExit("GITHUB_REPOSITORY must identify the connected repository")
    if args.notify:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        if report["repository"] != repo:
            raise SystemExit("Report does not match repository")
        print(sync_issue(report, repo, token))
        return 0
    report = collect(repo, token, datetime.now(timezone.utc))
    args.report.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 1 if report["status"] == "ALERT" else 0


if __name__ == "__main__":
    sys.exit(main())
