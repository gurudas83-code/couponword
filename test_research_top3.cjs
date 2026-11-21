// Offline regression: explicit Top 3 must use source-backed local matches
// without retailer API calls, imaginary stock, or a model-number "3" trap.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const catalogue = JSON.parse(fs.readFileSync("public/data/mobile_research_catalogue.json", "utf8"));
const preview = JSON.parse(fs.readFileSync("data/mobile_research_preview.json", "utf8"));
assert.equal(catalogue.model_cards.length, 232);

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id, value: "", innerHTML: "", textContent: "", hidden: false,
      addEventListener() {}, scrollIntoView() {}, focus() {},
    });
  }
  return elements.get(id);
}
let shoppingCalls = 0;
const window = {
  location: {hash: "", search: ""},
  addEventListener() {},
  localStorage: {getItem() { return null; }, setItem() {}, removeItem() {}},
  CouponWorldShoppingRecommend() { shoppingCalls++; },
};
const document = {
  getElementById: element,
  querySelectorAll() { return []; },
  addEventListener() {},
};
function fetch(url) {
  if (url.includes("mobile_research_catalogue")) return Promise.resolve({ok: true, json: async () => catalogue});
  if (url.includes("mobile_research_preview")) return Promise.resolve({ok: true, json: async () => preview});
  if (url.includes("/coupons.json")) return Promise.resolve({ok: true, json: async () => []});
  if (url.includes("india_sales_eight_research") || url.includes("india_recent_manufacturer_research")) {
    return Promise.resolve({ok: true, json: async () => null});
  }
  throw new Error("Unexpected data request: " + url);
}
const context = vm.createContext({window, document, fetch, console, URL, URLSearchParams, Map, Set});
vm.runInContext(fs.readFileSync("mobile-research-preview.js", "utf8"), context);

(async () => {
  await new Promise(resolve => setImmediate(resolve));
  const research = window.CouponWorldMobileResearch;
  assert(research, "Existing research engine did not initialize");
  const matches = research.submit("top 3 phones under 25000");
  const first = element("mobileResearchResults").innerHTML;
  assert.match(first, /Research-Verified Top 3/, "Three sourced models must be visible from local catalog");
  assert.equal((first.match(/class="research-top3-result"/g) || []).length, 3);
  assert.match(first, /Current price and selected budget range unverified|Dated reference in selected band/);
  assert.match(first, /Check live price on Amazon \(search\)/);
  assert.match(first, /Check live price on Flipkart \(search\)/);
  assert.match(first, /not measured camera, gaming or battery superiority/);
  assert.match(first, /tag=guru07cc-21/);
  assert.equal(shoppingCalls, 0, "Research Top 3 must not make an external shopping/paid API call");

  research.submit("top three battery phones");
  const second = element("mobileResearchResults").innerHTML;
  assert.match(second, /Research-Verified Top 3|Research-Verified picks \([012]\/3 available\)/);
  assert.equal(shoppingCalls, 0);

  // Phone (3) is a real model name; the top-three instruction detector
  // must never reinterpret the isolated model number as a rank request.
  research.search("Nothing Phone (3)");
  const named = element("mobileResearchResults").innerHTML;
  assert.doesNotMatch(named, /Research-Verified Top 3/);

  research.submit("phone under 20000");
  const normal = element("mobileResearchResults").innerHTML;
  assert.doesNotMatch(normal, /Research-Verified Top 3/);
  assert.match(normal, /not a verified Top-3 recommendation/);
  console.log("PASS: local Research-Verified Top 3, source gate, budget warning, retailer searches, no paid calls, model 3 identity, normal research unaffected");
})().catch(error => {console.error(error); process.exitCode = 1;});
