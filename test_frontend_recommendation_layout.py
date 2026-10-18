import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent


class FrontendRecommendationLayoutTests(unittest.TestCase):
    def setUp(self):
        self.app = (ROOT / "app.js").read_text(encoding="utf-8")
        self.css = (ROOT / "style.css").read_text(encoding="utf-8")

    def test_each_recommendation_section_owns_a_card_grid(self):
        self.assertGreaterEqual(self.app.count('class="ai-section-card-grid"'), 2)
        self.assertIn('<div class="ai-section-card-grid">${primaryCards}</div>', self.app)
        self.assertIn('<div class="ai-section-card-grid">${valueCards}</div>', self.app)
        self.assertIn("${primaryCards || `<p class=\"card-note\">", self.app)

    def test_outer_wrapper_is_content_sized_and_sections_do_not_stretch(self):
        self.assertRegex(
            self.css,
            r"#shoppingBrainCard\s*\{\s*display:block;\s*\}",
        )
        self.assertRegex(self.css, r"\.ai-result-card\s*\{[^}]*min-height:0;[^}]*height:auto;")
        self.assertRegex(
            self.css,
            r"\.ai-section-card-grid\s*\{[^}]*grid-template-columns:repeat\(2,minmax\(340px,1fr\)\)",
        )

    def test_mobile_uses_one_column_and_desktop_cards_have_a_readable_minimum(self):
        mobile_rule = re.search(
            r"@media \(max-width:850px\)\{\s*\.ai-section-card-grid\s*\{\s*grid-template-columns:1fr;",
            self.css,
        )
        self.assertIsNotNone(mobile_rule)
        self.assertNotIn("position:absolute", self.css[self.css.find(".ai-result-card{"):self.css.find(".ai-recommendation-section")])


if __name__ == "__main__":
    unittest.main()
