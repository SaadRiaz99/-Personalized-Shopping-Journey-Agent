# General Agent Report — Personalized Shopping Agent

## Overview

This report covers all agents integrated into the Personalized Shopping Agent system, including their architecture, capabilities, and how they collaborate to deliver a complete shopping experience.

## Agent Inventory

| Agent | Type | Location | Status |
|-------|------|----------|--------|
| **Agent Orchestrator** | Coordinator | `backend/app/services/agent_orchestrator.py` | Integrated |
| **Intent Parser** | LLM/Rule-based | `backend/app/services/intent_parser.py` | Integrated |
| **Catalog Search** | Search | `backend/app/services/catalog_search.py` | Integrated |
| **Recommendation** | Filter/Sort | `backend/app/services/recommendation.py` | Integrated |
| **Price Match** | Comparison | `backend/app/services/price_match.py` | Integrated |
| **Deal Agent** | Optimization | `backend/app/services/deal_agent.py` | Integrated |
| **Safety Guardrail** | Filter | `backend/app/services/safety_guardrail.py` | Integrated |
| **Privacy Guardrail** | Compliance | `backend/app/services/privacy_guardrail.py` | Integrated |
| **Price Guardrail** | Validation | `backend/app/services/price_guardrail.py` | Integrated |
| **Standalone Catalog Agent** | CLI | `Catalog_search_agent/catalog_search_agent.py` | Standalone |
| **Standalone Deal Agent** | CLI | `Deal_Agent/deal_agent.py` | Standalone |
| **Standalone Post-Purchase Agent** | CLI | `Post_Purchase_Agent/post_purchase_agent.py` | Standalone |
| **Discovery Agent** | Search | `discoveryAgent.js` | Standalone |

## Agent Architecture

### Collaboration Council Pattern

The system implements a multi-agent pipeline (SEDA-style):

```
User Query
    ↓
[1] Safety Guardrail     ← blocks restricted content
    ↓
[2] Privacy Guardrail    ← redacts PII, enforces consent
    ↓
[3] Intent Parser        ← extracts shopping intent
    ↓
[4] Product Search       ← catalog / recommendations
    ↓
[5] Price Match          ← competitor comparison
    ↓
[6] Deal Optimization    ← discount stacking
    ↓
[7] Output Guardrail     ← ensures safe response
    ↓
Response → WebSocket → Frontend
```

### Individual Agents

#### 1. Agent Orchestrator
- **File**: `backend/app/services/agent_orchestrator.py`
- Manages full agent lifecycle: create → run → complete
- Orchestrates multi-agent collaboration (Researcher → Auditor → Stylist)
- Broadcasts state changes via WebSocket
- Integrates all guardrails and services

#### 2. Intent Parser
- **File**: `backend/app/services/intent_parser.py`
- LLM-powered intent extraction (OpenAI-compatible)
- Rule-based fallback with regex keyword matching
- Extracts: category, budget, occasion, style, urgency

#### 3. Price Match Agent
- **File**: `backend/app/services/price_match.py`
- Checks prices across 5 retailers (Amazon, BestBuy, Walmart, Target, eBay)
- 15-day price history tracking
- Discount authorization with 25% margin cap
- Price drop alerts

#### 4. Deal Agent
- **File**: `backend/app/services/deal_agent.py`
- 13 seeded promotions across loyalty tiers
- Smart discount stacking engine
- Budget integrity enforcement (120% cap)
- Privacy-compliant mode

#### 5. Safety Guardrail
- **File**: `backend/app/services/safety_guardrail.py`
- Blocks 7 restricted categories (weapons, drugs, adult, alcohol, gambling, counterfeit, hacking)
- Sub-millisecond regex-based checking

#### 6. Privacy Guardrail
- **File**: `backend/app/services/privacy_guardrail.py`
- Three-tier enforcement: input redaction, access control, output scanning
- GDPR right-to-forget and CCPA opt-out support
- Rule-based primary with LLM fallback

#### 7. Price Guardrail
- **File**: `backend/app/services/price_guardrail.py`
- SKU format validation, price range bounds
- Fraud detection (suspicious price ratios)
- Rate limiting (50 req/hr per user)
- Abuse prevention ($2000/session cap)

#### 8. Standalone Catalog Agent
- **File**: `Catalog_search_agent/catalog_search_agent.py`
- OpenAI Agents SDK with function tools and guardrails
- 906 products across 9 categories
- Mock version for offline use

#### 9. Standalone Post-Purchase Agent
- **File**: `Post_Purchase_Agent/post_purchase_agent.py`
- Customer satisfaction tracking
- Return/refund processing
- Feedback collection and analysis

## Frontend Integration

The React frontend (`frontend/`) provides UIs for each agent:

| Page | Route | Agent |
|------|-------|-------|
| Dashboard | `/` | Collaboration Council |
| Agents | `/agents` | Agent CRUD + Run |
| Catalog | `/catalog` | Catalog Search |
| Deals | `/deals` | DealAgent |
| Price Match | `/price-match` | Price Match |
| Products | `/products` | Product Browser |
| Preferences | `/preferences` | User Preferences |

## Running the System

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Then open `http://localhost:5173` in a browser.

### Standalone Agents
```bash
# Catalog Search Agent (offline)
cd Catalog_search_agent
python catalog_search_agent_mock.py

# Deal Agent
cd Deal_Agent
python deal_agent_mock.py

# Post-Purchase Agent
cd Post_Purchase_Agent
python post_purchase_agent_mock.py
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Health check |
| POST | `/api/auth/login` | User login |
| POST | `/api/auth/register` | User registration |
| GET/POST/DELETE | `/api/agents` | Agent CRUD |
| POST | `/api/agents/{id}/run` | Execute agent |
| POST | `/api/agents/collaboration` | Run council pipeline |
| POST | `/api/intent` | Parse natural language query |
| GET | `/api/products` | List/search products |
| GET/PUT | `/api/preferences` | User preferences |
| POST | `/api/price-match/check` | Check competitor price |
| GET | `/api/price-match/discounts` | List discounts |
| POST | `/api/price-match/discounts/{id}/apply` | Apply discount |
| GET | `/api/price-match/alerts` | Price drop alerts |
| GET | `/api/deals/promotions` | List promotions |
| POST | `/api/deals/optimize` | Optimize cart discounts |
| POST | `/api/deals/apply/{stack_id}` | Apply discount stack |
| GET/PUT | `/api/privacy/profile` | Privacy profile management |
| DELETE | `/api/privacy/forget` | GDPR right to erasure |
| POST | `/api/privacy/opt-out` | CCPA opt-out |
| GET | `/api/privacy/export` | Data export |
| GET | `/api/catalog/search` | Catalog search |
| GET | `/api/catalog/categories` | List categories |
| WS | `/ws/agents/{agent_id}` | WebSocket agent events |

---

*Report generated for the general-agent branch overviewing the full agent ecosystem.*
