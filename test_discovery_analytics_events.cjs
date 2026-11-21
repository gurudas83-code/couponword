// Consent-independent, anonymized on-page measurement QA: no user identifiers.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const script = fs.readFileSync("assets/discovery-analytics.js", "utf8");
const events = [];
const documentEvents = {};
const windowEvents = {};
const observations = {};
const window = {
  location: {search:"?utm_source=google",pathname:"/",origin:"https://coupon-world.in",href:"https://coupon-world.in/"},
  innerWidth:390,
  sessionStorage:{getItem(){return null},setItem(){}},
  gtag(eventName,name,params){assert.equal(eventName,"event");events.push({name,params})},
  performance:{getEntriesByType(type){return type==="navigation"?[{responseEnd:220}]:[]}},
  addEventListener(name,handler){windowEvents[name]=handler},
};
window.PerformanceObserver = class {
  constructor(callback){this.callback=callback}
  observe(options){observations[options.type]=this.callback}
};
const document={
  referrer:"https://www.google.com/search?q=phone",
  visibilityState:"visible",
  addEventListener(name,handler){documentEvents[name]=handler}
};
vm.runInNewContext(script,{window,document,URL,URLSearchParams,Date,Math,Number,JSON});
assert(events.some(e=>e.name==="discovery_landing"));
function click(url){
 const anchor={href:url};
 documentEvents.click({target:{closest(selector){return selector==="a[href]"?anchor:null}}});
}
// Budget chips are BUTTON elements, not anchor tags: track these too.
documentEvents.click({target:{closest(selector){
  if(selector==="a[href]") return null;
  if(selector.indexOf("[data-mobile-query]")>=0) return {
    matches(check){return check.indexOf("[data-mobile-query]")>=0},
    getAttribute(key){return key==="data-analytics-intent"?"budget_15000":null}
  };
  return null;
}}});
assert(events.some(e=>e.name==="research_action"&&e.params.action_kind==="budget_shortcut"), "Budget button conversion event missing");
click("https://www.amazon.in/s?k=iphone&tag=secrets");
click("https://www.flipkart.com/apple-iphone/p/itm123");
const outbound=events.filter(e=>e.name==="cw_retailer_outbound");
assert.equal(outbound.length,2);
assert.equal(outbound[0].params.retailer,"amazon.in");
assert.equal(outbound[0].params.listing_type,"retailer_search");
assert.equal(outbound[1].params.retailer,"flipkart.com");
assert(!JSON.stringify(outbound).includes("secrets"));
assert(!JSON.stringify(outbound).includes("iphone"));
observations["largest-contentful-paint"]({getEntries(){return [{startTime:874}]}});
observations["layout-shift"]({getEntries(){return [{value:0.03,hadRecentInput:false},{value:0.2,hadRecentInput:true}]}});
observations["event"]({getEntries(){return [{interactionId:12,duration:52}]}});
document.visibilityState="hidden";
documentEvents.visibilitychange();
windowEvents.pagehide();
const perf=events.filter(e=>e.name==="cw_field_performance");
assert.equal(perf.length,1);
assert.equal(perf[0].params.lcp_ms,874);
assert.equal(perf[0].params.cls_milli,30);
assert.equal(perf[0].params.inp_proxy_ms,52);
assert.equal(perf[0].params.response_end_ms,220);
assert(!JSON.stringify(perf).includes("query"));
console.log("PASS anonymized retailer outbound and 4 field-speed signals; no purchase or real-device SLA claim");
