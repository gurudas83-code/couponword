#!/usr/bin/env python3
"""
Coupon World Complete System Audit v1.0

Purpose
-------
Read-only audit for Coupon World.

Checks:
A. Repository health
B. Frontend / website files
C. Product database
D. Product pages
E. SEO / sitemap / robots
F. Affiliate link readiness
G. Intent engine
H. Market discovery
I. Product identity
J. Official source resolver
K. Official spec extractor
L. Product intelligence / fit engine
M. Recommendation ranker
N. Master shopping pipeline
O. Image readiness
P. Price / stock readiness
Q. Frontend <-> backend integration
R. API / hosting readiness
S. Secrets / deployment hygiene
T. Backup / duplicate clutter
U. Overall readiness + blockers + next actions

This script is READ-ONLY.
It does not modify product data, HTML, knowledge files, or deployment config.

Run:
    py python/couponworld_complete_audit.py

Optional:
    py python/couponworld_complete_audit.py --json
    py python/couponworld_complete_audit.py --write-report
"""

from __future__ import annotations

import argparse
import ast
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PYTHON_DIR = ROOT / "python"
DATA_DIR = ROOT / "data"
PRODUCTS_DIR = ROOT / "products"

EXPECTED_CORE_FILES = [
    "intent_engine.py",
    "market_discovery.py",
    "product_identity_v2.py",
    "official_source_resolver.py",
    "official_spec_extractor.py",
    "product_intelligence_bridge.py",
    "product_fit_signal_builder.py",
    "weighted_fit_engine.py",
    "real_recommendation_ranker.py",
    "shopping_intelligence_pipeline.py",
]

FRONTEND_FILES = [
    "index.html",
    "style.css",
    "app.js",
    "robots.txt",
    "sitemap.xml",
]

BACKUP_PATTERNS = (
    "_backup",
    "_before_",
    "_old",
    "_bak",
)

SECRET_PATTERNS = (
    r"TAVILY_API_KEY\s*=\s*[\"'][^\"']+[\"']",
    r"OPENAI_API_KEY\s*=\s*[\"'][^\"']+[\"']",
    r"SECRET\s*=\s*[\"'][^\"']+[\"']",
    r"PASSWORD\s*=\s*[\"'][^\"']+[\"']",
)

API_HINTS = (
    "fastapi",
    "flask",
    "uvicorn",
    "http.server",
    "api/",
    "/api",
    "fetch(",
    "axios",
)

SHOPPING_UI_HINTS = (
    "shopping",
    "recommend",
    "fit",
    "query",
    "search",
    "product-card",
    "recommendation",
)


@dataclass
class Finding:
    area: str
    status: str
    message: str
    details: dict[str, Any] | None = None


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def safe_load_json(path: Path) -> tuple[Any, str | None]:
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except UnicodeDecodeError:
        try:
            return json.loads(path.read_text(encoding="utf-8-sig")), None
        except Exception as exc:
            return None, str(exc)
    except Exception as exc:
        return None, str(exc)


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except Exception:
            return ""
    except Exception:
        return ""


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def module_functions(path: Path) -> list[str]:
    text = read_text(path)
    if not text:
        return []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    return [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ]


def count_html_product_pages() -> int:
    if not PRODUCTS_DIR.exists():
        return 0
    return sum(1 for path in PRODUCTS_DIR.rglob("index.html") if path.is_file())


def inspect_coupon_db() -> dict[str, Any]:
    db = ROOT / "coupons.json"
    result = {
        "exists": db.exists(),
        "valid_json": False,
        "product_count": 0,
        "active_count": 0,
        "missing_image": 0,
        "missing_price": 0,
        "missing_brand": 0,
        "affiliate_tag_matches": 0,
        "affiliate_tag_missing": 0,
    }

    if not db.exists():
        return result

    data, error = safe_load_json(db)
    if error:
        result["error"] = error
        return result

    result["valid_json"] = True

    if isinstance(data, dict):
        products = data.get("products") or data.get("coupons") or []
    else:
        products = data

    if not isinstance(products, list):
        products = []

    result["product_count"] = len(products)

    for product in products:
        if not isinstance(product, dict):
            continue

        if product.get("active") is not False:
            result["active_count"] += 1

        if not clean(product.get("image")):
            result["missing_image"] += 1

        if product.get("price") in (None, ""):
            result["missing_price"] += 1

        if not clean(product.get("brand")):
            result["missing_brand"] += 1

        link = clean(
            product.get("affiliate_url")
            or product.get("link")
            or product.get("url")
        )

        if "amazon." in link or "amzn." in link:
            if "tag=guru0906-21" in link:
                result["affiliate_tag_matches"] += 1
            else:
                result["affiliate_tag_missing"] += 1

    return result


def inspect_knowledge() -> dict[str, Any]:
    result = {}

    for rel in (
        "data/product_knowledge.json",
        "data/official_specs.json",
        "data/knowledge_review.json",
        "data/runtime_shopping_intelligence.json",
    ):
        path = ROOT / rel
        key = Path(rel).name
        result[key] = {
            "exists": path.exists(),
            "product_count": 0,
        }

        if not path.exists():
            continue

        data, error = safe_load_json(path)

        if error:
            result[key]["error"] = error
            continue

        if isinstance(data, dict):
            products = data.get("products", [])
            if isinstance(products, list):
                result[key]["product_count"] = len(products)

            if key == "runtime_shopping_intelligence.json":
                result[key]["status"] = data.get("status")
                result[key]["stage_counts"] = data.get("stage_counts", {})

    return result


def inspect_frontend() -> dict[str, Any]:
    result = {
        "files": {},
        "has_search_ui_hint": False,
        "has_backend_fetch_hint": False,
        "has_recommendation_ui_hint": False,
    }

    combined = ""

    for rel in FRONTEND_FILES:
        path = ROOT / rel
        result["files"][rel] = path.exists()
        if path.exists() and path.suffix in {".html", ".js", ".css"}:
            combined += "\n" + read_text(path).lower()

    result["has_search_ui_hint"] = any(
        hint in combined for hint in ("search", "query", "input")
    )

    result["has_backend_fetch_hint"] = any(
        hint in combined for hint in ("fetch(", "axios", "/api", "api.")
    )

    result["has_recommendation_ui_hint"] = any(
        hint in combined for hint in SHOPPING_UI_HINTS
    )

    return result


def inspect_seo() -> dict[str, Any]:
    robots = ROOT / "robots.txt"
    sitemap = ROOT / "sitemap.xml"
    index = ROOT / "index.html"

    result = {
        "robots_exists": robots.exists(),
        "sitemap_exists": sitemap.exists(),
        "index_exists": index.exists(),
        "canonical_hint": False,
        "schema_org_hint": False,
        "sitemap_url_count": 0,
    }

    if index.exists():
        html = read_text(index).lower()
        result["canonical_hint"] = 'rel="canonical"' in html
        result["schema_org_hint"] = "schema.org" in html

    if sitemap.exists():
        xml = read_text(sitemap)
        result["sitemap_url_count"] = len(re.findall(r"<loc>", xml, re.I))

    return result


def inspect_backend_api() -> dict[str, Any]:
    result = {
        "api_server_detected": False,
        "api_files": [],
        "python_backend_modules": [],
        "github_pages_static": exists("CNAME") or exists(".nojekyll"),
    }

    for path in PYTHON_DIR.glob("*.py"):
        text = read_text(path).lower()

        if any(hint in text for hint in API_HINTS[:4]):
            result["api_server_detected"] = True
            result["api_files"].append(path.name)

        if any(
            token in path.name
            for token in (
                "intent",
                "market",
                "resolver",
                "fit",
                "recommend",
                "shopping",
                "knowledge",
                "intelligence",
            )
        ):
            result["python_backend_modules"].append(path.name)

    return result


def inspect_core_modules() -> dict[str, Any]:
    modules: dict[str, Any] = {}

    for name in EXPECTED_CORE_FILES:
        path = PYTHON_DIR / name
        modules[name] = {
            "exists": path.exists(),
            "syntax_ok": False,
            "functions": [],
        }

        if not path.exists():
            continue

        text = read_text(path)

        try:
            ast.parse(text)
            modules[name]["syntax_ok"] = True
        except SyntaxError as exc:
            modules[name]["syntax_error"] = str(exc)

        modules[name]["functions"] = module_functions(path)

    return modules


def inspect_security() -> dict[str, Any]:
    hits = []

    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue

        if ".git" in path.parts or "__pycache__" in path.parts:
            continue

        if path.suffix.lower() not in {".py", ".js", ".json", ".html", ".env", ".txt"}:
            continue

        text = read_text(path)
        if not text:
            continue

        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text, re.I):
                hits.append(str(path.relative_to(ROOT)))
                break

    return {
        "hardcoded_secret_files": sorted(set(hits)),
        "tavily_env_present": bool(os.environ.get("TAVILY_API_KEY")),
    }


def inspect_backup_clutter() -> dict[str, Any]:
    backups = []

    for path in PYTHON_DIR.glob("*.py"):
        lowered = path.name.lower()
        if any(pattern in lowered for pattern in BACKUP_PATTERNS):
            backups.append(path.name)

    return {
        "count": len(backups),
        "files": backups[:100],
    }


def inspect_gitignore() -> dict[str, Any]:
    path = ROOT / ".gitignore"
    text = read_text(path).lower() if path.exists() else ""

    return {
        "exists": path.exists(),
        "ignores_env": ".env" in text,
        "ignores_pycache": "__pycache__" in text,
        "ignores_one_off_approval_helpers": "approve_product_" in text,
    }


def add(findings: list[Finding], area: str, status: str, message: str, **details: Any) -> None:
    findings.append(
        Finding(
            area=area,
            status=status,
            message=message,
            details=details or None,
        )
    )


def build_findings(audit: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []

    repo = audit["repository"]
    if repo["python_file_count"] >= 10:
        add(findings, "Repository", "PASS", "Python architecture is present.", python_files=repo["python_file_count"])
    else:
        add(findings, "Repository", "WARNING", "Python architecture appears unusually small.")

    frontend = audit["frontend"]
    missing_frontend = [k for k, v in frontend["files"].items() if not v]
    if missing_frontend:
        add(findings, "Frontend", "WARNING", "Some expected frontend files are missing.", missing=missing_frontend)
    else:
        add(findings, "Frontend", "PASS", "Core static frontend files are present.")

    db = audit["product_database"]
    if db["exists"] and db["valid_json"]:
        add(findings, "Product Database", "PASS", f"Product database is readable with {db['product_count']} records.")
    else:
        add(findings, "Product Database", "BLOCKER", "coupons.json is missing or invalid.", error=db.get("error"))

    if db["missing_price"] > 0:
        add(findings, "Price", "WARNING", f"{db['missing_price']} products have no stored price.")
    else:
        add(findings, "Price", "PASS", "Stored product prices are populated.")

    if db["missing_image"] > 0:
        add(findings, "Images", "WARNING", f"{db['missing_image']} products have no image field.")
    else:
        add(findings, "Images", "PASS", "Stored product image fields are populated.")

    if db["affiliate_tag_missing"] > 0:
        add(findings, "Affiliate", "WARNING", f"{db['affiliate_tag_missing']} Amazon links appear to lack the expected affiliate tag.")
    else:
        add(findings, "Affiliate", "PASS", "No obvious missing Amazon affiliate tags were found.")

    modules = audit["core_modules"]
    missing_modules = [name for name, info in modules.items() if not info["exists"]]
    broken_modules = [name for name, info in modules.items() if info["exists"] and not info["syntax_ok"]]

    if missing_modules:
        add(findings, "AI Backend", "BLOCKER", "Core shopping modules are missing.", missing=missing_modules)
    elif broken_modules:
        add(findings, "AI Backend", "BLOCKER", "Some core modules have syntax errors.", broken=broken_modules)
    else:
        add(findings, "AI Backend", "PASS", "All expected shopping intelligence modules exist and parse successfully.")

    required_functions = {
        "intent_engine.py": ["parse_query"],
        "market_discovery.py": ["discover_market"],
        "product_identity_v2.py": ["build_identity"],
        "official_source_resolver.py": ["resolve_product"],
        "official_spec_extractor.py": ["extract_one"],
        "product_fit_signal_builder.py": ["build_fit_signals"],
        "weighted_fit_engine.py": ["calculate_product_fit"],
    }

    for module_name, funcs in required_functions.items():
        info = modules.get(module_name, {})
        present = set(info.get("functions", []))
        missing = [fn for fn in funcs if fn not in present]
        if missing:
            add(findings, "AI Backend", "BLOCKER", f"{module_name} is missing required callable(s).", missing=missing)

    backend_api = audit["backend_api"]
    if backend_api["api_server_detected"]:
        add(findings, "API", "PASS", "A Python API/server implementation appears to exist.", files=backend_api["api_files"])
    else:
        add(findings, "API", "BLOCKER", "No deployable Python API/server layer was detected. Static GitHub Pages cannot execute the shopping pipeline directly.")

    if frontend["has_backend_fetch_hint"]:
        add(findings, "Frontend-Backend Link", "PASS", "Frontend contains an API/fetch integration hint.")
    else:
        add(findings, "Frontend-Backend Link", "BLOCKER", "Frontend does not appear to call a shopping backend API yet.")

    runtime = audit["knowledge"].get("runtime_shopping_intelligence.json", {})
    if runtime.get("exists"):
        counts = runtime.get("stage_counts", {})
        if counts.get("recommendations_returned", 0) >= 3:
            add(findings, "Shopping Pipeline", "PASS", "Runtime pipeline has produced at least 3 recommendations.", stage_counts=counts)
        elif counts:
            add(findings, "Shopping Pipeline", "BLOCKER", "Runtime pipeline exists but is not yet producing the required Top 3-5.", stage_counts=counts)
        else:
            add(findings, "Shopping Pipeline", "WARNING", "Runtime pipeline file exists but stage counts are unavailable.")
    else:
        add(findings, "Shopping Pipeline", "WARNING", "No runtime shopping intelligence result file was found.")

    seo = audit["seo"]
    if seo["robots_exists"] and seo["sitemap_exists"]:
        add(findings, "SEO", "PASS", f"robots.txt and sitemap.xml exist; sitemap contains {seo['sitemap_url_count']} URLs.")
    else:
        add(findings, "SEO", "WARNING", "robots.txt or sitemap.xml is missing.")

    if seo["canonical_hint"] and seo["schema_org_hint"]:
        add(findings, "SEO", "PASS", "Homepage contains canonical/schema hints.")
    else:
        add(findings, "SEO", "WARNING", "Homepage canonical or schema markup may be incomplete.")

    security = audit["security"]
    if security["hardcoded_secret_files"]:
        add(findings, "Security", "BLOCKER", "Possible hardcoded secrets detected.", files=security["hardcoded_secret_files"])
    else:
        add(findings, "Security", "PASS", "No obvious hardcoded API secrets detected by static scan.")

    if security["tavily_env_present"]:
        add(findings, "Runtime Config", "PASS", "TAVILY_API_KEY is available in the current environment.")
    else:
        add(findings, "Runtime Config", "WARNING", "TAVILY_API_KEY is not present in this shell environment.")

    clutter = audit["backup_clutter"]
    if clutter["count"] > 20:
        add(findings, "Repository Hygiene", "WARNING", f"{clutter['count']} backup/before Python files are present. Consider moving them to archive/legacy.")
    else:
        add(findings, "Repository Hygiene", "PASS", "Backup-file clutter is within a manageable range.")

    return findings


def readiness_score(findings: list[Finding]) -> int:
    weights = {
        "PASS": 1.0,
        "WARNING": 0.5,
        "BLOCKER": 0.0,
    }

    if not findings:
        return 0

    score = sum(weights.get(f.status, 0.0) for f in findings)
    return round((score / len(findings)) * 100)


def next_actions(findings: list[Finding]) -> list[str]:
    blockers = [f for f in findings if f.status == "BLOCKER"]
    warnings = [f for f in findings if f.status == "WARNING"]

    actions = []

    priority_map = [
        ("Shopping Pipeline", "Make the master pipeline reliably return 3-5 verified products with Fit >=50%."),
        ("AI Backend", "Repair missing/broken core shopping intelligence module contracts."),
        ("API", "Create a lightweight backend API endpoint for the shopping intelligence pipeline."),
        ("Frontend-Backend Link", "Connect the site search/query UI to the backend API and render returned recommendation cards."),
        ("Images", "Define a safe image-source contract for recommendation cards."),
        ("Price", "Add a live/current price source or clearly show price as unavailable."),
        ("Security", "Move any secrets to environment variables and remove them from tracked files."),
        ("SEO", "Finish canonical/schema/sitemap/robots readiness after the live shopping flow works."),
    ]

    seen = set()

    for area, action in priority_map:
        if any(f.area == area for f in blockers + warnings):
            if action not in seen:
                actions.append(action)
                seen.add(action)

    if not actions:
        actions.append("Proceed to deployment integration testing and live beta validation.")

    return actions[:10]


def collect_audit() -> dict[str, Any]:
    python_files = list(PYTHON_DIR.glob("*.py")) if PYTHON_DIR.exists() else []

    audit = {
        "audit_version": "1.0",
        "root": str(ROOT),
        "repository": {
            "python_file_count": len(python_files),
            "product_page_count": count_html_product_pages(),
            "has_git": (ROOT / ".git").exists(),
            "has_cname": (ROOT / "CNAME").exists(),
            "has_readme": (ROOT / "README.md").exists(),
        },
        "frontend": inspect_frontend(),
        "product_database": inspect_coupon_db(),
        "knowledge": inspect_knowledge(),
        "seo": inspect_seo(),
        "backend_api": inspect_backend_api(),
        "core_modules": inspect_core_modules(),
        "security": inspect_security(),
        "backup_clutter": inspect_backup_clutter(),
        "gitignore": inspect_gitignore(),
    }

    findings = build_findings(audit)
    audit["findings"] = [asdict(f) for f in findings]

    status_counts = Counter(f.status for f in findings)

    audit["summary"] = {
        "pass": status_counts.get("PASS", 0),
        "warning": status_counts.get("WARNING", 0),
        "blocker": status_counts.get("BLOCKER", 0),
        "overall_readiness_percent": readiness_score(findings),
        "architecture_ready": not any(
            f.status == "BLOCKER" and f.area in {"AI Backend", "Repository"}
            for f in findings
        ),
        "shopping_engine_ready": not any(
            f.status == "BLOCKER" and f.area == "Shopping Pipeline"
            for f in findings
        ),
        "frontend_ready": not any(
            f.status == "BLOCKER" and f.area == "Frontend"
            for f in findings
        ),
        "backend_ready": not any(
            f.status == "BLOCKER" and f.area in {"AI Backend", "API"}
            for f in findings
        ),
        "frontend_backend_linked": not any(
            f.status == "BLOCKER" and f.area == "Frontend-Backend Link"
            for f in findings
        ),
        "live_query_ready": not any(
            f.status == "BLOCKER"
            and f.area in {"Shopping Pipeline", "API", "Frontend-Backend Link"}
            for f in findings
        ),
        "deployment_ready": status_counts.get("BLOCKER", 0) == 0,
    }

    audit["next_actions"] = next_actions(findings)

    return audit


def print_audit(audit: dict[str, Any]) -> None:
    summary = audit["summary"]

    print("=" * 84)
    print("COUPON WORLD COMPLETE SYSTEM AUDIT v1.0")
    print("=" * 84)
    print("ROOT:", audit["root"])
    print()

    for finding in audit["findings"]:
        marker = {
            "PASS": "[PASS]",
            "WARNING": "[WARN]",
            "BLOCKER": "[BLOCKER]",
        }.get(finding["status"], "[INFO]")

        print(f'{marker:10} {finding["area"]}: {finding["message"]}')

        details = finding.get("details")
        if details:
            for key, value in details.items():
                print(f"           {key}: {value}")

    print()
    print("=" * 84)
    print("READINESS SUMMARY")
    print("=" * 84)
    print("PASS                      :", summary["pass"])
    print("WARNINGS                  :", summary["warning"])
    print("CRITICAL BLOCKERS         :", summary["blocker"])
    print("OVERALL READINESS         :", f'{summary["overall_readiness_percent"]}%')
    print()
    print("ARCHITECTURE READY        :", "YES" if summary["architecture_ready"] else "NO")
    print("SHOPPING ENGINE READY     :", "YES" if summary["shopping_engine_ready"] else "NO")
    print("FRONTEND READY            :", "YES" if summary["frontend_ready"] else "NO")
    print("BACKEND READY             :", "YES" if summary["backend_ready"] else "NO")
    print("FRONTEND-BACKEND LINKED   :", "YES" if summary["frontend_backend_linked"] else "NO")
    print("LIVE QUERY READY          :", "YES" if summary["live_query_ready"] else "NO")
    print("DEPLOYMENT READY          :", "YES" if summary["deployment_ready"] else "NO")

    print()
    print("=" * 84)
    print("NEXT ACTIONS")
    print("=" * 84)

    for index, action in enumerate(audit["next_actions"], start=1):
        print(f"{index}. {action}")

    print("=" * 84)


def write_report(audit: dict[str, Any]) -> tuple[Path, Path]:
    report_dir = ROOT / "audit_reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    json_path = report_dir / "couponworld_complete_audit.json"
    md_path = report_dir / "couponworld_complete_audit.md"

    json_path.write_text(
        json.dumps(audit, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Coupon World Complete System Audit",
        "",
        f"- Overall readiness: **{audit['summary']['overall_readiness_percent']}%**",
        f"- Pass: **{audit['summary']['pass']}**",
        f"- Warnings: **{audit['summary']['warning']}**",
        f"- Blockers: **{audit['summary']['blocker']}**",
        "",
        "## Findings",
        "",
    ]

    for finding in audit["findings"]:
        lines.append(
            f"- **{finding['status']} â€” {finding['area']}**: {finding['message']}"
        )

    lines.extend(["", "## Next Actions", ""])

    for index, action in enumerate(audit["next_actions"], start=1):
        lines.append(f"{index}. {action}")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a read-only complete Coupon World system audit"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON instead of formatted audit",
    )
    parser.add_argument(
        "--write-report",
        action="store_true",
        help="Write audit_reports/couponworld_complete_audit.json and .md",
    )

    args = parser.parse_args()

    audit = collect_audit()

    if args.json:
        print(json.dumps(audit, indent=2, ensure_ascii=False))
    else:
        print_audit(audit)

    if args.write_report:
        json_path, md_path = write_report(audit)
        print()
        print("REPORT JSON:", json_path)
        print("REPORT MD  :", md_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
