# Phase-G reviewed local release manifest

| Order | Commit | Scope | Verification |
|---:|---|---|---|
| 1 | `c14bb0e` | Active route audit, valid Render revision field, Task-1 report | 7 targeted tests |
| 2 | `a9ae8e4` | Indian budget parser and 111 table-driven fixtures | parser/breadth tests pass |
| 3 | `54b842f` | Preserve evidenced exact catalogue candidates beyond cap | 18 targeted tests |
| 4 | `68716b4` | Preserve price observation time through retailer offers | 20 targeted tests |
| 5 | `41f828e` | Separate capability score from budget/evidence coverage | 26 targeted tests, 20 repetitions |
| 6 | `118a36c` | Frontend source-bound price display, Signature evidence, acceptance reports | 162-test suite final pass |
| 7 | `cbd2f09` | Premium quality audit and reviewed release manifest | audit/report only |
| 8 | `f2a3a87` | Bounded OnePlus 15 and S26 Ultra source blockers | no catalogue change; prior tests remain green |
| 9 | `e3dfb5b` | Source-specific OnePlus `/15` metadata extraction correction | 165-test suite PASS; no catalogue admission |
| 10 | `6eef4cd` | Bounded OnePlus/Samsung first-party price-path and JSON-LD availability adapter | 9 focused tests PASS; no catalogue admission |

Previous HEAD `118a36c` is preserved. No push or deploy was performed in this turn.
Uncommitted caches and backups remain outside this manifest. The manifest is a local
review artifact; it does not certify production readiness.
