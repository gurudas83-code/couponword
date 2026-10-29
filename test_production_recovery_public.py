from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class ProductionRecoveryPublicTests(unittest.TestCase):
    def test_public_artifact_contains_guides_and_safe_preview(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "public"
            result = subprocess.run(
                [sys.executable, "scripts/build_public_pages.py", "--output", str(output)],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue((output / "guides/index.html").is_file())
            preview = json.loads((output / "data/mobile_research_preview.json").read_text(encoding="utf-8"))
            self.assertEqual(len(preview["products"]), 10)
            self.assertTrue(all(not row["commerce"]["purchase_cta_eligible"] for row in preview["products"]))

    def test_homepage_exposes_research_and_accessibility_paths(self):
        html = (ROOT / "index.html").read_text(encoding="utf-8")
        self.assertIn("Compare 4 Verified Smartphones", html)
        self.assertIn('href="#main-content"', html)
        self.assertIn('id="mobileNav"', html)
        self.assertIn('og:image', html)

    def test_deal_wall_is_fail_closed(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("deal.active === true", app)
        self.assertIn("deal.cta_eligible === true", app)
        self.assertIn("DEAL_MAX_AGE_MS", app)
        self.assertIn("Verified offers are currently unavailable.", app)
        self.assertNotIn("Date.now();", app.split("DEALS_FILE", 1)[0])

    def test_recommendation_has_timeout_retry_and_stale_guard(self):
        app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn("AbortController", app)
        self.assertIn("RECOMMENDATION_TIMEOUT_MS", app)
        self.assertIn("data-retry-recommendation", app)
        self.assertIn("requestId !== recommendationRequestId", app)

    def test_backend_health_import_is_lazy_and_render_compatible(self):
        sys.path.insert(0, str(ROOT / "python"))
        import shopping_api

        self.assertIsNone(shopping_api.run_pipeline)
        response = shopping_api.app.test_client().get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")
        source = (ROOT / "python/shopping_api.py").read_text(encoding="utf-8")
        self.assertIn('host="0.0.0.0"', source)
        self.assertIn('os.environ.get("PORT", "8000")', source)


if __name__ == "__main__":
    unittest.main()
