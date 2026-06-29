# Deployment Guide

## Overview

This guide covers deployment options for the Personalized Shopping Agent: a FastAPI backend (Python), React frontend (Vite/TypeScript), and SQLite database.

---

## 1. Docker Compose (Local / Single-Server)

**Prerequisites:** Docker + Docker Compose

```bash
docker compose up --build -d
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:80`
- Data persisted via SQLite file (`backend/app/shopping.db`)

**Customization** — add a `.env` file at the project root:

```env
SECRET_KEY=<your-secret>
LLM_API_KEY=<your-openai-key>
GUARDRAIL_ENABLED=true
```

---

## 2. Cloud Deployment

### 2a. AWS (ECS Fargate + CloudFront)

| Component | Service | Notes |
|---|---|---|
| Backend | ECS Fargate (2 vCPU, 4 GB) | 2+ tasks, ALB in front |
| Frontend | S3 + CloudFront | Static files; invalidate on deploy |
| Database | RDS (PostgreSQL) | Migrate from SQLite via Alembic |
| CI/CD | CodePipeline → ECR → ECS | Auto-deploy on `main` push |

**Migration Steps:**
1. Replace SQLite with PostgreSQL in `app/database.py`
2. Add an `alembic.ini` for schema migrations
3. Store static files in S3, serve via CloudFront
4. Set `GUARDRAIL_ENABLED=true` and `LLM_API_KEY` in ECS env vars

### 2b. GCP (Cloud Run + Cloud Storage)

| Component | Service | Notes |
|---|---|---|
| Backend | Cloud Run (min 1, max 10 instances) | Pull from Artifact Registry |
| Frontend | Cloud Storage + Load Balancer | Static bucket, CDN enabled |
| Database | Cloud SQL (PostgreSQL) | Private IP via VPC connector |

**Migration Steps:**
1. Create `cloudbuild.yaml` for Cloud Build CI/CD
2. Use Cloud SQL Auth Proxy or private IP for DB access
3. Mount `/.opencode/` to a Filestore or GCS Fuse bucket for state

### 2c. Azure (App Service + Static Web Apps)

| Component | Service | Notes |
|---|---|---|
| Backend | App Service (B2 plan) | Linux Python stack |
| Frontend | Static Web Apps | GitHub Action deploys `frontend/dist` |
| Database | Azure Database for PostgreSQL | Flexible Server |

---

## 3. CI/CD Pipeline (GitHub Actions)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.14" }
      - run: pip install -r backend/requirements.txt pytest pytest-asyncio
      - run: python -m pytest backend/tests/ -v

  deploy-backend:
    needs: test
    steps:
      # Build & push Docker image, then update ECS/Cloud Run service

  deploy-frontend:
    needs: test
    steps:
      - uses: actions/setup-node@v4
        with: { node-version: "22" }
      - run: npm ci && npm run build
        working-directory: frontend
      # Upload frontend/dist to S3 / Cloud Storage / Azure Static Web Apps
```

---

## 4. Database Considerations

- **Current:** SQLite (`backend/app/shopping.db`) — suitable for dev/single-user.
- **Production:** Replace with PostgreSQL.
  - Add `databases[sqlite]` or `asyncpg` to `requirements.txt`
  - Update `app/database.py` connection string from env var `DATABASE_URL`
  - Add connection pooling (`pool_size=5, max_overflow=10`)

---

## 5. Environment Variables

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | JWT signing secret |
| `LLM_API_KEY` | `""` | OpenAI-compatible API key |
| `LLM_ENDPOINT` | `https://api.openai.com/v1/chat/completions` | LLM endpoint |
| `LLM_MODEL` | `gpt-4o-mini` | Model name |
| `GUARDRAIL_ENABLED` | `true` | Toggle guardrails |
| `DATABASE_URL` | `sqlite:///./shopping.db` | DB connection string |
| `CORS_ORIGINS` | `*` | Allowed origins |

---

## 6. Monitoring & Logging

- Backend logs: stdout (captured by Docker/Cloud provider)
- Application metrics: instrument with Prometheus client (`prometheus-fastapi-instrumentator`)
- Sentry: add `sentry-sdk` for error tracking
- Uptime: CloudWatch / Cloud Monitoring / Azure Monitor health check on `/health`

---

## 7. Scaling

- Backend: horizontally scalable (stateless except DB). Use DB-backed session store.
- Frontend: fully static — served via CDN, no scaling concerns.
- Guardrails: CPU-bound; separate into a background worker if needed.
- Rate limiting: current in-memory (`PriceGuardrail._sessions`); replace with Redis for multi-instance.
