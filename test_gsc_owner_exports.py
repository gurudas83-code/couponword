"""Offline regression for user-supplied Google Search Console CSV exports.

No live Google account is available in CI; all values here are synthetic.
"""
from __future__ import annotations

import csv
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from scripts.gsc_owner_export_audit import analyze, read_zip_tables, safe_csv


SITE = "https://coupon-world.in"


def csv_content(head, rows):
    from io import StringIO
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(head)
    writer.writerows(rows)
    return output.getvalue()


def make_zip(path, files):
    with zipfile.ZipFile(path, "w") as archive:
        for filename, contents in files.items():
            archive.writestr(filename, contents)


def make_sitemap(path, routes):
    ns = "http://www.sitemaps.org/schemas/sitemap/0.9"
    top = ET.Element("{" + ns + "}urlset")
    for route in routes:
        node = ET.SubElement(top, "{" + ns + "}url")
        ET.SubElement(node, "{" + ns + "}loc").text = SITE + route
    ET.ElementTree(top).write(path, encoding="utf-8")


class OwnerExportAuditTests(unittest.TestCase):
    def setup_fixture(self, root):
        sitemap = root / "sitemap.xml"
        performance = root / "Performance.zip"
        indexing = root / "Pages.zip"
        make_sitemap(sitemap, ["/", "/phones/", "/seo/top-30-phone-research-india.html"])
        make_zip(performance, {
            "Dates.csv": csv_content(
                ["Date", "Clicks", "Impressions", "CTR", "Position"],
                [["2026-11-17", "2", "100", "2%", "22.5"],
                 ["2026-11-18", "1", "80", "1.25%", "24.1"]]),
            "Queries.csv": csv_content(
                ["Top queries", "Clicks", "Impressions", "CTR", "Position"],
                [["phone under 20000", "1", "45", "2.2%", "14.5"],
                 ["=HYPERLINK(foo)", "0", "10", "0%", "34.0"]]),
            "Pages.csv": csv_content(
                ["Top pages", "Clicks", "Impressions", "CTR", "Position"],
                [[SITE + "/", "2", "60", "3.3%", "20"],
                 [SITE + "/seo/top-30-phone-research-india.html", "1", "20", "5%", "13"],
                 [SITE + "/old-unlisted/", "0", "10", "0%", "50"]]),
        })
        make_zip(indexing, {
            "Chart.csv": csv_content(["Date", "Indexed", "Not indexed"],
                                     [["2026-11-16", "12", "32"],
                                      ["2026-11-19", "15", "31"]]),
            "Table.csv": csv_content(["Reason", "Source", "Validation", "Pages"],
                                     [["Discovered - currently not indexed", "Google systems",
                                       "Not Started", "14"],
                                      ["Excluded by 'noindex' tag", "Website", "Not Started", "17"]])
        })
        return sitemap, performance, indexing

    def test_real_owner_export_fixtures_keep_gsc_totals_distinct_from_sitemap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sitemap, perf, index = self.setup_fixture(root)
            audit = analyze(sitemap, perf, index, SITE + "/")
            self.assertEqual(audit["candidate_sitemap_urls"], 3)
            self.assertEqual(audit["performance"]["clicks"], 3)
            self.assertEqual(audit["performance"]["impressions"], 180)
            self.assertEqual(audit["performance"]["ctr"], round(3 / 180, 6))
            self.assertEqual(audit["indexing"]["indexed_pages"], 15)
            self.assertEqual(audit["indexing"]["not_indexed_pages"], 31)
            self.assertEqual(audit["visible_performance_urls_in_sitemap"], 2)
            self.assertFalse(audit["property_provenance_verified_from_zip"])
            self.assertTrue(audit["performance_rows_are_not_indexing_verdicts"])
            self.assertTrue(all(row["gsc_indexing_verdict_for_this_url"] is None
                                for row in audit["sitemap_comparison"]))
            self.assertEqual(audit["indexing"]["reasons"][0]["pages"], 17)

    def test_missing_exports_leave_google_metrics_unmeasured(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sitemap, perf, index = self.setup_fixture(root)
            only_performance = analyze(sitemap, perf, None, "sc-domain:coupon-world.in")
            self.assertIsNone(only_performance["indexing"]["indexed_pages"])
            only_indexing = analyze(sitemap, None, index, SITE + "/")
            self.assertIsNone(only_indexing["performance"]["clicks"])
            self.assertEqual(only_indexing["performance"]["top_pages"], [])

    def test_no_chart_means_no_property_level_clicks_even_with_page_rows(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sitemap, performance, _ = self.setup_fixture(root)
            make_zip(performance, {"Pages.csv": csv_content(
                ["Top pages", "Clicks", "Impressions"],
                [[SITE + "/", "2", "20"]])})
            audit = analyze(sitemap, performance, None, SITE + "/")
            self.assertIsNone(audit["performance"]["clicks"])
            self.assertEqual(audit["visible_performance_urls_in_sitemap"], 1)

    def test_rejects_invalid_property_and_foreign_sitemap(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            sitemap, perf, index = self.setup_fixture(root)
            with self.assertRaises(ValueError):
                analyze(sitemap, perf, index, "https://someone-else.example/")
            make_sitemap(sitemap, ["/", "/?q=foo"])
            with self.assertRaises(ValueError):
                analyze(sitemap, perf, index, SITE + "/")

    def test_csv_formula_and_unexpected_zip_inputs_are_safe(self):
        self.assertEqual(safe_csv("=HYPERLINK(foo)"), "'=HYPERLINK(foo)")
        self.assertEqual(safe_csv("+SUM(1)"), "'+SUM(1)")
        self.assertEqual(safe_csv("@user"), "'@user")
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "empty.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("../../not-csv.txt", "do not extract")
            with self.assertRaisesRegex(ValueError, "no CSV"):
                read_zip_tables(path)


if __name__ == "__main__":
    unittest.main()
