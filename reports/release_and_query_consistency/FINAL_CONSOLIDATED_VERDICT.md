# Final consolidated verdict

## Query consistency

The existing parser mapped the four 30k budget spellings to the same structured
intent. The scoped correction now also extracts explicitly named exact models
in `python/intent_engine.py`, and frozen compatibility reuses the versioned
semantic signature in `phase_e_offline_certification.py`. Raw lexical keywords
cannot create false cache distinctions; budgets, brands, exact models, variants,
use cases, exclusions and priority weights remain part of the signature.

The corpus now has 1000 semantic signatures. The previous 950 map had an
identity defect: different exact-model queries were grouped by budget/category
alone. Remaining incorrect corpus equivalence cases are **0**. The older
reported 334-group heuristic artifact is not present in Git or preserved
reports, so its corpus identity cannot be independently confirmed; no
arbitrary reconciliation is claimed.

The required frozen replay is **4/4 executed, 4/4 scored, 0 incomplete, 0
technical failures, and 4/4 Run-A/Run-B semantic matches**. All four returned
the same ordered pair (`cw-mobile-79` Lava Bold N2 Lite, 9099; `cw-mobile-77`
Lava Virat V1, 9889) with `VERIFIED_SCOPE`. Full-corpus recommendation
equivalence and live market quality are not claimed.

Focused validation: canonical signature tests **4/4 PASS**; the three affected
catalogue/offline regression tests **3/3 PASS**. The complete eight-test offline
harness was **7 PASS / 1 FAIL**: the historical non-catalogue pilot could not
restore its mutable candidate snapshot after current catalogue revisions and
reported `FIXTURE_GAP`. It remains visible and is not silently skipped or
counted as a query-consistency PASS.

## Release decision

- 42 historical reviewed commits are exact on GitHub `origin/main`.
- Eight newer commits are local-only and unpushed (six pre-existing plus two
  scoped query-consistency corrections).
- Dirty data, caches, backups and research files were preserved.
- Pages workflow exists but was not run; live artifact is UNVERIFIED.
- Render revision and frontend/API parity are UNVERIFIED.
- Continuous offer refresh/monitoring remains BLOCKED.

**PHASE-E TECHNICAL: PASS for verified local/frozen gates.**

**RELEASE READY: NO for production.** Review the scoped diff and obtain separate
push/staging authorization only after concrete live revision and artifact checks.
