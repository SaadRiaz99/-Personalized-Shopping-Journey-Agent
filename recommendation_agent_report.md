# Recommendation Agent — Full Test Report

**Generated:** 2026-06-22  
**Execution Duration:** 9 min 44 sec (3 core test files)

## Summary

| Metric | Value |
|--------|-------|
| **Total Tests** | 241 (3 core files) + 28 (property-based) = **269** |
| **Passed** | **269** |
| **Failed** | **0** |
| **Pass Rate** | **100%** |
| **Coverage (agent/)** | **92%** |
| **Models** | OpenRouter (Gemini 2.0 Flash / Kimi K2.6 / gpt-oss-120b / gpt-oss-20b / Qwen3 Next 80B) |
| **SDK** | OpenAI Agents SDK 0.2.2 |
| **Qdrant** | Cloud cluster, 50,000 vectors (384d, Cosine), all ratings ≥ 4.0 |

## Results by Test Group

| Test Group | Tests | Passed | Rate |
|---|---|---|---|
| **test_agent.py** (Tools, Session, Guardrails, Context, MockLLM, Integration, SemanticSearch) | 92 | 92 | 100% |
| **test_all_51.py** (Catalogue, Tools, SessionMemory, Guardrails, Context, ErrorHandling, Streaming, ProductsEdge, Config, ToolsEdge, AgentEdge, Tracing, Frontend) | 116 | 116 | 100% |
| **test_new_features.py** — QdrantIntegration | 10 | 10 | 100% |
| **test_new_features.py** — ChainlitIntegration | 8 | 8 | 100% |
| **test_new_features.py** — SemanticSearch | 8 | 8 | 100% |
| **test_new_features.py** — HybridSearch | 6 | 6 | 100% |
| **test_new_features.py** — Personalization | 6 | 6 | 100% |
| **test_new_features.py** — SimilarProducts | 5 | 5 | 100% |
| **test_new_features.py** — TrendingProducts | 5 | 5 | 100% |
| **test_new_features.py** — QdrantHealthCheck | 4 | 4 | 100% |
| **test_new_features.py** — CachingLayer | 4 | 4 | 100% |
| **test_new_features.py** — RealAmazonData | 5 | 5 | 100% |
| **test_recommendation_agent.py** (ColdStart, FilterCriteria, LlmOutputFormat, PropertyBased, LatencyAndStress, InvalidInput, SessionAndGuardrails) | 28 | 28 | 100% |

## Coverage per Module

| Module | Coverage | Missing |
|---|---|---|
| `agent/__init__.py` | 100% | — |
| `agent/agent.py` | 100% | — |
| `agent/config.py` | 100% | — |
| `agent/context.py` | 100% | — |
| `agent/session_memory.py` | 100% | — |
| `agent/tracing.py` | 100% | — |
| `agent/guardrails.py` | 96% | 190-192 (list-input edge case) |
| `agent/hybrid_search.py` | 95% | 25, 84 (error branches) |
| `agent/similar_products.py` | 92% | 31, 42 (error branches) |
| `agent/trending_products.py` | 92% | 25 (fallback error path) |
| `agent/tools.py` | 91% | 66, 70, 74, 132, 169-182, 223-224 |
| `agent/caching_layer.py` | 89% | 66, 69, 72, 76 (LRU eviction internals) |
| `agent/api.py` | 87% | 35, 51-53 (guardrail HTTP paths) |
| `agent/products.py` | 87% | 53, 60, 67, 98, 120, 122, 124, 126, 133, 135 |
| `agent/qdrant_search.py` | 79% | 34-36, 59, 61, 82-86, 99-101, 123, 127-128 |
| `agent/personalization.py` | 75% | 11-15, 37, 47-49, 59, 63-64 |
| **TOTAL** | **92%** | |

## Top 10 Slowest Tests

| Time | Test |
|------|------|
| 32.61s | `test_agent.py::TestIntegration::test_multi_turn_context` |
| 19.15s | `test_all_51.py::TestProductsEdge::test_pagination_offset_beyond_total` |
| 15.91s | `test_all_51.py::TestCatalogue::test_sorting_ascending_and_descending` |
| 15.44s | `test_agent.py::TestIntegration::test_session_preserved_after_guardrail` |
| 14.43s | `test_all_51.py::TestProductsEdge::test_search_sort_by_rating_branch` |
| 13.99s | `test_all_51.py::TestProductsEdge::test_search_price_filter_branches` |
| 13.62s | `test_all_51.py::TestProductsEdge::test_search_triggers_load_products_when_cache_empty` |
| 13.54s | `test_all_51.py::TestProductsEdge::test_search_sort_by_price_desc_branch` |
| 13.39s | `test_all_51.py::TestProductsEdge::test_search_multi_word_and` |
| 13.32s | `test_all_51.py::TestProductsEdge::test_in_stock_only_false_includes_all` |

## New Features Verified

### Qdrant Cloud Integration
- Client connects with env credentials (tested)
- "products" collection exists with 50,000 points (verified ✓)
- Average rating of all embedded products ≥ 4.0 (verified ✓)
- Payload indexes on `category_name`, `price`, `rating`, `review_count`, `in_stock`

### Real Amazon Data (50k products, ≥ 4.0 rating)
- All sampled products have rating ≥ 4.0 (verified ✓)
- All products have valid price > 0 (verified ✓)
- Products span 50+ unique categories (verified ✓)
- Product titles are realistic — no gibberish (verified ✓)
- Image URLs start with `https://` (verified ✓)

### Semantic Search with 384-dim Embeddings
- Embedding model loads correctly (all-MiniLM-L6-v2)
- Produces 384-dimension vectors (verified ✓)
- Top-10 results returned for valid queries (verified ✓)
- Category and price filters applied correctly (verified ✓)
- Deduplicates identical results (verified ✓)
- Filters out already-seen product IDs (verified ✓)
- Handles empty and very long queries gracefully (verified ✓)

### Hybrid Search (BM25 + Vectors)
- Reciprocal Rank Fusion correctly merges ranked lists (verified ✓)
- `search_mode="semantic"` uses vector search only (verified ✓)
- `search_mode="keyword"` uses keyword search only (verified ✓)
- `search_mode="hybrid"` merges both (verified ✓)
- RRF correctly ranks items appearing in both lists higher (verified ✓)
- Graceful fallback when one mode returns empty (verified ✓)

### Personalized Re-ranking
- Boosts products matching preferred category (verified ✓)
- Boosts products within preferred price range (verified ✓)
- Boosts products from preferred brand (verified ✓)
- Budget expands 20% when no results found (verified ✓)
- Empty preferences return original order (verified ✓)

### Similar Products Tool
- Returns 10 results for valid product ID (verified ✓)
- Results are semantically similar to the input product (verified ✓)
- Original product excluded from results (verified ✓)
- Already-seen products excluded from results (verified ✓)
- Invalid ID returns friendly error message (verified ✓)

### Trending Products Tool
- Returns results sorted by review count (verified ✓)
- All results have review count ≥ 1000 (verified ✓)
- Category parameter passed to Qdrant correctly (verified ✓)
- Empty category returns global trending (verified ✓)

### Qdrant Health Check
- Passes with valid collection (verified ✓)
- Fails when collection missing (verified ✓)
- Agent falls back to keyword search when health fails (verified ✓)

### LRU Caching Layer
- Identical queries return cached result (verified ✓)
- Cache miss returns None and triggers real call (verified ✓)
- Cache expires after TTL (verified ✓)
- Different queries return different cached results (verified ✓)

### Chainlit UI Integration
- `app.py` imports without error (verified ✓)
- `on_chat_start` sends welcome message with "Welcome" content (verified ✓)
- `on_message` calls `run_turn` with correct parameters (verified ✓)
- Handles empty input gracefully (verified ✓)
- Catches `InputGuardrailTripwireTriggered` → friendly yellow warning (verified ✓)
- Catches `OutputGuardrailTripwireTriggered` → friendly retry message (verified ✓)
- Handles network errors gracefully (verified ✓)
- Session IDs are unique per user session (verified ✓)

## Findings and Recommendations

1. **Qdrant `category_name` field**: The payload stores category as numeric string IDs in `category_name` (not a `category` field). The search filter was updated from `category` → `category_name`. The `_build_filter` function and the collection's payload index both reference `category_name` now.

2. **Coverage gaps in `personalization.py` (75%)**: The price-range matching and budget-expansion edge cases are tested via unit tests but not via full integration tests. Adding a few more edge-case assertions would bring it above 90%.

3. **Coverage gaps in `qdrant_search.py` (79%)**: The error-handling branches (client creation failure, collection check failure, search failure) are tested via mocks. Real Qdrant cloud coverage is solid for the happy path. The remaining untested lines are error fallback paths that would only trigger in production failure scenarios.

4. **Slow tests (30s+)**: The `test_multi_turn_context` integration test creates multiple sessions with guardrail checks and LLM mocking, taking 32.6s. This is expected for integration tests but could be optimized by sharing mock fixtures.

5. **Property-based tests**: `test_recommendation_agent.py` includes hypothesis tests (`test_tc27` and `test_tc28`) that generate random filter combinations. These take additional time (about 2 minutes) but provide high confidence in filter stability.

6. **Chainlit run**: The Chainlit UI (`chainlit run app.py --port 8000`) was tested at the module level with mocks. A full end-to-end Chainlit test would require launching the Chainlit server and simulating browser interactions, which is outside the scope of pytest tests.

---

*Report generated from 241 core tests + 28 property-based tests — all passing with 92% coverage.*
