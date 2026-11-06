"""Publication guardrails: evidence, exact constraints, deduplication and SEO."""
import copy
import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from xml.etree import ElementTree as ET

from python.mobile_query_answers import historical_groups, load_groups, candidates, parsed_group, description, maker_url, brand_key

ROOT=Path(__file__).resolve().parent
PUBLIC=ROOT/'public'
SITE='https://coupon-world.in'

class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.tags=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))

class AnswersTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalogue=json.loads((PUBLIC/'data/mobile_research_catalogue.json').read_text())
        cls.cards=cls.catalogue['model_cards']
        cls.groups=load_groups()
        cls.report={'answers':[dict(query_ids=g['query_ids']) for g in cls.groups]}
        cls.sitemap={e.text for e in ET.parse(PUBLIC/'sitemap.xml').getroot().iter() if e.tag.endswith('}loc')}

    def test_all_historical_wordings_and_benchmarks_accounted_for(self):
        old=historical_groups()
        ids=[q for g in old for q in g['query_ids']]
        self.assertEqual(len(ids),1000);self.assertEqual(len(set(ids)),1000)
        covered={q for a in self.report['answers'] for q in a['query_ids']}
        self.assertTrue(set(ids)<=covered)
        for p in json.loads((ROOT/'data/mobile_query_benchmark_phase3.json').read_text()):self.assertIn(p['id'],covered)
        self.assertEqual(len(self.report['answers']),len(self.groups))

    def test_mass_query_pages_are_not_published(self):
        self.assertFalse((PUBLIC/'answers').exists())
        self.assertFalse((PUBLIC/'hi/answers').exists())
        self.assertFalse((PUBLIC/'data/mobile_query_answer_coverage.json').exists())
        self.assertFalse(any('/answers/' in u for u in self.sitemap))

    def test_price_and_memory_stay_on_the_same_reference(self):
        g=parsed_group('8GB RAM 256GB phone under 20000','T')
        base=copy.deepcopy(next(c for c in self.cards if c.get('research_budget_reference') and len(c.get('specifications',{}))>=8))
        ref=base['research_budget_reference'];ref.update(ram_gb=8,storage_gb=128,reference_price_inr=19000)
        self.assertEqual(candidates(g,[base]),[])
        ref['storage_gb']=256
        self.assertEqual(len(candidates(g,[base])),1)
        ref['reference_price_inr']=20000
        self.assertEqual(candidates(g,[base]),[])
        ref['reference_price_inr']=19999;ref['stock_indication']='OUT_OF_STOCK'
        self.assertEqual(candidates(g,[base]),[])

    def test_brand_exclusions_and_soft_preferences_remain_distinct(self):
        g=parsed_group('Redmi nahi chahiye phone under 20000','T')
        self.assertTrue(all(brand_key(c['brand'])!='redmi' for c in candidates(g,self.cards)))
        soft=parsed_group('Samsung preferred but battery more important under 25k','T')
        self.assertTrue(any(brand_key(c['brand'])!='samsung' for c in candidates(soft,self.cards)))
        hard=parsed_group('Samsung only phone under 30000','T')
        self.assertTrue(all(brand_key(c['brand'])=='samsung' for c in candidates(hard,self.cards)))

    def test_zero_results_do_not_claim_market_absence(self):
        g=next(g for g in self.groups if g['query']=='best Apple phone under 7000')
        self.assertEqual(candidates(g,self.cards),[])
        self.assertIn('not proof',description(g,[]))

    def test_source_hosts_and_exact_comparison_are_preserved(self):
        self.assertFalse(maker_url('https://samsung.com.evil.test/spec'))
        self.assertFalse(maker_url('http://www.samsung.com/in/'))
        g=parsed_group('Galaxy A36 vs Galaxy A56','T')
        self.assertEqual({c['model_key'] for c in candidates(g,self.cards)},set(g['pair']))
        exact=parsed_group('Galaxy A36 8GB 256GB','T')
        self.assertEqual(exact['target'],'galaxy a36 5g')

    def test_literal_ois_and_regional_alias_do_not_leak_into_matches(self):
        g=parsed_group('phone under 25000 with AMOLED OIS and 8GB RAM','T')
        self.assertIn('ois',g['must'])
        rows=candidates(g,self.cards)
        self.assertTrue(rows)
        self.assertTrue(all(str(c['specifications'].get('ois',{}).get('value')).lower() in {'yes','true','supported'} for c in rows))
        self.assertFalse(any(c['model_key']=='cmf|phone 1' for c in rows))
        poco=[c for c in rows if c['model_key'] in {'poco|x7 pro','poco|x7 pro 5g'}]
        self.assertEqual(len(poco),1)
        self.assertEqual(poco[0]['specifications']['battery_mah_typical']['value'],6550)

if __name__=='__main__':unittest.main()
