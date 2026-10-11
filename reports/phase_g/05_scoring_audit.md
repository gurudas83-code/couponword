# Task 5 — capability/evidence separation (PARTIAL)

Root cause: old sorting used fit = normalized match × evidence coverage. Budget supplied
full points to every affordable candidate, inflating cheap low-capability models; the score
also mixed missing data with physical capability. The route had its own sorting expression.

Repair in the existing weighted_fit_engine: quality_score is the existing weighted mean
of known non-budget signals, with separate quality_evidence_coverage_percent. No new
hardware scale, invented benchmark or price floor was introduced. Existing conservative
fit>=50 and evidence>=50 eligibility requirements remain unchanged. Both existing ranking
entry points use one deterministic sort helper: quality, quality coverage, conservative
eligibility fit, exact stable ID. Final model-family deduplication remains in the pipeline.
API exposes the score/contract and explicit completion_status=INCOMPLETE when short;
frontend labels capability match separately from requirement match/evidence coverage.

26 targeted tests PASS; JavaScript syntax check PASS. Eight budgets × three priority
profiles ×20 input-order permutations remain stable. Also replayed3 historical API diagnostic
snapshots20 times each; eligibility fit unchanged, order stable. CSV records before/after
candidate positions with historical prices; these are NOT newly verified current offers
or proof of final canonical top3 admission.

Remaining acceptance gaps (do not mark Task5 or PhaseG complete):
- Premium candidate coverage remains insufficient. Sorting the present pool cannot prove
  best premium recommendations. No minimum price was imposed to conceal this gap.
- Existing normalized camera/processor/display scales are heuristics, not calibrated
  comparable lab measurements. Build-quality evidence and correlated-factor audit incomplete.
- Separate Value Alternative selection is not implemented: a defensible premium peer/value
  contract still requires representative verified premium evidence, not invented classifications.
- Unknown dimensions are not claimed strong. A high known-capability score must be read
  alongside its separate coverage; the conservative admission gate protects sparse evidence.

No production release authorized by these passing unit tests. Continue remaining market
evidence/peer-contract work from the checkpoint; do not claim zero error.
