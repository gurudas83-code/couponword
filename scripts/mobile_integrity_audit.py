#!/usr/bin/env python3
"""Read-only integrity audit for all 235 mobile discovery rows and 232 model cards.

This is a monitoring utility, not a new research/price engine. Existing
mobile_research_catalogue builds the exact published source-of-truth. A successful
HTTP HEAD request proves reachability only, never model identity or buyability.
403/429 are access restrictions, not evidence that a listing is unavailable.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from python.mobile_research_catalogue import build_public_catalogue

APPROVED_SUFFIXES = (
    "amazon.in", "flipkart.com", "croma.com", "samsung.com", "apple.com",
    "google.com", "mi.com", "oneplus.in", "oppo.com", "realme.com",
    "motorola.in", "motorola.com", "lavamobiles.com", "vivo.com", "iqoo.com",
    "nothing.tech", "po.co", "tecno-mobile.com", "tecno-mobile.in",
    "infinixmobiles.in", "91mobiles.com", "smartprix.com",
    "reliancedigital.in", "notebookcheck.net", "phonearena.com",
    "nothing.community", "vijaysales.com", "poorvika.com",
)
MERCHANTS = {
    "Amazon": ("www.amazon.in", "/s", "k"),
    "Flipkart": ("www.flipkart.com", "/search", "q"),
    "Croma": ("www.croma.com", "/search/", "text"),
}


def safe_url(value: str) -> bool:
    try:
        parsed = urlsplit(str(value or ""))
        host = (parsed.hostname or "").lower()
        return (parsed.scheme == "https" and parsed.username is None
                and parsed.password is None and parsed.port in (None, 443)
                and host and not re.fullmatch(r"[\d.]+", host)
                and any(host == suffix or host.endswith("." + suffix)
                        for suffix in APPROVED_SUFFIXES))
    except ValueError:
        return False


def tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def catalogue_and_audit() -> tuple[dict, dict[str, set[str]]]:
    pub = build_public_catalogue(ROOT)
    wb = json.loads((ROOT / "data/mobile_workbook_research.json").read_text(encoding="utf-8"))
    corpus = json.loads((ROOT / "data/mobile_query_corpus_1000.json").read_text(encoding="utf-8"))
    model_cards, discovery = pub["model_cards"], pub["records"]
    if (len(model_cards), len(discovery), len(wb["models"]), corpus["counts"]["total"]) != (232, 235, 232, 1000):
        raise ValueError("Mobile inventory or regression corpus changed; audit baseline review required")

    urls: dict[str, set[str]] = defaultdict(set)
    issues, retailer_counts, evidence_dates = [], Counter(), Counter()
    model_by_key = {x["model_key"]: x for x in model_cards}
    if len(model_by_key) != 232:
        raise ValueError("Duplicate canonical model key")
    by_display: dict[str, list[str]] = defaultdict(list)

    for row in discovery:
        for url in row.get("source_urls") or []:
            urls[url].add("discovery_source")
            if not safe_url(url):
                issues.append({"id": row["record_key"], "kind": "INVALID_DISCOVERY_URL", "url": url})
        if not row.get("source_urls"):
            issues.append({"id": row["record_key"], "kind": "NO_DISCOVERY_SOURCE"})

    for card in model_cards:
        display = (card["brand"] + " " + card["model"]).lower().strip()
        if display.startswith((card["brand"].lower() + " ")*2):
            display = display[len(card["brand"]) + 1:]
        by_display[" ".join(display.split())].append(card["model_key"])
        for field, spec in (card.get("specifications") or {}).items():
            url = str(spec.get("source_url") or "")
            if url:
                urls[url].add("specification_source")
                if not safe_url(url):
                    issues.append({"id": card["model_key"], "kind": "INVALID_SPEC_URL", "field": field, "url": url})
            date = str(spec.get("checked_at") or spec.get("checked_date") or "")[:10]
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
                evidence_dates[date] += 1

        links = card.get("retailer_search_links") or []
        if {x.get("retailer") for x in links} != set(MERCHANTS) or len(links) != 3:
            issues.append({"id": card["model_key"], "kind": "RETAILER_SET_INCOMPLETE"})
        for link in links:
            merchant = link.get("retailer")
            url = str(link.get("url") or "")
            retailer_counts[merchant] += 1
            urls[url].add("retailer_model_search")
            if merchant not in MERCHANTS or not safe_url(url):
                issues.append({"id": card["model_key"], "kind": "INVALID_RETAILER_URL", "url": url})
                continue
            host, route, param = MERCHANTS[merchant]
            parts = urlsplit(url)
            q = parse_qs(parts.query).get(param, [""])[0]
            if (parts.hostname != host or parts.path != route
                    or not tokens(card["model_key"].replace("|", " ")).issubset(tokens(q))):
                issues.append({"id": card["model_key"], "kind": "GENERIC_OR_MISMATCHED_RETAILER_SEARCH", "retailer": merchant, "url": url})
            if link.get("link_scope") != "MODEL_TARGETED_SEARCH_NOT_VERIFIED_PRODUCT":
                issues.append({"id": card["model_key"], "kind": "RETAILER_LINK_NOT_LABELLED_SEARCH", "retailer": merchant})

        ref = card.get("research_budget_reference")
        if ref:
            urls[ref["source_url"]].add("historical_budget_observation")
            if not safe_url(ref["source_url"]):
                issues.append({"id": card["model_key"], "kind": "INVALID_BUDGET_SOURCE"})
            if ref.get("live_offer") is not False or ref.get("ranking_weight") != 0:
                issues.append({"id": card["model_key"], "kind": "UNSAFE_HISTORICAL_PRICE_PROMOTION"})
            if not re.search(r"\d{4}-\d{2}-\d{2}", str(ref.get("checked_at") or "")):
                issues.append({"id": card["model_key"], "kind": "MISSING_PRICE_OBSERVATION_DATE"})

    duplicate_displays = {name: keys for name, keys in by_display.items() if len(keys) > 1}
    counts = Counter(i["kind"] for i in issues)
    blocking = sorted([i for i in issues if i["kind"] in {
        "INVALID_DISCOVERY_URL", "INVALID_SPEC_URL", "INVALID_RETAILER_URL",
        "RETAILER_SET_INCOMPLETE", "GENERIC_OR_MISMATCHED_RETAILER_SEARCH",
        "RETAILER_LINK_NOT_LABELLED_SEARCH", "INVALID_BUDGET_SOURCE",
        "UNSAFE_HISTORICAL_PRICE_PROMOTION", "MISSING_PRICE_OBSERVATION_DATE",
    }], key=lambda x: (x["kind"], x["id"]))
    report = {
        "audit_checked_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "mode": "READ_ONLY_LINK_AND_QUERY_EVIDENCE_MONITOR",
        "research_snapshot_as_of": wb["research_as_of"],
        "date_warning": "Audit time is NOT manufacturer fact date, offer observation date or live-price verification",
        "inventory": {"discovery_records": len(discovery), "model_cards": len(model_cards),
                      "workbook_models": len(wb["models"]), "query_corpus": corpus["counts"]["total"],
                      "specification_fields": sum(len(x.get("specifications") or {}) for x in model_cards),
                      "historical_budget_references": sum(bool(x.get("research_budget_reference")) for x in model_cards),
                      "search_links": dict(retailer_counts), "unique_links": len(urls)},
        "source_checked_date_counts": dict(sorted(evidence_dates.items())),
        "duplicate_display_identities": duplicate_displays,
        "diagnostic_counts": dict(counts),
        "blocking_issue_count": len(blocking),
        "blocking_issues": blocking[:100],
        "unverified_discovery_rows": [x["record_key"] for x in discovery if not x.get("source_urls")],
        "note": "All 235 discovery rows and all 696 retailer search links structurally checked; HTTP reachability, if enabled, is separate and not exact SKU verification",
    }
    return report, urls


class NoFollow(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        return None


def probe_one(opener, url: str) -> dict:
    if not safe_url(url):
        return {"status": "NOT_PROBED_UNSAFE_URL"}
    request = Request(url, method="HEAD",
                      headers={"User-Agent": "CouponWorldMobileSourceMonitor/1.0", "Accept": "text/html,*/*"})
    try:
        with opener.open(request, timeout=7) as response:
            code = response.status
        return {"status": "REACHABLE_HTTP" if code == 200 else "HTTP_OTHER", "http_status": code}
    except HTTPError as exc:
        code = exc.code
        return {"status": ("ACCESS_BLOCKED" if code in (401, 403, 429) else
                           "REDIRECT_UNRESOLVED" if 300 <= code < 400 else
                           "NOT_FOUND" if code in (404, 410) else "HTTP_ERROR"),
                "http_status": code}
    except (URLError, OSError, TimeoutError, ValueError) as exc:
        return {"status": "NETWORK_UNCONFIRMED", "error": type(exc).__name__}


def probe_links(urls: dict[str, set[str]], max_seconds: int) -> dict:
    """HEAD only; skip the rest of a host after 3 access blocks, without bypassing CAPTCHAs."""
    by_host: dict[str, list[str]] = defaultdict(list)
    for url in sorted(urls):
        by_host[(urlsplit(url).hostname or "").lower()].append(url)
    deadline = time.monotonic() + max_seconds

    def probe_host(item):
        host, links = item
        results: dict[str, dict] = {}
        blocked_streak = 0
        opener = build_opener(NoFollow())
        for pos, url in enumerate(links):
            if time.monotonic() >= deadline:
                for remaining in links[pos:]:
                    results[remaining] = {"status": "NOT_PROBED_TIME_BUDGET"}
                break
            if blocked_streak >= 3:
                for remaining in links[pos:]:
                    results[remaining] = {"status": "NOT_PROBED_HOST_ACCESS_BLOCKED"}
                break
            result = probe_one(opener, url)
            results[url] = result
            blocked_streak = blocked_streak + 1 if result["status"] == "ACCESS_BLOCKED" else 0
        return host, results

    results: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(probe_host, item) for item in sorted(by_host.items())]
        for future in as_completed(futures):
            host, group = future.result()
            results.update(group)
    statuses = Counter(v["status"] for v in results.values())
    return {
        "attempted": sum(x not in ("NOT_PROBED_HOST_ACCESS_BLOCKED", "NOT_PROBED_TIME_BUDGET", "NOT_PROBED_UNSAFE_URL") for x in [v["status"] for v in results.values()]),
        "total_urls": len(urls),
        "statuses": dict(statuses),
        "details": [{"url": u, "kinds": sorted(urls[u]), **results.get(u, {"status": "NOT_PROBED"})} for u in sorted(urls)],
        "disclaimer": "HTTP HEAD success is NOT exact model/variant, page-content, price or stock verification; 403/429 is NOT a broken link.",
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report", default="mobile-integrity-audit.json")
    ap.add_argument("--probe", action="store_true", help="Bounded, read-only HTTP HEAD reachability checks")
    ap.add_argument("--max-seconds", type=int, default=480)
    args = ap.parse_args()
    report, urls = catalogue_and_audit()
    if args.probe:
        report["http_reachability"] = probe_links(urls, min(max(args.max_seconds, 30), 600))
    path = Path(args.report)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    status = "PASS" if not report["blocking_issue_count"] else "FAIL"
    print(json.dumps({"result": status, "inventory": report["inventory"],
                      "blocking": report["blocking_issue_count"],
                      "diagnostics": report["diagnostic_counts"],
                      "network": (report.get("http_reachability") or {}).get("statuses")}, sort_keys=True))
    summary = os.getenv("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fp:
            fp.write("### Six-hour mobile integrity audit\n\n"
                     + f"- {report['inventory']['discovery_records']} discovery / {report['inventory']['model_cards']} model cards\n"
                     + f"- {sum(report['inventory']['search_links'].values())} retailer search links structurally checked\n"
                     + f"- {report['inventory']['query_corpus']} query benchmarks retained\n"
                     + f"- Blocking structural issues: {report['blocking_issue_count']}\n"
                     + f"- HTTP reachability is not a price, model, variant or stock verification\n")
    return 1 if report["blocking_issue_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
