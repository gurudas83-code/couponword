import json
import unittest
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, parse_qs, unquote
from xml.etree import ElementTree as ET
from python.affiliate_links import amazon_link

ROOT=Path(__file__).resolve().parent
class Page(HTMLParser):
    def __init__(self,text):
        super().__init__();self.tags=[];self.text=[];self.feed(text)
    def handle_starttag(self,tag,attrs):self.tags.append((tag,dict(attrs)))
    def handle_data(self,text):self.text.append(text)

class ReleaseTests(unittest.TestCase):
    def test_tag_replaces_only_amazon_india(self):
        u=amazon_link('https://www.amazon.in/s?k=phone&tag=old-21&tag=other-21')
        self.assertEqual(parse_qs(urlsplit(u).query)['tag'],['guru07cc-21'])
        self.assertEqual(parse_qs(urlsplit(u).query)['k'],['phone'])
        self.assertEqual(amazon_link(u),u)
        for u in ['https://www.flipkart.com/search?q=phone','https://www.croma.com/','https://amazon.in.evil.test/']:
            self.assertEqual(amazon_link(u),u)
    def test_twenty_distinct_indexable_substantial_pages(self):
        pages=json.loads((ROOT/'data/phone-guides.json').read_text())['pages']
        self.assertEqual(len(pages),20)
        sitemap={x.text for x in ET.parse(ROOT/'public/sitemap.xml').getroot().iter() if x.tag.endswith('}loc')}
        titles=set()
        for item in pages:
            route='/seo/'+item['slug']+'.html';text=(ROOT/'public'/route.lstrip('/')).read_text();page=Page(text)
            self.assertGreater(len(' '.join(page.text).split()),350)
            self.assertNotIn(item['title'],titles);titles.add(item['title'])
            self.assertEqual(sum(t=='h1' for t,a in page.tags),1)
            canonical=[a['href'] for t,a in page.tags if t=='link' and a.get('rel')=='canonical']
            self.assertEqual(canonical,['https://coupon-world.in'+route]);self.assertIn(canonical[0],sitemap)
            self.assertIn('index,follow',text)
            for tag,a in page.tags:
                if tag=='a' and a.get('href','').startswith('/'):
                    path=unquote(urlsplit(a['href']).path);target=ROOT/'public'/path.lstrip('/')
                    self.assertTrue(target.is_file() or (target/'index.html').is_file(),a['href'])
            self.assertIn('sponsored',text)
    def test_all_public_amazon_links_have_tag_and_disclosure(self):
        count=0
        def visit(value):
            nonlocal count
            if isinstance(value,dict):
                for x in value.values():visit(x)
            elif isinstance(value,list):
                for x in value:visit(x)
            elif isinstance(value,str) and value.startswith('https://') and urlsplit(value).hostname in {'amazon.in','www.amazon.in'}:
                self.assertEqual(parse_qs(urlsplit(value).query).get('tag'),['guru07cc-21']);count+=1
        for path in (ROOT/'public').rglob('*.json'):visit(json.loads(path.read_text()))
        self.assertGreater(count,232)
        for path in (ROOT/'public').rglob('*.html'):
            for tag,a in Page(path.read_text()).tags:
                if tag=='a' and urlsplit(a.get('href','')).hostname in {'amazon.in','www.amazon.in'}:
                    self.assertEqual(parse_qs(urlsplit(a['href']).query).get('tag'),['guru07cc-21'])
                    self.assertIn('sponsored',a.get('rel',''))

if __name__=='__main__':unittest.main()
