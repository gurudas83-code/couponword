"""Synthetic offers only; never writes a real evidence store or calls retailers."""
import copy
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
from amazon_evidence_collector import AmazonEvidenceCollector
from flipkart_evidence_collector import FlipkartEvidenceCollector
from canonical_product import CanonicalProduct
from retailer_contract import RetailerOffer
from offer_normalizer import normalize_offer
from price_evidence import PriceEvidence
from evidence_validator import validate_price_evidence
from evidence_offer_updater import apply_price_evidence
from evidence_freshness import is_offer_fresh
from multi_retailer_engine import compare_offers
from multi_retailer_orchestrator import MultiRetailerOrchestrator
from retailer_evidence_collector_manager import RetailerEvidenceCollectorManager
import retailer_offer_store as store

NOW = datetime(2026, 10, 21, 12, tzinfo=timezone.utc)
ASIN = 'B000000001'
URL = 'https://www.amazon.in/dp/' + ASIN

def offer(**changes):
    values = dict(product_id='synthetic-phone', retailer='amazon', retailer_product_id=ASIN,
                  brand='Test', model='Test Phone', variant='8GB/128GB', price=12000,
                  availability='in_stock', product_url=URL, source='synthetic-authorized-provider',
                  last_checked=NOW.isoformat(), confidence=1)
    values.update(changes)
    return RetailerOffer(**values)

def evidence(**changes):
    values = dict(product_id='synthetic-phone', retailer='amazon', retailer_product_id=ASIN,
                  price=12000, availability='in_stock', source_url=URL,
                  source_type='synthetic-authorized-provider', observed_at=NOW.isoformat(), confidence=1)
    values.update(changes)
    return PriceEvidence(**values)

class FreshnessTests(unittest.TestCase):
    def test_six_hour_boundary_and_invalid_times(self):
        with patch('evidence_freshness.datetime') as clock:
            clock.now.return_value = NOW
            clock.fromisoformat.side_effect = datetime.fromisoformat
            for stamp, expected in [(NOW.isoformat(), True),
                    ((NOW-timedelta(hours=6)).isoformat(), True),
                    ((NOW-timedelta(hours=6,seconds=1)).isoformat(), False),
                    ((NOW+timedelta(seconds=1)).isoformat(), False),
                    ('2026-10-21T11:00:00', False), ('bad', False), ('', False)]:
                with self.subTest(stamp=stamp):
                    self.assertEqual(is_offer_fresh(offer(last_checked=stamp)), expected)

    def test_normalizer_preserves_original_observation_and_metadata(self):
        raw = offer(last_checked=(NOW-timedelta(days=2)).isoformat()).to_dict()
        raw['metadata'] = {'evidence_observed_at': raw['last_checked'], 'proof': 'synthetic'}
        before = copy.deepcopy(raw)
        result = normalize_offer('amazon', raw)
        self.assertEqual(result.last_checked, raw['last_checked'])
        self.assertEqual(result.metadata['evidence_observed_at'], raw['last_checked'])
        self.assertEqual(result.metadata['proof'], 'synthetic')
        self.assertEqual(raw, before)

    def test_normalizer_does_not_invent_observation(self):
        raw = offer().to_dict()
        del raw['last_checked']
        self.assertEqual(normalize_offer('amazon', raw).last_checked, '')

    def test_evidence_missing_time_stays_missing_and_is_rejected(self):
        item = evidence(observed_at='')
        self.assertEqual(item.observed_at, '')
        self.assertIn('invalid_observation_time', validate_price_evidence(offer(), item)[1])

    def test_observation_metadata_precedes_serialization_time(self):
        item = offer(metadata={'evidence_observed_at': (NOW-timedelta(days=2)).isoformat()})
        self.assertFalse(is_offer_fresh(item))

class ProviderTests(unittest.TestCase):
    def setUp(self):
        self.product = CanonicalProduct('synthetic-phone','Test Phone 8GB/128GB','Test','Test Phone','8GB/128GB')

    def provider(self, **overrides):
        data = dict(asin=ASIN, retailer_product_id=ASIN, price=12000, mrp=None,
                    availability='in_stock', observed_at=(NOW-timedelta(days=2)).isoformat(),
                    source_url=URL, source='synthetic-authorized-provider')
        data.update(overrides)
        return SimpleNamespace(api_available=True, get_product=Mock(return_value=SimpleNamespace(**data)))

    def test_amazon_preserves_time(self):
        provider = self.provider()
        item = AmazonEvidenceCollector(provider).collect(self.product, offer())
        self.assertEqual(item.observed_at, provider.get_product.return_value.observed_at)

    def test_amazon_rejects_wrong_response_asin(self):
        self.assertIsNone(AmazonEvidenceCollector(self.provider(asin='B000000002')).collect(self.product, offer()))

    def test_amazon_missing_timestamp_does_not_become_live(self):
        self.assertIsNone(AmazonEvidenceCollector(self.provider(observed_at='')).collect(self.product, offer()))

    def test_amazon_unavailable_provider_is_not_called(self):
        provider = self.provider()
        provider.api_available = False
        self.assertIsNone(AmazonEvidenceCollector(provider).collect(self.product, offer()))
        provider.get_product.assert_not_called()

    def test_flipkart_preserves_time(self):
        provider = self.provider(source_url='https://www.flipkart.com/test/p/item?pid='+ASIN)
        item = FlipkartEvidenceCollector(provider).collect(self.product, offer(retailer='flipkart'))
        self.assertEqual(item.observed_at, provider.get_product.return_value.observed_at)

    def test_flipkart_no_provider_never_fetches_public_html(self):
        with patch.object(FlipkartEvidenceCollector, '_collect_from_product_page') as fetch:
            self.assertIsNone(FlipkartEvidenceCollector().collect(self.product, offer(retailer='flipkart')))
            fetch.assert_not_called()

    def test_flipkart_invalid_provider_response_never_falls_back(self):
        for changes in ({'observed_at':''}, {'retailer_product_id':'WRONG'}, {'price':None}):
            with self.subTest(changes=changes), patch.object(FlipkartEvidenceCollector, '_collect_from_product_page') as fetch:
                self.assertIsNone(FlipkartEvidenceCollector(self.provider(**changes)).collect(self.product, offer(retailer='flipkart')))
                fetch.assert_not_called()

    def test_provider_failures_are_not_retried_as_scraping(self):
        for error in (TimeoutError('synthetic'), PermissionError('403 synthetic'), RuntimeError('429 synthetic')):
            provider = self.provider()
            provider.get_product.side_effect = error
            with self.subTest(error=type(error).__name__), patch.object(FlipkartEvidenceCollector, '_collect_from_product_page') as fetch:
                with self.assertRaises(type(error)):
                    FlipkartEvidenceCollector(provider).collect(self.product, offer(retailer='flipkart'))
                provider.get_product.assert_called_once()
                fetch.assert_not_called()

class PersistenceTests(unittest.TestCase):
    def test_failed_disk_replace_preserves_previous_observation(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(store,'OFFERS_DB',Path(directory)/'offers.json'):
            store.add_verified_offer(offer())
            saved=store.OFFERS_DB.read_bytes()
            with patch.object(store.os,'replace',side_effect=OSError('synthetic disk failure')):
                with self.assertRaises(OSError):
                    store.add_verified_offer(offer(price=11000))
            self.assertEqual(store.OFFERS_DB.read_bytes(),saved)
            self.assertEqual(list(Path(directory).glob('*.tmp')),[])

    def test_missing_and_nonfinite_price_is_rejected(self):
        for price in (None, float('nan'), float('inf')):
            with self.subTest(price=price):
                self.assertIn('invalid_price', validate_price_evidence(offer(), evidence(price=price))[1])

    def test_missing_persistence_and_affiliate_link_do_not_create_an_offer(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(store,'OFFERS_DB',Path(directory)/'offers.json'):
            self.assertIsNone(store.find_fresh_verified_offer(product_id='synthetic-phone',now=NOW))
            store.add_verified_offer(offer(price=None,availability='unknown',affiliate_url=URL+'?tag=synthetic'))
            self.assertIsNone(store.find_fresh_verified_offer(product_id='synthetic-phone',now=NOW))

    def test_nonfinite_stored_price_cannot_become_current(self):
        for price in (float('nan'),float('inf')):
            with self.subTest(price=price), patch.object(store,'load_offer_database',return_value={'offers':[offer(price=price).to_dict()]}):
                self.assertIsNone(store.find_fresh_verified_offer(product_id='synthetic-phone',now=NOW))

    def test_real_orchestrator_preserves_good_record_on_invalid_refresh(self):
        product=CanonicalProduct('synthetic-phone','Test Phone 8GB/128GB','Test','Test Phone','8GB/128GB')
        provider=SimpleNamespace(api_available=True,get_product=Mock(return_value=SimpleNamespace(
            asin=ASIN,price=12000,mrp=None,availability='in_stock',observed_at=NOW.isoformat(),source='synthetic')))
        manager=SimpleNamespace(collect_offers=Mock(return_value=[offer(price=None,availability='unknown')]))
        engine=MultiRetailerOrchestrator(manager,RetailerEvidenceCollectorManager([AmazonEvidenceCollector(provider)]))
        with tempfile.TemporaryDirectory() as directory, patch.object(store,'OFFERS_DB',Path(directory)/'offers.json'):
            engine.run(product,write=True)
            saved=store.OFFERS_DB.read_bytes()
            self.assertIsNotNone(store.find_fresh_verified_offer(product_id='synthetic-phone',variant='8GB/128GB',now=NOW))
            provider.get_product.assert_called_once()
            provider.get_product.return_value.price=None
            engine.run(product,write=True,seed_evidence=[evidence(price=None)])
            self.assertEqual(store.OFFERS_DB.read_bytes(),saved)

    def test_comparison_rejects_old_or_future_offer_after_normalization(self):
        with patch('evidence_freshness.datetime') as clock:
            clock.now.return_value=NOW
            clock.fromisoformat.side_effect=datetime.fromisoformat
            for stamp in ((NOW-timedelta(hours=7)).isoformat(),(NOW+timedelta(hours=1)).isoformat()):
                item=normalize_offer('amazon',offer(last_checked=stamp).to_dict())
                result=compare_offers([item])
                self.assertEqual(result['comparable_offer_count'],0)
                self.assertIsNone(result['best_offer'])

    def test_positive_roundtrip_and_all_existing_stock_variant_expiry_gates(self):
        with tempfile.TemporaryDirectory() as directory, patch.object(store,'OFFERS_DB',Path(directory)/'offers.json'):
            with patch('evidence_validator.datetime') as clock:
                clock.now.return_value=NOW
                clock.fromisoformat.side_effect=datetime.fromisoformat
                self.assertTrue(validate_price_evidence(offer(), evidence())[0])
            updated=apply_price_evidence(offer(), evidence())
            store.add_verified_offer(updated)
            store.add_verified_offer(updated)
            self.assertEqual(len(store.load_offer_database()['offers']), 1)
            for variant, when, expected in [('8GB/128GB',NOW,True), ('12GB/256GB',NOW,False),
                    ('8GB/128GB',NOW+timedelta(hours=6,seconds=1),False)]:
                self.assertEqual(store.find_fresh_verified_offer(product_id='synthetic-phone',brand='Test',model='Test Phone',variant=variant,now=when) is not None,expected)
            self.assertEqual(store.load_offer_database()['offers'][0]['metadata']['evidence_observed_at'],NOW.isoformat())
            for state in ['unknown','out_of_stock']:
                store.add_verified_offer(apply_price_evidence(offer(), evidence(availability=state)))
                self.assertIsNone(store.find_fresh_verified_offer(product_id='synthetic-phone',variant='8GB/128GB',now=NOW))

    def test_invalid_provider_identity_and_time_rejected(self):
        for changes, code in [({'retailer_product_id':'WRONG'},'retailer_product_id_mismatch'),
                ({'observed_at':'bad'},'invalid_observation_time'),
                ({'observed_at':(NOW+timedelta(days=10000)).isoformat()},'future_observation_time')]:
            with self.subTest(changes=changes):
                self.assertIn(code,validate_price_evidence(offer(),evidence(**changes))[1])

if __name__ == '__main__':
    unittest.main()
