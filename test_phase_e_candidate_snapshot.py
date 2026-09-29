"""Offline regression for repeat mobile discovery and price provenance."""

import ast
import json
import os
import re
import tempfile
import time
import unittest
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SOURCE = Path(__file__).parent / "python" / "market_discovery.py"
FUNCTIONS = {
    "clean", "normalize_key", "discovery_cache_key",
    "candidate_snapshot_key", "load_discovery_cache",
    "save_discovery_cache", "get_candidate_snapshot",
    "save_candidate_snapshot", "discover_market",
    "trusted_price_budget_priority", "category_accessory_gate", "_request_search",
}


class CandidateSnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        tree = ast.parse(SOURCE.read_text(encoding="utf-8"))
        functions = [
            node for node in tree.body
            if isinstance(node, ast.FunctionDef) and node.name in FUNCTIONS
        ]
        self.ns = {
            "Any": Any, "Path": Path, "json": json, "re": re,
            "time": time, "deepcopy": deepcopy,
            "datetime": datetime, "timezone": timezone,
            "DISCOVERY_CACHE_PATH": Path(self.temp.name) / "discovery.json",
            "DISCOVERY_CACHE_MAX_AGE_SECONDS": 86400,
            "get_recent_cached_price": lambda url: None,
            "parse_query": lambda query: {"category": "smartphone"},
            "build_discovery_queries": lambda query, intent: [
                "smartphone under 20000 india", "smartphone under 20000 india buy"
            ],
        }
        exec(compile(ast.Module(body=functions, type_ignores=[]), str(SOURCE), "exec"), self.ns)

    def test_old_scoring_snapshot_does_not_pin_new_battery_ranking(self):
        legacy_key = (
            '__candidate_snapshot__::'
            + self.ns['discovery_cache_key']('best battery under 20000', 'smartphone')
            + '::15'
        )
        self.ns['save_discovery_cache']({legacy_key: {
            'saved_at': datetime.now(timezone.utc).isoformat(),
            'candidates': self.sample_pool(),
        }})
        self.assertIsNone(self.ns['get_candidate_snapshot'](
            query='best battery under 20000', category='smartphone', max_candidates=15,
        ))
        self.ns['save_candidate_snapshot'](
            query='best battery under 20000', category='smartphone',
            candidates=self.sample_pool(), max_candidates=15,
        )
        self.assertIsNotNone(self.ns['get_candidate_snapshot'](
            query='best battery under 20000', category='smartphone', max_candidates=15,
        ))
        self.assertIn(legacy_key, self.ns['load_discovery_cache']())

    def sample_pool(self):
        return [{
            "candidate_id": f"market-{n:02d}", "title": f"Phone {n}",
            "source_url": f"https://www.amazon.in/dp/B000000{n:02d}",
            "asin": f"B000000{n:02d}", "search_price_text": "₹19,999",
            "search_price_evidence_method": "amazon_exact_asin_search_card",
        } for n in range(1, 16)]

    def test_pins_successful_pool_and_only_refreshes_exact_asin_price(self):
        pool = self.sample_pool()
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=pool, max_candidates=15,
        )
        # An unrelated product with a cheaper price is no reason to switch
        # the successful candidate set on a repeat request.
        self.ns["search_asins"] = lambda query, max_cards: [
            {"asin": "B00000001", "search_price_text": "₹18,999",
             "search_price_evidence_method": "amazon_exact_asin_search_card"},
            {"asin": "B00000002", "search_price_text": "₹18,998",
             "search_price_evidence_method": "amazon_exact_asin_search_card"},
            {"asin": "B00000003", "search_price_text": "₹18,997",
             "search_price_evidence_method": "amazon_exact_asin_search_card"},
            {"asin": "B00000999", "search_price_text": "₹9,999",
             "search_price_evidence_method": "amazon_exact_asin_search_card"},
        ]
        result = self.ns["discover_market"](
            "best phone under 20000", max_candidates=15, live_fast=True,
        )
        self.assertEqual([x["asin"] for x in result["candidates"]],
                         [x["asin"] for x in pool])
        self.assertEqual(result["candidates"][0]["search_price_text"], "₹18,999")
        self.assertEqual(result["candidates"][3]["search_price_text"], "")
        self.assertEqual(result["candidate_snapshot"]["fresh_price_asins"], 3)
        # Returned fresh evidence must not get written back as persistent
        # price evidence in the identity snapshot.
        again = self.ns["get_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            max_candidates=15,
        )
        self.assertEqual(again["candidates"][0]["search_price_text"], "")

    def test_expired_snapshot_cannot_pin_an_old_market(self):
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=self.sample_pool(), max_candidates=15,
        )
        cache = self.ns["load_discovery_cache"]()
        entry = next(v for k, v in cache.items() if k.startswith("__candidate_snapshot__"))
        entry["saved_at"] = (datetime.now(timezone.utc) - timedelta(days=2)).isoformat()
        self.ns["save_discovery_cache"](cache)
        self.assertIsNone(self.ns["get_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            max_candidates=15,
        ))

    def test_zero_fresh_prices_researches_instead_of_pinning_empty_pool(self):
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=self.sample_pool(), max_candidates=15,
        )
        self.ns["search_asins"] = lambda query, max_cards: []
        self.ns["get_recent_discovery_cache"] = lambda **kwargs: []
        self.ns["os"] = os
        self.ns["COMMERCE_DOMAINS"] = []
        # The AST fixture executes selected functions without importing
        # TavilyClient. Keep this branch offline even if the developer's
        # environment has TAVILY_API_KEY set.
        self.ns["TavilyClient"] = lambda **kwargs: None

        class ReachedLiveDiscovery(Exception):
            pass

        def live_discovery(**kwargs):
            raise ReachedLiveDiscovery

        self.ns["fallback_search_channel"] = live_discovery
        with self.assertRaises(ReachedLiveDiscovery):
            self.ns["discover_market"](
                "best phone under 20000", max_candidates=15, live_fast=True,
            )

    def test_recent_verified_price_keeps_pinned_pool_when_cards_fail(self):
        pool = self.sample_pool()
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=pool, max_candidates=15,
        )
        self.ns["search_asins"] = lambda query, max_cards: []
        cached_urls = {item["source_url"] for item in pool[:3]}
        self.ns["get_recent_cached_price"] = lambda url: (
            {"price": 19000} if url in cached_urls else None
        )
        result = self.ns["discover_market"](
            "best phone under 20000", max_candidates=15, live_fast=True,
        )
        self.assertEqual(result["candidate_snapshot"]["status"], "reused_verified_pool")
        self.assertEqual(result["candidate_snapshot"]["fresh_price_asins"], 0)
        self.assertEqual(result["candidates"][0]["search_price_text"], "")

    def test_replacement_is_explicit_and_still_strips_price(self):
        original = self.sample_pool()
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=original, max_candidates=15,
        )
        changed = [dict(item) for item in original]
        changed[0]["asin"] = "B00000999"
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=changed, max_candidates=15,
        )
        self.assertEqual(self.ns["get_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            max_candidates=15,
        )["candidates"][0]["asin"], original[0]["asin"])
        self.ns["save_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            candidates=changed, max_candidates=15, replace=True,
        )
        refreshed = self.ns["get_candidate_snapshot"](
            query="best phone under 20000", category="smartphone",
            max_candidates=15,
        )
        self.assertEqual(refreshed["candidates"][0]["asin"], "B00000999")
        self.assertEqual(refreshed["candidates"][0]["search_price_text"], "")

    def test_budget_ranking_uses_only_current_exact_asin_card_prices(self):
        priority = self.ns["trusted_price_budget_priority"]
        card = {"search_price_evidence_method": "amazon_exact_asin_search_card"}
        self.assertEqual(priority({**card, "search_price_text": "₹9,999"}, 10000), 2)
        self.assertEqual(priority({**card, "search_price_text": "₹19,999"}, 10000), 0)
        self.assertEqual(priority({**card, "search_price_text": "Rs. 9,999"}, 10000), 2)
        self.assertEqual(priority({"search_price_text": "₹9,999"}, 10000), 1)
        self.assertEqual(priority({**card, "search_price_text": "₹9,999 onwards"}, 10000), 1)

    def test_smartphone_discovery_rejects_tripod_adapter(self):
        gate = self.ns["category_accessory_gate"]
        self.assertEqual(gate(
            "Action Pro Made in India Universal 360 Tripod Adapter",
            "smartphone",
        )["status"], "reject")
        self.assertEqual(gate("Redmi A7 Pro 4G smartphone", "smartphone")["status"], "pass")


if __name__ == "__main__":
    unittest.main()
