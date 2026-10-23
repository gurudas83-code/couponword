import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent
CSS = (ROOT / "style.css").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")


class Issue14ResponsiveStaticTests(unittest.TestCase):
    def test_long_deal_text_is_not_hard_clamped(self):
        self.assertNotIn("-webkit-line-clamp:3", CSS.split(".deal-title", 1)[1].split(".discount", 1)[0])
        self.assertIn(".deal-title", CSS)
        self.assertIn("overflow-wrap:anywhere", CSS)
        self.assertIn("word-break:break-word", CSS)

    def test_metadata_and_code_rows_can_wrap(self):
        self.assertIn(".deal-meta{display:flex", CSS)
        self.assertIn("flex-wrap:wrap;min-width:0", CSS)
        self.assertIn(".code-row{display:flex", CSS)
        self.assertIn("flex-wrap:wrap", CSS)

    def test_ai_result_text_is_safe_for_long_fixture_content(self):
        self.assertIn(".ai-result-card h3", CSS)
        self.assertIn(".ai-result-card p", CSS)
        self.assertGreaterEqual(CSS.count("overflow-wrap:anywhere"), 4)

    def test_required_responsive_breakpoints_exist(self):
        for breakpoint in ("980px", "850px", "720px", "540px", "520px"):
            self.assertIn(breakpoint, CSS)

    def test_no_global_overflow_hiding_patch(self):
        self.assertNotIn("overflow-x:hidden", CSS.replace(" ", ""))

    def test_existing_frontend_and_cta_contract_remain_present(self):
        self.assertIn("heroSearch", APP)
        self.assertIn("searchInput", APP)
        self.assertIn("shoppingBrainCard", CSS)
        self.assertIn("offerCtaLabel", APP)
        self.assertIn("Check latest price", APP)


if __name__ == "__main__":
    unittest.main()
