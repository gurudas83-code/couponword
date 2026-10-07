import copy,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'python'))
from mobile_page_evidence import render_mobile_evidence
class MobilePageEvidenceTests(unittest.TestCase):
    def product(self):
        return next(p for p in json.loads((ROOT/'coupons.json').read_text(encoding='utf-8-sig')) if p.get('asin')=='B0GPWRYNM1')
    def test_exact_facts_sources_conditions_and_no_offer_fabrication(self):
        text=render_mobile_evidence(self.product())
        for expected in ('Verified phone details','19 hours','At 100% Power','https://www.realme.com/in/realme-c83','Recorded'):
            self.assertIn(expected,text)
        self.assertNotIn('19999',text)
    def test_wrong_ram_and_unknown_asin_are_not_published(self):
        p=self.product();p['title']=p['title'].replace('4GB RAM','8GB RAM')
        self.assertEqual(render_mobile_evidence(p),'')
        p=self.product();p['asin']='B000000000'
        self.assertEqual(render_mobile_evidence(p),'')
    def test_rejected_record_and_unsafe_link_do_not_render(self):
        data=json.loads((ROOT/'data/phase_e_release_evidence.json').read_text())
        record=next(r for r in data['records'] if r['asin']=='B0GPWRYNM1')
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'data.json'
            record['resolver_verified']=False;path.write_text(json.dumps(data))
            self.assertEqual(render_mobile_evidence(self.product(),path),'')
            record['resolver_verified']=True
            for fact in record['specifications'].values():fact['source_url']='javascript:alert(1)'
            path.write_text(json.dumps(data));self.assertEqual(render_mobile_evidence(self.product(),path),'')
if __name__=='__main__':unittest.main()
