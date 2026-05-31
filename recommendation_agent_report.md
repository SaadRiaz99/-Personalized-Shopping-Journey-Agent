# Recommendation Agent — Stability Test Report

**Model:** Groq (Llama 4 Scout) via OpenAI Agents SDK  

**Test file:** `tests/test_recommendation_agent.py`  

**Number of runs:** 20  

**Total test executions:** 520  

**Total wall-clock time:** 565.7s  


## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Pass Rate** | 520/520 (100.0%) across 20 runs |
| **Total Failures** | 0 |
| **Flaky Tests (any failure)** | — (see below) |
| **Fastest Run** | 27.23s |
| **Slowest Run** | 30.26s |
| **Average Run Time** | 28.29s |
| **Total Wall Time** | 565.7s |
| **Model** | Groq (Llama 4 Scout 17B) |
| **SDK** | OpenAI Agents SDK 0.17.3 |
| **Execution Date** | 2026-06-01 |

## Per-Test Stability (across all runs)

| Test ID | Category | Input | Pass Rate | Avg Latency | Min/Max Latency |
|---------|----------|-------|-----------|-------------|-----------------|
| `test_tc01_fresh_session_has_empty_history` | Cold Start | fresh session has empty history | 🟩 100.0% | 0.002s | 0.0s / 0.036s |
| `test_tc02_fresh_session_default_preferences` | Cold Start | fresh session default preferences | 🟩 100.0% | 0.000s | 0.0s / 0.001s |
| `test_tc03_cold_search_returns_all_catalogue` | Cold Start | cold search returns all catalogue | 🟩 100.0% | 3.933s | 3.656s / 5.049s |
| `test_tc04_independent_sessions_dont_share_state` | Cold Start | independent sessions dont share sta | 🟩 100.0% | 0.001s | 0.0s / 0.004s |
| `test_tc05_category_search_electronics` | Filter Criteria | category search electronics | 🟩 100.0% | 1.490s | 1.372s / 1.949s |
| `test_tc06_tag_and_min_rating` | Filter Criteria | tag and min rating | 🟩 100.0% | 0.239s | 0.215s / 0.339s |
| `test_tc07_multi_word_and_query` | Filter Criteria | multi word and query | 🟩 100.0% | 1.677s | 1.543s / 1.837s |
| `test_tc08_nonexistent_category_returns_empty` | Filter Criteria | nonexistent category returns empty | 🟩 100.0% | 1.561s | 1.452s / 1.839s |
| `test_tc09_search_with_min_rating_filter` | Filter Criteria | search with min rating filter | 🟩 100.0% | 2.878s | 2.751s / 3.088s |
| `test_tc10_search_pagination` | Filter Criteria | search pagination | 🟩 100.0% | 2.843s | 2.723s / 3.275s |
| `test_tc11_search_returns_valid_json` | LLM Output Format | search returns valid json | 🟩 100.0% | 1.736s | 1.607s / 1.844s |
| `test_tc12_each_product_has_required_schema` | LLM Output Format | each product has required schema | 🟩 100.0% | 1.760s | 1.627s / 1.888s |
| `test_tc13_filter_by_tag_only_valid_tag` | LLM Output Format | filter by tag only valid tag | 🟩 100.0% | 0.215s | 0.194s / 0.29s |
| `test_tc14_get_item_details_returns_valid_schema` | LLM Output Format | get item details returns valid sche | 🟩 100.0% | 0.042s | 0.039s / 0.047s |
| `test_tc15_search_completes_under_15s` | Latency / Stress | search completes under s | 🟩 100.0% | 1.574s | 1.447s / 2.001s |
| `test_tc16_load_products_completes_under_15s` | Latency / Stress | load products completes under s | 🟩 100.0% | 0.000s | 0.0s / 0.001s |
| `test_tc17_broad_tag_filter_completes_under_15s` | Latency / Stress | broad tag filter completes under s | 🟩 100.0% | 0.227s | 0.192s / 0.353s |
| `test_tc18_get_item_negative_id` | Invalid Input | get item negative id | 🟩 100.0% | 0.164s | 0.142s / 0.277s |
| `test_tc19_get_item_zero_id` | Invalid Input | get item zero id | 🟩 100.0% | 0.163s | 0.14s / 0.253s |
| `test_tc20_search_empty_string` | Invalid Input | search empty string | 🟩 100.0% | 0.390s | 0.349s / 0.572s |
| `test_tc21_search_special_chars_and_injection` | Invalid Input | search special chars and injection | 🟩 100.0% | 1.632s | 1.517s / 1.821s |
| `test_tc22_filter_by_tag_empty_string` | Invalid Input | filter by tag empty string | 🟩 100.0% | 0.203s | 0.178s / 0.281s |
| `test_tc23_session_preserves_seen_ids` | Session & Guardrails | session preserves seen ids | 🟩 100.0% | 0.001s | 0.0s / 0.004s |
| `test_tc24_guardrail_blocks_empty_output` | Session & Guardrails | guardrail blocks empty output | 🟩 100.0% | 0.004s | 0.001s / 0.042s |
| `test_tc25_guardrail_handles_list_input` | Session & Guardrails | guardrail handles list input | 🟩 100.0% | 0.001s | 0.001s / 0.004s |
| `test_tc26_get_or_create_returns_same_session` | Session & Guardrails | get or create returns same session | 🟩 100.0% | 0.000s | 0.0s / 0.002s |

## Run-to-Run Timing

| Run # | Duration | Passed | Failed | Notes |
|-------|----------|--------|--------|-------|
| 1 | 28.82s | 26 | 0 | cold cache (JSON load) |
| 2 | 29.14s | 26 | 0 | warm cache |
| 3 | 28.57s | 26 | 0 |  |
| 4 | 28.49s | 26 | 0 |  |
| 5 | 28.64s | 26 | 0 |  |
| 6 | 30.26s | 26 | 0 |  |
| 7 | 28.24s | 26 | 0 |  |
| 8 | 27.95s | 26 | 0 |  |
| 9 | 27.23s | 26 | 0 |  |
| 10 | 27.87s | 26 | 0 |  |
| 11 | 27.81s | 26 | 0 |  |
| 12 | 28.48s | 26 | 0 |  |
| 13 | 28.91s | 26 | 0 |  |
| 14 | 28.46s | 26 | 0 |  |
| 15 | 27.61s | 26 | 0 |  |
| 16 | 27.76s | 26 | 0 |  |
| 17 | 27.72s | 26 | 0 |  |
| 18 | 27.73s | 26 | 0 |  |
| 19 | 28.39s | 26 | 0 |  |
| 20 | 27.63s | 26 | 0 |  |

## Failed & Flaky Test Analysis

✅ **100% stability across all runs.** No test ever failed.

### Edge-Case Behavior Notes

- **Cold start:** Sessions are fully isolated; seen_ids and preferences start empty.

- **Invalid IDs:** Negative and zero IDs gracefully return `'No item found'`.

- **Empty/blank input:** Search with `""` returns full catalogue capped at 20 (empty substring matches all titles); guardrails block empty outputs.

- **SQL injection patterns:** The agent's substring search does not crash on special characters.

- **Pagination:** `offset` and `limit` slice correctly; `total` reflects pre-pagination count.

- **Guardrail list input:** The `isinstance(input, list)` branch is now tested via `test_tc25`.


## Concrete Next Steps

### Fix Logic Errors

1. Add a small JSON fixture for tests — replace `products.json` load with a controlled file to eliminate latency variance.

2. Add direct unit tests for `products.search()` filtering parameters (`min_price`, `max_price`, `sort_by`, etc.).

### Reduce Context-Drift (LLM)

1. The system prompt already forbids hallucination — but consider adding few-shot examples of correct tool usage.

2. For multi-turn consistency, inject `seen_ids` into the prompt so the LLM knows what was already shown.

### Expand Test Coverage

1. Add property-based tests (Hypothesis) for `search()` with random filter combinations.

2. Add end-to-end mock-LLM tests using `unittest.mock.patch` on `Runner.run()`.

3. Add stress tests with concurrent sessions (10+ simultaneous `get_or_create_session` calls).


---


