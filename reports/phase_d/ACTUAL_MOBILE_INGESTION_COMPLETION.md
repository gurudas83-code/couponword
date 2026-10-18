# Actual mobile ingestion result

Execution date: 18 October 2026
Worktree: `C:\Users\HP\Documents\projects\couponword-phase-d-coverage`

This run executed the existing exact-evidence admission path. It did not turn
the research manifest into a shopping catalogue and did not fabricate missing
official pages, prices or canonical IDs.

## 1. Execution gap and correction

The earlier `run_mobile_coverage.py` command only merged source manifests and
advanced a cursor. It did not call the official evidence store or
`mobile_intelligence_repository.save_mobile_dna`, so `208/208` meant only
manifest reconciliation. The coordinator now has two explicit modes:

- `--dry-run`: evaluates exact official evidence without writing.
- `--execute`: admits only resolver-verified exact evidence through the
  existing `save_mobile_dna` function, idempotently.

Research-only rows remain pending until an official source and exact physical
variant are actually verified.

## 2. Admission batch

The dry-run inspected 22 exact evidence rows:

| Outcome | Count |
| --- | ---: |
| Ready for admission | 12 |
| Existing duplicate reused | 9 |
| Identity conflict | 1 |

The identity conflict is Samsung Galaxy F36 5G: the requested evidence row is
8/128, while the official page name declares 6GB memory. It remains blocked.

The 12 newly admitted exact variants are:

| Brand | Model | Physical variant | Official evidence |
| --- | --- | --- | --- |
| OnePlus | N6 Lite | 4/64 | `https://www.oneplus.in/n6-lite/specs` |
| Lava | Bold N2 | 4/64 | `https://www.lavamobiles.com/smartphones/bold-n2` |
| Lava | Bold N2 Lite | 3/64 | `https://www.lavamobiles.com/smartphones/bold-n2-lite` |
| Samsung | Galaxy A06 5G Light | 4/64 | `https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a06-5g-light-gray-64gb-sm-a066bzadins/` |
| Samsung | Galaxy F70e 5G | 6/128 | `https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f70e-5g-spotlight-blue-128gb-sm-e076bdbbins/` |
| Lava | Virat V1 | 4/64 | `https://www.lavamobiles.com/smartphones/virat-v1` |
| Lava | Virat V1 5G | 4/64 | `https://www.lavamobiles.com/smartphones/virat-v1-5g` |
| realme | C83 5G | 4/64 | `https://www.realme.com/in/realme-c83` |
| Samsung | Galaxy A56 5G | 8/128 | `https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a56-5g-awesome-graphite-128gb-sm-a566ezkzins/` |
| Samsung | Galaxy M17e 5G | 4/128 | `https://www.samsung.com/in/smartphones/galaxy-m/galaxy-m17e-5g-blitz-blue-128gb-sm-m076blbains/` |
| Samsung | Galaxy M17 5G | 4/128 | `https://www.samsung.com/in/smartphones/galaxy-m/galaxy-m17-5g-black-128gb-sm-m176bzkains/` |
| Motorola | Signature | 12/256 | `https://www.motorola.in/smartphones-motorola-signature/p?skuId=609` |

Each record has a deterministic `dna-*` ID, exact RAM/storage, official URL
and verified identity evidence. `canonical_product_id` remains null and no
current offer or retailer button was created.

## 3. Before/after counts

| Metric | Before | After | Change |
| --- | ---: | ---: | ---: |
| Private Product DNA | 9 | 21 | +12 |
| Official evidence records | 35 | 35 | 0 |
| Exact evidence records | 22 | 22 | 0 |
| Canonical mobile IDs | 34 | 34 | 0 |
| Fresh in-stock offers | 0 | 0 | 0 |
| Current-price eligible additions | 0 | 0 | 0 |

The master inventory now includes official evidence rows as well as the
research sources: 232 known models, 147 exact variant rows and 237 manifest
rows. The 197 research-only rows still need official-source verification.

## 4. Remaining blockers and recovery

- **197 `MISSING_OFFICIAL_EVIDENCE` rows:** existing sources are research
  directories or incomplete seeds; no exact manufacturer proof is stored.
- **17 `OFFICIAL_EVIDENCE_ONLY` rows:** evidence exists, but exact variant or
  canonical admission is still unresolved.
- **1 identity conflict:** Galaxy F36 8/128 conflicts with the official 6GB
  page name and is intentionally not admitted.
- **0 fresh offers:** all stored offers fail the current six-hour exact-offer
  gate; no price or stock claim was promoted.

No CAPTCHA, access control or retailer restriction was bypassed. No scoring,
identity threshold or recommendation rule was changed.

## 5. Validation

- Exact evidence dry-run: 22 records classified.
- Actual admissions: 12.
- Repeat execution: 21 duplicates reused; 0 duplicate records created.
- Focused Phase-D/manifest tests: 10/10 PASS.
- Earlier verified mobile batch and coverage tests: 34/34 PASS.
- Python compilation and `git diff --check`: PASS.

The historical fixture gap remains unchanged.

## 6. Files and commit state

Changed by this execution:

- `python/run_mobile_coverage.py`
- `data/mobile_intelligence_repository.json`
- `data/mobile_universe_2023_2026.json`
- `data/mobile_coverage_gap_2023_2026.json`
- `data/mobile_coverage_progress.json`
- this report

Existing dirty evidence, price-cache, discovery-cache and output files were
preserved. No push, merge or deployment was performed.

The exact admission command is:

```text
py python/run_mobile_coverage.py --market IN --start-year 2023 --end-year 2026 --resume --until-exhausted --execute
```

The next queue remains the 197 research-only rows in
`data/mobile_coverage_gap_2023_2026.json`. Their status is incomplete because
the repository does not contain authoritative exact evidence for them; the
coverage denominator remains unverified.

## 7. Complete official-source verification pass (18 October 2026)

The resumable coordinator then attempted all 197 research-only rows through
the existing `official_source_resolver`, `official_spec_extractor`,
`product_evidence_store` and Product DNA admission path. The source-attempt
receipt is `outputs/phase_d_official_verification.json`; it contains one
checkpointed result for every row.

| Result | Count |
| --- | ---: |
| Rows attempted | 197 |
| Official source blocked/not found | 136 |
| Official page fetch blocked | 2 |
| Official page found but exact requested RAM/storage not independently exposed | 52 |
| Exact official evidence saved | 7 |
| New private Product DNA admissions | 6 |
| Alias/duplicate evidence reused | 1 |

The seven exact evidence rows were:

| Brand | Model | Physical variant | Official source |
| --- | --- | --- | --- |
| Samsung | Galaxy A37 5G | 8/128 | `https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a37-5g-awesome-charcoal-128gb-sm-a376ezadins/` |
| Samsung | Galaxy A57 5G | 8/256 | `https://www.samsung.com/in/smartphones/galaxy-a/galaxy-a57-5g-awesome-navy-256gb-sm-a576bdbfins/` |
| Samsung | Galaxy F70 Pro 5G | 6/128 | `https://www.samsung.com/in/smartphones/galaxy-f/galaxy-f70-pro-5g-aura-green-128gb-sm-e476bzgbins/` |
| Samsung | Galaxy M47 5G | 6/128 | `https://www.samsung.com/in/smartphones/galaxy-m/galaxy-m47-5g-rogue-red-128gb-sm-m476bzrbins/` |
| Samsung | Galaxy S24 5G alias | 8/256 | `https://www.samsung.com/in/smartphones/galaxy-s/galaxy-s24-onyx-black-256gb-sm-s921ezkwins/` |
| Samsung | Galaxy S25 FE | 8/128 | `https://www.samsung.com/in/smartphones/galaxy-s/galaxy-s25-fe-navy-128gb-sm-s731bdbbins/` |
| Samsung | Galaxy S26 Ultra | 12/256 | `https://www.samsung.com/in/smartphones/galaxy-s/galaxy-s26-ultra-black-256gb-certified-re-newed-sm5s948bzkbins/` |

The S24 5G row has the same official URL and physical variant as the existing
`Galaxy S24` record, so it was retained as evidence provenance but did not
create a second Product DNA record. Final counts are:

| Metric | Start of this pass | Final | Change |
| --- | ---: | ---: | ---: |
| Private Product DNA | 21 | 27 | +6 |
| Official evidence records | 35 | 42 | +7 |
| Exact verified variant rows | 22 | 29 | +7 |
| Canonical shopping IDs | 34 | 34 | 0 |
| Fresh in-stock offers | 0 | 0 | 0 |
| Research-only rows | 197 | 190 | -7 |

The source resolver also received a narrow approved-domain alias map for
OPPO, POCO, iQOO, Google, Infinix, Tecno, CMF and Xiaomi/Redmi. A model-family
guard now rejects numeric cross-family false positives such as iPhone 11 →
iPad 11 and iPhone SE 3 → Apple Watch SE 3. Failed sitemap crawls are memoized
for the current process only; successful sitemap caching is unchanged. DNA
admission now reuses an existing exact source URL plus RAM/storage variant,
preventing an alias from creating a duplicate Product DNA record.

No retailer price, availability, canonical shopping ID or active buy button was
created by this pass. The 190 remaining rows are genuine official-source or
exact-variant evidence gaps, not silently admitted products. The known queue is
exhausted for this run, but the market denominator is still unverified.

## 8. Final validation and resume

- Source checkpoint: 197/197 rows recorded.
- Private DNA admission: 27 durable records; all 27 have matching exact
  official evidence and HTTPS source URLs in the working evidence store.
- Focused resolver, alias, duplicate-prevention and Phase-D coverage tests:
  17/17 PASS in the final focused run.
- Python compilation: PASS.
- Fresh offers: 0; shopping eligibility remains unchanged.
- Galaxy F36 8/128 identity conflict remains blocked.
- Push, merge and deployment: not performed.

If another authorized run is needed, the exact resumable command is:

```text
py python/run_mobile_coverage.py --market IN --start-year 2023 --end-year 2026 --resume --verify-sources --execute --until-exhausted
```

Because every current row is checkpointed, this command will skip completed
source attempts and only process newly added or explicitly retried rows.
