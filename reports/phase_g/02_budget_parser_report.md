# Task 2 — budget parsing

Root cause: detect_budget supported k/thousand but not lakh/decimal bare amounts,
currency prefixes or plain shopping amounts; normalization removed Hindi combining
characters before interpreting them. Specification units could be mistaken for money.

The existing parser now recognizes currency prefixes, lakh/lac, decimal k/lakh,
Indian comma amounts, Hindi lakh phrases, explicit ranges (including shared suffix),
and bare shopping amounts. Negative specification-unit guards reject GB/TB/mAh/Hz/MP.
Known brand/model numbers without shopping budget context remain non-budgets.
Budget constraints still flow to the existing hard-constraint engine; no eligibility
threshold or product fact changed. Preferences use the existing downstream logic.

Regression fixture table: test_phase_g_budget_parser.CASES (111 rows), derived from
the user-requested eight budgets and query forms, plus negative identity/spec examples.
Before: actual run failed53 assertions. After: all111 budget fixtures pass;
brand/category/preference preservation and two existing breadth tests pass (4 test methods).
Logs before repair: workspace outputs/phase-g-parser-before.log.

Scope limitation: this is specified-query coverage, not a claim of universal natural
language accuracy. All existing regressions will run once at final acceptance.
