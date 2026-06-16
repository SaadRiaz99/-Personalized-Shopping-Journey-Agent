# Catalog Search Agent - Test Report

- **Date:** 2026-06-16
- **Provider:** OpenCode Zen (big-pickle)
- **Product Catalog:** 906 products across 9 categories
- **Framework:** FastAPI (standalone + integrated in backend) + Qdrant vector search + sentence-transformers
- **Total Tests:** 82
- **Unit Tests:** 57 (passed: 57, failed: 0)
- **Integration Tests:** 25 (skipped: 25 — require ZEN_API_KEY)
- **Pass Rate:** 100% of runnable tests

## Search Features

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Token-level scoring with stemming, singular/plural, fuzzy matching via `difflib`, stop word filtering, relevance ranking. |
| **Vector Search** | Qdrant in-memory + `all-MiniLM-L6-v2` embeddings (384-dim, cosine distance). |
| **Hybrid Search** | `0.4 * semantic_score + 0.6 * vector_similarity`. Requires `semantic_score > 0` to pass relevance gate. |
| **Scaled Threshold** | Match threshold scales by query word length: `<=5 chars` → 0.9, `6-8 chars` → 0.8, `>=9 chars` → 0.7. Prevents false positives (e.g. "phone"/"honey" = 0.8 SequenceMatcher coincidence). |
| **Price/Category/Rating Filters** | All search endpoints accept category, min/max price, and min rating filters. |
| **Feedback Tool** | `add_feedback(product_id, rating, comment)` stores per-user ratings in `FEEDBACK_STORE`. |
| **AI Agent** | Conversational search via Zen LLM (`POST /api/agent/query` with natural language). |

## Manual Search Tests

| Query | Results | Notes |
|-------|---------|-------|
| **ice** | Ice Cube Tray Silicone, Ice Bucket with Tongs, Ice Axe 70cm, Ice Cream Vanilla 1qt | All ice-related products — no false positives |
| **ball** | Exercise Ball 65cm, Soccer Ball Size 5, Massage Ball Lacrosse, Golf Balls 12-Pack | All ball-related products — no false positives |
| **phone** | Car Phone Mount, Phone Mount Dashboard, Phone Mount Vent 2-Arm | Only phone-mount products — no honey, swimsuits, or books |
| **headphones** | Wireless Bluetooth Headphones | Single relevant result — no phone mounts |

## Test Suite Structure

| Category | Tests | Type | Description |
|----------|-------|------|-------------|
| Product Search | 23 | Unit | Search by name, category, price, rating, min price, combined filters, zero results, semantic singular/plural, semantic fuzzy |
| Product Details | 13 | Unit | Valid IDs, invalid IDs, various product IDs, out-of-stock |
| Categories | 2 | Unit | List all categories, category count |
| Product Data Integrity | 5 | Unit | Required fields, valid prices, ratings range, unique IDs, valid categories |
| Feedback | 2 | Unit | Store & retrieve feedback, multiple entries |
| FastAPI Endpoints | 8 | Unit | Search, product, categories, feedback endpoint behavior |
| Catalog Queries | 10 | Integration | Natural language product searches via LLM |
| Guardrail Rejection | 6 | Integration | Non-catalog queries correctly rejected |
| Edge Cases | 7 | Integration | Special characters, stock checks, comparisons, gifts, multi-intent |
| Invalid ID Handling | 1 | Integration | Graceful handling of non-existent product IDs |
| Out-of-Stock Mention | 1 | Integration | Stock status mentioned in response |

## How to Run

### Standalone (Catalog_search_agent/)
```powershell
cd Catalog_search_agent
pip install -r requirements.txt

# Unit tests only (no API key needed)
pytest test_agent.py -v -m "not needs_api"

# Integration tests (requires ZEN_API_KEY)
$env:ZEN_API_KEY = "sk-..."
pytest test_agent.py -v -m needs_api

# All tests
$env:ZEN_API_KEY = "sk-..."
pytest test_agent.py -v

# Start server
$env:ZEN_API_KEY = "sk-..."
uvicorn catalog_search_agent:app --reload --port 8000
```

### Integrated in Backend
```powershell
cd backend
pip install -r requirements.txt
$env:ZEN_API_KEY = "sk-..."
uvicorn app.main:app --reload --port 8000
```

### Frontend
```powershell
cd frontend
npm install
npm run dev
```
