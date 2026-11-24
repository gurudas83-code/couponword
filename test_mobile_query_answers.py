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
        cls.catalogue=json.loads((PUBLIC/'data/mobile_research_catalogue.json').read_text(encoding='utf-8'))
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
        for p in json.loads((ROOT/'data/mobile_query_benchmark_phase3.json').read_text(encoding='utf-8')):self.assertIn(p['id'],covered)
        self.assertEqual(len(self.report['answers']),len(self.groups))

    def test_only_reviewed_answer_hubs_are_published(self):
        coverage_path=PUBLIC/'data/mobile_query_answer_coverage.json'
        self.assertTrue(coverage_path.exists())
        coverage=json.loads(coverage_path.read_text(encoding='utf-8'))
        self.assertEqual(coverage['historical_wordings'],1000)
        self.assertEqual(coverage['answer_groups'],len(self.groups))
        self.assertEqual(coverage['indexable_groups'],12)
        self.assertEqual(coverage['noindex_groups'],len(self.groups)-12)
        self.assertTrue((PUBLIC/'answers').exists())
        self.assertTrue((PUBLIC/'hi/answers').exists())
        answer_urls={u for u in self.sitemap if '/answers/' in u and not u.endswith('/coverage/')}
        self.assertEqual(len(answer_urls),26)
        self.assertLessEqual(len(list((PUBLIC/'answers').iterdir())),14)
        self.assertLessEqual(len(list((PUBLIC/'hi/answers').iterdir())),14)

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


    def test_original_corpus_1000_answer_regression_and_latency(self):
        """Exercise all original query texts against current parsed answers and source-gated candidates."""
        import time
        corpus=json.loads((ROOT/'data/mobile_query_corpus_1000.json').read_text(encoding='utf-8'))
        cases=[row for split in ('train','validation','test') for row in corpus['splits'][split]]
        self.assertEqual(len(cases),1000)
        self.assertEqual(len({c['id'] for c in cases}),1000)
        latencies=[]
        counts={'nonempty':0,'honest_incomplete':0,'parser_mismatch':0,'exceptions':0}
        failures=[]
        for row in cases:
            start=time.perf_counter()
            try:
                group=parsed_group(row['query'],row['id'])
                if group['cap'] != row['budget_context']:
                    counts['parser_mismatch']+=1
                    failures.append((row['id'],'budget',group['cap'],row['budget_context']))
                matches=candidates(group,self.cards)
                answer=description(group,matches)
                if not isinstance(answer,str) or not answer.strip():
                    failures.append((row['id'],'empty answer'))
                if matches:
                    counts['nonempty']+=1
                else:
                    counts['honest_incomplete']+=1
                for candidate in matches:
                    reference=candidate.get('research_budget_reference') or {}
                    price=reference.get('reference_price_inr')
                    if not isinstance(price,(int,float)) or not price < row['budget_context']:
                        failures.append((row['id'],'invalid budget match',candidate.get('model_key')))
            except Exception as exc:
                counts['exceptions']+=1
                failures.append((row['id'],'exception',str(exc)))
            latencies.append((time.perf_counter()-start)*1000)
        ordered=sorted(latencies)
        print('CORPUS_1000_ANSWER_REPORT '+json.dumps({
            'total':len(cases),'nonempty':counts['nonempty'],
            'honest_incomplete':counts['honest_incomplete'],
            'parser_mismatch':counts['parser_mismatch'],
            'exceptions':counts['exceptions'],
            'mean_ms':round(sum(latencies)/len(latencies),3),
            'p95_ms':round(ordered[int(.95*(len(ordered)-1))],3),
            'max_ms':round(max(latencies),3),
            'failed_examples':failures[:30]
        },ensure_ascii=False))
        self.assertFalse(failures[:30],str(failures[:30]))


    def test_voice_transcript_modulation_1000_and_variants(self):
        """Measure actual JS voice-transcript parser, not microphone/STT accuracy."""
        import subprocess
        import time
        corpus=json.loads((ROOT/'data/mobile_query_corpus_1000.json').read_text(encoding='utf-8'))
        originals=[r for key in ('train','validation','test') for r in corpus['splits'][key]]
        variants=[]
        for row in originals:
            q=row['query']
            variants.extend((q, q.replace('phone','mobile').replace('under','below'),
                             q.replace('mobile','phone').replace('below','under')))
        # Spoken number, Hindi, and mixed-language transcript samples.
        spoken=[
            ('दस हजार में अच्छा मोबाइल',10000),
            ('पंद्रह हजार में कैमरा फोन',15000),
            ('बीस हजार में गेमिंग मोबाइल',20000),
            ('पच्चीस हजार के अंदर फोन',25000),
            ('तीस हजार में बैटरी वाला फोन',30000),
            ('20k phone under',20000),
            ('mobile under 15000',15000),
            ('phone below 25000',25000)
        ]
        js=r"""
const fs=require('fs'), vm=require('vm');
const source=fs.readFileSync('assets/cw-query-parser.js','utf8');
const sandbox={window:{}};vm.runInNewContext(source,sandbox);
const parser=sandbox.window.CouponWorldQueryParser;
const items=JSON.parse(fs.readFileSync(0,'utf8'));
const durations=[],answers=[];
for(const item of items){
 const t=process.hrtime.bigint();
 try{const result=parser.modulate(item);answers.push({budget:result.budget,query:result.query,category:result.category});}
 catch(e){answers.push({error:String(e)});}
 durations.push(Number(process.hrtime.bigint()-t)/1e6);
}
process.stdout.write(JSON.stringify({durations,answers}));
"""
        started=time.perf_counter()
        result=subprocess.run(['node','-e',js],input=json.dumps(variants+[q for q,_ in spoken]),
                              text=True,encoding='utf-8',capture_output=True,cwd=ROOT,timeout=90,check=True)
        elapsed=round((time.perf_counter()-started)*1000,2)
        values=json.loads(result.stdout)
        times=sorted(values['durations'])
        failures=[i for i,x in enumerate(values['answers']) if 'error' in x or not x.get('query')]
        missing_budget=[originals[i]['id'] for i in range(len(originals))
                        if values['answers'][3*i].get('budget')!=originals[i]['budget_context']]
        spoken_mismatches=[(q,b,values['answers'][len(variants)+i].get('budget'))
                           for i,(q,b) in enumerate(spoken)
                           if values['answers'][len(variants)+i].get('budget')!=b]
        print('VOICE_TRANSCRIPT_1000_REPORT '+json.dumps({
            'original_queries':len(originals),'total_transcripts':len(variants)+len(spoken),
            'parser_failures':len(failures),'original_budget_mismatches':len(missing_budget),
            'spoken_budget_mismatches':spoken_mismatches,
            'mean_parser_ms':round(sum(values['durations'])/len(times),4),
            'p95_parser_ms':round(times[int(.95*(len(times)-1))],4),
            'max_parser_ms':round(times[-1],4),'batch_wall_ms':elapsed,
            'budget_mismatch_examples':missing_budget[:20]
        },ensure_ascii=False))
        self.assertEqual(len(failures),0,str(failures[:12]))


    def test_diagnostic_623_unanswered_against_232_models(self):
        """Classify gaps without inventing missing prices or manufacturer evidence."""
        from collections import Counter
        from python.mobile_query_answers import documented, regional_records, brand_key, norm, model_title, supported
        raw=json.loads((ROOT/'data/mobile_query_corpus_1000.json').read_text(encoding='utf-8'))
        cases=[r for split in ('train','validation','test') for r in raw['splits'][split]]
        models=regional_records(self.cards)
        summary=Counter()
        by_brand=Counter()
        by_budget=Counter()
        examples={}
        detail=[]
        for row in cases:
            group=parsed_group(row['query'],row['id'])
            matched=candidates(group,self.cards)
            if matched:continue
            # Identity filter: never mix an explicit model or prohibited brand.
            avoid={brand_key(x.removeprefix('brand_')) for x in group['avoid'] if x.startswith('brand_')}
            soft={brand_key(x[6:]) for x in group['preferred'] if x.startswith('brand_')}
            allow={brand_key(x) for x in group['brands']}-avoid-soft
            identity=[]
            for c in models:
                b=brand_key(c['brand'])
                if b in avoid or (allow and b not in allow):continue
                if group['target']:
                    eq=norm(c['model'])==norm(group['target']) or norm(model_title(c))==norm(group['target'])
                    if group['action']=='compare_against_model':
                        if eq:continue
                    elif not eq:continue
                if group.get('pair') and c['model_key'] not in group['pair']:continue
                identity.append(c)
            sourced=[c for c in identity if documented(c)]
            budgeted=[]
            for c in sourced:
                ref=c.get('research_budget_reference') or {}
                p=ref.get('reference_price_inr')
                if isinstance(p,(int,float)) and ref.get('checked_at') and ref.get('live_offer') is False and ref.get('ranking_weight')==0 and p<group['cap'] and (group['lower'] is None or p>=group['lower']):
                    if not __import__('re').search(r'OUT.OF.STOCK|UNAVAILABLE|SOLD.OUT|DISCONTINUED',str(ref.get('stock_indication','')),__import__('re').I):
                        budgeted.append(c)
            ready=[c for c in budgeted if all(supported(c,c.get('research_budget_reference') or {},feature) for feature in group['must'])]
            if not identity: reason='NO_IDENTITY_IN_232'
            elif not sourced: reason='INSUFFICIENT_MANUFACTURER_SPECS'
            elif not budgeted: reason='MISSING_OR_OUT_OF_BAND_PRICE'
            elif not ready: reason='HARD_SPEC_VARIANT_GATE'
            else:reason='OTHER'
            summary[reason]+=1
            by_budget[str(row['budget_context'])]+=1
            by_brand[row.get('brand_context') or 'unrestricted']+=1
            if len(examples.get(reason,[]))<8:examples.setdefault(reason,[]).append({'id':row['id'],'query':row['query'],'identity':len(identity),'sourced':len(sourced),'priced':len(budgeted)})
            detail.append({'id':row['id'],'query':row['query'],'category':reason,'matching_catalogue_models':len(identity),'manufacturer_documented_models':len(sourced),'historical_price_eligible_models':len(budgeted)})
        print('UNANSWERED_623_EVIDENCE_AUDIT '+json.dumps({
            'total_unanswered':len(detail),'catalogue_models':len(self.cards),
            'reason_counts':dict(summary),'by_budget':dict(sorted(by_budget.items())),
            'by_brand':dict(by_brand),'examples':examples,
            'can_show_identity_matched_unpriced':sum(x['matching_catalogue_models']>0 for x in detail),
            'has_manufacturer_documented_unpriced':sum(x['manufacturer_documented_models']>0 for x in detail),
            'query_detail_first_30':detail[:30]
        },ensure_ascii=False))
        for offset in range(0,len(detail),40):
            print('UNANSWERED_623_AUDIT_CHUNK '+json.dumps({'offset':offset,'rows':detail[offset:offset+40]},ensure_ascii=False))
        self.assertEqual(len(detail),623)
        self.assertEqual(sum(summary.values()),623)

if __name__=='__main__':unittest.main()
