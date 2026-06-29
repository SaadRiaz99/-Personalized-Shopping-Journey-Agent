# Price Guardrail — Individual Test Report
**Date:** 2026-06-29 10:57:14
**Passed:** 46 | **Failed:** 1 | **Total:** 47

## Results
| Test Case | Status | Detail |
|---|---|---|
| sku_valid | PASS |  |
| sku_no_prefix | PASS |  |
| sku_wrong_format | PASS |  |
| sku_lowercase | PASS |  |
| sku_letters | PASS |  |
| sku_empty | PASS |  |
| sku_short | PASS |  |
| sku_special | PASS |  |
| sku_spaces | PASS |  |
| sku_unusual | PASS |  |
| price_negative | PASS |  |
| price_zero | PASS |  |
| price_penny | PASS |  |
| price_below_min | PASS |  |
| price_max | PASS |  |
| price_above_max | PASS |  |
| price_very_high | PASS |  |
| price_exact_max | PASS |  |
| price_typical | PASS |  |
| price_large_valid | PASS |  |
| fraud_zero | PASS |  |
| fraud_negative | PASS |  |
| fraud_suspicious | PASS |  |
| fraud_gouging | PASS |  |
| fraud_normal | PASS |  |
| fraud_exact_ratio | FAIL |  |
| fraud_exact_gouge | PASS |  |
| fraud_equal | PASS |  |
| fraud_barely_suspicious | PASS |  |
| fraud_barely_gouge | PASS |  |
| rate_first | PASS |  |
| rate_50th | PASS |  |
| rate_51st | PASS |  |
| rate_diff_users | PASS |  |
| rate_reset | PASS |  |
| rate_new_window | PASS |  |
| rate_sequential | PASS |  |
| rate_exact_cap | PASS |  |
| abuse_under | PASS |  |
| abuse_exact | PASS |  |
| abuse_over | PASS |  |
| abuse_new | PASS |  |
| abuse_record | PASS |  |
| abuse_reset | PASS |  |
| combine_valid | PASS |  |
| combine_abuse_rate | PASS |  |
| combine_success | PASS |  |