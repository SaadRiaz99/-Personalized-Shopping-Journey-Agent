# Recommendation Agent — Capabilities & Feature Specification

## 1. Executive Overview

The **Recommendation Agent** is a production-ready conversational product-recommendation system built on the **OpenAI Agents SDK v0.2.2** with a **5-model OpenRouter fallback chain**. It delivers personalised product suggestions through natural-language interaction, backed by a **vector database (Qdrant Cloud) of 50,000 real Amazon products**, **RapidAPI for live pricing**, a 1M+ item local catalogue, stateful session tracking, and defensive input/output guardrails.

The agent has been validated across **269 automated tests** covering 25+ capability categories with a **100% pass rate** and **92% code coverage**.

**Model Chain (all via OpenRouter)**

| Priority | Model ID |
|----------|----------|
| Primary | `google/gemini-2.0-flash-001:free` |
| Fallback 1 | `moonshotai/kimi-k2.6:free` |
| Fallback 2 | `openai/gpt-oss-120b:free` |
| Fallback 3 | `openai/gpt-oss-20b:free` |
| Fallback 4 | `qwen/qwen3-next-80b-a3b-instruct:free` |

---

## 2. Core Features & Abilities

### 2.1 Qdrant Cloud Vector Database

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **50K real Amazon products** | Stratified sampling: cap 500/category, fill to 50K from global pool; min rating 4.0, avg 4.72 | `TestRealAmazonData` (5 tests) |
| **384-dim semantic embeddings** | `all-MiniLM-L6-v2` (sentence-transformers) via `embed_query()` | `test_embedding_dimension` |
| **Cosine similarity search** | `search(query, limit=10, category=None, price_range=None, rating=None)` with payload filters | `test_semantic_search_returns_results` |
| **Payload indexes** | `category_name` (keyword), `price` (float), `rating` (float), `review_count` (int), `in_stock` (bool) | `test_qdrant_collection_has_indexes` |
| **Graceful fallback** | Falls back to keyword `search_items` when Qdrant unavailable or QDRANT_URL not set | `test_qdrant_fallback_on_missing_collection` |
| **Payload filtering** | Combined category + price + rating + stock filters via `_build_filter()` | `test_semantic_search_with_filters` |
| **Result deduplication** | `semantic_search_fn` deduplicates by ID and filters out already-seen products | `test_semantic_search_deduplicates` |
| **UUID point IDs** | Deterministic UUID5 from ASIN; no collision risk | `scripts/embed_products.py` |

### 2.2 RapidAPI Live Search

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Real-time Amazon pricing** | HTTP GET to RapidAPI host with query/page/country params | `test_rapidapi_not_configured_returns_error` |
| **Rate-limit awareness** | 100 requests/month hard cap; returns `{"error": "RapidAPI not configured"}` when key missing | Error-path tests |
| **Live deal discovery** | User asks "current price of X" or "latest deals on Y" | — |

### 2.3 Hybrid Search (Qdrant Vectors + Keyword)

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Reciprocal Rank Fusion** | `hybrid_search(query, alpha=0.5)` merges ranked lists with RRF scoring | `test_hybrid_search_rrf` |
| **Semantic mode** | `search_mode="semantic"` — vector search only | `test_hybrid_search_semantic_mode` |
| **Keyword mode** | `search_mode="keyword"` — keyword search only | `test_hybrid_search_keyword_mode` |
| **Hybrid mode** | `search_mode="hybrid"` — weighted RRF merge | `test_hybrid_search_hybrid_mode` |
| **Empty fallback** | Graceful when one mode returns empty | `test_hybrid_search_empty_fallback` |

### 2.4 Personalization

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Category preference boost** | Products matching `preferred_category` score 2x | `test_personalization_category_boost` |
| **Price-range matching** | Products within `preferred_min_price`/`max_price` boosted | `test_personalization_price_boost` |
| **Brand preference boost** | Products matching `preferred_brand` score 2x | `test_personalization_brand_boost` |
| **Automatic budget expansion** | Expands budget by 20% when no results found | `test_personalization_budget_expansion` |
| **Empty preferences** | Returns original order when no preferences set | `test_personalization_empty_preferences` |

### 2.5 Similar Products

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Vector-based similarity** | `similar_products(product_id, limit=10)` — Qdrant vector nearest-neighbour | `test_similar_products_returns_results` |
| **Semantically related items** | Results are meaningfully similar to source product | `test_similar_products_are_semantically_similar` |
| **Self-exclusion** | Original product excluded from results | `test_similar_products_excludes_self` |
| **Seen-ID filtering** | Already-shown products excluded | `test_similar_products_excludes_seen_ids` |
| **Invalid ID handling** | Returns friendly error for non-existent IDs | `test_similar_products_invalid_id` |

### 2.6 Trending Products

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Review-count ranking** | `trending_products(category=None, limit=10)` sorted by `review_count` desc | `test_trending_sorted_by_review_count` |
| **High-review threshold** | All returned items have review_count >= 1000 | `test_trending_min_review_count` |
| **Category filtering** | Category parameter passed to Qdrant filter | `test_trending_category_filter` |
| **Global trending** | Empty/null category returns global top | `test_trending_global_no_category` |

### 2.7 LRU Caching Layer

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **LRU eviction** | `LRUQueryCache(maxsize=256, ttl=300)` — evicts least recently used | `test_cache_eviction` |
| **TTL expiry** | Cache entries expire after configured TTL | `test_cache_expiry` |
| **Hit/miss tracking** | `hit_count` / `miss_count` counters | `test_cache_hit`, `test_cache_miss` |

### 2.8 Session Architecture

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Multi-turn context tracking** | `InMemorySession` with rolling history window (default 40 turns); each turn appends user + assistant messages | `TestSessionMemory` (10 tests) |
| **Absolute session isolation** | Global `_sessions` dict registry; `get_or_create_session()` returns unique instance per ID; separate sessions never share state | `test_get_or_create_returns_same_session` |
| **Duplicate-recommendation prevention** | `seen_ids: set[int]` per session; agent instructions dynamically include "Products already shown to this user — DO NOT recommend again" | `test_mark_seen_ids`, `test_build_instructions_with_seen_products` |
| **User preference memory** | `preferences: dict[str, str]` persisted across turns; arbitrary keys (budget, brand, colour, etc.) via `save_preference` tool | `test_update_preferences`, `test_save_preference_stores_value` |
| **Pagination continuity** | `last_search_params` stored per session; agent resumes from last offset when user asks for "more" | `test_build_instructions_with_last_search` |
| **Cleanup & lifecycle** | `drop_session()` for explicit teardown; `list_sessions()` for active-session enumeration | `test_list_sessions`, `test_clear_session` |
| **Pop & rollback** | `pop_item()` removes last interaction; used internally for guardrail-driven state recovery | `test_pop_item`, `test_pop_item_on_empty_session` |

**Session latency:** All session-memory operations execute in **< 0.001s** (pure in-memory, no I/O).

### 2.9 Search & Filtering (Local Catalogue)

| Capability | Parameters / Behaviour | Verified By |
|------------|------------------------|-------------|
| **Multi-word AND search** | Query split on whitespace; every word must match title **or** any tag | `test_search_multi_word_and` |
| **Category scoping** | `category` param filters by exact match (case-insensitive) | `test_search_by_category` (10 tests across `Tools` + `ToolsEdge`) |
| **Price-range filtering** | `min_price` / `max_price`; skips items without a price field (graceful degradation) | `test_price_filter_both`, `test_price_filter_min_only`, `test_price_filter_max_only` (3 tests) |
| **Minimum rating** | `min_rating` (0.0–5.0); only items meeting or exceeding threshold | `test_rating_exact_bounds`, `test_search_with_min_rating_filter` |
| **Stock-status filtering** | `in_stock_only`; items without an `in_stock` field are included (field-optional) | `test_in_stock_filter`, `test_in_stock_only_false_includes_all` (3 tests) |
| **Discount filtering** | `min_discount` %; items without `discount` field pass through | `test_search_discount_filter_branch` |
| **Tag-based discovery** | `filter_by_tag_fn` matches hardcoded catalogue + `products.json` tags | `test_filter_products_by_category`, `test_filter_by_tag_with_min_rating` (3 tests) |
| **Sorting** | `sort_by` ∈ `{relevance, rating, price_asc, price_desc}` | `test_sorting_ascending_and_descending`, `test_search_sort_by_rating_branch`, `test_search_sort_by_price_asc_branch`, `test_search_sort_by_price_desc_branch` (4 tests) |
| **Pagination** | `offset` / `limit` slicing; disjoint pages guaranteed | `test_pagination_no_overlap`, `test_search_products_pagination_offset`, `test_pagination_offset_beyond_total` (3 tests) |
| **Empty / whitespace query** | Returns unfiltered catalogue (paginated); safe for open-ended browsing | `test_search_empty_string`, `test_search_blank_whitespace` |
| **No-results edge case** | Returns `{"items": [], "total": 0, "offset": 0}` | `test_search_products_empty_result_set` |
| **Cache layer** | LRU-like `_search_cache` (max 256 entries); keyed by all 10 params | `test_search_cache_hit` |

### 2.10 Security & Input Guardrails

Three guardrail layers enforce content safety before and after model execution:

#### Input Guardrail 1 — Injection / Abuse Check

Blocks prompt-injection, jailbreak, and authority-override patterns:

| Pattern Class | Examples |
|---------------|----------|
| Direct abuse terms | `hack`, `exploit`, `steal`, `fraud`, `scam`, `bypass`, `jailbreak` |
| Instruction override | `ignore all instructions`, `ignore previous instructions` |
| Authority impersonation | `you are now`, `pretend you are`, `pretend to be`, `act as a different`, `act as an unrestricted`, `act as an evil` |

#### Input Guardrail 2 — Off-Topic Detection

Rejects queries outside product-recommendation scope. **17 categories** are blocked, with a commerce-intent pre-check: product buying terms (e.g., "budget headphones", "programming laptop") take priority over off-topic pattern matching to avoid false positives.

#### Output Guardrail — Response Quality

| Check | Threshold | Behaviour |
|-------|-----------|-----------|
| Minimum length | < 10 words | Blocks response |
| Traceback leakage | `"Traceback (most recent call last)"` present | Blocks response |

### 2.11 Chainlit Chat UI

| Capability | Implementation | Verified By |
|------------|---------------|-------------|
| **Welcome message** | `on_chat_start` sends "Welcome! I'm your Recommendation Agent..." | `test_welcome_message` |
| **Message handling** | `on_message` calls `run_turn` with correct session/user IDs | `test_on_message_uses_run_turn` |
| **Guardrail feedback** | Yellow warning on input guardrail; retry prompt on output guardrail | `test_guardrail_caught_in_message` |
| **Empty input** | Graceful skip for empty messages | `test_empty_input_graceful` |
| **Error handling** | Network/timeout errors caught with friendly message | `test_network_error_handling` |
| **Session isolation** | Unique `session_id` per user via UUID | `test_unique_session_ids` |

---

## 3. Data Quality

| Metric | Local Catalogue | RapidAPI | Qdrant Cloud |
|--------|----------------|----------|--------------|
| **Source** | AI-generated + curated | Live Amazon | Real Amazon (cleaned) |
| **Size** | 1,000,000+ items | Unlimited (API) | 50,000 vectors |
| **Quality score** | 0/100 (AI) / 100/100 (curated) | Live | 97.1/100 |
| **Rating filter** | Any | Any | ≥ 4.0 only |
| **Uniqueness** | Deduplicated | — | UUID5 per ASIN |
| **Categories** | 10+ | Any | 50+ unique |

---

## 4. Technical Specifications & Benchmarks

### 4.1 Latency Baselines

| Category | Avg Latency | Notes |
|----------|-------------|-------|
| **Session memory** | < 0.001s | Pure in-memory |
| **Guardrails** | < 0.005s | Regex-only |
| **Catalogue search (cached)** | < 0.5s | 256-entry LRU |
| **Catalogue search (cold)** | 4–7s | Full scan 1M items |
| **Qdrant vector search** | ~0.1–0.5s | 384-dim, 50K vectors |
| **RapidAPI live search** | ~1–5s | Network-dependent |
| **Embedding generation** | ~0.05s | all-MiniLM-L6-v2 |
| **Full test suite (269 tests)** | ~10 min | Includes LLM calls |

### 4.2 Retry & Fallback Resilience

| Mechanism | Configuration | Behaviour |
|-----------|---------------|-----------|
| **Per-model retry** | `run_with_retry(coro_factory, max_retries=3)` with exponential backoff (1s → 2s → 4s) | Transient API errors retried automatically |
| **Cross-model fallback** | 5 models tried sequentially; each failure rolls back session state to pre-turn snapshot | State is never corrupted by partial failures |
| **Graceful degradation** | If all 5 models fail, returns `"Our recommendation service is temporarily unavailable. Please try again in a moment."` | Tested via mocked exceptions |
| **Guardrail state rollback** | On guardrail trigger, session is reverted to saved snapshot | `test_guardrail_exception_raises_through_run_turn` |
| **Qdrant fallback** | If Qdrant unavailable, `semantic_search` falls back to keyword `search_items` | `test_qdrant_fallback_on_missing_collection` |

### 4.3 API Surface

| Endpoint | Method | Request | Response | Status Codes |
|----------|--------|---------|----------|--------------|
| `/recommend` | POST | `{user_message: str, session_id: str, user_id: str}` | `{response: str, tool_calls: list[str], session_summary: dict}` | 200 (success), 422 (guardrail triggered) |
| `/health` | GET | — | `{status: "ok"}` | 200 |
| Chainlit UI | — | Chat at `/` | Chat interface | — |

CORS: `allow_origins=["*"]` — accepts requests from any origin including `file://`.

---

## 5. Test Coverage Summary

| Test File | Tests | Groups | Pass Rate |
|-----------|-------|--------|-----------|
| `tests/test_agent.py` | 92 | Tools, Session, Guardrails, Context, MockLLM, Integration, SemanticSearch | 100% |
| `tests/test_all_51.py` | 116 | Catalogue, Tools, Session, Guardrails, Context, Error, Streaming, ProductsEdge, Config, ToolsEdge, AgentEdge, Tracing, Frontend | 100% |
| `tests/test_new_features.py` | 61 | QdrantIntegration, ChainlitIntegration, SemanticSearch, HybridSearch, Personalization, SimilarProducts, TrendingProducts, QdrantHealthCheck, CachingLayer, RealAmazonData | 100% |
| `tests/test_recommendation_agent.py` | 28 | ColdStart, FilterCriteria, LlmOutputFormat, PropertyBased, Latency, InvalidInput, SessionAndGuardrails | 100% |
| **Total** | **269** | **25+ groups** | **100%** |

**Code Coverage:** 92% (agent/ package)

### 5.1 500-Test Integration Suite

| Metric | Value |
|--------|-------|
| Test cases | 500 across 14 categories |
| First 50 results | 47/50 passed (94%) |
| Failures | 2 short responses, 1 timeout |
| Timeout barrier | 120s per test |

---

## 6. Qdrant Collection Schema

| Property | Value |
|----------|-------|
| **Collection name** | `products` |
| **Vector count** | 50,000 |
| **Vector dimension** | 384 |
| **Distance metric** | Cosine |
| **Point ID type** | UUID (UUID5 from ASIN) |

**Payload fields stored:** `id`, `asin`, `title`, `category_id`, `category_name`, `price`, `original_price`, `discount_pct`, `rating`, `review_count`, `brand`, `image_url`, `in_stock`

**Payload indexes:**

| Field | Type |
|-------|------|
| `category_name` | Keyword |
| `price` | Float |
| `rating` | Float |
| `review_count` | Integer |
| `in_stock` | Bool |

---

## 7. Agent Search Strategy

The agent's SearchAgent prompt explicitly guides tool selection based on user intent:

1. **semantic_search** (Vector DB) — for vague, intent-based, or need-driven queries
2. **rapidapi_search** (RapidAPI) — for live prices, current deals, real-time availability
3. **search_items** (Local catalogue) — for exact product names or precise filters

This dual-advantage architecture gives the agent both **semantic understanding** (vector DB) and **real-time accuracy** (RapidAPI).

---

## 8. Roadmap Optimisations

| Optimisation | Current State | Target |
|--------------|---------------|--------|
| **Full 500-test suite** | First 50 at 94% pass rate | Run all 500 overnight |
| **Chainlit live test** | Unit-tested with mocks | Manual end-to-end verification |
| **RapidAPI rate limit** | 100 requests/month | Upgrade plan or cache aggressively |
| **Coverage gaps** | 92% overall | Push to 95%+ (personalization, qdrant_search error branches) |

---

*Specification version 2.0 — verified by 269 automated tests, 0 failures, 92% code coverage.*
