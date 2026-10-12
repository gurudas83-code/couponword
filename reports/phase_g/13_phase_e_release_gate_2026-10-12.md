# Phase-E release gate — 2026-10-12

## Test environment

- Full unittest discovery: **170 run; 168 PASS, 0 FAIL, 0 ERROR, 2 SKIP**.
- The skips are explicit and justified: optional `google.genai` is not
  installed, and the optional semantic v1.3 fixture is absent. No test was
  deleted or counted as PASS.

## Original Gate-3 matrix

The existing `CASES` fixture was used. Fourteen calls means two frozen repeats
for each of the seven queries. All calls returned HTTP 200, exactly three
recommendations, valid exact-listing price evidence, canonical identity and
stable count/order:

| Query | Calls | Result |
|---|---:|---|
| mobile under 10000 | 2 | PASS, 3 each |
| mobile under 15000 | 2 | PASS, 3 each |
| best phone under 20000 | 2 | PASS, 3 each |
| Samsung phone under 20000 | 2 | PASS, 3 each |
| best battery under ₹20k | 2 | PASS, 3 each |
| best battery under ₹30k | 2 | PASS, 3 each |
| best battery under ₹50k | 2 | PASS, 3 each |

The premium guard regression is covered separately: ₹1.2L/₹1.5L responses keep
their evidenced rows but expose `market_quality_status=INCOMPLETE` unless
durable premium coverage is explicitly verified.

## Release candidate

- Release SHA: `20cd26447d5417b887959c88966c06aeb29b6e1a`
- Rollback baseline: `5167712b369c81ab85779819763eee6e9b90a831`
- Remote `origin/main` remains at the rollback baseline; no push/deploy occurred.
- Durable source, test and evidence changes are committed. Runtime caches,
  generated audits, backups and ZIP remain uncommitted and excluded.
- Existing frontend/backend compatibility and renderer regressions remain green
  from the prior acceptance record; no page generation was added here.

## Status

- Local Phase-E acceptance: **PASS**.
- Production acceptance: **BLOCKED** until explicit push/deploy authorization,
  live revision verification and one live seven-query matrix.
- Premium market coverage: **INCOMPLETE** by design; no misleading premium
  best-in-market claim is released.
