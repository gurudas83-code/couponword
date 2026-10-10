"""Workbook research rows must not become trusted prices or product identities."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'python'))
from mobile_intelligence_builder import load_universe_seed, seed_from_dict, assess_seed
from product_evidence_store import extraction_is_cacheable


class WorkbookImportTests(unittest.TestCase):
    def test_all_source_rows_preserve_unknown_identity_and_price(self):
        payload = load_universe_seed(ROOT / 'data/india_smartphone_specifications_2023_2026.json')
        rows = payload['products']
        self.assertEqual(payload['product_count'], 80)
        self.assertEqual({x['workbook_row'] for x in rows}, set(range(2, 82)))
        for row in rows:
            with self.subTest(model=row['model']):
                self.assertFalse(row['publish_eligible'])
                self.assertEqual(row['canonical_product_id'], '')
                for key in ('ram_gb', 'storage_gb', 'current_price', 'retailer_product_id', 'launch_date'):
                    self.assertIsNone(row[key])
                self.assertEqual(assess_seed(seed_from_dict(row)).status, 'NEEDS_IDENTITY')
                self.assertFalse(extraction_is_cacheable(row)[0])
                self.assertFalse(row['resolver_verified'])
                for spec in row['specifications'].values():
                    self.assertTrue({'value', 'label', 'source', 'confidence'} <= spec.keys())
                    self.assertEqual(spec['source'], 'user_workbook_unverified')
                    self.assertEqual(spec['confidence'], 0)

    def test_additions_are_discovery_seeds_and_catalogued_models_are_not_readded(self):
        universe = load_universe_seed()
        self.assertEqual(universe['product_count'], len(universe['products']))
        additions = [x for x in universe['products'] if x.get('source') == 'user_workbook_2026_10_10']
        self.assertEqual(len(additions), 61)
        self.assertEqual(len({x['workbook_row'] for x in additions}), 61)
        for row in additions:
            self.assertFalse(row['publish_eligible'])
            self.assertNotIn(row['model'], ('Galaxy A36 5G', 'Galaxy A56 5G'))
            self.assertFalse(row['existing_catalogue_source_ids'])
            self.assertEqual(row['source_class'], 'unverified_research_candidate')
