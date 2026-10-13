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

## Corpus-to-snapshot compatibility

The corpus contains **1000 query IDs and 1000 unique structured signatures**;
the discovery cache contains **42** candidate snapshots. Compatibility now
compares category, budget range, brand, must-have variant constraints,
preferences and exclusions. Exact-model, RAM and storage-tagged corpus rows
are never mapped to a generic budget snapshot. The first ten corpus rows
therefore remain **0/10 executable** under the strict mapping, while the
separate generic pilot remains **1/1 executable**. This prevents a false
identity/variant match.

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

## Frozen catalogue integration lane

The harness now supports `--catalogue-mode`, building candidates only from
registry-owned ASINs matched to the existing catalogue and labeling the source
`FROZEN_CATALOGUE_INTEGRATION`. Identity, evidence, eligibility, scoring,
ranking and serialization remain the existing pipeline stages.

Pilot `mobile under 10000`: **1/1 real catalogue-backed execution**, **1/1
deterministic**, with 3 recommendations. Missing or stale offers remain under
the existing incomplete/unknown contracts. The full corpus is not certified;
verified offer coverage and bounded runtime remain the blockers.

## Catalogue execution completion update

The catalogue lane was then run against the first ten original corpus IDs:

- **10/10 pipeline executions**
- **5** returned scored recommendations
- **5** returned honest incomplete results
- **0** technical execution failures
- **0** fixture gaps in the catalogue lane
- Deterministic semantic replay: **10/10 matches**

The attempted 100-query batch exceeded the local command execution window
before producing a receipt; it is therefore **UNEXECUTED**, not a pass. The
remaining limitation is bounded runtime for the current evidence resolver and
offer coverage, not a hidden recommendation result.

## Resolver performance completion update

Profiling confirmed repeated `product_evidence_store.load_store()` hydration
inside `find_verified_evidence()` for every candidate. The existing pipeline
now loads the immutable evidence store once per `_run_pipeline_once` batch and
passes it into exact variant-aware lookups. No scoring, identity or freshness
rule changed.

After the fix, the 20-query catalogue replay completed in **20/20 executions**
(8 scored, 12 incomplete, 0 technical failures, 20/20 deterministic matches)
in 16.23 seconds. The 100-query batch completed **100/100** (41 scored, 59
incomplete, 0 technical failures, 100/100 deterministic matches). A 1000-query
attempt was stopped after proving the current per-query resolver cost remains
too high for one local run; no partial 1000 receipt is counted as PASS.

## Resumable 1000-query certification update

The runner now accepts `--offset`, `--limit` and an append-only `--checkpoint`.
Each batch records the corpus hash, Run-A/Run-B counts and semantic-match status.
A fresh checkpointed ten-query batch completed **10/10** executions (5 scored,
5 incomplete, 0 technical failures, 10/10 deterministic matches). The full
1000-query Run-A and Run-B receipts remain **UNEXECUTED**; the earlier
single-process attempt was stopped and is not counted as certification.

Next exact action: continue the original corpus in bounded checkpointed batches
until all 1000 IDs have Run-A and Run-B receipts, then aggregate the checkpoint
without changing the engine or evidence rules.

## Phase-E 1000-query execution receipt

The existing frozen-catalogue runner completed both independent passes:

- Run-A: **1000/1000** executed.
- Run-B: **1000/1000** executed.
- Executed with scored recommendations: **342**.
- Executed incomplete: **658**.
- Technical execution failures: **0**.
- Fixture gaps: **0**.
- Budget violations in returned recommendations: **0**.
- Semantic Run-A/Run-B matches: **922/1000**; mismatches: **78**.

The mismatches cluster in the later corpus IDs and show a shared-state/cache
effect: Run-A mutates the existing runtime/evidence cache, after which Run-B
can change qualifying counts for the same frozen catalogue. This is a proven
determinism defect in the existing execution path; it is not a scoring or
identity threshold change. Market-quality certification remains separate and
unverified for the 658 incomplete cases and for recommendations without an
independent market-quality oracle. Phase-E technical certification is
**INCOMPLETE** until the cache isolation defect is repaired and the 1000-query
semantic replay reaches 1000/1000.

## Determinism repair attempt

The proven write path was `shopping_intelligence_pipeline._run_pipeline_once`
calling `save_verified_evidence()` while processing the frozen catalogue. The
certification lane now disables that persistent evidence write only when
`--catalogue-mode` is active; normal production runs retain their existing
verified-evidence persistence behavior. A focused replay of a previously
mismatched query produced identical Run-A/Run-B semantic outputs, including
zero-result and stage counts.

Focused frozen-lane tests: **2/2 PASS**. The broader harness still has one
pre-existing failure in the non-catalogue pilot because the mutable working
cache no longer contains its historical three-result fixture. The saved
1000-query receipts remain **922/1000** until a fresh full replay after this
repair.

Fresh post-fix replay status: new Run-A receipts completed offsets `0`, `100`,
and `200` (**300/1000**). Offset `300` was stopped before completion to
preserve completed receipts; fresh Run-B has not started. The new benchmark is
therefore **INCOMPLETE**, and no fresh deterministic total is claimed.

## Final post-fix 1000-query replay

The resumed fresh namespaces completed independently:

- Run-A: **1000/1000**.
- Run-B: **1000/1000**.
- Deterministic semantic matches: **1000/1000**; mismatches: **0**.
- Scored recommendations: **0**.
- Honest incomplete responses: **1000**.
- Technical failures: **0**.
- Fixture gaps: **0**.

The frozen catalogue/evidence/offer inputs remained semantically stable across
both passes. The result is a valid determinism and execution PASS, but not a
market-quality PASS: the frozen lane currently has no qualifying verified
recommendations for this corpus. The non-catalogue historical pilot fixture
still fails its three-result expectation because its mutable working evidence
state cannot be reconstructed from the current cache without the original
fixture snapshot.

The original Gate-3 focused regression remains **7/7 PASS**. Phase-E offline
technical certification is **PASS** for deterministic frozen execution;
market-quality certification remains **INCOMPLETE**.

## Positive-path validation

The historical 342-to-0 change is explained by the old mutable run: it used
temporary cache prices/evidence and persisted newly extracted records while
processing the catalogue. The durable current stores do not contain those
same buyable facts. The current retailer offer store has **8** offers total;
the mobile records are dated **2026-08-28/29** (and one test record is dated
2026-09-20), so they fail the current freshness contract. The three Lava
registry identities have exact product/evidence records, but no current exact
retailer offer in the durable offer store.

Representative catalogue queries (`mobile under 10000`, `mobile under
50000`, and the generic original-corpus cases) therefore produced **0
verified buyable recommendations**. Positive scored integration cases: **0/10
supportable** from the existing durable evidence; positive deterministic
cases: **0/0**. This is a verified offer-coverage gap, not a relaxed threshold
or a new resolver defect. No stale price was promoted to current.

The historical non-catalogue three-result test remains **FAIL** because its
original mutable evidence fixture is not present in the current durable store;
the required replacement is the archived evidence and exact offer snapshot
for that test, not fabricated products.

## Verified offer recovery and positive path

Four existing registry products were verified through the approved exact Amazon
product-page adapter and paired with their existing official evidence:

| Canonical ID | Exact variant | ASIN | Observed price | Availability |
|---|---|---|---:|---|
| `cw-mobile-79` Lava Bold N2 Lite | 3GB/64GB | `B0GPXTY8V5` | ₹9,099 | in stock |
| `cw-mobile-77` Lava Virat V1 | 4GB/64GB | `B0HG9SZ7HD` | ₹9,889 | in stock |
| `cw-mobile-100` Samsung Galaxy A56 5G | 8GB/128GB | `B0H1WY55ZL` | ₹31,999 | in stock |
| `cw-mobile-105` Motorola Signature | 12GB/256GB | `B0GKB38XWZ` | ₹59,869 | in stock |

Each observation has an exact ASIN, direct product URL, buy-box price,
explicit stock state and UTC observation timestamp. The immutable offer receipt
is `data/phase_e_positive_offer_snapshot_2026-10-13.json` with catalogue hash
`d05b25c0c60d9e857543f07f18c47f38112fa6c5832457ff8f824433edf4922b`, evidence
hash `4355adf15284b0965eb5220ae4fa735bd02900c77282669b2a1a6a610d4fe809` and
offer hash `ac332d0b28499a1f262b136b691d7c1b907370d7d821e505f7e768c7573b5dcd`.

Positive integration replay using the existing pipeline produced **4/4 scored
query cases** (under ₹10,000, under ₹50,000, exact A56 and exact Virat) and
**4/4 deterministic Run-A/Run-B matches**. The under-₹10,000 result returned
the two genuinely eligible Lava phones; the under-₹50,000 result returned
three phones led by A56 at ₹31,999. No threshold or identity rule changed.

## Final-gap focused validation

After a bounded refresh of the same four exact ASINs, the existing pipeline
returned scored results for all six requested budgets:

| Query | Result | Top returned evidence |
|---|---|---|
| under ₹10k | PASS | Bold N2 Lite ₹9,099; Virat V1 ₹9,889 |
| under ₹20k | PASS | Bold N2 Lite; Virat V1 |
| under ₹30k | PASS | Bold N2 Lite; Virat V1 |
| under ₹40k | PASS | A56 ₹31,999; Bold N2 Lite; Virat V1 |
| under ₹50k | PASS | A56 ₹31,999; Bold N2 Lite; Virat V1 |
| under ₹1.2 lakh | PASS | Motorola Signature ₹59,849; A56 ₹31,999; Bold N2 Lite |

The equivalent spellings `mobile under 30000`, `mobile under 30 k` and
`mobile under 30k` produced identical two-result sets and scores: **3/3
deterministic matches**. Preference checks produced 2 scored and 1 honest
incomplete response (battery under ₹20k has insufficient verified capability
coverage); all three were deterministic. Exact identity, RAM/storage, fresh
price and stock gates held. Camera and gaming responses retained their
explanations and evidence basis.

The refreshed immutable offer receipt is
`data/phase_e_positive_offer_snapshot_2026-10-13-refresh.json`; Motorola's
observed buy-box changed from ₹59,869 to ₹59,849, so the earlier snapshot was
preserved rather than overwritten. The historical three-result test remains
unresolved because its original evidence fixture is unavailable. Local HEAD is
`20d3cd4fe6a1501d7c00e5e3c5abb2f220421194`; `origin/main` is
`5167712b369c81ab85779819763eee6e9b90a831`. Render production SHA is
**UNVERIFIED** from this local environment.

## Score transparency and release audit

For criterion weights `w_i` and normalized match values `m_i`, the existing
engine computes:

`raw_fit = round(100 * sum(w_i*m_i for known criteria) / sum(w_i for known criteria))`

`evidence_coverage = round(100 * sum(w_i for known criteria) / sum(w_i for all criteria))`

`fit = round(raw_fit * evidence_coverage / 100)`.

Unknown criteria contribute zero points and zero known weight; they receive no
unsupported credit. Eligibility still requires no hard-constraint failures,
`fit >= 50` and evidence coverage `>= 50`. Capability `quality_score` excludes
budget and is reported separately. Ranking uses quality score, quality evidence
coverage, fit and stable identity; affiliate data is not used.

The API now carries `score_trace` with policy version, interpreted query
weights, existing criterion match/weight/points/status/reason, eligibility
failures and criterion-level source URL/observation provenance. `app.js` renders it in an
expandable **Why this Fit Score?** section. Focused score-trace and frozen
replay tests pass (**2/2**); frontend syntax validation passes.

The historical pilot remains **FAIL** (5 harness tests: 4 PASS, 1 FAIL; its
three-result expectation depends on an unavailable archived evidence snapshot).
It was not deleted, skipped or weakened; the separate verified positive-path
replacement passes.

Git audit: local `main` is **37 commits ahead** of `origin/main` (`5167712…`),
and no remote branch contains current HEAD. Runtime/price/evidence caches,
generated outputs and backups remain uncommitted and excluded. Render and live
frontend revisions are **UNVERIFIED**. The pending release includes backend,
frontend, data and historical report changes and needs a separate push review.
The existing `admin.html` generator now includes a structured evidence-review
record form. It reuses the current evidence vocabulary and emits a review JSON
record with `writes_calculated_score: false`; it cannot overwrite evidence or
Fit scores. No second evidence database or dashboard was created.
