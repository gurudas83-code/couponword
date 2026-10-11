import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python'))
from product_evidence_store import find_verified_evidence
from retailer_product_registry import find_catalogued_mobile_id
from product_fit_signal_builder import smartphone_battery_signal

class SignatureEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.bundle=json.loads((ROOT/'data/phase_e_release_evidence.json').read_text(encoding='utf-8'))
        self.record=next(r for r in self.bundle['records'] if r.get('asin')=='B0GKB38XWZ')

    def test_exact_owner_and_physical_variant(self):
        title='Motorola Signature (Pantone Carbon, 12GB RAM +256GB Storage)'
        self.assertEqual(find_catalogued_mobile_id(retailer_product_id='B0GKB38XWZ',
            candidate_title=title,candidate_brand='Motorola'),'cw-mobile-105')
        self.assertEqual(self.record['variant_signature'],{'ram_gb':'12','storage_gb':'256'})
        self.assertIsNotNone(find_verified_evidence(asin='B0GKB38XWZ',title=title,store_data=self.bundle))
        self.assertIsNone(find_verified_evidence(asin='B0GKB38XWZ',
            title='Motorola Signature 16GB RAM 512GB Storage',store_data=self.bundle))

    def test_manufacturer_claims_have_sources_and_no_regional_support_guess(self):
        specs=self.record['specifications']
        for key,value in specs.items():
            self.assertTrue(value['source_url'].startswith('https://'))
            self.assertTrue(value['observed_at'])
            self.assertIn('identity_match',value)
        self.assertNotIn('software_support',specs)
        evidence='; '.join(str(v['value']) for v in specs.values())
        self.assertNotIn('52 hours',evidence)
        self.assertNotIn('7 years',evidence)
        self.assertNotEqual(smartphone_battery_signal(evidence)['basis'],'capacity_proxy')

if __name__=='__main__':
    unittest.main()
