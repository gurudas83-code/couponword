// Deterministic cold-start regression without real sleeping, paid calls, or network access.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");

const source = fs.readFileSync("app.js", "utf8");
const constants = source.slice(
  source.indexOf("const RECOMMENDATION_TIMEOUT_MS ="),
  source.indexOf("// Keep the published site", source.indexOf("const RECOMMENDATION_TIMEOUT_MS ="))
);
const start = source.indexOf("async function loadShoppingRecommendation(");
const end = source.lastIndexOf('\nloadShoppingRecommendation("");');
assert(start !== -1 && end > start, "Expected existing single frontend recommendation route");
const fn = source.slice(start, end);
assert.equal((source.match(/"\/api\/recommend\?q="/g) || []).length, 1);

function harness() {
  const timers = new Map();
  let timerId = 0;
  const requests = [];
  let resolveRequest;
  let rejectRequest;
  const progress = { textContent: "" };
  const button = { addEventListener() {} };
  const card = {
    innerHTML: "",
    querySelector(selector) {
      if (selector === "[data-recommendation-progress]") return progress;
      if (selector === "[data-retry-recommendation]") return button;
      return null;
    }
  };
  const section = { hidden: true, scrollIntoView() {} };
  const window = {
    setTimeout(callback, delay) {
      const id = ++timerId;
      timers.set(id, { callback, delay });
      return id;
    },
    clearTimeout(id) {
      timers.delete(id);
    }
  };
  const fetch = (url, { signal }) => {
    requests.push(url);
    return new Promise((resolve, reject) => {
      resolveRequest = resolve;
      rejectRequest = reject;
      signal.addEventListener("abort", () => {
        const error = new Error("aborted");
        error.name = "AbortError";
        reject(error);
      });
    });
  };
  const context = vm.createContext({
    window, fetch, AbortController,
    document: { getElementById: id => id === "shoppingBrainCard" ? card : id === "aiRecommendation" ? section : null },
    API_BASE_URL: "https://couponword.onrender.com",
    recommendationRequestId: 0,
    recommendationController: null,
    analyticsSearchTerm: q => q,
    trackAnalyticsEvent() {},
    standardBuyingGuideFallback: () => '<a href="#mobileResearchSearch">Browse saved smartphone research</a>',
    isResearchComparisonQuery: () => false,
    loadResearchComparisonFallback: async () => null,
    escapeHTML: s => s,
    console: { error() {}, log() {} },
  });
  const routing = source.slice(source.indexOf("function isExplicitTopThreeQuery("), source.indexOf("function submitMobileResearchIfApplicable("));
  vm.runInContext(constants + "\n" + routing + "\n" + fn, context);
  return {
    context, timers, requests, card, progress, section,
    load(query, background) {
      return vm.runInContext(
        'loadShoppingRecommendation(' + JSON.stringify(query) +
        ', {background: ' + String(!!background) + '})', context
      );
    },
    settle(payload) {
      resolveRequest({ ok: true, json: async () => payload });
    }
  };
}

async function run() {
  const visible = harness();
  const inFlight = visible.load("gaming phone under 20000", false);
  assert.equal(visible.requests.length, 1, "No duplicate API call on user search");
  assert(visible.card.innerHTML.includes("Browse saved smartphone research"));
  assert(visible.card.innerHTML.includes('role="status"'));
  assert.deepEqual([...visible.timers.values()].map(t => t.delay).sort((a,b) => a-b),
    [8000, 75000]);

  // A response after the old 15-second timeout must still be accepted.
  visible.timers.forEach(t => { if (t.delay === 8000) t.callback(); });
  assert.match(visible.progress.textContent, /may be waking up/);
  assert.equal(visible.requests.length, 1);
  visible.settle({ recommendations: [], result_status: "PARTIAL" });
  await inFlight;
  assert.match(visible.card.innerHTML, /No strong match found/);
  assert.equal(visible.timers.size, 0, "Both wake hint and request timeout cleared");

  const hung = harness();
  const hungPromise = hung.load("gaming phone under 20000");
  const deadline = [...hung.timers.values()].find(t => t.delay === 75000);
  assert(deadline, "Explicit request keeps bounded 75-second deadline");
  deadline.callback();
  await hungPromise;
  assert.match(hung.card.innerHTML, /did not respond within 75 seconds/);
  assert.match(hung.card.innerHTML, /Browse saved smartphone research/);
  assert.equal(hung.requests.length, 1, "Do not automatically replay paid/shopping requests");
  assert.equal(hung.timers.size, 0);

  // Empty Top 3 must not manufacture ranked winners or strand the shopper.
  const emptyTop3 = harness();
  const top3Promise = emptyTop3.load("top 3 camera phones under 20000");
  assert.equal(emptyTop3.requests.length, 1, "Explicit Top 3 uses one existing API request");
  assert.match(emptyTop3.requests[0], /\/api\/recommend\?q=best%20camera%20phones%20under%2020000/);
  emptyTop3.settle({
    recommendations: [],
    response_reason: "NO_CURRENT_VERIFIED_OFFER",
    result_status: "PARTIAL",
    market_data_status: "CURRENT_OFFERS_UNAVAILABLE",
    hard_gate_rejections: [{code: "NO_CURRENT_VERIFIED_OFFER"}]
  });
  await top3Promise;
  assert.match(emptyTop3.card.innerHTML, /Verified Top 3 is not available/);
  assert.match(emptyTop3.card.innerHTML, /No current verified retailer offer passed/);
  assert.match(emptyTop3.card.innerHTML, /Explore 30 source-linked phone candidates/);
  assert.match(emptyTop3.card.innerHTML, /href="\/compare\/"/);
  assert(!emptyTop3.card.innerHTML.includes("</p>\\n"), "Literal newline escapes must not leak into HTML");
  assert.equal(emptyTop3.requests.length, 1, "No hidden paid or extra API call");

  const exactVariant = harness();
  const exactPromise = exactVariant.load("top 3 phones with 8GB 256GB under 25000");
  exactVariant.settle({
    recommendations: [],
    response_reason: "EXACT_VARIANT_UNAVAILABLE",
    result_status: "PARTIAL",
    hard_gate_rejections: [{code: "EXACT_VARIANT_UNAVAILABLE"}]
  });
  await exactPromise;
  assert.match(exactVariant.card.innerHTML, /requested RAM\/storage variant could not be verified/);

  const background = harness();
  const bgPromise = background.load("phone under 25000", true);
  assert.deepEqual([...background.timers.values()].map(t => t.delay), [15000]);
  background.timers.values().next().value.callback();
  await bgPromise;
  assert.equal(background.requests.length, 1);
  assert.equal(background.timers.size, 0);
  assert.equal(background.card.innerHTML, "", "Background failures remain unobtrusive");
  console.log("PASS: free-tier cold start, success after wake, bounded timeout, old short background checks, no duplicate shopping calls");
}

run().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
