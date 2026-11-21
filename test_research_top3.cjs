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

const appSource = fs.readFileSync("app.js", "utf8");
const routeStart = appSource.indexOf("function isExplicitTopThreeQuery(");
const routeEnd = appSource.indexOf('heroSearchButton.addEventListener("click"', routeStart);
assert(routeStart >= 0 && routeEnd > routeStart, "Existing hero search route not found");
let routedSearch = null;
const routeContext = vm.createContext({
  window: {CouponWorldMobileResearch: {
    isResearchQuery() { return false; },
    submit(query) { routedSearch = query; },
  }},
  document: {getElementById() { return {scrollIntoView() {}}; }},
});
vm.runInContext(appSource.slice(routeStart, routeEnd), routeContext);
assert.equal(vm.runInContext('submitMobileResearchIfApplicable("top 3 phones under 25000")', routeContext), true);
assert.equal(routedSearch, "top 3 phones under 25000");
assert.equal(vm.runInContext('submitMobileResearchIfApplicable("iPhone 13")', routeContext), false,
  "A normal model number must not be mistaken for Top 3");

(async () => {
  await new Promise(resolve => setImmediate(resolve));
  const research = window.CouponWorldMobileResearch;
  assert(research, "Existing research engine did not initialize");
  const matches = research.submit("top 3 phones under 25000");
  const first = element("mobileResearchResults").innerHTML;
  assert.match(first, /Research-Verified (?:Top 3|picks)/, "Top 3 must render India-exact evidence lane");
  assert((first.match(/class="research-top3-result"/g) || []).length <= 3);
  assert((first.match(/class="research-top3-result"/g) || []).length > 0, "25k must retain a sourced maker-India variant");
  assert.match(first, /Current price and selected budget range unverified|Dated reference in selected band/);
  assert.match(first, /Check live price on Amazon \(search\)/);
  assert.match(first, /Check live price on Flipkart \(search\)/);
  assert.match(first, /not measured camera, gaming or battery superiority/);
  assert.match(first, /tag=guru07cc-21/);
  assert.equal(shoppingCalls, 0, "Research Top 3 must not make an external shopping/paid API call");

  // Budget Top 3 must never admit unpriced models just to fill three slots.
  for (const budget of [10000, 15000, 20000, 25000, 30000]) {
    research.submit("top 3 phones under " + budget);
    const budgetHtml = element("mobileResearchResults").innerHTML;
    const budgetPicks = (budgetHtml.match(/class="research-top3-result"/g) || []).length;
    const picks = Array.from(budgetHtml.matchAll(/class="research-top3-result"[\s\S]*?data-mobile-model-card="([^"]+)"/g), m => m[1]);
    assert.equal(picks.length, budgetPicks, budget + " all chosen phones must be parseable");
    for (const key of picks) {
      const card = catalogue.model_cards.find(m => m.model_key === key);
      assert(card && card.india_identity_evidence.status === "INDIA_EXACT_VARIANT_DOCUMENTED",
        key + " cannot be recommended without official Indian market evidence");
      const ref = card.research_budget_reference;
      assert(ref && card.india_identity_evidence.verified_variants.some(v =>
        v.ram_gb === ref.ram_gb && v.storage_gb === ref.storage_gb),
        key + " manufacturer RAM/storage must match priced RAM/storage");
    }

    const datedQualified = (budgetHtml.match(/Dated reference in selected band; current price unverified/g) || []).length;
    assert.equal(budgetPicks, datedQualified, budget +
      " must not rank a phone without a dated reference in its budget band");
    assert.doesNotMatch(budgetHtml, /Current price and selected budget range unverified/,
      budget + " has an unpriced phone incorrectly inside ranked Top 3");
    assert.match(budgetHtml, /Price-unknown phones appear separately below/,
      "Price unknown research must stay in a separate lane");
  }
  research.submit("top 3 phones under 10000");
  const lowerBudget = element("mobileResearchResults").innerHTML;
  assert.match(lowerBudget, /Research-Verified (?:Top 3|picks)/);
  assert((lowerBudget.match(/class="research-top3-result"/g) || []).length <= 3);
  assert.match(lowerBudget, /Additional relevant phones|Price-unknown phones appear separately below/);

    research.submit("top 3 phones under 15000");
  const midBudget = element("mobileResearchResults").innerHTML;
  assert.match(midBudget, /Research-Verified (?:Top 3|picks)/);
  assert((midBudget.match(/class="research-top3-result"/g) || []).length <= 3);
  assert.doesNotMatch(midBudget, /class="research-top3-result"[\s\S]*?data-mobile-model-card="oppo\|a5x"/,
    "Wrong A5x 4G/5G reference must never become a Top 3 research recommendation");

    research.submit("top three battery phones");
  const second = element("mobileResearchResults").innerHTML;
  assert.match(second, /Research-Verified Top 3|Research-Verified picks \([0-3]\/3 available\)/);
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
