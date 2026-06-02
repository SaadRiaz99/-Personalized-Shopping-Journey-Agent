# Catalog Search Agent - Test Report

- **Date:** 2026-06-02
- **Provider:** OpenRouter (openai/gpt-4o-mini)
- **Product Catalog:** 906 products across 7 categories
- **Framework:** pytest + pytest-asyncio
- **Total Tests:** 66
- **Passed:** 66
- **Failed:** 0
- **Pass Rate:** 100%

## Test Suite Structure

| Category | Tests | Type | Description |
|----------|-------|------|-------------|
| Product Search | 20 | Unit | Search by name, category, price, rating, combined filters, zero results |
| Product Details | 13 | Unit | Valid IDs, invalid IDs, various product IDs, out-of-stock |
| Categories | 2 | Unit | List all categories, category count |
| Product Data Integrity | 5 | Unit | Required fields, valid prices, ratings range, unique IDs, valid categories |
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
