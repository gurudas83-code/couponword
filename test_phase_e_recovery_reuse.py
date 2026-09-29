"""Request-scoped recovery reuse must not weaken evidence or freshness gates."""
import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import market_discovery as discovery
import shopping_intelligence_pipeline as pipeline


class RecoveryReuseTests(unittest.TestCase):
    def test_completed_candidate_reuse_requires_same_fresh_exact_price(self):
        url = 'https://www.amazon.in/dp/B0GNZPHXGN'
        price = {'source_url': url, 'verified': True, 'currency': 'INR', 'price': 9999}
        record = {'candidate': {'source_url': url},
                  'profile': {'price': 9999, 'provenance': {'price_evidence': dict(price)}}}
        cache = {'exact-key': {'stored_at': 0, 'record': record}}
        with patch.object(pipeline.time, 'monotonic', return_value=1), \
             patch.object(pipeline, 'get_recent_cached_price', return_value=price) as fresh:
            result = pipeline._reusable_candidate_record(cache, 'exact-key')
            self.assertEqual(result, record)
            result['profile']['price'] = 1
            self.assertEqual(record['profile']['price'], 9999)
            self.assertIsNone(pipeline._reusable_candidate_record(cache, 'different-variant-key'))
            for changed in (None, dict(price, price=10001), dict(price, verified=False),
                            dict(price, source_url='https://www.amazon.in/dp/B0CYQ3WSFP')):
                fresh.return_value = changed
                self.assertIsNone(pipeline._reusable_candidate_record(cache, 'exact-key'))
        with patch.object(pipeline.time, 'monotonic', return_value=61):
            self.assertIsNone(pipeline._reusable_candidate_record(cache, 'exact-key'))

    def test_identical_search_is_reused_without_mutating_provider_rows(self):
        provider = Mock(return_value=[{'title': 'observed', 'asin': 'B0GNZPHXGN'}])
        cache = {}
        first = discovery._request_search(cache, 'fallback', provider, query='mobile under 10000', max_results=20)
        first[0]['title'] = 'mutation'
        second = discovery._request_search(cache, 'fallback', provider, query='mobile under 10000', max_results=20)
        self.assertEqual(second[0]['title'], 'observed')
        self.assertEqual(provider.call_count, 1)
        discovery._request_search(cache, 'fallback', provider, query='mobile under 15000', max_results=20)
        discovery._request_search({}, 'fallback', provider, query='mobile under 10000', max_results=20)
        self.assertEqual(provider.call_count, 3)

    def test_empty_or_expired_search_retries(self):
        provider = Mock(return_value=[])
        cache = {}
        for _ in range(2):
            discovery._request_search(cache, 'fallback', provider, query='phone')
        self.assertEqual(provider.call_count, 2)
        provider.return_value = [{'asin': 'B0GNZPHXGN'}]
        with patch.object(discovery.time, 'monotonic', side_effect=[0, 61, 61]):
            discovery._request_search(cache, 'fallback', provider, query='phone')
            discovery._request_search(cache, 'fallback', provider, query='phone')
        self.assertEqual(provider.call_count, 4)


if __name__ == '__main__':
    unittest.main()
