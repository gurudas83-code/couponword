# Release manifest and pending actions

## Exact state at audit start

- Local baseline: `78553b1a9eb895f417eea869af01e987d93503bb`
- `origin/main`: `2db6534eb4dba1cdb6f18df46bf2275e0a9b0d1e`
- Historical reviewed commits on remote: 42
- Local-only commits pending push: 7 (six pre-existing plus this scoped query-consistency commit)
- Push/deploy: NO

## Six local-only commits

- `b4c70db` Fix frozen Phase E offer handoff and score replay
- `25c279d` Repair official mobile source and manufacturer offer gates
- `0c5be2f` Admit fresh exact manufacturer offers
- `0421a19` Expose verified manufacturer offers in API traces
- `ab94013` Make retailer offer persistence atomic
- `78553b1` Record Phase G integration closure
- Scoped query-consistency commit `Add semantic query consistency release audit`
  (current local HEAD; report files are included)

## Scoped query-consistency changes in this working tree

- `python/intent_engine.py`: versioned semantic intent signature and hash
- `phase_e_offline_certification.py`: reuse the authoritative signature for
  frozen snapshot compatibility
- `test_phase_e_query_consistency.py`: equivalent-budget and constraint-separation tests
- `reports/release_and_query_consistency/`: required reports and frozen replay receipt

## Explicit exclusions

Do not stage the dirty runtime JSON, discovery caches, backups, ZIP, `outputs/`,
`reports/master_system_audit/` or audit helper scripts shown by `git status`.
They remain preserved locally and are not release inputs.

## Safe next action (requires separate authorization)

Review the scoped diff, decide whether volatile T5 Pro evidence needs a separate
durable-data commit, then push only the reviewed source/report scope. Run the
Pages workflow manually and verify its allow-listed artifact. Verify Render
revision and API/UI smoke tests. Keep production NO-GO while either live
revision or durable-data parity is unknown. Rollback baseline is the current
`origin/main` SHA above.
