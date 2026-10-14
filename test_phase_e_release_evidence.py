import copy
import json
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import product_evidence_store as store
from retail_price_evidence import build_price_evidence

class ReleaseEvidenceTests(unittest.TestCase):
    def test_public_pages_artifact_excludes_admin_and_internal_files(self):
        root = Path(__file__).resolve().parent
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public"
            result = subprocess.run(
                [sys.executable, "scripts/build_public_pages.py", "--output", str(output)],
                cwd=root,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "index.html").is_file())
            self.assertTrue((output / "coupons.json").is_file())
            self.assertTrue((output / "data" / "seo-pages.json").is_file())
            for forbidden in (
                "admin.html", "validator.html", "python", "reports",
                "outputs", "backups", "phase_e_current.zip",
            ):
                self.assertFalse((output / forbidden).exists(), forbidden)

    def test_verified_under_10000_snapshot_supersedes_unrecoverable_three_result_fixture(self):
        snapshot = json.loads(
            (Path(__file__).resolve().parent / "data" /
             "phase_e_positive_offer_snapshot_2026-10-13-refresh.json")
            .read_text(encoding="utf-8")
        )
        under_10000 = [
            row for row in snapshot["offers"]
            if row["availability"] == "in_stock" and row["price"] <= 10000
        ]
        self.assertEqual(
            [(row["product_id"], row["retailer_product_id"], row["price"])
             for row in under_10000],
            [
                ("cw-mobile-79", "B0GPXTY8V5", 9099.0),
                ("cw-mobile-77", "B0HG9SZ7HD", 9889.0),
            ],
        )
        for row in under_10000:
            self.assertTrue(row["identity_evidence_url"].startswith("https://"))
            self.assertTrue(row["observed_at"])

    def test_frozen_offer_price_requires_exact_asin_and_verified_source(self):
        snapshot = json.loads(
            (Path(__file__).resolve().parent / "data" /
             "phase_e_positive_offer_snapshot_2026-10-13-refresh.json")
            .read_text(encoding="utf-8")
        )
        offer = snapshot["offers"][0]
        candidate = {
            "source": "FROZEN_CATALOGUE_INTEGRATION",
            "asin": offer["retailer_product_id"],
            "frozen_offer": {**offer, "snapshot_id": snapshot["snapshot_id"]},
        }
        evidence = build_price_evidence(candidate)
        self.assertTrue(evidence["verified"])
        self.assertEqual(evidence["price"], offer["price"])
        self.assertEqual(evidence["verified_at"], offer["observed_at"])
        self.assertEqual(evidence["evidence_method"], "amazon_primary_buybox")

        mismatched = dict(candidate, asin="B000000000")
        self.assertFalse(build_price_evidence(mismatched)["verified"])

    def test_admin_review_is_read_only_and_public_api_has_no_mutation_route(self):
        root = Path(__file__).resolve().parent
        admin = (root / "admin.html").read_text(encoding="utf-8").lower()
        self.assertIn("writes_calculated_score: false", admin)
        self.assertNotIn("fetch(", admin)
        self.assertNotIn("xmlhttprequest", admin)
        self.assertNotIn("axios", admin)

        from python.shopping_api import app
        methods_by_route = {
            rule.rule: set(rule.methods)
            for rule in app.url_map.iter_rules()
        }
        mutation_methods = {"POST", "PUT", "PATCH", "DELETE"}
        for route, methods in methods_by_route.items():
            if route.startswith("/api/"):
                self.assertFalse(methods & mutation_methods, route)

    def test_clean_install_and_variant_guard(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(store, 'STORE_PATH', Path(tmp)/'missing.json'):
            data = store.load_store()
            bundled = json.loads(store.BUNDLED_EVIDENCE_PATH.read_text(encoding='utf-8'))['records']
            self.assertGreaterEqual(len(bundled), 11)
            self.assertEqual({r['asin'] for r in data['records']}, {r['asin'] for r in bundled})
            self.assertEqual(len(data['records']), len(bundled))
            for asin, model in [('B0GN24SV22', 'M17e'), ('B0H5BRHZBX', 'M17')]:
                self.assertIsNotNone(store.find_verified_evidence(asin=asin, title=f'Samsung Galaxy {model} 5G 4GB RAM 128GB Storage', store_data=data))
                self.assertIsNone(store.find_verified_evidence(asin=asin, title=f'Samsung Galaxy {model} 5G 6GB RAM 128GB Storage', store_data=data))
            a56 = store.find_verified_evidence(asin='B0H1WY55ZL', title='Samsung Galaxy A56 5G 8GB RAM 128GB Storage', store_data=data)
            self.assertIsNotNone(a56)
            self.assertIsNone(store.find_verified_evidence(asin='B0H1WY55ZL', title='Samsung Galaxy A56 5G 8GB RAM 256GB Storage', store_data=data))
            self.assertIsNotNone(store.find_verified_evidence(asin='B0GPWRYNM1',title='realme C83 5G 4GB RAM 64GB Storage',store_data=data))
            self.assertIsNone(store.find_verified_evidence(asin='B0GPWRYNM1',title='realme C83 5G 6GB RAM 128GB Storage',store_data=data))
            self.assertFalse(store.STORE_PATH.exists())

    def test_newer_runtime_wins_and_original_time_preserved(self):
        baseline=json.loads(store.BUNDLED_EVIDENCE_PATH.read_text(encoding='utf-8'))['records'][0]
        current=copy.deepcopy(baseline);current['saved_at']='2099-01-01T00:00:00+00:00'
        current['features']=['new runtime evidence']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'runtime.json';path.write_text(json.dumps({'records':[current]}))
            with patch.object(store,'STORE_PATH',path):
                rows=store.load_store()['records']
            self.assertEqual(rows[0],current)
            self.assertEqual(json.loads(path.read_text())['records'],[current])

    def test_rejected_bundle_not_loaded(self):
        bad=json.loads(store.BUNDLED_EVIDENCE_PATH.read_text(encoding='utf-8'))
        for row in bad['records']:row['resolver_verified']=False
        with tempfile.TemporaryDirectory() as tmp:
            seed=Path(tmp)/'seed.json';seed.write_text(json.dumps(bad))
            with patch.object(store,'STORE_PATH',Path(tmp)/'missing'),patch.object(store,'BUNDLED_EVIDENCE_PATH',seed):
                self.assertEqual(store.load_store()['records'],[])

if __name__=='__main__':unittest.main()
