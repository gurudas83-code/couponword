import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "python"))

import shopping_api
import retail_price_evidence


class SecurityAuditTests(unittest.TestCase):
    def test_pipeline_exception_response_is_generic(self):
        with patch.object(
            shopping_api,
            "run_pipeline",
            side_effect=RuntimeError("INTERNAL_TEST_SENTINEL"),
        ):
            response = shopping_api.app.test_client().get(
                "/api/recommend?q=mobile"
            )

        self.assertEqual(response.status_code, 500)
        body = response.get_json()
        self.assertEqual(
            body,
            {
                "status": "error",
                "error": "Shopping intelligence pipeline failed",
            },
        )
        self.assertNotIn("INTERNAL_TEST_SENTINEL", response.get_data(as_text=True))

    def test_api_rejects_empty_and_oversized_queries(self):
        client = shopping_api.app.test_client()
        self.assertEqual(client.get("/api/recommend").status_code, 400)
        self.assertEqual(
            client.get("/api/recommend?q=" + ("x" * 301)).status_code,
            400,
        )

    def test_frontend_link_guard_and_attribute_escaping_are_present(self):
        source = (ROOT / "app.js").read_text(encoding="utf-8")
        self.assertIn('!["http:", "https:"]', source)
        self.assertIn('escapeHTML(safeLink(deal.link))', source)
        self.assertIn('src="${escapeHTML(imageUrl)}"', source)
        self.assertNotIn('href="${safeLink(deal.link)}"', source)

    def test_public_artifact_builder_excludes_internal_files(self):
        with tempfile.TemporaryDirectory(prefix="cw-public-security-") as directory:
            output = Path(directory) / "public"
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts" / "build_public_pages.py"),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                check=True,
            )

            self.assertIn("public artifact ready", result.stdout)
            forbidden = {
                "admin.html",
                "validator.html",
                "python",
                "reports",
                "outputs",
                "backups",
                "phase_e_current.zip",
            }
            leaked = [
                str(path.relative_to(output))
                for path in output.rglob("*")
                if path.name.lower() in forbidden
            ]
            self.assertEqual(leaked, [])
            self.assertFalse((output / "data" / "retailer_product_registry.json").exists())

    def test_retail_price_redirect_is_rejected_after_following_redirects(self):
        class RedirectedResponse:
            status_code = 200
            url = "https://127.0.0.1/internal"
            text = '{"@type":"Product","offers":{"price":"19999"}}'

        with patch.object(
            retail_price_evidence.requests,
            "get",
            return_value=RedirectedResponse(),
        ):
            result = retail_price_evidence.fetch_structured_price(
                "https://www.amazon.in/dp/B000000000"
            )

        self.assertEqual(result["status"], "rejected")
        self.assertIn("approved HTTPS source", result["reason"])


if __name__ == "__main__":
    unittest.main()
