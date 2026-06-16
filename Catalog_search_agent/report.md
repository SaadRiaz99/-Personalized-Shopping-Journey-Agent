# Catalog Search Agent - Test Report

- **Date:** 2026-06-03
- **Provider:** OpenRouter (openai/gpt-4o-mini)
- **Product Catalog:** 906 products across 7 categories
- **Framework:** pytest + pytest-asyncio + VCR.py
- **Total Tests:** 71
- **Unit Tests:** 46 (passed: 46, failed: 0)
- **Integration Tests:** 25 (require API key to run)
- **Pass Rate:** 100% of runnable tests (46/46)

## Recent Enhancements

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Token-level scoring replaces exact substring matching. Handles stemming, singular/plural, fuzzy matching via `difflib`, stop word filtering, and relevance ranking. |
| **Price Range Filter** | `search_products` now accepts `min_price` alongside `max_price` for price range queries (e.g. "products between $50 and $150"). |
| **Feedback Tool** | New `add_feedback(product_id, rating, comment)` tool stores per-user ratings in `FEEDBACK_STORE`. Agent instructions include guidance to use it. |
| **Guardrail Resilience** | Guardrail agent wraps `Runner.run()` in try/except to handle model hallucination tool calls gracefully, defaulting to allowing the query. |
| **VCR Removed from Parametrized Tests** | Removed VCR cassettes from parametrized integration tests to avoid cassette sharing conflicts. Tests run live when API key is set. |

## Test Suite Structure

| Category | Tests | Type | Description |
|----------|-------|------|-------------|
| Product Search | 23 | Unit | Search by name, category, price, rating, min price, combined filters, zero results, semantic singular/plural, semantic fuzzy |
| Product Details | 13 | Unit | Valid IDs, invalid IDs, various product IDs, out-of-stock |
| Categories | 2 | Unit | List all categories, category count |
| Product Data Integrity | 5 | Unit | Required fields, valid prices, ratings range, unique IDs, valid categories |
| Feedback | 2 | Unit | Store & retrieve feedback, multiple entries |
| Catalog Queries | 10 | Integration | Natural language product searches via LLM |
| Guardrail Rejection | 6 | Integration | Non-catalog queries correctly rejected |
| Edge Cases | 7 | Integration | Special characters, stock checks, comparisons, gifts, multi-intent |
| Invalid ID Handling | 1 | Integration | Graceful handling of non-existent product IDs |
| Out-of-Stock Mention | 1 | Integration | Stock status mentioned in response |

## How to Run

```powershell
# Unit tests only (no API key needed)
pytest test_agent.py -v -m "not needs_api"

# Integration tests (requires API key)
$env:OPENROUTER_API_KEY = "your-key"
pytest test_agent.py -v -m needs_api

# All tests
$env:OPENROUTER_API_KEY = "your-key"
pytest test_agent.py -v
```
