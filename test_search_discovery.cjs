const vm = require('node:vm');
const fs = require('node:fs');
const assert = require('node:assert/strict');
const source = fs.readFileSync('assets/discovery-analytics.js','utf8');
function run(referrer, utm='', store=new Map()) {
 const events=[], handlers={};
 const window={location:new URL('https://coupon-world.in/seo/camera-phone-buying-guide.html'+utm),gtag:(...args)=>events.push(args),sessionStorage:{getItem:k=>store.get(k)||null,setItem:(k,v)=>store.set(k,v)}};
 const document={referrer,addEventListener:(name,fn)=>handlers[name]=fn};
 vm.runInNewContext(source,{window,document,URL,URLSearchParams,Date});
 return {events,handlers,store};
}
for (const [ref,expected] of [['https://chatgpt.com/','chatgpt'],['https://gemini.google.com/','gemini'],['https://www.meta.ai/','meta_ai'],['https://www.google.co.in/search?q=private','google'],['https://chatgpt.com.evil.test/','other_referral'],['','direct_or_unattributed']]) {
 const r=run(ref);assert.equal(r.events[0][2].discovery_source,expected);assert(!JSON.stringify(r.events).includes('private'));
}
const first=run('https://chatgpt.com/');const next=run('https://coupon-world.in/seo/camera-phone-buying-guide.html','',first.store);assert.equal(next.events[0][2].discovery_source,'chatgpt');
const utm=run('', '?utm_source=gemini&email=secret');assert.equal(utm.events[0][2].discovery_source,'gemini');assert(!JSON.stringify(utm.events).includes('secret'));
utm.handlers.click({target:{closest:()=>({href:'https://www.amazon.in/s?k=private&tag=guru07cc-21'})}});assert.equal(utm.events[1][2].action_kind,'retailer_research');assert(!JSON.stringify(utm.events).includes('private'));
const interaction=run('https://www.google.co.in/');
const control={href:'https://coupon-world.in/compare/',matches:selector=>selector.includes('[data-analytics-intent]'),getAttribute:name=>name==='data-analytics-intent'?'compare':null};
interaction.handlers.click({target:{closest:()=>control}});
assert.equal(interaction.events.at(-1)[0],'event');assert.equal(interaction.events.at(-1)[1],'research_action');assert.equal(interaction.events.at(-1)[2].intent,'compare');
console.log('PASS discovery platform attribution, internal continuation, safe event fields and retailer clicks');
