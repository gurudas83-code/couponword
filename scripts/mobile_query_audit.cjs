#!/usr/bin/env node
// Read-only 1,000-query smoke/coverage audit of the EXISTING browser research engine.
// A no-result query is a coverage gap, not proof that the product does not exist.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const assert = require("node:assert/strict");

const root = path.resolve(__dirname, "..");
const output = process.argv.includes("--report")
  ? process.argv[process.argv.indexOf("--report") + 1] : "mobile-query-audit.json";
const corpus = JSON.parse(fs.readFileSync(path.join(root, "data/mobile_query_corpus_1000.json"), "utf8"));
const catalogue = JSON.parse(fs.readFileSync(path.join(root, "public/data/mobile_research_catalogue.json"), "utf8"));
const preview = JSON.parse(fs.readFileSync(path.join(root, "data/mobile_research_preview.json"), "utf8"));
const tests = ["train", "validation", "test"].flatMap(split =>
  (corpus.splits[split] || []).map(row => ({...row, split}))
);
assert.equal(tests.length, 1000, "Query corpus changed from 1,000");

const elements = new Map();
function element(id) {
  if (!elements.has(id)) {
    elements.set(id, {
      id, value:"", innerHTML:"", textContent:"", hidden:false, tagName:"DIV", events:{},
      addEventListener(name, callback) {this.events[name] = callback;},
      scrollIntoView() {}
    });
  }
  return elements.get(id);
}
const document = {
  getElementById:element, querySelectorAll:() => [], events:{},
  addEventListener(name, callback) {this.events[name] = callback;}
};
const window = {location:{hash:""}, addEventListener() {}};
const context = vm.createContext({
  document, window, console, URL, URLSearchParams,
  fetch: async url => ({ok:true, json:async () => url.includes("mobile_research_catalogue")
    ? catalogue : url.includes("mobile_research_preview") ? preview : []})
});
vm.runInContext(fs.readFileSync(path.join(root, "mobile-research-preview.js"), "utf8"), context);

setImmediate(() => {
  const app = window.CouponWorldMobileResearch;
  assert(app && typeof app.search === "function", "Existing mobile research API missing");
  const grouped = {}, zero = [], failures = [];
  let withMatches = 0, totalReturned = 0, sourceSupported = 0, zeroWithUnpricedLeads = 0;
  for (const item of tests) {
    let rows;
    try {
      rows = app.search(item.query);
      if (!Array.isArray(rows)) throw new Error("Query did not return an array");
      for (const row of rows) {
        if (!row || !row.card || !row.card.model_key) throw new Error("Noncanonical match");
        if (row.card.purchase_cta_eligible === true || row.card.current_offer_verified === true)
          throw new Error("Research-only card incorrectly promoted to live commerce");
      }
      const html = element("mobileResearchResults").innerHTML;
      if (/<a[^>]+href="http:\/\//i.test(html)) throw new Error("Insecure outgoing retailer link");
      if (rows.length) {
        withMatches++;
        totalReturned += rows.length;
        sourceSupported += rows.filter(row =>
          Object.values(row.card.specifications || {}).some(v => v.source_url && v.source_url.startsWith("https://"))
        ).length;
      } else if (zero.length < 125) {
        if (html.includes("research-unpriced-leads")) zeroWithUnpricedLeads++;
        zero.push({id:item.id, split:item.split, query:item.query, tags:item.tags || []});
      }
      for (const tag of item.tags || []) {
        (grouped[tag] ||= {queries:0, with_results:0}).queries++;
        if (rows.length) grouped[tag].with_results++;
      }
    } catch (error) {
      failures.push({id:item.id, query:item.query, type:error.constructor.name, message:String(error.message).slice(0,220)});
    }
  }
  const result = {
    checked_at_utc:new Date().toISOString(),
    mode:"RESEARCH_ANSWER_REGRESSION_AUDIT_NOT_RETAILER_OR_PERFORMANCE_VERIFICATION",
    corpus_total:tests.length,
    with_research_matches:withMatches,
    zero_research_matches:tests.length-withMatches-failures.length,
    zero_with_separate_unpriced_research_leads:zeroWithUnpricedLeads,
    source_supported_result_count:sourceSupported,
    total_research_rows_returned:totalReturned,
    hard_runtime_failures:failures.length,
    by_query_tag:grouped,
    unresolved_query_examples:zero,
    runtime_failures:failures.slice(0,100),
    interpretation:"Research matches are NOT ranked winners, buyable offers or all suitable India devices. 0 matches means source coverage gap or hard constraints, NOT no product exists."
  };
  fs.mkdirSync(path.dirname(output), {recursive:true});
  fs.writeFileSync(output, JSON.stringify(result,null,2)+"\n", "utf8");
  console.log(JSON.stringify({
    corpus:result.corpus_total,
    with_research_matches:withMatches,
    zero_research_matches:result.zero_research_matches,
    zero_with_separate_unpriced_research_leads:zeroWithUnpricedLeads,
    runtime_failures:result.hard_runtime_failures,
    source_supported_result_count:sourceSupported
  }));
  if (failures.length) process.exitCode=1;
});
