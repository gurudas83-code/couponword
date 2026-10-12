# Coupon-World Phase-E final certification

Date: 2026-10-12  
Local release candidate: `f1b797be861fd3fda92849f6205c9466c1b09189`  
Current local HEAD after certification report: recorded in Git history  
Remote baseline: `5167712b369c81ab85779819763eee6e9b90a831`

## Status table

| Phase | Original gates | Passed | Failed | Not verified | Actual completion % | Remaining actions |
|---|---|---:|---:|---:|---:|---|
| A — production parity | local/remote/runtime/frontend parity | local checks | 0 | live Render/frontend SHA, live smoke | 50% | authorized push, deploy and live verification |
| B — intelligence UI | exact variant, price/source/time, reasons, unknowns, incomplete state | local API/renderer regressions | 0 known | browser production presentation | 80% | live browser smoke |
| C — analytics | event emission and actual receipts | code paths not re-audited in this run | 0 known | GA4/dashboard receipts | 50% | verify live events separately |
| D — mobile knowledge coverage | 126 priority seeds, verified identity/specs/offers/rankability | committed catalogue/evidence gates | no fabricated coverage claim | complete 126 reconciliation | 60% | reconcile verified/pending/rejected counts |
| E — local acceptance | parser, Gate-3, deterministic frozen checks | parser 1000/1000; Gate-3 14/14; 170 tests | 0 | full recommendation 1000 replay | 85% | production deployment and live gates |

## Measured evidence

- Parser/intent corpus `data/mobile_query_corpus_1000.json`: **1000/1000 PASS** in the saved versioned benchmark report. This validates parsing and expected constraint extraction, not recommendation quality.
- Full recommendation e2e report available for 10 representative queries: **6/10 PASS**, 4 incomplete/quality failures. No 1000-query full recommendation receipt exists; status is **NOT VERIFIED**.
- Original Phase-E Gate-3: seven fixture queries, two frozen calls each, **14/14 PASS**. Every call returned three eligible results with valid exact-listing price evidence, canonical identity and stable count/order.
- Full unittest discovery: **172 discovered; 170 PASS, 0 FAIL, 0 ERROR, 2 SKIP**. Skips are the optional `google.genai` dependency and absent optional semantic v1.3 fixture.
- Premium safety: ₹1.2L/₹1.5L responses expose `market_quality_status=INCOMPLETE` when premium coverage is not verified.

## Four saved E2E failures

These are from the saved remote `mobile_search_benchmark_e2e_report.json`
snapshot, not from the passing local Gate-3 fixture. The snapshot shows eight
discovered/evidence-ready candidates in each failing case, so the failure is
after discovery. It does not include the per-candidate rejection trace needed
to name a narrower source function; no code defect is proven by this receipt.

| ID/query | Actual result | Stage and root cause | Status |
|---|---|---|---|
| E001 `best phone under 20000` | 2 picks: redmi 15C 5G Prime Edition ₹19,499; Titan iQOO Z10 Lite 5G ₹18,999 | eligibility/selection retained only two verified qualifying rows in that remote snapshot; local Gate-3 has three under the frozen local evidence | BLOCKED — catalogue/evidence snapshot mismatch |
| E004 `Samsung phone under 25000` | 1 pick: Samsung Galaxy F36 5G ₹22,950 | brand-filtered eligibility had only one verified qualifying Samsung row in the remote snapshot | BLOCKED — verified Samsung coverage gap |
| E007 `gaming phone under 30000` | 2 picks, both realme 16X 5G variants at ₹27,999 | capability eligibility/variant dedup left two verified rows; the receipt does not prove whether other rows failed identity, evidence or score gates | BLOCKED — rejection trace/evidence gap |
| E010 `Samsung` | 1 pick: Samsung Galaxy F36 5G ₹22,950 | unbounded Samsung query had only one verified eligible row in the remote snapshot | BLOCKED — verified Samsung coverage gap |

The saved E2E report is therefore insufficient to justify a parser, identity,
threshold or scoring change. Filling these slots would require verified
catalogue/evidence additions, which are outside this controlled repair and must
not be fabricated. The local original Gate-3 remains **14/14 PASS**.

### Failure classifications

- **E001 — SNAPSHOT_DIFFERENCE:** the remote receipt has two eligible rows,
  while the local frozen Gate-3 snapshot has three for its approved fixture.
  The saved remote report contains no catalogue/evidence hash or per-candidate
  rejection trace, so the count difference cannot be attributed to a source
  function.
- **E004 — VERIFIED_COVERAGE_GAP:** only Galaxy F36 is verified in the saved
  Samsung-filtered remote result. Missing/rejected Samsung variants are not
  independently evidenced in the receipt.
- **E007 — INSUFFICIENT_DIAGNOSTICS:** two realme variants survived; the report
  has no rejection-stage rows for the other six candidates, so identity,
  evidence and score causes cannot be separated.
- **E010 — CONTRACT_GAP:** the saved generic Samsung expectation requires three
  picks, but no independent catalogue contract establishes three verified
  Samsung choices for an unbounded query. The one-row result is therefore an
  incomplete market response, not proof of a code failure.

The responsible existing paths are the pipeline's `run_pipeline` eligibility
and result-status path and the benchmark evaluator's `evaluate` function. No
shared code defect is proven, so no source or scoring change was made.

## Offline 1,000-query limitation

The committed 1,000-row corpus and `mobile_query_benchmark_phase3_report.json`
provide an independently labeled **intent/parser** result of 1000/1000. The
repository does not contain an approved independent expected-output file for
full recommendation correctness, nor a frozen full-pipeline replay harness
that records all semantic outputs without live discovery/retailer calls. The
available 10-query recommendation report is not a substitute. Consequently:

- Parser correctness: **1000/1000 PASS**.
- Full recommendation contractual correctness: **NOT VERIFIED** (no approved
  expected answer for the remaining rows).
- Full 1,000-query deterministic replay: **NOT VERIFIED**; no semantic
  before/after corpus receipt exists.
- No new code defect was identified to fix safely from the available evidence.

## Offline certification harness

`phase_e_offline_certification.py` and its focused test now provide a bounded
replay entry point. It freezes the corpus hash, refuses live network use,
requires an explicit complete catalogue/evidence/offer fixture manifest before
invoking the real pipeline, and writes machine-readable results to
`data/phase_e_offline_certification.json`.

The first run processed all 1,000 queries twice at the harness level:

- Full-pipeline executable cases: **1 pilot query; 0/1000 corpus rows**
- Fixture gaps: **1000**
- Deterministic semantic matches: **0/0 executable**
- Quality review cases: 40 **PROPOSED**, not independently approved

This is an honest infrastructure result: candidate snapshots exist, but the
required durable evidence/offer fixture manifest does not. The harness will
not silently use live discovery or treat candidate snapshots as complete
pipeline fixtures. E007 remains **INSUFFICIENT_DIAGNOSTICS** and E010 remains
**CONTRACT_GAP**; no third recommendation was invented.

The real-engine pilot now proves one executable path using the existing frozen
`mobile under 10000` candidate snapshot. It ran intent parsing, 15-candidate
selection, canonical identity, official/evidence gates, eligibility, scoring,
ranking and response serialization twice: **1/1 executed, 1/1 deterministic,
3 recommendations returned**. The other corpus queries remain fixture gaps;
this pilot is not a 1000-query market-quality claim.

## Frozen manifest attempt

`data/phase_e_offline_fixture_manifest.json` now records the durable source
inventory: 37 registry products, 9 official-spec products and 8 saved offer
records. The offer/cache files are modified in the worktree and are explicitly
excluded from release. Because discovery inputs are not a complete frozen
semantic snapshot (`complete_frozen_inputs=false`), the 10-query pilot
executed **0/10** and the full replay executed **0/1000**; all were recorded as
`FIXTURE_GAP`, with no network calls. Deterministic comparisons are **0/0
executable**, not 1000 passes.

## A–D recheck conclusions

- **A — NOT VERIFIED:** local HEAD and remote baseline are known; no current Render backend/frontend SHA or live smoke receipt is available.
- **B — PASS locally:** prior renderer/API acceptance and current Gate-3 payload checks preserve exact variant, price evidence, source/time, reasons, trade-offs and unknown fields. Production browser presentation remains NOT VERIFIED.
- **C — NOT VERIFIED:** code-level analytics receipt was not claimed as GA4/dashboard delivery. No traffic, clicks or revenue numbers are inferred.
- **D — INCOMPLETE:** the priority universe file contains 187 seed rows, while the requested historical 126-priority reconciliation is not a verified-catalogue count. Unverified seeds remain pending and are not counted as completed products.

## Release decision

**RELEASE READY: NO for production.** Local code is release-candidate quality for the original seven-query contract, but production closure requires an authorized push, exact Render/backend and frontend revision verification, one live seven-query matrix, representative browser smoke and critical latency/error checks. No push or deploy was performed.

The remaining blocker is deployment authorization and live verification, plus the missing full recommendation 1000-query deterministic receipt. No new Phase-F or Phase-G work was started.

## Resume checkpoint

Next session: read this file first; do not repeat parser, premium source or local Gate-3 work. If production authorization is granted, push the reviewed local release SHA, verify remote/Render/frontend revisions, run the live seven-query matrix once, then record PASS/FAIL/NOT VERIFIED outcomes.
