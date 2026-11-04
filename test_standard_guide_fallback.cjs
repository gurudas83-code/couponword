const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const script = fs.readFileSync('mobile-research-preview.js','utf8');
async function scenario(fail) {
 const els = new Map();
 const el = id => {if (!els.has(id)) els.set(id,{id,value:'',innerHTML:'',textContent:'',hidden:false,events:{},addEventListener(k,v){this.events[k]=v},scrollIntoView(){}});return els.get(id)};
 const window = {location:{hash:'',search:''},addEventListener(){}};
 const document={getElementById:el,querySelectorAll:()=>[],addEventListener(){}};
 const context = vm.createContext({window,document,console,URLSearchParams,fetch:async url=>{if(fail)throw new Error('offline');return {ok:true,json:async()=>url.includes('catalogue')?{records:[],model_cards:[]}:url.includes('preview')?{products:[]}:[]}}});
 vm.runInContext(script,context);
 window.CouponWorldMobileResearch.search('phone under 30000');
 assert(el('mobileResearchResults').innerHTML.includes('Standard Buying Guide'));
 await new Promise(resolve=>setImmediate(resolve));
 if(fail){assert(el('mobileResearchSearchStatus').textContent.includes('temporarily unavailable'));window.CouponWorldMobileResearch.search('phone under 50000');assert(!el('mobileResearchSearchStatus').textContent.includes('Loading'));assert(el('mobileResearchResults').innerHTML.includes('/guides/smartphone-buying-guide/'));}
}
(async()=>{await scenario(true);await scenario(false);const source=fs.readFileSync('app.js','utf8');const start=source.indexOf('function standardBuyingGuideFallback()');const end=source.indexOf('async function loadShoppingRecommendation',start);const context=vm.createContext({});vm.runInContext(source.slice(start,end),context);assert(context.renderOfferUnavailable().includes('Standard Buying Guide'));assert(fs.existsSync('public/guides/smartphone-buying-guide/index.html'));console.log('PASS loading, offline, repeated failed search and unavailable-offer guide fallbacks');})();
