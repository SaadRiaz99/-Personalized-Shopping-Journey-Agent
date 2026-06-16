# Catalog Search Agent

AI-powered product catalog search with hybrid semantic + vector search. FastAPI server with Qdrant in-memory vector DB and OpenCode Zen LLM.

## Quick Start

```powershell
cd Catalog_search_agent
pip install -r requirements.txt
$env:ZEN_API_KEY = "sk-..."
uvicorn catalog_search_agent:app --reload --port 8000
```

First startup downloads `all-MiniLM-L6-v2` (~80MB) and indexes 906 products into Qdrant. Subsequent starts are instant.

## REST API

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Status, provider, product count |
| `GET /api/products/search?query=` | Hybrid search with pagination & filters |
| `GET /api/products/{id}` | Single product details |
| `GET /api/categories` | All product categories |
| `POST /api/feedback` | Rate a product (1-5) |
| `POST /api/agent/query` | Conversational AI search (needs ZEN_API_KEY) |

## Search Features

- **Semantic scoring** — token matching with stemming, fuzzy matching (`difflib`), stop word filtering
- **Vector search** — Qdrant in-memory + all-MiniLM-L6-v2 embeddings (384-dim, cosine)
- **Hybrid scoring** — `0.4 * semantic + 0.6 * vector` (products need semantic_score > 0 to pass gate)
- **Scaled relevance** — match threshold adapts to query word length to prevent false positives
- **Filters** — category, min/max price, min rating, sorting, pagination

## Frontend

Open `http://localhost:5173/catalog` in the frontend (React + Vite) for the full UI with product grid, filters, and AI Chat sidebar.

## Tests

```powershell
pytest test_agent.py -v -m "not needs_api"   # 57 unit tests, no API key needed
pytest test_agent.py -v -m needs_api          # 25 integration tests (needs ZEN_API_KEY)
pytest test_agent.py -v                       # all 82 tests
```

## Files

| File | Description |
|------|-------------|
| `catalog_search_agent.py` | FastAPI server with Qdrant, Zen agent, hybrid search |
| `products.json` | 906 products across 9 categories |
| `test_agent.py` | 57 unit + 25 integration tests |
| `conftest.py` | pytest fixtures (Zen API key, VCR, agent setup) |
| `requirements.txt` | Python dependencies |
| `report.md` | Detailed test report |
