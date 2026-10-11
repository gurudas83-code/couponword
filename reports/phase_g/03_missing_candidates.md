# Task 3 — recall and remaining coverage gaps

2026-10-11: 105 catalogue records,40 in Mobiles;37 registry canonical mobile keys;
187 research seed models/declared variants (NOT verified phones);28 runtime evidence
records and12 reviewed release evidence records. These sets overlap and must not be summed.
Current usable offers/eligible counts require current price checks, not catalogue counting.

Proven cap defect: final discovery unconditionally broke at max_candidates even when
the remaining row already had exact canonical ownership and usable exact-variant evidence.
The correction bounds new research while retaining such evidenced catalogue rows after
the cap. It does not approve them: identity, current price, budget and fit still run.
Unverified research tails remain bounded. Old pinned snapshots are invalidated through
catalogue-breadth-v4. Pools larger than the requested cap are not saved as fixed-size snapshots.

18 targeted tests PASS (new recall2, discovery diversity, local fallback, budget breadth).
Frozen reproducer35 evidenced rows previously stopped30; now retains35. Unknown/unregistered
tails still stop30. This is a cap regression fixture, not35 real verified phones.

Outstanding candidates/gaps:
- Motorola Signature12/256 Carbon B0GKB38XWZ: official model facts and exact identity
  exist; latest saved exact retailer response supplied no current price. Do not reuse59990
  as fresh. Existing pending admission remains uncommitted and unchanged.
- Samsung Galaxy S24 B0CQYGPGPP8/256: last recorded exact-page check hit CAPTCHA;
  search-card64900 was not admitted as verified. Retry normal provider only when available.
- OnePlus12R: prior search returned other models; no exact matching offer admitted.
- Other187 research seeds have not all completed exact official/retailer verification.
  Their presence is not evidence of current sale, verified specifications or eligibility.

03_coverage_audit.csv preserves existing before-fix observations for available budgets;
12k/120k/150k are explicitly NOT_RUN there. Final controlled eight-budget results belong
in Task6 acceptance; historical observations are not relabelled current.

Status: recall repair PASS on frozen regression; full current market coverage INCOMPLETE.
No exhaustive India-market claim, fabricated specification or external source price added.

Final acceptance update: CSV now contains the actual current eight-budget run plus150k repeat, superseding historical-only rows. Runtime evidence has15 cacheable exact variants. See06_final_acceptance.md for exact picks/timings and bounded OnePlus15 extractor rejection/new candidate B0FTR5NGHJ.
