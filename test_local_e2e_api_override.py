"""Focused regression checks for the loopback-only frontend API override."""

from pathlib import Path
import unittest


APP = (Path(__file__).resolve().parent / "app.js").read_text(encoding="utf-8")
INDEX = (Path(__file__).resolve().parent / "index.html").read_text(encoding="utf-8")


class LocalE2EApiOverrideTests(unittest.TestCase):
    def test_loopback_hosts_use_existing_local_backend_route(self):
        self.assertIn('"http://127.0.0.1:8000"', APP)
        self.assertIn('window.location.hostname', APP)
        self.assertIn('"/api/recommend?q="', APP)

    def test_published_hosts_keep_render_backend(self):
        self.assertIn('"https://couponword.onrender.com"', APP)

    def test_no_second_recommendation_client_was_added(self):
        self.assertEqual(APP.count('"/api/recommend?q="'), 1)

    def test_frontend_bundle_version_changes_with_local_override(self):
        self.assertIn('/app.js?v=14', INDEX)


if __name__ == "__main__":
    unittest.main()
