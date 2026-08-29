# Personalized Shopping Agent

A multi-agent AI shopping platform that combines specialized agents for product search, deal optimization, price matching, gift finding, cross-selling, and more — all coordinated through an intelligent orchestrator with privacy and safety guardrails.

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React/TS)                     │
│  Dashboard · Agents · Catalog · Deals · Gift Finder       │
│  Cross-Sell · Price Match · Products · Recommendations    │
└─────────────────────────┬────────────────────────────────┘
                          │ HTTP / WebSocket
┌─────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                        │
│                                                           │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐   │
│  │  Auth &      │  │  Agent       │  │  Guardrails     │   │
│  │  Users       │  │  Orchestrator │  │  (Privacy,      │   │
│  └─────────────┘  └──────────────┘  │   Safety, Price) │   │
│                     │               └────────────────┘   │
│                     ▼                                     │
│  ┌──────────────────────────────────────────────────┐     │
│  │           Specialist Agents                       │     │
│  │  Catalog · Deal · Gift Finder · Cross-Sell        │     │
│  │  Price Match · Recommendation · Intent Parser     │     │
│  └──────────────────────────────────────────────────┘     │
│                     │                                      │
│  ┌──────────────────▼──────────────────────────────────┐  │
│  │           Shared Module (906-Product Catalog)        │  │
│  └─────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Features

- **Agent Orchestrator** — Coordinates multi-agent collaboration with event-driven architecture
- **Catalog Search Agent** — Full-text and category-based product search across 906 products
- **Deal Agent** — Discount stacking optimization with loyalty tiers and BOGO support
- **Gift Finder Agent** — Occasion, age, relationship, and interest-based gift matching
- **Cross-Sell Agent** — Complementary, upsell, and accessory product recommendations
- **Price Match Agent** — Competitor price comparison with history tracking and alerts
- **Intent Parser** — LLM-powered shopping intent extraction with rule-based fallback
- **Privacy Guardrail** — GDPR/CCPA compliance with consent management and data anonymization
- **Safety Guardrail** — Blocks restricted categories (weapons, drugs, adult content)
- **Price Guardrail** — Rate limiting, SKU validation, and fraud detection
- **WebSocket Support** — Real-time agent execution updates
- **Auth** — JWT with 2FA, refresh tokens, session management, role-based access

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Framer Motion |
| Backend | Python 3.14, FastAPI, uvicorn |
| Database | SQLite (via sqlite3) |
| Communication | REST, WebSocket |
| AI/LLM | OpenAI-compatible API (configurable) |
| Deployment | Docker, Docker Compose, nginx |

## Quick Start

```bash
# Clone and enter
git clone https://github.com/SaadRiaz99/-Personalized-Shopping-Journey-Agent.git
cd Personalized-Shopping-Journey-Agent

# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate    # Windows
pip install -r requirements.txt
cp .env.example .env      # Edit with your LLM_API_KEY
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 and register a user. Demo accounts are disabled by default. For local-only demos, explicitly set `SEED_DEMO_USERS=true`; never enable this in production.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `LLM_API_KEY` | API key for LLM provider (OpenAI-compatible) |
| `LLM_ENDPOINT` | LLM API endpoint URL |
| `LLM_MODEL` | Model name (default: gpt-4o-mini) |
| `ENVIRONMENT` | Use `production` in deployed environments |
| `JWT_SECRET_KEY` | Random JWT signing secret; required in production |
| `SEED_DEMO_USERS` | Opt-in local demo accounts; keep `false` in production |
| `AGENT_DB_PATH` | SQLite database path for local development |

## API Routes

| Prefix | Description |
|--------|-------------|
| `/api/auth/*` | Login, register, 2FA, sessions |
| `/api/agents/*` | Agent CRUD and execution |
| `/api/catalog/*` | Product catalog search |
| `/api/deals/*` | Deal optimization and promotions |
| `/api/gift-finder/*` | Occasion-based gift recommendations |
| `/api/cross-sell/*` | Complementary and upsell products |
| `/api/price-match/*` | Price comparison and discounts |
| `/api/products/*` | Product listing |
| `/api/recommendations/*` | Personalized recommendations |
| `/api/preferences/*` | User preference management |
| `/api/privacy/*` | Privacy settings and consent |
| `/api/wishlist/*` | Wishlist CRUD and price alerts |
| `/ws/agents/*` | Real-time agent updates via WebSocket |

## Project Structure

```
├── backend/            # FastAPI application
│   ├── app/
│   │   ├── routes/     # API route handlers
│   │   ├── services/   # Business logic & agents
│   │   ├── models.py   # Pydantic schemas
│   │   ├── database.py # SQLite operations
│   │   ├── auth.py     # JWT authentication
│   │   └── main.py     # App entry point
│   └── tests/          # 563-test agent suite
├── frontend/           # React + TypeScript application
│   └── src/
│       ├── components/ # Reusable UI components
│       ├── pages/      # Route pages
│       ├── services/   # API client
│       └── contexts/   # React contexts
├── shared/             # Shared module (product catalog)
├── docs/               # Documentation & test reports
│   ├── agent_reports/  # Per-agent test case results
│   └── *.md            # Project reports and deployment guide
└── docker-compose.yml  # Deployment config
```

## Oracle Cloud Deployment

For Oracle Cloud Always Free deployment instructions, see [HANDOFF_README.md](file:///E:/Work/Smit/Agent/Personalized-Shopping-Agent/HANDOFF_README.md) and [DEPLOYMENT_GUIDE.md](file:///E:/Work/Smit/Agent/Personalized-Shopping-Agent/DEPLOYMENT_GUIDE.md).

## Code Review and Security Status

The August 2026 repository review covered backend routes and services, authentication, database access, frontend API integration, tests, Docker images, and deployment configuration.

Implemented remediations:

- Removed committed Oracle SSH key files from the current repository version and added private-key patterns to `.gitignore`.
- Replaced SHA-256 password storage with Argon2id while retaining legacy-hash verification for login-time migration.
- Made `JWT_SECRET_KEY` mandatory in production and configured Render to generate it securely.
- Disabled predictable demo users by default.
- Replaced deterministic demo 2FA codes with standard TOTP authenticator codes.
- Added authenticated ownership checks for sessions, budgets, privacy profiles, and wishlist records.
- Removed the endpoint that accepted JWTs in URL query parameters.
- Added the missing backend test dependencies and tightened frontend quality configuration.

Important operator action: the previously committed SSH private key remains present in older Git history. Revoke/replace that key in Oracle Cloud, then purge it from repository history with `git filter-repo` before treating the repository as secure.

Production follow-ups:

- Use PostgreSQL or another persistent managed database instead of container-local SQLite.
- Move refresh tokens to Secure, HttpOnly, SameSite cookies.
- Add API rate limiting, structured security logging, and continuous dependency scanning.
- Require a successful TOTP confirmation code before finalizing 2FA enrollment.
