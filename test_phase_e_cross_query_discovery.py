"""Cross-query discovery never treats stale or unrelated prices as current."""

import ast
import re
import sys
import types
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class CrossQueryDiscoveryTests(unittest.TestCase):
    def test_galaxy_handset_title_gets_samsung_discovery_priority(self):
        source = Path(__file__).parent / "python" / "market_discovery.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "known_brand_from_title")
        ns = {"re": re,
              "normalize_key": lambda title: " ".join(re.findall(r"[a-z0-9]+", title.lower())),
              "BRAND_DOMAINS": {"samsung": ["samsung.com"]}}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
        brand = ns[fn.name]
        self.assertEqual(brand("Galaxy F70e 5G (4GB RAM)"), "samsung")
        self.assertIsNone(brand("Gesto Galaxy Projector"))
        self.assertIsNone(brand("Galaxy Tab A9"))

    def test_live_generic_results_do_not_suppress_cross_query_candidates(self):
        source = Path(__file__).parent / "python" / "market_discovery.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "fallback_search_channel")
        existing = {"asin": "B0HFSRQLH6", "search_title": "realme C100i phone",
                    "product_url": "https://www.amazon.in/dp/B0HFSRQLH6",
                    "search_price_text": "₹15999", "search_price_currency": "INR",
                    "search_price_evidence_method": "amazon_exact_asin_search_card"}
        newcomer = {"asin": "B0GNZSK9HJ", "title": "Galaxy F70e 5G",
                    "url": "https://www.amazon.in/dp/B0GNZSK9HJ",
                    "search_price_text": "₹15959", "provider": "recent_cross_query_exact_asin"}
        ns = {"Any": Any, "clean": lambda v: str(v or "").strip(),
              "local_known_product_fallback": lambda **kw: [],
              "get_recent_discovery_cache": lambda **kw: [],
              "search_asins": lambda *args, **kw: [existing],
              "host_of": lambda url: urlparse(url).hostname,
              "looks_like_product_result": lambda *args: True,
              "cache_discovery_results": lambda **kw: None,
              "parse_query": lambda query: {"brands": [], "budget_max": 20000},
              "recent_cross_query_commerce_results": lambda **kw: [newcomer]}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
        rows = ns[fn.name](query="smartphone under 20000", category="smartphone",
                            include_domains=["amazon.in"], channel="commerce",
                            max_results=20)
        self.assertEqual({r["asin"] for r in rows},
                         {"B0HFSRQLH6", "B0GNZSK9HJ"})

    def test_only_recent_exact_asin_in_budget_can_cross_queries(self):
        source = Path(__file__).parent / "python" / "market_discovery.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        fn = next(node for node in tree.body if isinstance(node, ast.FunctionDef)
                  and node.name == "recent_cross_query_commerce_results")
        now = datetime.now(timezone.utc)
        url = "https://www.amazon.in/dp/B0GNZSK9HJ?tag=example"
        prices = {
            "https://www.amazon.in/dp/B0GNZSK9HJ": {
                "verified": True, "price": 15959,
                "evidence_method": "amazon_exact_asin_search_card",
                "verified_at": now.isoformat(),
            },
        }
        cache = {"smartphone::samsung phone": {
            "saved_at": now.isoformat(), "results": [{
                "provider": "amazon_search_cards", "asin": "B0GNZSK9HJ",
                "title": "Samsung Galaxy F70e 5G 4GB 128GB",
                "url": url, "search_price_text": "₹1",  # untrusted historical field
            }],
        }}
        fake = types.ModuleType("retail_price_evidence")
        fake.CACHE_MAX_AGE_SECONDS = 21600
        fake.load_cache = lambda: prices
        fake.normalize_url = lambda value: value.split("?")[0]
        old = sys.modules.get("retail_price_evidence")
        sys.modules["retail_price_evidence"] = fake
        self.addCleanup(lambda: sys.modules.pop("retail_price_evidence", None)
                        if old is None else sys.modules.__setitem__("retail_price_evidence", old))
        ns = {"Any": Any, "datetime": datetime, "timezone": timezone,
              "re": re, "urlparse": urlparse,
              "DISCOVERY_CACHE_MAX_AGE_SECONDS": 86400,
              "clean": lambda v: " ".join(str(v or "").split()),
              "load_discovery_cache": lambda: cache,
              "looks_like_product_result": lambda title, url, category: True}
        exec(compile(ast.Module(body=[fn], type_ignores=[]), str(source), "exec"), ns)
        find = ns[fn.name]
        found = find(category="smartphone", budget=20000, max_results=10)
        self.assertEqual([x["asin"] for x in found], ["B0GNZSK9HJ"])
        self.assertEqual(found[0]["search_price_text"], "₹15959")
        self.assertEqual(find(category="smartphone", budget=10000, max_results=10), [])
        cache["smartphone::samsung phone"]["saved_at"] = (
            now - timedelta(days=5)).isoformat()
        self.assertEqual(len(find(category="smartphone", budget=20000, max_results=10)), 1)
        cache["smartphone::samsung phone"]["saved_at"] = (
            now - timedelta(days=8)).isoformat()
        self.assertEqual(find(category="smartphone", budget=20000, max_results=10), [])
        cache["smartphone::samsung phone"]["saved_at"] = now.isoformat()
        prices["https://www.amazon.in/dp/B0GNZSK9HJ"]["verified_at"] = (
            now - timedelta(hours=7)).isoformat()
        self.assertEqual(find(category="smartphone", budget=20000, max_results=10), [])


if __name__ == "__main__":
    unittest.main()
