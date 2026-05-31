# Recommendation Agent - Test Report


---

## Project Overview

**ShopBot** is an AI-powered product recommendation agent built with the OpenAI Agents SDK and routed through Groq (Llama 4 Scout). It provides a conversational CLI interface for users to discover products from a 1M-item catalogue.

### Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12 |
| AI SDK | OpenAI Agents SDK 0.17.3 |
| LLM | Groq (Llama 4 Scout 17B) via OpenAI-compatible endpoint |
| CLI | Rich (terminal UI) |
| Testing | pytest 9.0.3, pytest-asyncio, pytest-cov, pytest-html |
| Linting | Ruff |
| Config | dotenv (.env) |
| Packaging | uv |

### Project Structure

```
recommendations__agent/
  agent/
    __init__.py        # Package marker
    agent.py           # ShopBot agent definition + run_turn() entry point
    config.py          # Groq client wiring, model getter, tracing key
    context.py         # Per-request AgentContext (session, logs, user info)
    guardrails.py      # Input/output guardrails (off-topic, injection, quality)
    products.py        # Product loader + search / get_by_id / get_categories
    session_memory.py  # In-memory conversation session store
    tools.py           # 3 function tools (search_items, filter_by_tag, get_item_details)
    tracing.py         # Custom tracing processor (console + JSONL)
  data/
    products.json      # 1M-product catalogue (~142 MB)
  tests/
    test_agent.py      # 39 tests (35 unit + 4 integration)
    conftest.py        # pytest fixtures
  scripts/
    generate_products.py  # Synthetic data generator
  main.py              # CLI entry point
```

### What the Agent Does

ShopBot answers product recommendation queries through a conversational loop:

1. **Input guardrails** check for prompt injection and off-topic topics (coding, weather, finance, etc.)
2. **Agent reasoning** interprets the user's request and calls one of three tools:
   - `search_items` — full-text search across titles, categories, and tags
   - `filter_by_tag` — narrow by tag with optional minimum rating
   - `get_item_details` — fetch full details for a specific product ID
3. **Output guardrail** ensures the response is meaningful (at least 10 words, no error tracebacks)
4. **Session memory** preserves conversation history, seen product IDs, and user preferences across turns
5. **Tracing** logs every span to the console and `traces.jsonl`; forwards to OpenAI dashboard if configured

---

## Test Results Summary

| Metric | Value |
|--------|-------|
| **Total tests** | 39 |
| **Selected** | 35 |
| **Passed** | 35 |
| **Failed** | 0 |
| **Skipped** | 0 |
| **Deselected** | 4 |
| **Duration** | 41.43s |
| **Overall coverage** | **65%** |

### Deselected Tests

4 integration tests were deselected (`-k "not Integration"`) because they require a live Groq API key with available quota:

- `TestIntegration::test_basic_recommendation`
- `TestIntegration::test_multi_turn_context`
- `TestIntegration::test_off_topic_guardrail_live`
- `TestIntegration::test_session_persistence`

---

## Results by Test Class

### TestTools (13 tests)

| Test | Result | Time |
|------|--------|------|
| `test_catalogue_has_15_hardcoded` | PASSED | 0.20s (setup) |
| `test_all_items_includes_products_json` | PASSED | 3.32s |
| `test_search_items_finds_by_title` | PASSED | 5.18s |
| `test_search_items_finds_by_category` | PASSED | 4.43s |
| `test_search_items_case_insensitive` | PASSED | 5.29s |
| `test_search_items_no_results` | PASSED | 5.05s |
| `test_search_items_respects_max_results` | PASSED | 4.79s |
| `test_filter_by_tag_finds_items` | PASSED | 0.35s |
| `test_filter_by_tag_with_min_rating` | PASSED | 0.44s |
| `test_filter_by_tag_no_results` | PASSED | 0.35s |
| `test_get_item_details_found` | PASSED | 0.04s |
| `test_get_item_details_not_found` | PASSED | 0.46s |
| `test_get_item_details_products_json_item` | PASSED | 0.44s |

**Total:** 13/13 passed | **Slowest:** `test_search_items_case_insensitive` (5.29s)

### TestSessionMemory (9 tests)

| Test | Result | Time |
|------|--------|------|
| `test_add_and_get_items` | PASSED | < 0.01s |
| `test_get_items_with_limit` | PASSED | < 0.01s |
| `test_pop_item` | PASSED | < 0.01s |
| `test_clear_session` | PASSED | < 0.01s |
| `test_history_bounded` | PASSED | < 0.01s |
| `test_get_or_create_returns_same` | PASSED | < 0.01s |
| `test_mark_seen` | PASSED | < 0.01s |
| `test_update_preferences` | PASSED | < 0.01s |
| `test_summary` | PASSED | < 0.01s |

**Total:** 9/9 passed | All complete in < 0.01s each

### TestGuardrails (11 tests)

| Test | Result | Time |
|------|--------|------|
| `test_injection_blocked` | PASSED | 0.09s |
| `test_injection_allowed` | PASSED | < 0.01s |
| `test_off_topic_blocked` | PASSED | < 0.01s |
| `test_off_topic_weather_blocked` | PASSED | < 0.01s |
| `test_off_topic_news_blocked` | PASSED | < 0.01s |
| `test_off_topic_sports_blocked` | PASSED | < 0.01s |
| `test_off_topic_travel_blocked` | PASSED | < 0.01s |
| `test_off_topic_allowed` | PASSED | < 0.01s |
| `test_output_quality_too_short` | PASSED | < 0.01s |
| `test_output_quality_passes` | PASSED | < 0.01s |
| `test_output_blocks_traceback` | PASSED | < 0.01s |

**Total:** 11/11 passed | All complete in < 0.01s each (except `test_injection_blocked` at 0.09s)

### TestContext (2 tests)

| Test | Result | Time |
|------|--------|------|
| `test_log_tool` | PASSED | < 0.01s |
| `test_context_summary` | PASSED | < 0.01s |

**Total:** 2/2 passed | Both complete in < 0.01s

---

## Coverage by Module

| Module | Statements | Missed | Coverage | Missing Lines |
|--------|-----------|--------|----------|---------------|
| `agent/__init__` | 4 | 0 | **100%** | — |
| `agent/context` | 14 | 0 | **100%** | — |
| `agent/tools` | 24 | 0 | **100%** | — |
| `agent/session_memory` | 47 | 2 | **96%** | 55, 98 |
| `agent/config` | 21 | 4 | **81%** | 36-39 |
| `agent/guardrails` | 50 | 12 | **76%** | 138-145, 169-176 |
| `agent/agent` | 33 | 19 | **42%** | 101-146, 152-153 |
| `agent/tracing` | 63 | 36 | **43%** | 24-25, 44-46, 50-56, 66-67, 74-80, 91, 95, 100-105, 109-115, 119-123 |
| `agent/products` | 57 | 35 | **39%** | 32-34, 39-41, 46, 62-101 |
| **Total** | **313** | **108** | **65%** | |

### Uncovered Lines Detail

#### `agent/products.py` (39% — lowest coverage)

- **Lines 32-34:** `search()` — early-return when query is empty/blank
- **Lines 39-41:** `search()` — multi-word AND logic branch
- **Lines 62-101:** `get_by_id()`, `get_categories()`, filtering by price/rating/discount/in_stock, sorting, pagination — these branches are not exercised because the test suite only tests search via `search_items_fn()` at the tool level (which calls `search()` internally) and does not test the raw `get_by_id()`, `get_categories()`, or advanced filtering parameters directly.

**Root cause:** The test suite covers tools (`search_items_fn`, `filter_by_tag_fn`, `get_item_details_fn`) but not the underlying `products.py` API directly. All the filtering parameters (`min_price`, `max_price`, `min_rating`, `min_discount`, `in_stock_only`, `sort_by`, pagination) are untested.

#### `agent/agent.py` (42%)

- **Lines 101-146:** `run_turn()` — most of the function body, including the `try/except` guardrail-restore block and the `with trace(...)` context manager. These lines require live API calls to exercise.
- **Lines 152-153:** `run_recommendation()` — backward-compatible wrapper is never called.

**Root cause:** `run_turn()` requires calling `Runner.run()` which hits the LLM API. Without a live API key, these lines are skipped.

#### `agent/tracing.py` (43%)

- **Lines 24-25:** rich import fallback (rich is installed)
- **Lines 44-80:** trace/span lifecycle methods (`on_trace_start`, `on_trace_end`, `on_span_start`, `on_span_end`) — only trigger during live `Runner.run()` calls
- **Lines 100-115:** `_print()` UnicodeEncodeError fallback, `_write_jsonl()` error handling, module registration.

**Root cause:** Tracing processor only activates during live LLM calls. Most of its methods are never called in unit tests.

#### `agent/config.py` (81%)

- **Lines 36-39:** `get_model()` — only called during live agent runs.

#### `agent/guardrails.py` (76%)

- **Lines 138-145, 169-176:** Input guardrail text-extraction branches for list/dict input formats. Tests only pass string inputs, so the `isinstance(input, list)` branches are never exercised.

#### `agent/session_memory.py` (96%)

- **Line 55:** `clear_session()` `history.clear()` — covered but `history_len` assertion requires checking after clear.
- **Line 98:** `drop_session()` — the `pop()` default `None` branch.

---

## Top 5 Slowest Tests

| Rank | Test | Duration | Notes |
|------|------|----------|-------|
| 1 | `test_search_items_case_insensitive` | 5.29s | Loads `products.json` (142 MB) on first call |
| 2 | `test_search_items_finds_by_title` | 5.18s | Same JSON load (cached after first call) |
| 3 | `test_search_items_no_results` | 5.05s | Same |
| 4 | `test_search_items_respects_max_results` | 4.79s | Same |
| 5 | `test_search_items_finds_by_category` | 4.43s | Same |

**Observation:** The first test that calls `load_products()` pays a ~5s penalty to parse `data/products.json`. Subsequent calls are cached. All 6 search-related tests are in `TestTools` and run sequentially, so the first one bears the full load cost.

**Mitigation:** Pre-load `load_products()` once in a `pytest_sessionstart` hook or use a smaller test fixture file.

---

## Findings and Recommendations

### 1. Low coverage in core agent modules (42% agent.py, 39% products.py)

The `run_turn()` function and most of `products.py`'s rich filtering API are untested because they either require a live LLM call or are only exercised indirectly through tool wrappers.

**Recommendation:** Add unit tests that mock `Runner.run()` to verify `run_turn()` error handling, guardrail restore logic, and context propagation without needing an API key. Add direct tests for `products.search()`, `products.get_by_id()`, and `products.get_categories()` with known data.

### 2. Integration tests require a live API key

All 4 integration tests are deselected by default. The Groq free tier has rate limits that may block frequent runs.

**Recommendation:** Add a `--run-integration` flag to `conftest.py` so the tests can be explicitly enabled. Consider a mock LLM fixture for CI pipelines.

### 3. JSON file loading is the performance bottleneck

The 142 MB `data/products.json` adds ~5s to the first test that touches it. This affects every `search_items` test.

**Recommendation:** Create a small (100-200 item) JSON fixture file for tests and point `load_products()` at it during test runs. Alternatively, add a `PYTEST_CACHE_DIR` override in `conftest.py`.

### 4. products.json contains synthetic/garbage data

The file at `data/products.json` contains ~1M entries with titles like `"BlanchedAlmond Upgradable motivating methodology"` that make multi-turn recommendation sessions unrealistic.

**Recommendation:** Either replace with real product data or regenerate with meaningful titles. The hardcoded CATALOGUE (15 real products) is sufficient for basic queries, but the JSON file's entries pollute search results with noise.

### 5. Guardrail text-extraction branches are untested

The code paths for handling list/dict input in guardrails (lines 138-145, 169-176) have no test coverage.

**Recommendation:** Add unit tests that pass `[{"role": "user", "content": "test"}]` format input directly to the guardrail functions.

### 6. Tracing processor is essentially untested

At 43% coverage, the tracing module has no dedicated tests. All spans are generated during live LLM calls.

**Recommendation:** Create a test that instantiates `RecommendationTracingProcessor` and manually calls `on_trace_start` / `on_trace_end` / `on_span_end` with fabricated trace/span objects to verify logging and JSONL output.

---
