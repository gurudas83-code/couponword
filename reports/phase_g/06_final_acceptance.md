# Task 6 — final local acceptance: INCOMPLETE

No push/deploy. These results are local, based on the existing evidence/retailer pipeline; passing payload guards do not certify complete market coverage.

## Eight budget checks

| Budget | Discovered | Eligible unique | Returned | Seconds | Exact returned listing / RAM-storage / price |
|---|---:|---:|---:|---:|---|
| 10000 | 19 | 3 | 3 | 12.02 | lava Bold N2 [B0GL1JFK48; 4/64] Rs9699; lava Bold N2 Lite [B0GPXTY8V5; 3/64] Rs9099; Lava Virat V1 [B0HG9SZ7HD; 4/64] Rs9889 |
| 12000 | 21 | 3 | 3 | 7.28 | lava Bold N2 [B0GL1JFK48; 4/64] Rs9699; lava Bold N2 Lite [B0GPXTY8V5; 3/64] Rs9099; Lava Virat V1 [B0HG9SZ7HD; 4/64] Rs9889 |
| 20000 | 33 | 9 | 3 | 14.15 | Samsung Galaxy M17 5G [B0H5BRHZBX; 4/128] Rs19999; Samsung Galaxy M17e 5G [B0GN24SV22; 4/128] Rs16998; realme C83 5G [B0GPWRYNM1; 4/64] Rs19999 |
| 30000 | 32 | 13 | 3 | 12.34 | Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370; Samsung Galaxy M17 5G [B0H5BRHZBX; 4/128] Rs19999; vivo T5x 5G [B0GTTXP6WF; 6/128] Rs27149 |
| 40000 | 31 | 15 | 3 | 8.09 | Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370; Samsung Galaxy A56 5G [B0H1WY55ZL; 8/128] Rs32999; Samsung Galaxy M17 5G [B0H5BRHZBX; 4/128] Rs19999 |
| 50000 | 31 | 17 | 3 | 11.07 | redmi Note 17 Pro Max 5G [B0HGM9RBMH; 8/256] Rs49998; Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370; Samsung Galaxy A56 5G [B0H1WY55ZL; 8/128] Rs32999 |
| 120000 | 30 | 18 | 3 | 7.15 | Motorola Signature [B0GKB38XWZ; 12/256] Rs59990; redmi Note 17 Pro Max 5G [B0HGM9RBMH; 8/256] Rs49998; Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370 |
| 150000 | 30 | 18 | 3 | 6.84 | Motorola Signature [B0GKB38XWZ; 12/256] Rs59990; redmi Note 17 Pro Max 5G [B0HGM9RBMH; 8/256] Rs49998; Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370 |
| 150000 | 30 | 18 | 3 | 3.51 | Motorola Signature [B0GKB38XWZ; 12/256] Rs59990; redmi Note 17 Pro Max 5G [B0HGM9RBMH; 8/256] Rs49998; Samsung Galaxy F36 5G [B0FLZ517QL; 6/128] Rs22370 |

All9 requests (8 budgets plus150k repeat) passed reported-evidence eligibility checks. The repeated150k evidence was unchanged and ordering remained identical.

## Catalogue counts and scope

105 total catalogue rows;40 Mobiles rows;36 mobile titles explicitly parse both physical RAM and storage;37 registry canonical mobile keys.187 research seed model/variant rows are NOT verified phones.28 runtime evidence records include15 cacheable exact RAM/storage variants.12 reviewed deployment records overlap runtime records. These counts must not be added together.
Eligible unique candidates by budget are in the table. Exclusive diagnostic rejection reasons are in03_coverage_audit.csv; canonical rejection and family dedup happen after fit and are separate.

## Provenance and regressions

Existing pending Signature admission reviewed: original104 catalogue rows,36 registry identities and11 release evidence records remain identical; only exact B0GKB38XWZ12/256 identity/model evidence was appended by the prior importer workflow. Fresh buybox price59990 observed2026-10-11T18:03:32.272183+00:00; later requests reused it with original timestamp and unknown current stock. No permanent current-price claim was added to catalogue.
Initial full suite161 tests:160 passed,1 failed because release test assumed11 records while reviewed bundle contains12. Corrected test compares all bundled identities/count, preserves minimum baseline and existing wrong-variant checks. Final full unittest suite:162/162 PASS across48 modules; zero errors/skips. Node syntax check PASS. Four legacy top-level semantic/Gemini diagnostic scripts are not unittest modules and were not run as a network regression suite.
Frontend regression discovered during API validation: unpriced retailer offer supplied a new last_checked timestamp while core supplied price. Renderer now ignores unpriced offers and uses core price source/time/exact variant together. Node-backed rendering regression passes. Existing generated-page tests pass; no pages were mass-generated.

## Performance and production

First local request12.02s, with existing caches retained.150k first6.84s/repeat3.51s. These are first-process/warm observations, NOT empty-cache cold-start benchmarks; cache deletion was deliberately avoided. No claim of controlled improvement over historical runs. Earlier failed-price reuse remains covered by regression tests.
GitHub main last read5167712b369c81ab85779819763eee6e9b90a831; new commits remain local. Render health timed out after30s; exact production SHA UNVERIFIED. Frontend/Render dashboard saved browser permission blocks remain; no bypass attempted. Static renderer tests do not constitute production browser smoke.

## Remaining critical acceptance gaps

- Premium pool still places Galaxy F36 as third pick at120k/150k. Complete premium peer coverage, calibrated capability comparisons, correlated-factor review and separate Value Alternative presentation remain unfinished. Task5 is not fully accepted.
- Official OnePlus15 India selected-SKU page returned only dynamic inputs to normal page extraction; no exact current price verified. Samsung S26 Ultra India page lists12/256,12/512,16/1TB options but its price controls were empty in extracted content. Both exist only as research seeds locally, absent from canonical catalogue/runtime verified evidence. They require exact model/variant + current retailer + official evidence admission; no inferred price/ID added.
- Normal official checks2026-10-11: https://www.oneplus.in/oneplus-15?sku=501111657 and https://www.samsung.com/in/smartphones/galaxy-s26-ultra/buy/?modelCode=SM-S948BZDBINS . Multiple variants/page navigation are not proof of selected stock or price.
- Build-quality and comparable independently measured endurance gaps remain unknown. Existing processor/display/camera normalization is heuristic, not a measured universal quality rating.
- Production SHA/browser/links smoke and true cold-start benchmarking remain unverified. Release readiness: NO. PhaseG genuinely complete: NO.

## Exact continuation

Preserve these commits and reports. Next small evidence batch: OnePlus15 physical12/256 from its official India selected-SKU page, then a lawful exact retailer listing through existing importer/evidence engines. Do not admit search snippets as current price. If exact sources remain unavailable, record that blocker and keep premium acceptance INCOMPLETE. No repeat of completed parser/full-suite/budget sweep unless a subsequent source change requires regression.
Full raw payloads/logs remain in workspace outputs/phase-g-api.json, phase-g-api.log and phase-g-suite-final.log. No generated caches/backups are release files.

## Final bounded premium-source check

Existing official_spec_extractor fetched OnePlus15 selected-SKU page successfully but rejected identity and extracted zero specifications. Existing Amazon search returned candidate B0FTR5NGHJ12/256 Infinite Black with a84999 search-card hint; this is NOT an admitted verified offer/model. Two other cards were15R variants and were not substituted for15. Raw evidence: workspace outputs/phase-g-oneplus15.json. Next exact action: inspect official OnePlus15 specifications-page identity through the existing extractor, then verify B0FTR5NGHJ actual listing brand/physical variant/price. Never admit the15R rows as15.
