import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python'))
import product_evidence_store as store

class ReleaseEvidenceTests(unittest.TestCase):
    def test_clean_install_and_variant_guard(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(store, 'STORE_PATH', Path(tmp)/'missing.json'):
            data = store.load_store()
            self.assertEqual(len(data['records']), 9)
            a56 = store.find_verified_evidence(asin='B0H1WY55ZL', title='Samsung Galaxy A56 5G 8GB RAM 128GB Storage', store_data=data)
            self.assertIsNotNone(a56)
            self.assertIsNone(store.find_verified_evidence(asin='B0H1WY55ZL', title='Samsung Galaxy A56 5G 8GB RAM 256GB Storage', store_data=data))
            self.assertIsNotNone(store.find_verified_evidence(asin='B0GPWRYNM1',title='realme C83 5G 4GB RAM 64GB Storage',store_data=data))
            self.assertIsNone(store.find_verified_evidence(asin='B0GPWRYNM1',title='realme C83 5G 6GB RAM 128GB Storage',store_data=data))
            self.assertFalse(store.STORE_PATH.exists())

    def test_newer_runtime_wins_and_original_time_preserved(self):
        baseline=json.loads(store.BUNDLED_EVIDENCE_PATH.read_text())['records'][0]
        current=copy.deepcopy(baseline);current['saved_at']='2099-01-01T00:00:00+00:00'
        current['features']=['new runtime evidence']
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'runtime.json';path.write_text(json.dumps({'records':[current]}))
            with patch.object(store,'STORE_PATH',path):
                rows=store.load_store()['records']
            self.assertEqual(rows[0],current)
            self.assertEqual(json.loads(path.read_text())['records'],[current])

    def test_rejected_bundle_not_loaded(self):
        bad=json.loads(store.BUNDLED_EVIDENCE_PATH.read_text())
        for row in bad['records']:row['resolver_verified']=False
        with tempfile.TemporaryDirectory() as tmp:
            seed=Path(tmp)/'seed.json';seed.write_text(json.dumps(bad))
            with patch.object(store,'STORE_PATH',Path(tmp)/'missing'),patch.object(store,'BUNDLED_EVIDENCE_PATH',seed):
                self.assertEqual(store.load_store()['records'],[])

if __name__=='__main__':unittest.main()
