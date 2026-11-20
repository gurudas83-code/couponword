#!/usr/bin/env python3
"""Compare owner-exported GSC reports with Coupon World's generated sitemap.

NO Google credentials, API calls or site edits. Never confuse technical
indexability, impressions or Search Console table rows with indexed URLs.
Owner exports have no authenticated property metadata: --property is a user
claim, not cryptographic verification of CSV provenance.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

HOST = "coupon-world.in"
SITE = "https://" + HOST
MAX_ZIP_ENTRIES = 100
MAX_CSV_BYTES = 10_000_000


def canonical_header(text: str) -> str:
    return re.sub(r"\s+", " ", str(text).lstrip("\ufeff").strip().lower().replace("_", " "))


def read_zip_tables(path: Path) -> list[dict]:
    """Inspect only CSV bytes, not extracted paths; enforce bounded input size."""
    tables = []
    with zipfile.ZipFile(path) as archive:
        members = [info for info in archive.infolist() if info.filename.lower().endswith(".csv")]
        if len(members) > MAX_ZIP_ENTRIES:
            raise ValueError("Excessive CSV count in owner export")
        for info in members:
            if info.file_size > MAX_CSV_BYTES:
                raise ValueError("Oversized owner CSV: " + info.filename)
            with archive.open(info) as stream:
                raw = stream.read(MAX_CSV_BYTES + 1)
            if len(raw) > MAX_CSV_BYTES:
                raise ValueError("Oversized owner CSV")
            reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
            if not reader.fieldnames:
                continue
            fields = {canonical_header(field): field for field in reader.fieldnames if field}
            rows = [
                {canonical_header(key): (value or "").strip()
                 for key, value in row.items() if key}
                for row in reader if row
            ]
            tables.append({"source": info.filename, "fields": set(fields), "rows": rows})
    if not tables:
        raise ValueError("Owner export ZIP has no CSV tables")
    return tables


def table_with(tables: list[dict], *fields: str) -> dict | None:
    target = set(fields)
    found = [table for table in tables if target <= table["fields"]]
    return found[0] if found else None


def num(value: str) -> float:
    cleaned = str(value).replace(",", "").replace("%", "").strip()
    if not cleaned or cleaned in ("—", "-", "~"):
        raise ValueError("Missing numeric value")
    n = float(cleaned)
    if not (float("-inf") < n < float("inf")):
        raise ValueError("Non-finite GSC metric")
    return n


def count(value: str) -> int:
    n = num(value)
    if n < 0 or int(n) != n:
        raise ValueError("Invalid count: " + str(value))
    return int(n)


def date_key(value: str):
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d/%m/%Y", "%d %b %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    raise ValueError("Unsupported GSC export date: " + value)


def sitemap_urls(sitemap: Path) -> list[str]:
    root = ET.parse(sitemap).getroot()
    ns = "{http://www.sitemaps.org/schemas/sitemap/0.9}"
    if root.tag != ns + "urlset":
        raise ValueError("Expected generated sitemap urlset")
    urls = []
    for entry in root.findall(ns + "url"):
        loc = entry.find(ns + "loc")
        if loc is None or not (loc.text or "").strip():
            raise ValueError("Empty sitemap location")
        url = loc.text.strip()
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != HOST or parsed.query or parsed.fragment:
            raise ValueError("Sitemap contains noncanonical host, query or fragment")
        urls.append(url)
    if len(urls) != len(set(urls)):
        raise ValueError("Duplicate sitemap URLs")
    if not urls:
        raise ValueError("Sitemap must have candidate URLs")
    return urls


def get_performance(tables: list[dict] | None):
    out = {"clicks": None, "impressions": None, "ctr": None,
           "dates": None, "source": None, "top_queries": [], "top_pages": []}
    if not tables:
        return out
    daily = table_with(tables, "date", "clicks", "impressions")
    if daily:
        parsed = []
        for row in daily["rows"]:
            parsed.append((date_key(row["date"]), count(row["clicks"]),
                           count(row["impressions"])))
        if parsed:
            dates = [r[0] for r in parsed]
            if len(dates) != len(set(dates)):
                raise ValueError("Duplicate daily performance rows")
            out.update({
                "clicks": sum(r[1] for r in parsed),
                "impressions": sum(r[2] for r in parsed),
                "dates": {"start": min(dates).isoformat(), "end": max(dates).isoformat(),
                          "days_in_export": len(parsed)},
                "source": daily["source"],
            })
            if out["impressions"] > 0:
                out["ctr"] = round(out["clicks"] / out["impressions"], 6)
    for header, key in (("top queries", "top_queries"), ("top pages", "top_pages")):
        table = table_with(tables, header, "clicks", "impressions")
        if not table:
            continue
        for row in table["rows"]:
            try:
                out[key].append({
                    "value": row[header],
                    "clicks": count(row["clicks"]),
                    "impressions": count(row["impressions"]),
                    "ctr": row.get("ctr") or None,
                    "position": row.get("position") or None,
                })
            except ValueError:
                continue
        out[key].sort(key=lambda x: (-x["impressions"], -x["clicks"], x["value"]))
    return out


def get_indexing(tables: list[dict] | None):
    out = {"indexed_pages": None, "not_indexed_pages": None, "chart_date": None,
           "chart_source": None, "reasons": []}
    if not tables:
        return out
    chart = table_with(tables, "date", "indexed", "not indexed")
    if chart and chart["rows"]:
        entries = []
        for row in chart["rows"]:
            entries.append((date_key(row["date"]), count(row["indexed"]),
                            count(row["not indexed"])))
        latest = max(entries, key=lambda r: r[0])
        out.update({"indexed_pages": latest[1], "not_indexed_pages": latest[2],
                    "chart_date": latest[0].isoformat(), "chart_source": chart["source"]})
    reasons = table_with(tables, "reason", "pages")
    if reasons:
        for row in reasons["rows"]:
            if not row["reason"]:
                continue
            out["reasons"].append({
                "reason": row["reason"],
                "pages": count(row["pages"]),
                "source": row.get("source") or None,
                "validation": row.get("validation") or None,
            })
        out["reasons"].sort(key=lambda x: -x["pages"])
    return out


def safe_csv(value):
    """Avoid CSV spreadsheet formula injection from query strings."""
    value = str(value or "")
    return "'" + value if value.startswith(("=", "+", "-", "@", "\t", "\r")) else value


def export_csv(path: Path, header: list[str], rows: list[dict]):
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=header, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: safe_csv(row.get(field)) for field in header})


def analyze(sitemap: Path, performance_zip: Path | None,
            indexing_zip: Path | None, property_claim: str) -> dict:
    if property_claim not in (SITE + "/", "sc-domain:" + HOST):
        raise ValueError("Owner-confirmed property must be coupon-world.in")
    urls = sitemap_urls(sitemap)
    performance = get_performance(read_zip_tables(performance_zip) if performance_zip else None)
    indexing = get_indexing(read_zip_tables(indexing_zip) if indexing_zip else None)

    page_rows = {}
    for row in performance["top_pages"]:
        url = row["value"]
        if urlsplit(url).netloc == HOST:
            page_rows[url] = row
    matched = set(urls) & set(page_rows)
    comparison = [
        {
            "url": url,
            "gsc_performance_row_present": url in page_rows,
            "gsc_page_clicks_in_visible_table": page_rows[url]["clicks"] if url in page_rows else None,
            "gsc_page_impressions_in_visible_table": page_rows[url]["impressions"] if url in page_rows else None,
            "gsc_indexing_verdict_for_this_url": None,
        }
        for url in urls
    ]
    return {
        "source": "OWNER_PROVIDED_GSC_CSV_EXPORTS_NOT_API",
        "owner_declared_property": property_claim,
        "property_provenance_verified_from_zip": False,
        "candidate_sitemap_urls": len(urls),
        "performance": performance,
        "indexing": indexing,
        "visible_performance_urls_in_sitemap": len(matched),
        "performance_rows_are_not_indexing_verdicts": True,
        "performance_tables_may_omit_queries_and_differ_from_chart_totals": True,
        "indexing_chart_counts_are_google_known_urls_not_sitemap_indexed_count": True,
        "sitemap_comparison": comparison,
        "notes": [
            "Chart-level performance totals only; never add query/page table rows as property traffic.",
            "Indexed count is Google-reported property total at chart date; not proof all sitemap candidates are indexed.",
            "Page-level GSC index verdict requires URL Inspection or indexed-page export.",
            "CSV ZIP does not identify or authenticate which GSC property/filter produced it.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sitemap", type=Path, required=True,
                        help="Generated public/sitemap.xml, not historical checked-in sitemap.xml")
    parser.add_argument("--performance-zip", type=Path)
    parser.add_argument("--indexing-zip", type=Path)
    parser.add_argument("--property", required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/gsc-owner-baseline"))
    args = parser.parse_args()
    if not (args.performance_zip or args.indexing_zip):
        parser.error("At least one owner GSC CSV ZIP export is required")
    result = analyze(args.sitemap, args.performance_zip, args.indexing_zip, args.property)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "baseline.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    export_csv(args.output_dir / "candidate-sitemap-performance.csv",
               ["url", "gsc_performance_row_present", "gsc_page_clicks_in_visible_table",
                "gsc_page_impressions_in_visible_table", "gsc_indexing_verdict_for_this_url"],
               result["sitemap_comparison"])
    export_csv(args.output_dir / "query-evidence.csv",
               ["value", "clicks", "impressions", "ctr", "position"],
               result["performance"]["top_queries"])
    print(json.dumps({
        "candidate_urls": result["candidate_sitemap_urls"],
        "google_indexed_pages": result["indexing"]["indexed_pages"],
        "google_not_indexed_pages": result["indexing"]["not_indexed_pages"],
        "gsc_clicks": result["performance"]["clicks"],
        "gsc_impressions": result["performance"]["impressions"],
        "sitemap_urls_in_visible_page_performance": result["visible_performance_urls_in_sitemap"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
