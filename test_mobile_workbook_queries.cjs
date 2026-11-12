const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const root = __dirname;
const catalogue = JSON.parse(fs.readFileSync(path.join(root, 'public/data/mobile_research_catalogue.json')));
const preview = JSON.parse(fs.readFileSync(path.join(root, 'data/mobile_research_preview.json')));
const elements = new Map();
function element(id) {
  if (!elements.has(id)) elements.set(id, {id, value:'', innerHTML:'', textContent:'', hidden:false, tagName:'DIV', events:{}, addEventListener(name, f) {this.events[name]=f;}, scrollIntoView(){}});
  return elements.get(id);
}
const document = {getElementById:element, querySelectorAll:()=>[], events:{}, addEventListener(name, f){this.events[name]=f;}};
const window = {location:{hash:''}, addEventListener(){}};
const context = vm.createContext({document, window, console, URL, URLSearchParams, fetch:async url=>({ok:true,json:async()=>url.includes('mobile_research_catalogue')?catalogue:url.includes('mobile_research_preview')?preview:[]})});
vm.runInContext(fs.readFileSync(path.join(root, 'mobile-research-preview.js'),'utf8'),context);
setImmediate(()=> {
 const api=window.CouponWorldMobileResearch;
 let checks=0;
 function check(name, fn){fn();checks++;console.log('PASS '+name);}
 const search=q=>api.search(q);
 check('232 model identities retained',()=>assert.equal(catalogue.model_cards.length,232));
 check('235 discovery rows retained',()=>assert.equal(catalogue.records.length,235));
 check('10 frozen variants retained',()=>assert.equal(preview.products.length,10));
 check('226 model cards have technical specifications',()=>assert.equal(catalogue.model_cards.filter(c=>Object.keys(c.specifications).length).length,226));
 check('86 references exclude negative stock',()=>{let rows=catalogue.model_cards.filter(c=>c.research_budget_reference);assert.equal(rows.length,86);assert(rows.every(c=>!/(OUT.OF.STOCK|UNAVAILABLE|DISCONTINUED)/i.test(c.research_budget_reference.stock_indication)));});
 check('budget is strict and nonempty',()=>{let r=search('phone under 20000');assert(r.length>0);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr<20000));});
 check('20k equals 20000',()=>assert.deepEqual(search('phone under 20k').map(x=>x.card.model_key),search('phone under 20000').map(x=>x.card.model_key)));
 check('Hindi budget matches English',()=>assert.deepEqual(search('20000 के अंदर मोबाइल').map(x=>x.card.model_key),search('phone under 20000').map(x=>x.card.model_key)));
 check('Hindi numerals match English',()=>assert.deepEqual(search('२०००० के अंदर मोबाइल').map(x=>x.card.model_key),search('phone under 20000').map(x=>x.card.model_key)));
 check('Hinglish budget matches English',()=>assert.deepEqual(search('mujhe 20 hazar ke andar mobile chahiye').map(x=>x.card.model_key),search('phone under 20000').map(x=>x.card.model_key)));
 check('best camera respects budget',()=>{let r=search('best camera phone under 20000');assert(r.length);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr<20000));assert(element('mobileResearchSearchStatus').textContent.includes('not a performance ranking'));});
 check('Samsung exclusion',()=>{let r=search('phone under 30000 exclude Samsung');assert(r.length);assert(r.every(x=>x.card.brand.toLowerCase()!=='samsung'));});
 check('Hinglish Samsung exclusion',()=>{let r=search('Samsung ko chhodkar mobile under 30000');assert(r.length);assert(r.every(x=>x.card.brand.toLowerCase()!=='samsung'));});
 check('exact Galaxy A36 variant',()=>{let r=search('Galaxy A36 8GB 256GB');assert.equal(r.length,1);assert(r[0].rows.every(x=>x.ram_gb===8&&x.storage_gb===256));});
 check('P1 manufacturer-listed configurations match exact model and memory',()=>{
   let count=0;
   for (const card of catalogue.model_cards) {
     for (const variant of card.verified_india_variants || []) {
       const query = `${card.brand} ${card.model} ${variant.ram_gb}GB RAM ${variant.storage_gb}GB storage`;
       const matches = search(query);
       assert.deepEqual(Array.from(matches, item => item.card.model_key), [card.model_key], query);
       assert(matches[0].rows.some(row => row.ram_gb === variant.ram_gb && row.storage_gb === variant.storage_gb), query);
       assert(element('mobileResearchResults').innerHTML.includes(card.photo.url), query);
       count++;
     }
   }
   assert.equal(count,20);
 });
 check('unsupported variant has zero results',()=>assert.equal(search('Galaxy A36 16GB 1TB').length,0));
 check('single storage is a hard constraint',()=>{let r=search('Galaxy A36 256GB');assert(r.length);assert(r.every(x=>x.rows.every(v=>v.storage_gb===256)));});
 check('model digits cannot select a sibling',()=>{let r=search('Pixel 9');assert(r.length);assert(r.every(x=>/\b9\b/.test(x.card.model)));});
 check('identity is not overridden by feature query',()=>{let r=search('Samsung camera phone');assert(r.length);assert(r.every(x=>x.card.brand.toLowerCase()==='samsung'));});
 check('unmatched identity is not broadened',()=>assert.equal(search('Imaginaryphone 999 camera').length,0));
 check('numeric battery constraint',()=>{let r=search('5000mah battery phone under 30000');assert(r.length);assert(r.every(x=>Number(x.card.specifications.battery_mah_typical.value)>=5000));});
 check('refresh constraint',()=>{let r=search('120hz display phone under 30000');assert(r.length);assert(r.every(x=>Number(x.card.specifications.display_refresh_max_hz.value)>=120));});
 check('explicit comparison returns both models',()=>{let r=search('Galaxy A36 vs Galaxy A56');assert.equal(r.length,2);assert(element('mobileResearchResults').innerHTML.includes('no performance winner'));});
 check('budget pagination expands',()=>{search('phone between 0 and 100000');assert(!element('mobileResearchResultsMore').hidden);element('mobileResearchResultsMore').events.click();assert((element('mobileResearchResults').innerHTML.match(/data-mobile-model-card=/g)||[]).length>6);});
 check('reference amounts hidden from result text',()=>{search('phone under 20000');assert(!/reference_price_inr|₹\s*\d|INR\s*\d/.test(element('mobileResearchResults').innerHTML));});
 check('232 Croma model targets replace generic category destinations',()=>{
   const seen=new Set();
   for(const card of catalogue.model_cards){
     const links=card.retailer_search_links||[];
     assert.equal(links.length,3);
     for(const link of links)assert.equal(link.link_scope,'MODEL_TARGETED_SEARCH_NOT_VERIFIED_PRODUCT');
     const retailer=links.find(x=>x.retailer==='Croma');
     const dest=new URL(retailer.url);
     assert.equal(dest.hostname,'www.croma.com');
     assert.equal(dest.pathname,'/search/');
     const q=(dest.searchParams.get('text')||'').toLowerCase();
     for(const token of card.model_key.replace('|',' ').split(/[^a-z0-9]+/g).filter(Boolean)){
       assert(q.includes(token),card.model_key+' -> '+q);
     }
     seen.add(retailer.url);
   }
   // Two legacy Redmi identities normalize to the same human product name.
   assert.equal(seen.size,231);
 });
 check('retailer search links visible',()=>{search('Galaxy A36');let html=element('mobileResearchResults').innerHTML;assert(html.includes('Search Amazon'));assert(html.includes('Search Flipkart'));assert(html.includes('Search Croma for this model'));});
 check('main search recognizes bare budget',()=>assert(api.isResearchQuery('under 20k')));
 check('strict boundary excludes equality',()=>{let ref=catalogue.model_cards.find(c=>c.research_budget_reference).research_budget_reference;assert(search('phone under '+ref.reference_price_inr).every(x=>x.card.research_budget_reference.reference_price_inr<ref.reference_price_inr));});
 check('repeated queries deterministic',()=>{let first=search('camera phone under 30000').map(x=>x.card.model_key);for(let i=0;i<20;i++)assert.deepEqual(search('camera phone under 30000').map(x=>x.card.model_key),first);});
 check('under 50000 stays within 40000 to below 50000',()=>{let r=search('mobile under 50000 nearby band');assert(r.length);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr>=40000&&x.card.research_budget_reference.reference_price_inr<50000));assert(element('mobileResearchSearchStatus').textContent.includes('40,000'));});
 check('under 30000 stays within 25000 to below 30000',()=>{let r=search('mobile under 30000 nearby band');assert(r.length);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr>=25000&&x.card.research_budget_reference.reference_price_inr<30000));});
 check('all budget shortcuts enforce their lower bands',()=>{for(let cap of [10000,15000,20000,25000,30000,40000,50000,60000]){let floor=Math.max(0,cap-(cap<=30000?5000:10000));assert(search('phone under '+cap+' nearby band').every(x=>x.card.research_budget_reference.reference_price_inr>=floor&&x.card.research_budget_reference.reference_price_inr<cap));}});
 check('explicit price range retains requested floor',()=>{let r=search('phone between 15000 and 30000');assert(r.length);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr>=15000&&x.card.research_budget_reference.reference_price_inr<=30000));assert(r.some(x=>x.card.research_budget_reference.reference_price_inr<25000));});
 check('explicit full-budget request includes documented cheaper phones without relaxing cap',()=>{let r=search('phone under 30000 full budget');assert(r.length);assert(r.every(x=>x.card.research_budget_reference.reference_price_inr<30000));assert(r.some(x=>x.card.research_budget_reference.reference_price_inr<25000));assert.deepEqual(r.map(x=>x.card.model_key),search('phone under 30000').map(x=>x.card.model_key));});
 check('Hindi full-budget request is equivalent',()=>assert.deepEqual(search('30000 के अंदर पूरे बजट मोबाइल').map(x=>x.card.model_key),search('phone under 30000 full budget').map(x=>x.card.model_key)));
 check('camera discovery sorting prioritizes relevant documented evidence, never price',()=>{let r=search('camera phone under 30000');let fields=['rear_main_mp','rear_camera_system','front_camera_system','ois'];let relevance=x=>fields.filter(k=>Object.prototype.hasOwnProperty.call(x.card.specifications||{},k)).length;for(let i=1;i<r.length;i++)assert(relevance(r[i-1])>=relevance(r[i]));});
 check('empty price band does not fall back to cheaper phones',()=>assert.equal(search('phone under 10000000 nearby band').length,0));
 check('band boundaries include floor and exclude strict cap',()=>{let card=catalogue.model_cards.find(c=>c.research_budget_reference);let ref=card.research_budget_reference;let old=ref.reference_price_inr;try{for(let [price,expected] of [[39999,false],[40000,true],[49999,true],[50000,false]]){ref.reference_price_inr=price;assert.equal(search('phone under 50000 nearby band').some(x=>x.card.model_key===card.model_key),expected);}}finally{ref.reference_price_inr=old;}});

 function clickAction(selector, key) { document.events.click({target:{closest(s){return s===selector?{getAttribute(){return key;}}:null;}}}); }
 check('M17 colour listings form one result',()=>{let r=search('camera phone under 30000');assert.equal(r.filter(x=>/galaxy m17 5g/.test(x.card.model.toLowerCase())).length,1);assert(element('mobileResearchResults').innerHTML.includes('matching catalogue entries grouped'));});
 check('Narzo colour listings form one result',()=>assert.equal(search('narzo 100 lite under 20000').length,1));
 check('Pro models are not merged with base models',()=>{let r=search('iPhone 16');assert(r.some(x=>x.card.model==='iPhone 16'));assert(r.some(x=>x.card.model==='iPhone 16 Pro'));assert(r.some(x=>x.card.model==='iPhone 16 Pro Max'));});
 check('4G and 5G identities remain separate',()=>{let r=search('Lava Bold N2');assert(r.some(x=>x.card.model==='Bold N2'));assert(r.some(x=>x.card.model==='Bold N2 5G'));});
 check('source evidence and checked date on results',()=>{search('Galaxy A36');let html=element('mobileResearchResults').innerHTML;assert(html.includes('Specification source'));assert(html.includes('Specification research snapshot:'));assert(html.includes('What to consider'));assert(html.includes('Before choosing'));});
 check('camera guidance avoids an unsupported winner',()=>{search('camera phone under 30000');assert(element('mobileResearchResults').innerHTML.includes('Megapixels alone do not establish photo quality'));});
 check('repeated brand prefix is removed from display',()=>{search('Redmi Note 15');assert(!element('mobileResearchResults').innerHTML.includes('Redmi Redmi'));});
 check('CPU clocks are not mislabelled as chipset names',()=>{search('Samsung S26 Ultra');assert(element('mobileResearchResults').innerHTML.includes('CPU clock (chipset name unconfirmed)'));});
 check('comparison query produces a real specification table',()=>{search('Galaxy A36 vs Galaxy A56');assert(element('mobileResearchCompare').innerHTML.includes('<table'));assert(element('mobileResearchCompare').innerHTML.includes('Battery'));assert(!element('mobileResearchCompare').innerHTML.includes('?GB'));assert(element('mobileResearchCompare').innerHTML.includes('Galaxy A36'));assert(element('mobileResearchCompare').innerHTML.includes('Galaxy A56'));});
 check('comparison can be cleared without automatic re-selection',()=>{clickAction('[data-research-compare-clear]');assert(element('mobileResearchCompare').hidden);});
 check('manual comparison adds and removes exact selected rows',()=>{let r=search('Galaxy A36 8GB 256GB');clickAction('[data-research-compare]',r[0].card.model_key);assert(!element('mobileResearchCompare').hidden);assert(element('mobileResearchCompare').innerHTML.includes('8GB / 256GB'));clickAction('[data-research-compare]',r[0].card.model_key);assert(element('mobileResearchCompare').hidden);});
 check('comparison limits selection to three phones',()=>{let r=search('phone between 0 and 100000');for(let item of r.slice(0,4))clickAction('[data-research-compare]',item.card.model_key);assert(element('mobileResearchCompare').innerHTML.includes('(3/3)'));assert(element('mobileResearchSearchStatus').textContent.includes('Compare up to 3'));clickAction('[data-research-compare-clear]');});

 check('physical RAM and internal storage wording retain exact variant',()=>{let r=search('Galaxy A36 8GB physical RAM 256GB internal storage');assert.equal(r.length,1);assert(r[0].rows.every(v=>v.ram_gb===8&&v.storage_gb===256));});
 check('applied condition chips expose all hard filters',()=>{search('phone under 30000 8GB RAM 256GB storage exclude Samsung');let html=element('researchAppliedFilters').innerHTML;assert(html.includes('30,000'));assert(html.includes('Exact physical RAM: 8GB'));assert(html.includes('Exact storage: 256GB'));assert(html.includes('Exclude: samsung'));});
 check('guided controls run the existing constrained search',()=>{element('researchGuidedBudget').value='30000';element('researchGuidedPriority').value='camera';element('researchGuidedRam').value='8';element('researchGuidedStorage').value='256';element('researchGuidedExclude').value='Samsung';element('researchGuidedApply').events.click();assert(element('mobileResearchQuery').value.includes('8GB physical RAM'));let r=search(element('mobileResearchQuery').value);assert(r.length);assert(r.every(x=>x.card.brand.toLowerCase()!=='samsung'&&x.card.research_budget_reference.reference_price_inr>0&&x.card.research_budget_reference.reference_price_inr<30000&&x.rows.every(v=>v.ram_gb===8&&v.storage_gb===256)));});
 check('guided full budget explicitly opts in matches the full-budget default',()=>{element('researchGuidedBudget').value='30000';element('researchGuidedScope').value='all';element('researchGuidedApply').events.click();assert(element('mobileResearchQuery').value.includes('full budget'));let r=search(element('mobileResearchQuery').value);assert(r.some(x=>x.card.research_budget_reference.reference_price_inr<25000));});
 check('clear search removes all conditions and resets guided inputs',()=>{element('researchClearSearch').events.click();assert.equal(element('mobileResearchQuery').value,'');assert(element('researchAppliedFilters').hidden);assert(element('mobileResearchResults').hidden);assert.equal(element('researchGuidedBudget').value,'');assert.equal(element('researchGuidedExclude').value,'');assert.equal(element('researchGuidedScope').value,'all');});
 check('empty guided controls do not launch an unconstrained search',()=>{element('researchGuidedApply').events.click();assert(element('researchGuidedStatus').textContent.includes('Choose a budget'));assert(element('mobileResearchResults').hidden);});
 check('unknown exact memory is explained without claiming market absence',()=>{search('Galaxy A36 16GB physical RAM 1TB storage');let html=element('mobileResearchResults').innerHTML;assert(html.includes('exact memory variant'));assert(html.includes('not proof that no suitable phone exists'));assert(html.includes('No constraint has been relaxed'));});
 check('invalid budget ranges have an actionable explanation',()=>{assert.equal(search('phone between 50000 and 20000').length,0);assert(element('mobileResearchResults').innerHTML.includes('lower budget is higher'));});
 check('build reliability only exposes documented fields and limitations',()=>{let r=search('build reliability phone under 50000');assert(r.length);assert(r.every(x=>x.card.specifications.ip_rating||x.card.specifications.durability));assert(element('mobileResearchResults').innerHTML.includes('does not establish drop resistance'));});
 check('all headline budget shortcuts cover ₹10k to ₹1L',()=>{
  const homepage=fs.readFileSync(path.join(root,'index.html'),'utf8');
  for (let cap of [10000,15000,20000,25000,30000,35000,40000,50000,60000,70000,80000,90000,100000]) {
   assert(homepage.includes('data-mobile-query="mobile under '+cap+'"'));
   const result=search('phone under '+cap);
   assert(result.every(x=>x.card.research_budget_reference.reference_price_inr<cap));
  }
 });
 check('research can hand a budget query to existing verified recommendation engine',()=>{
  let forwarded=null;
  window.CouponWorldShoppingRecommend=(query)=>{forwarded=query;};
  const query='camera phone under 30000 exclude Samsung';
  search(query);
  assert(element('mobileResearchResults').innerHTML.includes('data-research-verified-recommend'));
  assert(element('mobileResearchResults').innerHTML.includes('not proven camera'));
  clickAction('[data-research-verified-recommend]');
  assert.equal(forwarded,query);
 });
 check('comparison is not misrepresented as a performance-ranked recommendation',()=>{
  search('Galaxy A36 vs Galaxy A56');
  assert(!element('mobileResearchResults').innerHTML.includes('data-research-verified-recommend'));
 });
 check('research retailer messaging distinguishes model searches from exact product offers',()=>{
  search('Galaxy A36');
  assert(element('mobileResearchResults').innerHTML.includes('Model-targeted retailer searches only'));
 });
 check('natural-language query noise does not hide the exact model',()=>{
   const plain=search('Samsung Galaxy A36');
   const verbose=search('please suggest exact model Samsung Galaxy A36 for India');
   assert.deepEqual(verbose.map(x=>x.card.model_key),plain.map(x=>x.card.model_key));
 });
 check('Hinglish avoid-brand grammar preserves exclusions',()=>{
   const r=search('vivo nahi chahiye phone under 15000');
   assert(r.every(x=>x.card.brand.toLowerCase()!=='vivo'));
 });
 check('budget zero results can show separated unpriced evidence without a false offer',()=>{
   const r=search('Apple iPhone 11 under 7000');
   assert.equal(r.length,0);
   const h=element('mobileResearchResults').innerHTML;
   assert(h.includes('Related research — NOT within-budget recommendations'));
   assert(h.includes('Budget status: not verified'));
   assert(!h.includes('purchase-cta'));
 });
 console.log(checks+' checks passed');
});
