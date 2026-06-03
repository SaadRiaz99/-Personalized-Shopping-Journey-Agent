# Recommendation Agent — Stability Test Report

**Generated:** 2026-06-03 17:10:06  

**Model:** OpenRouter (Gemini 2.0 Flash / Kimi K2.6 / gpt-oss-120b / gpt-oss-20b / Qwen3 Next 80B) via OpenAI Agents SDK  

**Test file:** `tests/test_all_51.py`  

**Number of runs:** 1  

**Total test executions:** 116  

**Total wall-clock time:** 78.5s  


## Executive Summary

| Metric | Value |
|--------|-------|
| **Overall Pass Rate** | 116/116 (100.0%) across 1 runs |
| **Total Failures** | 0 |
| **Flaky Tests (any failure)** | — (see below) |
| **Fastest Run** | 78.55s |
| **Slowest Run** | 78.55s |
| **Average Run Time** | 78.55s |
| **Total Wall Time** | 78.5s |
| **Models** | OpenRouter (Gemini 2.0 Flash / Kimi K2.6 / gpt-oss-120b / gpt-oss-20b / Qwen3 Next 80B) |
| **SDK** | OpenAI Agents SDK 0.2.2 |
| **Execution Date** | 2026-06-03 |

## Per-Test Stability (across all runs)

| Test ID | Category | Input | Pass Rate | Avg Latency | Min/Max Latency |
|---------|----------|-------|-----------|-------------|-----------------|
| `test_in_stock_filter` | Catalogue & Search | test in stock filter | :green_circle: 100.0% | 1.643s | 1.643s / 1.643s |
| `test_pagination_no_overlap` | Catalogue & Search | test pagination no overlap | :green_circle: 100.0% | 0.552s | 0.552s / 0.552s |
| `test_price_range_filter` | Catalogue & Search | test price range filter | :green_circle: 100.0% | 1.647s | 1.647s / 1.647s |
| `test_products_load_correctly` | Catalogue & Search | test products load correctly | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_rating_filter` | Catalogue & Search | test rating filter | :green_circle: 100.0% | 1.700s | 1.7s / 1.7s |
| `test_search_by_category` | Catalogue & Search | test search by category | :green_circle: 100.0% | 0.409s | 0.409s / 0.409s |
| `test_search_by_keyword` | Catalogue & Search | test search by keyword | :green_circle: 100.0% | 5.901s | 5.901s / 5.901s |
| `test_sorting_ascending_and_descending` | Catalogue & Search | test sorting ascending and descendi | :green_circle: 100.0% | 3.442s | 3.442s / 3.442s |
| `test_compare_products_returns_comparison_table` | Tools | test compare products returns compa | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_filter_products_by_category` | Tools | test filter products by category | :green_circle: 100.0% | 0.004s | 0.004s / 0.004s |
| `test_filter_products_by_discount` | Tools | test filter products by discount | :green_circle: 100.0% | 0.395s | 0.395s / 0.395s |
| `test_filter_products_by_price` | Tools | test filter products by price | :green_circle: 100.0% | 0.445s | 0.445s / 0.445s |
| `test_get_product_details_found` | Tools | test get product details found | :green_circle: 100.0% | 0.040s | 0.04s / 0.04s |
| `test_get_product_details_not_found` | Tools | test get product details not found | :green_circle: 100.0% | 0.172s | 0.172s / 0.172s |
| `test_get_session_context_returns_summary` | Tools | test get session context returns su | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_list_categories_returns_10` | Tools | test list categories returns | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_save_preference_stores_value` | Tools | test save preference stores value | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_search_products_avoids_duplicates` | Tools | test search products avoids duplica | :green_circle: 100.0% | 1.669s | 1.669s / 1.669s |
| `test_search_products_marks_seen` | Tools | test search products marks seen | :green_circle: 100.0% | 1.763s | 1.763s / 1.763s |
| `test_search_products_returns_items` | Tools | test search products returns items | :green_circle: 100.0% | 1.657s | 1.657s / 1.657s |
| `test_add_and_get_items` | Session Memory | test add and get items | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_clear_session` | Session Memory | test clear session | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_get_items_with_limit` | Session Memory | test get items with limit | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_get_or_create_returns_same_session` | Session Memory | test get or create returns same ses | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_history_bounded_to_max` | Session Memory | test history bounded to max | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_list_sessions` | Session Memory | test list sessions | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_mark_seen_ids` | Session Memory | test mark seen ids | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_pop_item` | Session Memory | test pop item | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_pop_item_on_empty_session` | Session Memory | test pop item on empty session | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_update_preferences` | Session Memory | test update preferences | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_guardrail_list_input_format` | Guardrails | test guardrail list input format | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_guardrail_list_with_non_dict_last_element` | Guardrails | test guardrail list with non dict l | :green_circle: 100.0% | 0.238s | 0.238s / 0.238s |
| `test_guardrail_with_non_string_non_list_input` | Guardrails | test guardrail with non string non  | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_injection_allowed` | Guardrails | test injection allowed | :green_circle: 100.0% | 0.004s | 0.004s / 0.004s |
| `test_injection_blocked` | Guardrails | test injection blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_off_topic_allowed` | Guardrails | test off topic allowed | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_off_topic_coding_blocked` | Guardrails | test off topic coding blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_off_topic_finance_blocked` | Guardrails | test off topic finance blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_off_topic_weather_blocked` | Guardrails | test off topic weather blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_output_quality_passes` | Guardrails | test output quality passes | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_output_too_short_blocked` | Guardrails | test output too short blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_output_traceback_blocked` | Guardrails | test output traceback blocked | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_context_summary_has_all_keys` | Context | test context summary has all keys | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_log_tool_appends_entry` | Context | test log tool appends entry | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_multiple_tool_logs_tracked` | Context | test multiple tool logs tracked | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_request_id_stored_correctly` | Context | test request id stored correctly | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_empty_query_handled` | Error Handling | test empty query handled | :green_circle: 100.0% | 0.005s | 0.005s / 0.005s |
| `test_invalid_api_key_handled_gracefully` | Error Handling | test invalid api key handled gracef | :green_circle: 100.0% | 0.006s | 0.006s / 0.006s |
| `test_network_timeout_handled` | Error Handling | test network timeout handled | :green_circle: 100.0% | 0.006s | 0.006s / 0.006s |
| `test_rate_limit_returns_friendly_message` | Error Handling | test rate limit returns friendly me | :green_circle: 100.0% | 0.606s | 0.606s / 0.606s |
| `test_first_chunk_arrives_quickly` | Streaming | test first chunk arrives quickly | :green_circle: 100.0% | 0.002s | 0.002s / 0.002s |
| `test_full_response_assembles_correctly` | Streaming | test full response assembles correc | :green_circle: 100.0% | 0.003s | 0.003s / 0.003s |
| `test_streamed_response_yields_chunks` | Streaming | test streamed response yields chunk | :green_circle: 100.0% | 0.005s | 0.005s / 0.005s |
| `test_streaming_session_memory_updated` | Streaming | test streaming session memory updat | :green_circle: 100.0% | 0.002s | 0.002s / 0.002s |
| `test_get_by_id_invalid` | Products Edge | test get by id invalid | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_get_by_id_valid` | Products Edge | test get by id valid | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_get_categories` | Products Edge | test get categories | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_in_stock_only_false_includes_all` | Products Edge | test in stock only false includes a | :green_circle: 100.0% | 1.870s | 1.87s / 1.87s |
| `test_load_products_corrupt_json` | Products Edge | test load products corrupt json | :green_circle: 100.0% | 0.746s | 0.746s / 0.746s |
| `test_load_products_file_not_found` | Products Edge | test load products file not found | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_pagination_offset_beyond_total` | Products Edge | test pagination offset beyond total | :green_circle: 100.0% | 4.657s | 4.657s / 4.657s |
| `test_price_filter_both` | Products Edge | test price filter both | :green_circle: 100.0% | 0.447s | 0.447s / 0.447s |
| `test_price_filter_max_only` | Products Edge | test price filter max only | :green_circle: 100.0% | 0.280s | 0.28s / 0.28s |
| `test_price_filter_min_only` | Products Edge | test price filter min only | :green_circle: 100.0% | 0.240s | 0.24s / 0.24s |
| `test_rating_exact_bounds` | Products Edge | test rating exact bounds | :green_circle: 100.0% | 1.760s | 1.76s / 1.76s |
| `test_search_blank_whitespace` | Products Edge | test search blank whitespace | :green_circle: 100.0% | 0.208s | 0.208s / 0.208s |
| `test_search_discount_filter_branch` | Products Edge | test search discount filter branch | :green_circle: 100.0% | 0.363s | 0.363s / 0.363s |
| `test_search_empty_string` | Products Edge | test search empty string | :green_circle: 100.0% | 0.218s | 0.218s / 0.218s |
| `test_search_in_stock_filter_branch` | Products Edge | test search in stock filter branch | :green_circle: 100.0% | 0.379s | 0.379s / 0.379s |
| `test_search_multi_word_and` | Products Edge | test search multi word and | :green_circle: 100.0% | 2.270s | 2.27s / 2.27s |
| `test_search_price_filter_branches` | Products Edge | test search price filter branches | :green_circle: 100.0% | 2.050s | 2.05s / 2.05s |
| `test_search_sort_by_price_asc_branch` | Products Edge | test search sort by price asc branc | :green_circle: 100.0% | 2.031s | 2.031s / 2.031s |
| `test_search_sort_by_price_desc_branch` | Products Edge | test search sort by price desc bran | :green_circle: 100.0% | 2.194s | 2.194s / 2.194s |
| `test_search_sort_by_rating_branch` | Products Edge | test search sort by rating branch | :green_circle: 100.0% | 2.038s | 2.038s / 2.038s |
| `test_search_triggers_load_products_when_cache_empty` | Products Edge | test search triggers load products  | :green_circle: 100.0% | 7.069s | 7.069s / 7.069s |
| `test_active_model_name_updates` | Config | test active model name updates | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_init_clients_does_not_crash` | Config | test init clients does not crash | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_model_fallback_chain_order` | Config | test model fallback chain order | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_openrouter_client_lazy_creation` | Config | test openrouter client lazy creatio | :green_circle: 100.0% | 0.561s | 0.561s / 0.561s |
| `test_run_with_retry_exhausts_and_raises` | Config | test run with retry exhausts and ra | :green_circle: 100.0% | 1.012s | 1.012s / 1.012s |
| `test_run_with_retry_succeeds_on_retry` | Config | test run with retry succeeds on ret | :green_circle: 100.0% | 1.010s | 1.01s / 1.01s |
| `test_run_with_retry_success` | Config | test run with retry success | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_cache_reload_paths` | Tools Edge | test cache reload paths | :green_circle: 100.0% | 5.137s | 5.137s / 5.137s |
| `test_compare_products_malformed_input` | Tools Edge | test compare products malformed inp | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_compare_products_no_valid_ids` | Tools Edge | test compare products no valid ids | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_compare_products_nonexistent_id` | Tools Edge | test compare products nonexistent i | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_compare_products_single_id` | Tools Edge | test compare products single id | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_compare_products_with_invalid_ids` | Tools Edge | test compare products with invalid  | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_compare_products_with_json_id` | Tools Edge | test compare products with json id | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_filter_by_tag_with_min_rating` | Tools Edge | test filter by tag with min rating | :green_circle: 100.0% | 0.017s | 0.017s / 0.017s |
| `test_rapidapi_search_http_error` | Tools Edge | test rapidapi search http error | :green_circle: 100.0% | 0.798s | 0.798s / 0.798s |
| `test_rapidapi_search_not_configured` | Tools Edge | test rapidapi search not configured | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_rapidapi_search_success` | Tools Edge | test rapidapi search success | :green_circle: 100.0% | 0.550s | 0.55s / 0.55s |
| `test_save_preference_overwrites_existing_key` | Tools Edge | test save preference overwrites exi | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_search_cache_hit` | Tools Edge | test search cache hit | :green_circle: 100.0% | 3.191s | 3.191s / 3.191s |
| `test_search_in_stock_only_filters_out_of_stock` | Tools Edge | test search in stock only filters o | :green_circle: 100.0% | 0.322s | 0.322s / 0.322s |
| `test_search_price_filter_filters_by_price` | Tools Edge | test search price filter filters by | :green_circle: 100.0% | 0.478s | 0.478s / 0.478s |
| `test_search_products_empty_result_set` | Tools Edge | test search products empty result s | :green_circle: 100.0% | 1.632s | 1.632s / 1.632s |
| `test_search_products_no_filters_returns_results` | Tools Edge | test search products no filters ret | :green_circle: 100.0% | 0.283s | 0.283s / 0.283s |
| `test_search_products_pagination_offset` | Tools Edge | test search products pagination off | :green_circle: 100.0% | 0.512s | 0.512s / 0.512s |
| `test_search_products_sort_by_rating` | Tools Edge | test search products sort by rating | :green_circle: 100.0% | 1.596s | 1.596s / 1.596s |
| `test_search_sort_by_price_ascending` | Tools Edge | test search sort by price ascending | :green_circle: 100.0% | 1.520s | 1.52s / 1.52s |
| `test_search_sort_by_price_descending` | Tools Edge | test search sort by price descendin | :green_circle: 100.0% | 1.715s | 1.715s / 1.715s |
| `test_search_with_category_filter` | Tools Edge | test search with category filter | :green_circle: 100.0% | 0.380s | 0.38s / 0.38s |
| `test_search_with_min_rating_filter` | Tools Edge | test search with min rating filter | :green_circle: 100.0% | 1.715s | 1.715s / 1.715s |
| `test_build_instructions_with_last_search` | Agent Edge | test build instructions with last s | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_build_instructions_with_preferences` | Agent Edge | test build instructions with prefer | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_build_instructions_with_seen_products` | Agent Edge | test build instructions with seen p | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_guardrail_exception_raises_through_run_turn` | Agent Edge | test guardrail exception raises thr | :green_circle: 100.0% | 0.002s | 0.002s / 0.002s |
| `test_run_recommendation_wrapper` | Agent Edge | test run recommendation wrapper | :green_circle: 100.0% | 0.004s | 0.004s / 0.004s |
| `test_tracing_force_flush_noop` | Tracing | test tracing force flush noop | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_tracing_shutdown_clears_active_traces` | Tracing | test tracing shutdown clears active | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_tracing_span_label_no_data` | Tracing | test tracing span label no data | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |
| `test_tracing_span_label_with_tool_name` | Tracing | test tracing span label with tool n | :green_circle: 100.0% | 0.001s | 0.001s / 0.001s |
| `test_tracing_write_jsonl_error_ignored` | Tracing | test tracing write jsonl error igno | :green_circle: 100.0% | 0.000s | 0.0s / 0.0s |

## Run-to-Run Timing

| Run # | Duration | Passed | Failed | Notes |
|-------|----------|--------|--------|-------|
| 1 | 78.55s | 116 | 0 | cold cache (JSON load) |

## Failed & Flaky Test Analysis

:check_mark: **100% stability across all runs.** No test ever failed.

---

*Report auto-generated by `generate_report.py` — 1 consecutive runs on 2026-06-03 at 17:10:06*
