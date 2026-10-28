# Worked exact-variant calculation

The reproducible worked calculation is isolated in `test_issue06_budget_benchmark.py` and uses clearly labelled fixture records, not production data or live offers.

At an exact ceiling of ₹18,000, fixture variants `a`, `b` and `c` pass the fixture current-offer gates. Independent metric leaders are intentionally different: `a` leads capacity, `b` leads camera resolution and `c` leads lower-is-better latency. Each leader receives 100 only for its own metric; other scores are computed by the direction-aware ratio. The test also verifies that structured measurement records from incompatible comparable groups do not merge.

This is a research/fixture calculation only. It is not evidence of a current retailer price, stock state or market-wide leadership.
