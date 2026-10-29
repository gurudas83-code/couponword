#!/usr/bin/env python3
"""Build the approved public GitHub Pages artifact."""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PUBLIC_FILES = (
    "index.html", "style.css", "app.js", "mobile-research-preview.js", "coupons.json", "CNAME",
    "robots.txt", "sitemap.xml", "buying-guides.html", "buying-guides.js",
)
PUBLIC_DATA_FILES = ("data/seo-pages.json", "data/mobile_research_preview.json")
PUBLIC_DIRECTORIES = ("assets", "products", "seo", "guides")
FORBIDDEN_NAMES = {
    "admin.html", "validator.html", "python", "reports", "outputs",
    "backups", ".git", "phase_e_current.zip",
}
SECRET_PATTERNS = (
    re.compile(r"(?:OPENAI|GEMINI|TAVILY|ANTHROPIC)_API_KEY\s*[:=]", re.I),
    re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC|PRIVATE) KEY-----", re.I),
    re.compile(r"(?:private_product_id|/outputs/|/reports/|C:\\Users\\)", re.I),
)


def _copy_file(relative: str, destination: Path) -> None:
    source = ROOT / relative
    if not source.is_file():
        raise FileNotFoundError(f"required public file is missing: {relative}")
    target = destination / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)


def _validate_public_content(output: Path) -> None:
    preview_path = output / "data" / "mobile_research_preview.json"
    preview = json.loads(preview_path.read_text(encoding="utf-8"))
    rows = preview.get("products")
    if preview.get("mode") != "PUBLIC_TECHNICAL_RESEARCH_PREVIEW" or not preview.get("default_enabled"):
        raise RuntimeError("public mobile research preview must remain explicitly enabled and research-only")
    if not isinstance(rows, list) or len(rows) != 10:
        raise RuntimeError("public mobile research preview must contain exactly 10 variants")
    ids = [row.get("canonical_product_id") for row in rows]
    if len(ids) != len(set(ids)) or any(not item for item in ids):
        raise RuntimeError("public mobile research preview contains duplicate or missing canonical IDs")
    for row in rows:
        commerce = row.get("commerce") or {}
        if any(commerce.get(key) not in (None, False, "") for key in ("price", "stock")):
            raise RuntimeError("research preview exposes commerce data")
        if commerce.get("purchase_cta_eligible") or commerce.get("publication_eligible"):
            raise RuntimeError("research preview exposes a commerce CTA")

    coupons_path = output / "coupons.json"
    coupons = json.loads(coupons_path.read_text(encoding="utf-8"))
    if not isinstance(coupons, list):
        raise RuntimeError("public coupons.json must contain a list")
    approved_hosts = {"amazon.in", "www.amazon.in", "amzn.in", "www.amzn.in", "flipkart.com", "www.flipkart.com", "croma.com", "www.croma.com"}
    for row in coupons:
        if not isinstance(row, dict) or row.get("cta_eligible") is not True:
            continue
        try:
            from urllib.parse import urlparse

            parsed = urlparse(str(row.get("link") or ""))
            price = float(str(row.get("price") or "").replace(",", "").replace("₹", ""))
        except (TypeError, ValueError):
            raise RuntimeError("public CTA row has an invalid price or URL")
        if row.get("active") is not True or price <= 0 or str(row.get("availability") or "").casefold() not in {"in_stock", "in stock", "available", "available_now"}:
            raise RuntimeError("public CTA row is missing active, positive-price and in-stock evidence")
        if parsed.scheme != "https" or parsed.hostname not in approved_hosts:
            raise RuntimeError("public CTA row points to an unapproved retailer host")
        if row.get("identity_verified") is not True and str(row.get("catalog_status") or "").casefold() != "verified":
            raise RuntimeError("public CTA row is missing verified identity evidence")

    for path in output.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".html", ".js", ".json", ".css", ".txt", ".xml", ".svg"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                raise RuntimeError(f"sensitive content pattern found in public artifact: {path.relative_to(output)}")


def build(output: Path) -> Path:
    output = output.resolve()
    if output == ROOT or output in ROOT.parents:
        raise ValueError("public artifact output cannot replace the repository")
    source_paths = [ROOT / item for item in PUBLIC_FILES + PUBLIC_DIRECTORIES]
    if any(output == source or source in output.parents for source in source_paths):
        raise ValueError("public artifact output cannot overlap a source path")
    if output.exists():
        shutil.rmtree(output)
    output.mkdir(parents=True)

    for relative in PUBLIC_FILES + PUBLIC_DATA_FILES:
        _copy_file(relative, output)
    for relative in PUBLIC_DIRECTORIES:
        source = ROOT / relative
        if not source.is_dir():
            raise FileNotFoundError(f"required public directory is missing: {relative}")
        shutil.copytree(source, output / relative)

    leaked = []
    for path in output.rglob("*"):
        parts = path.relative_to(output).parts
        if path.name in FORBIDDEN_NAMES or any(part in FORBIDDEN_NAMES for part in parts):
            leaked.append(str(path.relative_to(output)))
    if leaked:
        raise RuntimeError("forbidden files entered public artifact: " + ", ".join(leaked))
    _validate_public_content(output)
    return output


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(f"public artifact ready: {build(args.output)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
