# Coupon-World Phase-E final certification

Date: 2026-10-13  
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
| E — local acceptance | parser, Gate-3, deterministic frozen checks, approved historical-test supersession | parser 1000/1000; Gate-3 14/14; 170 tests; 21/21 closure checks; approved two-result successor | old three-result test preserved FAIL/FIXTURE_GAP | full recommendation 1000 replay and live deployment | local acceptance YES | staging/live gates |

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

## Final release preflight (2026-10-13)

The 40 functional local-only commits reviewed in this preflight end at
`c3bf5e8d9b83d22cdd25f951b808b8cbfdda4c60`. `origin/main` is
`5167712b369c81ab85779819763eee6e9b90a831`. This report is a separate
report-only local commit, so the branch is **41 commits ahead** after recording
the preflight; no remote branch contains the current local tip. No push or
deployment was performed.

### Historical three-result fixture

The non-catalogue pilot still fails: `mobile under 10000` is classified as
`FIXTURE_GAP` because there is no version-matching candidate snapshot, so the
pipeline executes `0` queries and cannot produce the historical expected three
results. The old three-result output was produced from mutable working evidence;
the immutable evidence/offer snapshot that created it was not found in the
repository or current caches. The failure remains visible in
`test_existing_snapshot_reaches_real_pipeline`; it was not deleted, skipped or
weakened. The replacement regression is the genuine frozen-catalogue replay
(`test_frozen_catalogue_lane_reaches_real_pipeline` plus the semantic replay and
score-trace checks), but closing the historical expectation requires explicit
review acceptance or recovery of the original immutable fixture. This is not a
market-quality PASS.

### Admin and security preflight

`python/shopping_api.py` exposes only `GET /health`, `GET /api/recommend` and
static-file routes. There is no POST/PUT/PATCH/DELETE evidence or score mutation
endpoint. `admin.html` only emits a review JSON record and hard-codes
`writes_calculated_score: false`; direct score/evidence mutation was therefore
not possible through the current page. However, the page is publicly reachable
and has no authentication, session or role check. Access control for a future
evidence-review write path is therefore **UNVERIFIED/FAIL** and blocks a
production release of that surface. Static secret scan found no hard-coded API
secret; provider keys are read from environment variables.

### Focused integration results

The necessary preflight checks produced **57 PASS, 1 FAIL** across 58 focused
tests. PASS groups were: Gate-3 API 7/7; battery 11/11; battery eligibility
3/3; variant identity 2/2; canonical output 2/2; multi-retailer identity 4/4;
release evidence 3/3; reviewed comparison 4/4; runtime reviewed comparison
4/4; mobile-page evidence 3/3; frontend offer traceability 1/1; price/freshness
3/3; premium safety guard 2/2; active route 2/2; performance boundaries 5/5;
recovery reuse 3/3. The offline harness was **5/6 PASS, 1 FAIL** (the
historical fixture above). `node --check app.js` passed and `git diff --check`
found only pre-existing trailing whitespace in the report header. The prior
full baseline remains 170 PASS and 2 optional SKIP; it was not rerun here.

### Exact release manifest

Pending functional local-only commits, in ancestry order (all 40 reviewed
before the report-only preflight commit):

1. `258aaa9` Keep verified catalogue candidates in bounded budget ranking
2. `0fdacc9` Separate eligibility checks from cross-budget market coverage review
3. `d84902d` Avoid repeated failed price lookups in live candidate evaluation
4. `d30d2a6` Recognize verified 165Hz displays and Snapdragon 8 Gen 5 tier
5. `c14bb0e` Audit active shopping route and expose verified deployment revision
6. `a9ae8e4` Parse Indian shopping budgets without treating specification units as money
7. `54b842f` Retain evidenced exact catalogue candidates beyond the new research cap
8. `68716b4` Preserve verified price observation times through retailer offer conversion
9. `41f828e` Separate capability ranking from affordability and evidence coverage
10. `118a36c` Validate Phase G acceptance and bind displayed prices to their evidence source
11. `cbd2f09` Document premium coverage blocker and reviewed Phase G release manifest
12. `f2a3a87` Record bounded OnePlus 15 and S26 Ultra premium evidence blockers
13. `0982dbd` Update Phase G manifest with premium source attempt
14. `e3dfb5b` Extract verified OnePlus 15 official metadata without relaxing variant gates
15. `6eef4cd` Support bounded manufacturer price evidence adapters
16. `1564022` Record Phase G manufacturer price audit
17. `9b4aba5` Guard premium recommendations with explicit market scope
18. `a12f5d5` Save controlled Phase E completion checkpoint
19. `20cd264` Classify unavailable semantic test inputs as skips
20. `b9f45a9` Record Phase E local release gate
21. `f1b797b` Correct release gate test totals
22. `51effe1` Add Phase E final certification report
23. `735b2b8` Document Phase E E2E evidence blockers
24. `5151173` Certify Phase E offline evidence limits
25. `7fd6316` Add offline Phase E certification harness
26. `4a4d33b` Make Phase E offline fixture gating explicit
27. `5208a71` Execute real Phase E pipeline pilot from frozen snapshot
28. `bbf55ea` Map corpus queries to compatible frozen snapshots
29. `3edff5e` Add frozen catalogue integration lane
30. `4a2ac11` Run original corpus through frozen catalogue lane
31. `2fcad14` Cache immutable evidence during Phase E batches
32. `b939aaa` Add resumable Phase E certification batches
33. `e4c218d` Isolate frozen catalogue evidence writes
34. `3dd5d17` Record final Phase E determinism acceptance
35. `fa7134f` Document Phase E positive path coverage gap
36. `20d3cd4` Add verified positive offer snapshot
37. `3a3b7d9` Complete Phase E budget and spelling validation
38. `2ad0506` Expose auditable Phase E score traces
39. `f2d662e` Complete Phase E score and release audit
40. `c3bf5e8` Add criterion evidence provenance to score trace

Tracked release candidates are the existing backend modules (`python/intent_engine.py`,
`market_discovery.py`, `official_spec_extractor.py`, `product_fit_signal_builder.py`,
`retail_price_evidence.py`, `shopping_api.py`, `shopping_intelligence_pipeline.py`,
`weighted_fit_engine.py`), `phase_e_gate3_api.py`,
`phase_e_offline_certification.py`, `app.js`, `admin.html`, the reviewed durable
evidence/offer JSON files, and the listed Phase-E tests/reports. The tracked
`data/phase_e_offline_certification.json` is a large generated receipt and is a
release-review risk; it must not be treated as live evidence. Uncommitted runtime
price/evidence caches, discovery/sitemap caches, audit JSON, `outputs/`, zip
archives, backup directories and `phase_e_*.before_gate1` files are excluded
from release staging and were preserved untouched.

When explicitly authorized, deployment order is: push the reviewed scoped
commit(s), deploy the backend, check `/health` and a representative
`/api/recommend` response, deploy the frontend, then run exact-variant,
price-timestamp, score-trace and no-write admin smoke checks. The current
production Render SHA and live frontend revision are **UNKNOWN** from this
environment. Rollback therefore requires the last SHA shown in the Render
dashboard; the verified repository baseline is `5167712b…`.

### Preflight decision (before owner approval)

**Historical decision only: Phase-E acceptance was FAIL/INCOMPLETE.** Technical frozen determinism and the
required identity, freshness, offer and score-trace checks pass, but the
historical fixture is unresolved and admin access control is not production
verified. **RELEASE READY: NO.** The single release blocker is explicit review
acceptance (or recovery) of the historical immutable fixture together with a
server-side authorization decision for the evidence-review surface; no push or
deploy should occur before that review.

This pre-approval decision is superseded by the owner-approved closure recorded
below. The old fixture remains visible as FAIL/FIXTURE_GAP and is not converted
to PASS.

## Last-two-blocker verification (2026-10-13)

The archived search covered the tracked Phase-E snapshots, the untracked
`phase_e_current.zip`, prior output receipts and the Git history. The archive
contains mutable cache copies, but no immutable evidence/offer bundle that
contains the historical third under-₹10k result. The durable refreshed positive
snapshot contains exactly two eligible records:

| Canonical ID | Exact variant | ASIN | Observed price | State |
|---|---|---|---:|---|
| `cw-mobile-79` | Lava Bold N2 Lite 3GB/64GB | `B0GPXTY8V5` | ₹9,099 | in_stock |
| `cw-mobile-77` | Lava Virat V1 4GB/64GB | `B0HG9SZ7HD` | ₹9,889 | in_stock |

The separate regression `test_verified_under_10000_snapshot_supersedes_unrecoverable_three_result_fixture`
passes and validates both exact identities, prices, source URLs and observation
timestamps. This is the documented supersession candidate: it proves the
current genuine evidence supports two results, while the old three-result test
remains FAIL and is formally superseded after the owner's approval. A worktree catalogue replay
also returned these two exact results with a 1/1 deterministic match; it is not
treated as a clean-deployment market-quality oracle because runtime caches are
uncommitted.

The new read-only admin/API regression passes. `admin.html` has no network or
mutation call and the Flask route map has no API POST/PUT/PATCH/DELETE route.
The page still has no authentication or role check, so it remains a local
review utility only and is excluded from the public artifact.
Public recommendation routes remain unchanged and the API/frontend smoke group
is **15/15 PASS**.

The focused total after this verification is **60 PASS, 1 FAIL** (the old
historical harness test remains visible; the new positive/admin tests pass).
No source engine, cache, backup or research snapshot was removed or overwritten.
The old failure is not retrospectively converted to PASS.

This blocker-verification test/report commit is the current local tip; the
branch is now **42 commits ahead** of `origin/main`. Read the exact tip and
working-tree receipt from Git rather than inferring a deployment revision.

## Phase-E release closure decision (2026-10-13)

### Formal test supersession record

| Item | Decision |
|---|---|
| Original expectation | Three products for the historical non-catalogue `mobile under 10000` test |
| Original immutable evidence | **UNRECOVERABLE** after searching tracked snapshots, Git history, archived zip contents and saved receipts |
| Current verified snapshot | Two exact, fresh, in-stock products: `cw-mobile-79` at ₹9,099 and `cw-mobile-77` at ₹9,889 |
| Replacement regression | `test_verified_under_10000_snapshot_supersedes_unrecoverable_three_result_fixture` — **PASS** |
| Old failure | `test_existing_snapshot_reaches_real_pipeline` remains visible and **FAIL** as `FIXTURE_GAP` |
| Owner decision | **APPROVED** — project owner approved historical-test supersession on 13 October 2026 |

The replacement test does not assert three results, relax any eligibility rule,
or reuse an unverified price. The original failing test and its evidence remain
unchanged; it is formally superseded, never retrospectively passed.

### Actual public-artifact admin audit

The existing root publishing instructions remain in place, but the new
`.github/workflows/public-pages-artifact.yml` uses the allow-list builder
`scripts/build_public_pages.py` before uploading a Pages artifact. The local
artifact build passed: approved homepage/deal/product/SEO assets were present,
while `admin.html`, `validator.html`, Python modules, reports, outputs,
backups, caches and `phase_e_current.zip` were absent. `admin.html` remains in
the repository root for local use; it is not copied into the public artifact.
This proves artifact exclusion locally, but no live HTTP 404 is claimed because
the workflow has not been deployed. The remote `origin/main` does not yet
contain this workflow (raw-file check returned 404), and the GitHub Pages API
was not publicly available (404), so the live Pages source is **UNKNOWN**. A
root-publishing Pages configuration would still expose `admin.html` until the
Pages source is explicitly switched to the Actions artifact.

### Closure verification

Relevant regressions and compatibility smoke checks are **21/21 PASS**:
release evidence 6/6, Gate-3 7/7, active route 2/2, frontend offer traceability
1/1, price/freshness 3/3, premium guard 2/2; `node --check app.js` also passed.
The complete release ancestry is **42 commits ahead** of
`5167712b369c81ab85779819763eee6e9b90a831` (40 functional commits plus the
two local verification/report commits). Local HEAD at this closure is read from
Git; production Render and live frontend revisions remain UNKNOWN. No push or
deployment occurred.

**Supersession approval: APPROVED. Admin exclusion: PASS (local artifact only;
live Pages source UNKNOWN). Phase-E local acceptance: YES. Staging readiness:
NO until the Actions artifact is pushed/run and staging smoke checks pass.
Production readiness: NO.**

### Reviewed 42-commit staging checklist

1. Push the reviewed 42-commit ancestry only after separate authorization; do
   not stage caches, backups, outputs or research receipts.
2. In GitHub Pages settings, select **GitHub Actions** as the source and run
   `public-pages-artifact.yml`; inspect the uploaded artifact before publishing.
3. Confirm the artifact contains the approved homepage/deal/product assets,
   excludes `admin.html` and internal files, and returns the expected public
   admin 404 after staging publication.
4. Run staging `/health`, one representative `/api/recommend`, exact-variant
   price/freshness, score-trace and frontend offer smoke checks.
5. Record the staging SHA and live Pages/Render revisions. Current production
   revisions remain UNKNOWN. Rollback is the last verified staging/Render SHA;
   repository fallback is `5167712b369c81ab85779819763eee6e9b90a831`.

**Remaining release blocker:** the remote Pages source has not been switched to
or verified against the allow-listed Actions artifact. **Next action:** obtain
separate authorization to push the reviewed 42-commit release, run the artifact
workflow, switch Pages to Actions, and complete staging smoke verification.

## Post-push frozen-offer handoff and score-trace verification (2026-10-14)

The reviewed 42-commit release is already present on `origin/main` at
`2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`. This local change is a scoped
follow-up and has not been pushed. It fixes the frozen Phase-E integration lane
by handing only the committed exact-ASIN offer snapshot
`data/phase_e_positive_offer_snapshot_2026-10-13-refresh.json` into the normal
price-evidence adapter, and by disabling persistent evidence writes during
catalogue-mode replay. Production persistence outside catalogue mode is
unchanged.

The frozen `mobile under 50000` replay now executes the real identity, evidence,
eligibility, scoring, ranking and serialization path and is deterministic on
repeat (1/1). Its exact verified Top-3 is:

| Rank | Exact variant | ASIN | Verified price | Fit | Raw fit | Evidence coverage |
|---|---|---|---:|---:|---:|---:|
| 1 | Samsung Galaxy A56 5G 8GB/128GB | B0H1WY55ZL | ₹31,999 | 62 | 77 | 80% |
| 2 | Lava Bold N2 Lite 3GB/64GB | B0GPXTY8V5 | ₹9,099 | 51 | 57 | 90% |
| 3 | Lava Virat V1 4GB/64GB | B0HG9SZ7HD | ₹9,889 | 50 | 56 | 90% |

The `best battery under 20000` replay is an honest executed incomplete result:
34 candidates reached identity, evidence and scoring, but none reached the
fit threshold (`qualifying_50_plus_raw=0`). The closest verified candidates
were Lava Virat V1 and Lava Bold N2 Lite at fit 49 with 91% evidence coverage;
their available battery evidence is playback/capacity-derived and does not
establish the active-use endurance required by the battery policy. Samsung
Galaxy A56 was rejected for the ₹20,000 hard budget. No threshold or identity
guard was changed, and no third phone was invented.

Focused verification after this fix:

| Check | Result |
|---|---|
| Frozen offer exact-ASIN/source guard | 7/7 PASS |
| Battery evidence guards | 11/11 PASS |
| Battery eligibility guards | 3/3 PASS |
| Gate-3 API tests | 7/7 PASS |
| Identity/canonical/price regressions | 8/8 PASS |
| Frontend offer/price/premium checks | 6/6 PASS |
| `node --check app.js` | PASS |
| Offline harness | 5 PASS, 1 FAIL (preserved historical `FIXTURE_GAP`) |

The historical three-result fixture remains visible and failed because its
immutable evidence is unrecoverable; the owner-approved genuine two-result
successor remains the applicable regression. The battery result is a verified
coverage/quality gap, not a proven engine defect. Live Render, GitHub Pages
workflow execution and production smoke verification remain **UNVERIFIED**;
no deployment was performed. Local engine acceptance is **PASS under the
approved supersession**, while full market-quality/production acceptance is
**INCOMPLETE** until the battery evidence gap and live smoke checks are closed.

The earlier closure paragraph's remote-workflow `404` observation is historical.
The current `origin/main` now contains `.github/workflows/public-pages-artifact.yml`
with `workflow_dispatch` only; the workflow has not been run, so live Pages
publication remains unverified.

Current local release receipt is one scoped commit ahead of
`origin/main=2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`; Git is the source of
the exact local `HEAD` SHA and no push was performed. The pre-existing modified caches, research files,
zip backup and `outputs/` receipts remain untracked or unstaged and were not
included in this commit.
