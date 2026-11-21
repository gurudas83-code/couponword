"use strict";
/* Offline regression: real repo category fixtures, no browser microphone, paid API or network. */
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const path = require("node:path");

const root=__dirname;
const box={URL,console};
vm.runInNewContext(fs.readFileSync(path.join(root,"assets/cw-query-parser.js"),"utf8"),box,{filename:"cw-query-parser.js"});
vm.runInNewContext(fs.readFileSync(path.join(root,"assets/cw-research-assistant.js"),"utf8"),box,{filename:"cw-research-assistant.js"});
const parser=box.CouponWorldQueryParser.modulate, core=box.CouponWorldAssistantCore;
const source=JSON.parse(fs.readFileSync(path.join(root,"data/india_tv_earbuds_40_catalogue.json"),"utf8")).records;
const reviewed=JSON.parse(fs.readFileSync(path.join(root,"data/category_research_verified.json"),"utf8")).records;
const records=source.concat(reviewed);
const hindi=parser("मुझे पंद्रह हजार में कैमरा फोन बताओ");
assert.equal(hindi.category,"phones");
assert.equal(hindi.budget,15000);
assert.match(hindi.query,/camera phone under 15000/);
assert(!hindi.query.includes("thousand"),"Hindi price must be normalized");
const other=parser("बीस हजार का टीवी बताओ");
assert.equal(other.category,"tvs");
assert.equal(other.budget,20000);
const tv=parser("55 inch Xiaomi TV");
assert.equal(tv.category,"tvs");
assert.equal(tv.budget,null,"55-inch must not turn into a price");
const tvMatches=core.selectResearch(records,tv,"tvs");
assert(tvMatches.length>0,"real 55-inch Xiaomi TV should match");
assert(tvMatches.every(x=>/xiaomi/i.test(x.brand)));
assert(tvMatches.every(x=>/\b55\b/.test(x.model)||x.specifications.some(s=>/size/i.test(s.label)&&/\b55\b/.test(s.value))));
const noTv=core.selectResearch(records,parser("Some Nonexistent TV XYZQ111"),"tvs");
assert.equal(noTv.length,0,"unknown named exact TV must not be substituted");
const anc=parser("noise cancelling earbuds");
assert.equal(anc.category,"earbuds");
const ancMatches=core.selectResearch(records,anc,"earbuds");
assert(ancMatches.length>0,"ANC source-linked earbuds available");
assert(ancMatches.every(x=>(x.specifications||[]).some(s=>/anc|noise cancel/i.test(s.label+" "+s.value)&&core.sourceUrl(s.source_url))));
assert(!ancMatches.some(x=>x.category==="tvs"),"never mix TV into earbuds");
const follow=parser("और battery भी",hindi);
assert.equal(follow.category,"phones");
assert.equal(follow.budget,15000,"a short follow-up inherits the earlier limit");
const changed=parser("55 inch TV",hindi);
assert.equal(changed.category,"tvs");
assert.equal(changed.budget,null,"new category must not inherit phone price");
const reviewedLinks=source.find(x=>x.retailers&&x.retailers.amazon&&x.retailers.amazon.retailer_research_url);
assert(reviewedLinks,"A reviewed TV/audio model should have a saved Amazon research destination");
const retailer=core.retailerOption({retailer:"amazon",
  url:reviewedLinks.retailers.amazon.retailer_research_url,
  exact_model_link:reviewedLinks.retailers.amazon.exact_model_link_verified});
assert(retailer&&retailer.url.startsWith("https://www.amazon.in/"),"Preserve existing Amazon research destination");
assert.equal(new URL(retailer.url).searchParams.get("tag"),"guru07cc-21","Amazon affiliate tag required");
assert.equal(retailer.affiliate,true);
assert.equal(core.retailerOption({retailer:"amazon",url:"https://amazon.in.evil.test/dp/X"}),null);
assert.equal(core.retailerOption({retailer:"flipkart",url:"https://www.amazon.in/dp/X"}),null);
assert.equal(core.retailerOption({retailer:"croma",url:"javascript:alert(1)"}),null);
assert.equal(core.retailerOption({retailer:"amazon",url:"http://www.amazon.in/dp/X"}),null);
assert.equal(core.sourceUrl("javascript:alert(1)"),"");
assert.equal(core.sourceUrl("http://example.org"),"");
const fields=core.resultFields(tvMatches[0],tv.query,3);
assert(fields.every(f=>f.url.startsWith("https://")));
const html=fs.readFileSync(path.join(root,"index.html"),"utf8");
assert.match(html,/id="cwAssistantForm"/);
assert.match(html,/assets\/cw-query-parser\.js/);
assert.match(html,/assets\/cw-research-assistant\.js/);
const prior=html.match(/data-mobile-query="/g)||[];
assert.equal(prior.length,5,"Keep the existing five budget buttons unchanged");
assert.match(html,/first-three-core-20261120/,"Preserve existing progressive search entry point");
const published=path.join(root,"public/data/assistant_category_research.json");
if(fs.existsSync(published)){
  const data=JSON.parse(fs.readFileSync(published,"utf8"));
  assert.equal(data.mode,"PUBLIC_RESEARCH_ASSISTANT_NO_OFFERS");
  assert(data.records.length>=30,"Material curated category coverage");
  assert(data.records.some(x=>x.category==="tvs"));
  assert(data.records.some(x=>x.category==="earbuds"));
  assert(data.records.some(x=>x.category==="accessories"));
  const links=data.records.flatMap(x=>x.retailer_links||[]);
  assert(links.some(x=>x.retailer==="amazon"),"Published catalog retains existing Amazon retailer links");
  assert(links.some(x=>x.retailer==="flipkart"),"Published catalog retains existing Flipkart retailer links");
  assert(links.some(x=>x.retailer==="croma"),"Published catalog retains existing Croma retailer searches");
  for(const item of links){
    const safe=core.retailerOption(item);
    assert(safe,"No unknown or unsafe retailer destination may be published");
    assert(item.exact_model_link===true||item.exact_model_link===false);
    assert(!("price_inr" in item)&&!("stock_status" in item)&&!("checkout_eligible" in item),
      "Retailer research URLs never imply live purchase eligibility");
  }
  const raw=JSON.stringify(data).toLowerCase();
  for (const forbidden of ["retailers","price_inr","purchase_cta_eligible","affiliate_url","private_product_id"])assert(!raw.includes('"'+forbidden+'"'),"Never export offer/private field "+forbidden);
}
// Real phone catalogue regression: a specific requested model must not be
// confused with Pro/Max variants or an unrelated search result.
const mobileCards=JSON.parse(fs.readFileSync(path.join(root,"data/mobile_research_catalogue.json"),"utf8")).model_cards;
const iphoneCandidates=mobileCards.filter(x=>x.brand==="Apple"&&/^iPhone 17(?: Pro(?: Max)?)?$/.test(x.model))
  .map(x=>({card:x}));
assert(iphoneCandidates.length>=3,"Original iPhone 17 / Pro / Max fixture is required");
const standard=parser("मुझे Apple mobile 17 चाहिए");
assert.equal(core.requestedPhoneIdentity(standard),"apple iphone 17");
const splitStandard=core.classifyPhoneMatches(standard,iphoneCandidates);
assert.equal(splitStandard.exact.length,1);
assert.equal(splitStandard.exact[0].card.model,"iPhone 17");
assert.equal(splitStandard.related.length,2,"Pro and Pro Max are related, not the requested standard model");
const pro=core.classifyPhoneMatches(parser("iPhone 17 Pro"),iphoneCandidates);
assert.equal(pro.exact.length,1);
assert.equal(pro.exact[0].card.model,"iPhone 17 Pro");
const max=core.classifyPhoneMatches(parser("iPhone 17 Pro Max"),iphoneCandidates);
assert.equal(max.exact.length,1);
assert.equal(max.exact[0].card.model,"iPhone 17 Pro Max");
assert.equal(core.classifyPhoneMatches(parser("iPhone 19"),iphoneCandidates).exact.length,0,
  "Unknown model must not silently use a different iPhone");
assert.equal(core.requestedPhoneIdentity(parser("Apple phone")),"",
  "Broad brand searches must not be narrowed into an exact model");
assert.equal(core.requestedPhoneIdentity(parser("Samsung Galaxy A56 5G")),"samsung galaxy a56 5g");
assert.equal(core.requestedPhoneIdentity(parser("Nothing Phone 3a")),"nothing phone 3a");
assert.equal(core.requestedPhoneIdentity(parser("compare iPhone 17 vs iPhone 17 Pro")),"",
  "Comparison intent is not a single exact-model request");

console.log("PASS Coupon World assistant: Hindi budget, TV size, ANC, unknown identity, follow-up memory, safety, UI, unchanged budget buttons"+(fs.existsSync(published)?", public payload":""));
