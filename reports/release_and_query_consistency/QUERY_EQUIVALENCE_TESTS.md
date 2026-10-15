# Query equivalence and frozen-result consistency

The unchanged original corpus data/mobile_query_corpus_1000.json has 1000
rows (train 800, validation 100, test 100), 1000 unique semantic
signatures, 0 duplicate groups, and 0 rows in duplicate groups.
The full equivalence map is QUERY_CANONICAL_GROUPS.csv.

python/intent_engine.py now emits versioned intent-signature-v1 signatures and
captures explicitly named exact models. Before this correction, different
named models sharing a budget were incorrectly grouped; the corpus map now
keeps Galaxy F05, iPhone 13, Smart 8 HD, T4X and M7 Pro distinct. Raw query
text and lexical keywords are excluded so budget formatting does not create
false cache keys. Meaning-changing fields remain distinct.

## Required 30k group

mobile under 30000, mobile under 30k, mobile under 30 k, and
mobile under 30,000 all parse to smartphone with budget_max=30000 and the
same semantic signature hash.

## Frozen replay receipt

frozen_30k_replay.json: 4/4 executed, 4/4 scored, 0 incomplete, 0
technical failures, 4/4 Run-A/Run-B semantic matches. Each returned the same
ordered pair: cw-mobile-79 Lava Bold N2 Lite (price 9099) then cw-mobile-77
Lava Virat V1 (price 9889), with VERIFIED_SCOPE quality status. This proves
same-snapshot interpretation and replay stability; it does not prove broader
market coverage or live freshness.

Focused tests: 4/4 canonical-signature tests PASS and 3/3 affected catalogue
regressions PASS. The full eight-test offline harness remains 7 PASS / 1 FAIL
because its historical non-catalogue `mobile under 10000` fixture is stale
against the current catalogue revision; this is a preserved fixture gap.
