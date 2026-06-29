# Personalized Shopping Agent — Project Report

## Overview

A multi-agent e-commerce platform that combines AI-powered product discovery, intent parsing, price matching, discount optimization, and a React frontend for an interactive shopping experience.

## Architecture

```
Personalized Shopping Agent/
├── backend/                     # FastAPI Python backend (port 8000)
│   ├── app/
│   │   ├── main.py              # App entry point + router registration
│   │   ├── models.py            # Pydantic data models
│   │   ├── routes/
│   │   │   ├── agents.py        # Agent CRUD + execution API
│   │   │   ├── deals.py         # [NEW] DealAgent promotions API
│   │   │   ├── intent.py        # Natural language intent parser API
│   │   │   ├── preferences.py   # User preference CRUD API
│   │   │   ├── price_match.py   # Price match / competitor check API
│   │   │   ├── products.py      # Product catalog listing API
│   │   │   └── ws.py            # WebSocket event broadcasting
│   │   └── services/
│   │       ├── agent_orchestrator.py  # Agent lifecycle management
│   │       ├── deal_agent.py          # [NEW] Discount stacking engine
│   │       ├── intent_parser.py       # LLM + rule-based intent parsing
│   │       ├── price_match.py         # Competitor price matching
│   │       └── recommendation.py      # Product filtering + search
│   └── requirements.txt
├── Catalog_search_agent/        # Standalone CLI agent (OpenAI SDK)
│   ├── catalog_search_agent.py       # LLM-powered catalog search
│   ├── catalog_search_agent_mock.py  # Offline keyword-based search
│   ├── generate_catalog.py           # Generates products.json (906 products)
│   └── requirements.txt
├── frontend/                    # React + TypeScript + Vite (port 5173)
│   ├── src/
│   │   ├── pages/               # Dashboard, Agents, Deals, Products, Preferences
│   │   ├── components/          # Layout, AgentCard, ProductCard
│   │   ├── services/api.ts      # Axios API client
│   │   └── types/index.ts       # TypeScript interfaces
│   └── package.json
├── discoveryAgent.js            # Standalone Node.js retail search module
└── PROJECT_REPORT.md            # This file
```

## Agents

| Agent | Location | Description |
|-------|----------|-------------|
| **AgentOrchestrator** | `backend/services/agent_orchestrator.py` | Manages agent CRUD, task execution, intent parsing, product search, WebSocket events |
| **PriceMatchAgent** | `backend/services/price_match.py` | Checks competitor prices (Amazon, BestBuy, Walmart, Target, eBay) across 8 SKUs; approves/caps discount at 25% margin |
| **DealAgent** | `backend/services/deal_agent.py` | [NEW] Discount stacking engine — 13 seeded promotions (loyalty tiers, BOGO, category markdowns, flash sales); optimizes best stack; respects budget cap (120%) and privacy opt-out |
| **IntentParser** | `backend/services/intent_parser.py` | LLM-powered (or rule-based fallback) extraction of category, budget, occasion, style, urgency from natural language |
| **CatalogSearchAgent** | `Catalog_search_agent/` | CLI agent using OpenAI Agents SDK with guardrail; mock version for offline use; 906 products across 9 categories |
| **DiscoveryAgent** | `discoveryAgent.js` | Node.js module for simulated multi-retailer product search |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| GET/POST/DELETE | `/api/agents` | Agent CRUD |
| POST | `/api/agents/{id}/run` | Execute an agent |
| POST | `/api/intent` | Parse natural language query |
| GET | `/api/products` | List/search products |
| GET/PUT | `/api/preferences` | User preferences |
| GET/POST | `/api/price-match/check` | Check competitor price |
| POST | `/api/price-match/agents/{id}/check` | Run price match via agent |
| GET | `/api/price-match/discounts` | List discounts |
| POST | `/api/price-match/discounts/{id}/apply` | Apply a discount |
| GET | `/api/deals/promotions` | [NEW] List active promotions |
| POST | `/api/deals/optimize` | [NEW] Optimize cart discounts |
| POST | `/api/deals/apply/{stack_id}` | [NEW] Auto-apply discount stack |
| WS | `/ws/agents` | WebSocket agent events |

## DealAgent — Key Features

- **13 seeded promotions**: Bronze 5% / Silver 10% / Gold 15% / Platinum 20% loyalty tiers, Flash Friday (15%), New User ($10 off), BOGO (cheapest free), Big Spender ($25 off $200+), category markdowns (Electronics 10%, Fashion 15%, Sports 12%, Home 8%), Privacy-Friendly (5%)
- **Smart stacking**: BOGO applied first (non-stackable), then best percentage, then category markdowns, then fixed discounts
- **Budget integrity**: Final total capped at 120% of stated budget
- **Privacy compliance**: Opted-out users only receive non-personalized public promotions

## Running the Project

```bash
# Backend
cd backend
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install
npm run dev

# Catalog Search Agent (CLI)
cd Catalog_search_agent
python generate_catalog.py            # Generate products.json
python catalog_search_agent_mock.py   # Offline mode (no API key)

# Price Match Test
cd backend
python -c "from app.services.price_match import price_match_agent; d = price_match_agent.check_price('SKU-LJ001', 349.99, 'p5', 'agent_001'); print(d.model_dump())"
```

## Test Results

- **Intent Parser**: 4/4 queries parsed correctly (birthday gift, wedding outfit, laptop search, casual browsing)
- **Frontend**: TypeScript type-checks clean, Vite production build (290KB JS)
- **Catalog Agent**: 906 products generated, search/categories/details all functional
- **DealAgent**: 5 scenarios verified — Bronze/Electronics, Gold/Mixed, Platinum/Budget, Silver/OptedOut, all 13 promotions listed
- **PriceMatchAgent**: 8 SKUs with competitor data, discount capped at 25% margin
