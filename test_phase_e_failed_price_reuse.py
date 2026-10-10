"""A failed exact-listing lookup is reused only inside its live evaluation."""
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, Mock

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import shopping_intelligence_pipeline as pipeline


class FailedPriceReuseTests(unittest.TestCase):
    url = 'https://www.amazon.in/dp/B0GNZPHXGN'

    def profile(self, evidence, status='retailer_identity_verified'):
        return pipeline.runtime_profile_from_extraction(
            candidate={'source_url': self.url, 'title': 'Frozen fixture'},
            identity={}, resolved={'status': status, 'commerce_evidence': evidence},
            extraction={}, intent={})

    def test_failed_exact_lookup_is_not_retried_or_promoted(self):
        evidence = {'source_url': self.url, 'verified': False, 'price': 9999,
                    'status': 'unavailable', 'reason': 'timeout'}
        with patch.object(pipeline, 'build_price_evidence') as lookup:
            profile = self.profile(evidence)
        lookup.assert_not_called()
        self.assertIsNone(profile['price'])
        self.assertFalse(profile['provenance']['price_evidence']['verified'])

    def test_other_listing_missing_result_and_deep_mode_retry(self):
        for evidence, status in [
            ({'source_url': self.url + '/other', 'verified': False}, 'retailer_identity_verified'),
            ({'source_url': self.url}, 'retailer_identity_verified'),
            (None, 'retailer_identity_verified'),
            ({'source_url': self.url, 'verified': False}, 'official_verified'),
        ]:
            with self.subTest(evidence=evidence, status=status), patch.object(
                pipeline, 'build_price_evidence', return_value={'verified': False}
            ) as lookup:
                self.assertIsNone(self.profile(evidence, status)['price'])
                lookup.assert_called_once()

    def test_new_evaluation_can_verify_price_after_failure(self):
        # There is no negative cache between requests: a new resolver result
        # is consumed independently, preserving the later verified price.
        with patch.object(pipeline, 'build_price_evidence') as lookup:
            failed = self.profile({'source_url': self.url, 'verified': False})
            successful = self.profile({'source_url': self.url, 'verified': True, 'price': 9999})
        lookup.assert_not_called()
        self.assertIsNone(failed['price'])
        self.assertEqual(successful['price'], 9999)

    def test_rejected_identity_never_fetches_price(self):
        candidate = {'candidate_id': 'fixture', 'title': 'Samsung Galaxy F36 5G 6GB RAM 128GB Storage',
                     'source_url': self.url}
        identity = {'brand': 'Samsung', 'model': 'Galaxy F36 5G',
                    'search_name': candidate['title']}
        comparison = Mock()
        comparison.to_dict.return_value = {'decision': 'reject', 'score': 0, 'reasons': ['wrong model']}
        with patch.object(pipeline, 'call_build_identity', return_value=identity), \
             patch.object(pipeline, 'compare_identity', return_value=comparison), \
             patch.object(pipeline, 'build_price_evidence') as lookup:
            result = pipeline._run_pipeline_once('mobile under 20000', live_fast=True,
                _discovery={'candidates': [candidate]}, _save_discovery_memory=False)
        lookup.assert_not_called()
        self.assertEqual(result['recommendations'], [])
        self.assertEqual(result['failures'][0]['stage'], 'live_commerce_verification')


if __name__ == '__main__':
    unittest.main()
