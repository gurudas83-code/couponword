# Final consolidated verdict

## Query consistency

The existing parser already mapped the four 30k budget spellings to the same
structured intent. The scoped correction adds a versioned semantic signature in
`python/intent_engine.py` and makes frozen compatibility reuse it in
`phase_e_offline_certification.py`. Raw lexical keywords cannot create false
semantic cache distinctions; budgets, brands, variants, use cases, exclusions
and priority weights remain part of the signature.

The required frozen replay is **4/4 executed, 4/4 scored, 0 incomplete, 0
technical failures, and 4/4 Run-A/Run-B semantic matches**. All four returned
the same ordered pair (`cw-mobile-79` Lava Bold N2 Lite, 9099; `cw-mobile-77`
Lava Virat V1, 9889) with `VERIFIED_SCOPE`. Full-corpus recommendation
equivalence and live market quality are not claimed.

Focused validation: canonical signature tests **3/3 PASS**; the three affected
catalogue/offline regression tests **3/3 PASS**. The complete eight-test offline
harness was **7 PASS / 1 FAIL**: the historical non-catalogue pilot could not
restore its mutable candidate snapshot after current catalogue revisions and
reported `FIXTURE_GAP`. It remains visible and is not silently skipped or
counted as a query-consistency PASS.

## Release decision

- 42 historical reviewed commits are exact on GitHub `origin/main`.
- Seven newer commits are local-only and unpushed (six pre-existing plus the
  scoped query-consistency commit).
- Dirty data, caches, backups and research files were preserved.
- Pages workflow exists but was not run; live artifact is UNVERIFIED.
- Render revision and frontend/API parity are UNVERIFIED.
- Continuous offer refresh/monitoring remains BLOCKED.

**PHASE-E TECHNICAL: PASS for verified local/frozen gates.**

**RELEASE READY: NO for production.** Review the scoped diff and obtain separate
push/staging authorization only after concrete live revision and artifact checks.
