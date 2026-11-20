// Search first-paint regression: optional India data must not hold core results.
// Synthetic network timings; tests functional behavior, NOT real-user 1s SLA.
const fs = require("node:fs");
const vm = require("node:vm");
const assert = require("node:assert/strict");
const {performance} = require("node:perf_hooks");

const core = JSON.parse(fs.readFileSync("public/data/mobile_research_catalogue.json", "utf8"));
const preview = JSON.parse(fs.readFileSync("data/mobile_research_preview.json", "utf8"));
const script = fs.readFileSync("mobile-research-preview.js", "utf8");
const elements = new Map();
let startedAt = 0;
let firstResultPaintMs = null;

function element(id) {
  if (!elements.has(id)) elements.set(id, {
    id, value: "", innerHTML: "", textContent: "", hidden: false,
    tagName: "DIV", events: {},
    addEventListener(event, fn) { this.events[event] = fn; },
    scrollIntoView() {}, focus() {},
  });
  return elements.get(id);
}
// Measure the FIRST meaningful result write, not later catalogue controls,
 // optional cards or Node's event-loop tick.
 const searchContainer = element("mobileResearchResults");
 let storedHtml = "";
 Object.defineProperty(searchContainer, "innerHTML", {
   get() { return storedHtml; },
   set(value) {
     storedHtml = String(value);
     if (firstResultPaintMs === null &&
         storedHtml.includes("research-budget-primary-grid") &&
         storedHtml.includes("data-mobile-model-card=")) {
       firstResultPaintMs = performance.now() - startedAt;
     }
   },
 });
 const document = {
  getElementById: element,
  querySelectorAll: () => [],
  addEventListener() {},
};
const deferred = [];
const called = [];
const verifiedCalls = [];
const window = {
  location: {hash: "", search: "?q=phone%20under%2020000"},
  addEventListener() {},
  localStorage: {getItem() { return null; }, setItem() {}, removeItem() {}},
  CouponWorldShoppingRecommend(query, options) {
    verifiedCalls.push({query, background: options.background});
  },
};
function fetch(url) {
  called.push(url);
  if (url.includes("mobile_research_catalogue")) return Promise.resolve({
    ok: true, json: async () => core
  });
  if (url.includes("mobile_research_preview")) return Promise.resolve({
    ok: true, json: async () => preview
  });
  if (url.includes("/coupons.json")) return Promise.resolve({
    ok: true, json: async () => []
  });
  if (url.includes("india_sales_eight_research") || url.includes("india_recent_manufacturer_research")) {
    return new Promise(resolve => deferred.push(() => resolve({ok: true, json: async () => null})));
  }
  throw new Error("Unexpected data fetch: " + url);
}
const context = vm.createContext({
  window, document, fetch, console,
  URL, URLSearchParams, Map, Set,
});
(async () => {
  startedAt = performance.now();
  vm.runInContext(script, context);
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(deferred.length, 2, "The two optional sources must remain pending");
  assert.equal(called.filter(s => s.includes("mobile_research_catalogue")).length, 1);
  const matches = window.CouponWorldMobileResearch.search("phone under 20000");
  assert(matches.length >= 1);
  assert.equal(element("mobileResearchResults").hidden, false);
  const html = element("mobileResearchResults").innerHTML;
  const visible = (html.match(/data-mobile-model-card=/g) || []).length;
  assert.equal(visible, Math.min(3, matches.length),
    "The first three research cards must show before optional fetch resolves");
  assert.match(html, /not a verified Top-3 recommendation/);
  assert.match(html, /Current checkout price, availability and delivery have NOT been confirmed/);
  assert(firstResultPaintMs !== null, "Core results never appeared before optional requests");
  assert(firstResultPaintMs < 1000,
    "Synthetic first meaningful result paint exceeded 1000ms: " + firstResultPaintMs);
  // Start initial URL query directly from the core, without a second paid API
  // call when the optional resources finally resolve.
  const callsBefore = verifiedCalls.length;
  deferred.forEach(resolve => resolve());
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(verifiedCalls.length, callsBefore,
    "Optional data refresh must not duplicate backend offer checks");
  assert.equal(called.filter(s => s.includes("india_sales_eight_research")).length, 1);
  assert.equal(called.filter(s => s.includes("india_recent_manufacturer_research")).length, 1);
  assert.match(element("mobileResearchResults").innerHTML, /not a verified Top-3 recommendation/);
  console.log("PASS: first three locally sourced research results before optional fetch, " +
    "no invented live offers, no duplicate API call, synthetic first meaningful paint " + firstResultPaintMs.toFixed(1) + "ms");
})().catch(error => { console.error(error); process.exitCode = 1; });
