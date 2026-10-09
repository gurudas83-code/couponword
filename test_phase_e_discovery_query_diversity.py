"""Supplemental discovery must preserve the original query lanes and identities."""
import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import market_discovery as discovery
import shopping_intelligence_pipeline as pipeline
import retail_price_evidence as prices


class QueryDiversityTests(unittest.TestCase):
    def test_fresh_exact_listing_cache_participates_in_budget_ranking(self):
        url = 'https://www.amazon.in/dp/B0GNZPHXGN'
        item = {'url': url, 'asin': 'B0GNZPHXGN'}
        cached = {'source_url': url, 'verified': True, 'currency': 'INR', 'price': 18794,
                  'verified_at': datetime.now(timezone.utc).isoformat()}
        with patch.object(prices, 'load_cache', return_value={prices.normalize_url(url): cached}):
            price = discovery.recent_discovery_price(item)
            self.assertEqual(price, 18794)
            self.assertEqual(discovery.trusted_price_budget_priority({'_recent_verified_price': price}, 20000), 2)
            self.assertEqual(discovery.trusted_price_budget_priority({'_recent_verified_price': price}, 15000), 0)
            self.assertIsNone(discovery.recent_discovery_price(dict(item, asin='B0CYQ3WSFP')))
            cached['source_url'] = 'https://www.amazon.in/dp/B0CYQ3WSFP'
            self.assertIsNone(discovery.recent_discovery_price(item))
            cached['source_url'] = url
            cached['verified_at'] = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
            self.assertIsNone(discovery.recent_discovery_price(item))
            cached.pop('verified_at')
            self.assertIsNone(discovery.recent_discovery_price(item))

    def discover(self, query, supplemental=False):
        with patch.dict(os.environ, {'TAVILY_API_KEY': ''}), \
             patch.object(discovery, 'get_candidate_snapshot', return_value=None), \
             patch.object(discovery, 'get_recent_discovery_cache', return_value=[]), \
             patch.object(discovery, 'get_partial_candidate_memory', return_value=[]), \
             patch.object(discovery, 'fallback_search_channel', return_value=[]):
            return discovery.discover_market(query, max_candidates=15, live_fast=True, supplemental=supplemental)

    def test_recovery_local_lane_matches_bounded_candidate_capacity(self):
        for cap, expected in ((15, 20), (30, 30), (100, 30)):
            with self.subTest(cap=cap), patch.dict(os.environ, {'TAVILY_API_KEY': ''}), \
                 patch.object(discovery, 'get_candidate_snapshot', return_value=None), \
                 patch.object(discovery, 'get_recent_discovery_cache', return_value=[]), \
                 patch.object(discovery, 'get_partial_candidate_memory', return_value=[]), \
                 patch.object(discovery, 'fallback_search_channel', return_value=[]) as search:
                discovery.discover_market('mobile under 120000', max_candidates=cap, live_fast=True)
                commerce = [call.kwargs for call in search.call_args_list
                            if call.kwargs.get('channel') == 'commerce']
                self.assertTrue(commerce)
                self.assertTrue(all(call['max_results'] == expected for call in commerce))

    def test_original_wording_survives_at_all_generic_budgets(self):
        for query in ('mobile under 10000', 'mobile under 15000', 'best phone under 20000',
                      'best battery under ₹20k', 'best battery under ₹30k', 'best battery under ₹50k'):
            with self.subTest(query=query):
                original = self.discover(query)['discovery_queries']
                result = self.discover(query, supplemental=True)['discovery_queries']
                self.assertEqual(result[:2], original)
                self.assertIn(query, result)
                self.assertLessEqual(len(result), 3)

    def test_brand_and_exact_memory_model_lanes_keep_scope(self):
        for query in ('Samsung phone under 20000', 'Samsung Galaxy F36 8GB RAM 256GB under 25000'):
            with self.subTest(query=query):
                result = self.discover(query)
                self.assertEqual(len(result['discovery_queries']), 2)
                self.assertTrue(all('samsung' in q.lower() for q in result['discovery_queries']))
                if 'F36' in query:
                    self.assertIn('f36', result['exact_model_scope']['model_tokens'])
                self.assertEqual(result['discovery_queries'], self.discover(query, True)['discovery_queries'])

    def test_agni_generation_is_an_exact_model_scope(self):
        result = self.discover('Lava Agni 4 5G under 40000')
        self.assertTrue(result['exact_model_scope']['active'])
        self.assertEqual(result['exact_model_scope']['model_tokens'], ['4', 'agni'])
        self.assertIn({'brand': 'agni', 'model': '4'}, result['exact_model_scope']['numeric_brand_pairs'])
        self.assertFalse(self.discover('Lava phone under 40000')['exact_model_scope']['active'])

    def test_distinct_agni_listings_survive_shortened_title_deduplication(self):
        cards = [dict(title='Lava Agni 4 5G (8GB RAM, 256GB Storage, '+colour+')',
                      asin=asin, url='https://www.amazon.in/dp/'+asin,
                      host='www.amazon.in', channel='commerce', query='Lava Agni 4',
                      content='', search_score=1.0)
                 for asin, colour in [('B0FT3DXJM3', 'Lunar Mist'),
                                      ('B0FT3J2W97', 'Phantom Black')]]
        cards.append(dict(cards[0], title='Lava Bold N2 4GB RAM 64GB Storage',
                          asin='B0GL1WGHJX', url='https://www.amazon.in/dp/B0GL1WGHJX'))
        with patch.dict(os.environ, {'TAVILY_API_KEY': ''}), \
             patch.object(discovery, 'get_candidate_snapshot', return_value=None), \
             patch.object(discovery, 'get_recent_discovery_cache', return_value=[]), \
             patch.object(discovery, 'get_partial_candidate_memory', return_value=[]), \
             patch.object(discovery, 'fallback_search_channel', return_value=cards):
            result = discovery.discover_market('Lava Agni 4 5G under 40000', live_fast=True)
        self.assertEqual({x['asin'] for x in result['candidates']},
                         {'B0FT3DXJM3', 'B0FT3J2W97'})
        self.assertEqual(len(result['candidates']), 2)

    def test_retry_preserves_original_variants_and_bounds_unique_reserve(self):
        first = {'candidates': [{'candidate_id': 'market-01', 'asin': 'A', 'title': 'original 4GB 128GB'}]}
        reserve = {'candidates': [
            {'candidate_id': 'market-01', 'asin': 'A', 'title': 'conflicting 8GB 256GB'},
            *[{'candidate_id': 'market-01', 'asin': str(i), 'title': 'observed'} for i in range(30)]
        ]}
        initial_result = {'intent': {'category': 'smartphone', 'budget_max': 20000},
                          'recommendations': [], 'stage_counts': {'eligible': 0}, 'timings': {}}
        final_result = dict(initial_result, recommendations=[{'asin': 'A'}], timings={})
        with patch.object(pipeline, 'discover_market', side_effect=[first, reserve]) as search, \
             patch.object(pipeline, '_run_pipeline_once', side_effect=[initial_result, final_result]) as score:
            result = pipeline.run_pipeline('best phone under 20000', live_fast=True)
        merged = score.call_args.kwargs['_discovery']['candidates']
        self.assertEqual(merged[0], first['candidates'][0])
        self.assertEqual(len(merged), 16)
        self.assertEqual(len({x['candidate_id'] for x in merged}), 16)
        self.assertEqual(len(result['discovery_recovery']['added_listing_ids']), 15)
        self.assertEqual(search.call_count, 2)
        self.assertFalse(score.call_args.kwargs['_save_discovery_memory'])

    def test_no_retry_for_exact_brand_variant_or_enough_results(self):
        for intent, exact, recs in [
            ({'brands': ['Samsung']}, False, []),
            ({'must_have': ['8gb_ram']}, False, []),
            ({}, True, []), ({}, False, [{}, {}, {}]),
        ]:
            result = {'intent': dict(category='smartphone', budget_max=20000, **intent),
                      'recommendations': recs, 'timings': {}}
            with patch.object(pipeline, 'discover_market', return_value={'exact_model_scope': {'active': exact}}) as search, \
                 patch.object(pipeline, '_run_pipeline_once', return_value=result):
                pipeline.run_pipeline('phone under 20000', live_fast=True)
            self.assertEqual(search.call_count, 1)


if __name__ == '__main__':
    unittest.main()
