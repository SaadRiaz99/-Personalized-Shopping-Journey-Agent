# Orchestrator Page Work Report — Catalog Agent Settings

## Overview

This report documents the Agent Orchestrator page functionality, covering catalog agent settings, configuration, and operational workflow.

---

## 1. Orchestrator Page — Agent Settings Panel

The Orchestrator page provides a centralized dashboard for managing all agents:

### Agent CRUD Operations

| Operation | API Endpoint | Description |
|-----------|-------------|-------------|
| **Create Agent** | `POST /api/agents` | Register a new agent with name, type, config |
| **List Agents** | `GET /api/agents` | View all registered agents with status |
| **Get Agent** | `GET /api/agents/{id}` | View single agent details |
| **Update Agent** | `PUT /api/agents/{id}` | Modify agent configuration |
| **Delete Agent** | `DELETE /api/agents/{id}` | Remove an agent |
| **Run Agent** | `POST /api/agents/{id}/run` | Execute agent with query |

### Agent Configuration Settings

```
Agent Config Schema:
{
  "name": "catalog_search",
  "type": "search",
  "enabled": true,
  "config": {
    "max_results": 20,
    "sort_by": "relevance",
    "price_min": 0,
    "price_max": 1000,
    "categories": ["electronics", "clothing", "home"],
    "rating_min": 3.5
  }
}
```

## 2. Catalog Agent Settings

| Setting | Type | Default | Description |
|---------|------|---------|-------------|
| `max_results` | integer | 20 | Maximum products to return |
| `sort_by` | string | "relevance" | Sort method (relevance, price_asc, price_desc, rating) |
| `price_min` | float | 0 | Minimum price filter |
| `price_max` | float | 1000 | Maximum price filter |
| `categories` | array | [] | Category filter list |
| `rating_min` | float | 0 | Minimum rating filter |
| `keyword` | string | "" | Search keyword |
| `semantic_search` | boolean | false | Enable LLM semantic search |

## 3. Orchestrator Pipeline Workflow

```
┌───────────────────────────────────────────────────────────┐
│               ORCHESTRATOR PAGE WORKFLOW                   │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  1. USER INPUT                                            │
│     → User types natural language query                   │
│     → Example: "find laptops under $1000"                 │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  2. GUARDRAIL PIPELINE                                    │
│     → Safety Guardrail: blocks unsafe content             │
│     → Privacy Guardrail: redacts PII                      │
│     → Price Guardrail: validates price bounds             │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  3. INTENT PARSER                                         │
│     → Extracts: category, budget, occasion, style, urgency│
│     → LLM-powered with rule-based fallback                │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  4. CATALOG SEARCH                                        │
│     → Searches 906 products across 9 categories           │
│     → Applies keyword/category/price/rating filters       │
│     → Returns matched products with scores                │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  5. PRICE MATCH & DEAL OPTIMIZATION                       │
│     → Checks competitor prices across 5 retailers         │
│     → Applies discount stacking (13 promotions)           │
│     → Enforces 25% margin cap and budget limits           │
└───────────────────────────────────────────────────────────┘
                              │
                              ▼
┌───────────────────────────────────────────────────────────┐
│  6. OUTPUT GENERATION                                     │
│     → Sorts by combined relevance + discount score        │
│     → Scans output for compliance                         │
│     → Returns final response to frontend                  │
└───────────────────────────────────────────────────────────┘
```

## 4. Frontend Orchestrator Page

The `/agents` route in the React frontend provides:

### Page Sections

| Section | Description |
|---------|------------|
| **Agent List** | Table of all agents with name, type, status, actions |
| **Agent Detail** | Expanded view of single agent configuration |
| **Run Agent** | Input form to execute an agent with a query |
| **Results Panel** | Display agent execution results in real-time |
| **WebSocket Feed** | Live agent state changes via WebSocket |

### UI Components

```
AgentCard ──────────────────────────────────────────
│  Name: Catalog Search Agent                       │
│  Type: search                                     │
│  Status: ● Online                                 │
│  Settings: [Configure] [Run] [Delete]             │
│  Last Run: 2s ago — 20 results found              │
└───────────────────────────────────────────────────┘
```

## 5. Catalog Agent Configuration Page

The catalog agent settings page allows:

- **Category Selection**: Toggle 9 product categories on/off
- **Price Range Slider**: Min/max price filter
- **Rating Filter**: Minimum star rating dropdown
- **Sort Order**: Relevance / Price Low-High / Price High-Low / Rating
- **Results Count**: Items per page (10/20/50)
- **Semantic Search Toggle**: Enable LLM-powered search

## 6. Test Results — Orchestrator Page

| Test Case | Description | Status |
|-----------|------------|--------|
| Agent Creation | Create agent via orchestrator API | ✅ PASS |
| Agent Listing | List all agents | ✅ PASS |
| Agent Detail | Get agent by ID | ✅ PASS |
| Agent Deletion | Delete existing agent | ✅ PASS |
| Agent Execution | Run agent with safe query | ✅ PASS |
| Agent Safety | Block unsafe query | ✅ PASS |
| Collaboration Council | 3-agent pipeline execution | ✅ PASS |
| WebSocket Events | Real-time state broadcast | ✅ PASS |

---

## 7. Summary

The Orchestrator Page provides a complete agent management interface with:
- Full CRUD operations for all agents
- Configurable catalog search settings
- Real-time WebSocket updates
- Integration with all 12 agent services
- 100% test pass rate on all orchestrator operations

---

*Report by: Saad Bin Riaz*
*Date: 2026-06-03*
