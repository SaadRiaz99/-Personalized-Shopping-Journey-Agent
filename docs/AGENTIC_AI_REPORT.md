# Agentic AI: Technical Architecture Report

## Overview

This report analyzes the **Personalized Shopping Agent** system as a case study in multi-agent AI architecture. The system implements a production-grade agentic AI pipeline with guardrails, orchestration, WebSocket event streaming, and a React frontend — demonstrating the core patterns of modern Agentic AI.

---

## 1. Core Architecture — Multi-Agent Orchestration

### Pattern: Centralized Agent Orchestrator (SEDA-style)

The `AgentOrchestrator` (`backend/app/services/agent_orchestrator.py`) acts as a **Staged Event-Driven Architecture** (SEDA) controller:

```
User Query
    ↓
[1] Safety Guardrail   ← blocks weapons/drugs/adult content
    ↓
[2] Privacy Guardrail  ← redacts PII, enforces GDPR/CCPA
    ↓
[3] Intent Parser      ← LLM extracts category/budget/occasion/urgency
    ↓
[4] Product Search     ← catalog lookup or recommendation engine
    ↓
[5] Price Match Audit  ← checks 5 retailers, applies discount rules
    ↓
[6] Output Guardrail   ← ensures no leaked PII in recommendations
    ↓
Response to User
```

Each stage is a discrete agent with:
- **Single Responsibility**: One concern per agent (safety, privacy, intent, pricing)
- **Sequential Pipeline**: Output of one feeds the next
- **Pluggable**: Agents can be added/removed without affecting the pipeline
- **Observable**: Each step emits WebSocket events for real-time UI updates

### Key Design Decisions

| Decision | Implementation | Rationale |
|----------|---------------|-----------|
| Agent lifecycle | CRUD via orchestrator + status enum | Enables monitoring, debugging, retry |
| Communication | In-process method calls (async) | Low latency for same-process agents |
| State persistence | In-memory dicts | Appropriate for session-scoped data |
| Real-time events | WebSocket broadcast per agent state change | Frontend can animate agent activity |

---

## 2. Agent Types & Patterns

### 2.1 Rule-Based Agents
- **PriceMatchAgent**: Deterministic competitor price comparison with discount cap (25% margin)
- **SafetyGuardrail**: Regex-based keyword blocking across 7 restricted categories
- **DealAgent**: Discount stacking engine with loyalty tier gating

### 2.2 LLM-Powered Agents
- **IntentParser**: Calls OpenAI-compatible API to extract structured shopping intent from natural language
- **PrivacyGuardrail (LLM fallback)**: Uses LLM for nuanced PII detection when rule-based systems are insufficient

### 2.3 Hybrid Agents
- **PrivacyGuardrail**: Rule-based primary + LLM fallback for edge cases
- **Collaborative Council**: 3 agents (Researcher → Auditor → Stylist) form a processing pipeline

---

## 3. Guardrail System — Defense in Depth

The system implements **4 layers of guardrails**:

### Layer 1: Safety Guardrail (`safety_guardrail.py`)
- **Pattern**: Static keyword matching with regex word boundaries
- **Categories**: weapons, drugs, adult, alcohol, gambling, counterfeit, hacking
- **Region-aware**: GDPR/CCPA adds prescription drug restrictions
- **Performance**: O(n*m) where n=query length, m=total keywords — sub-millisecond

### Layer 2: Privacy Guardrail (`privacy_guardrail.py`)
- **Pattern**: Three-tier privacy enforcement
  - **Input**: Redacts PII (email, phone, SSN, address, credit card)
  - **Access**: Controls agent data access based on user privacy profile
  - **Output**: Scans recommendations for leaked personal data
- **Fallback**: Rule-based primary, LLM-based for nuanced cases
- **Compliance**: Supports GDPR right-to-forget, CCPA opt-out, configurable data retention

### Layer 3: Price Guardrail (NEW — `price_guardrail.py`)
- **Pattern**: Multi-validator pipeline
  - **Input Validation**: SKU format (regex), price range (bounds checking)
  - **Fraud Detection**: Suspicious competitor price ratios, price gouging detection
  - **Rate Limiting**: Per-user sliding window (50 req/hr)
  - **Abuse Prevention**: Total discount cap ($2000/session)
- **Stateless**: User sessions tracked in memory with auto-expiry

### Layer 4: Price Match Guardrail (enhanced — `price_match.py`)
- **Business Rules**: 25% margin cap on discounts
- **Pattern**: Authorize → Apply → Record flow with state machine
- **Discount States**: pending → approved → applied (or declined)

### Guardrail Evaluation

```
Query arrives
  ├─ Safety:        ~0.001ms (regex O(n))
  ├─ Privacy Input: ~0.5ms rules / ~500ms LLM
  ├─ Price Input:   ~0.01ms (regex + bounds)
  ├─ Fraud Detect:  ~0.001ms (ratio check)
  ├─ Rate Limit:    ~0.001ms (dict lookup)
  └─ Abuse Check:   ~0.001ms (accumulator)
```

---

## 4. Multi-Agent Collaboration — The Council Pattern

The **Collaboration Council** (`run_collaborative_task`) demonstrates a sophisticated multi-agent workflow:

### Agent Roles

| Role | Function | Tools |
|------|----------|-------|
| **Researcher** | Intent parsing + catalog search | LLM + catalog_search API |
| **Auditor** | Price verification across 5 retailers | PriceMatchAgent tools |
| **Stylist** | Sort, personalize, present | Rating + discount sorting |

### Collaboration Protocol

```
Researcher ──(intent + products)──→ Auditor ──(audited products)──→ Stylist ──(final)──→ User
```

Each agent:
1. Is instantiated as a tracked `Agent` object with unique ID
2. Updates its status (idle → running → completed)
3. Broadcasts state changes via WebSocket
4. Receives only the data it needs (principle of least privilege)

---

## 5. Technology Stack & Tradeoffs

| Component | Technology | Why |
|-----------|-----------|-----|
| Backend | FastAPI (Python) | Async-native, Pydantic validation, automatic OpenAPI docs |
| AI SDK | OpenAI Agents SDK | Function-tool pattern, guardrail decorators, structured outputs |
| Frontend | React 19 + Vite 8 + Framer Motion | Component-based, animated transitions, type-safe with TypeScript 6 |
| Real-time | WebSockets (FastAPI) | Bidirectional agent state streaming |
| LLM | OpenAI / Groq / Gemini (swappable) | OpenAI-compatible API allows provider flexibility |
| Models | Pydantic v2 | Strict type enforcement, serialization, validation |

### Tradeoffs
- **In-memory state**: Fast but not horizontally scalable (session affinity needed)
- **Sequential pipeline**: Simple but adds latency (each step awaits previous)
- **Regex guardrails**: Fast but limited — LLM fallback handles nuance but adds cost
- **Mock competitor data**: Demonstrates pattern without real retailer API integration

---

## 6. System Properties

### Observability
- Every agent state change → WebSocket event
- Guardrail decisions logged with explanation
- Collaboration steps broadcast in real-time

### Security
- PII redacted before reaching agents
- Data access gated by privacy level (strict/balanced/open)
- Rate limiting prevents brute-force price checking
- Fraud detection catches anomalous pricing

### Extensibility
- New agents: Add a class + register with orchestrator
- New guardrails: Add to input/output pipeline
- New data sources: Implement `function_tool` decorators
- New LLM providers: Change endpoint + model env vars

---

## 7. Agentic AI — Key Takeaways

### What Makes This "Agentic"?

1. **Autonomous Goal Pursuit**: Agents receive high-level tasks ("find best deals under $50") and decompose them
2. **Tool Use**: Agents call function_tools (search, filter, price-check) to interact with external systems
3. **Stateful Execution**: Agents maintain internal state across their lifecycle
4. **Guardrails as Constraints**: Safety, privacy, and business rules constrain agent behavior
5. **Orchestration**: Multiple agents collaborate on a shared goal with data handoffs
6. **Observability**: Full audit trail of agent decisions

### Production Considerations for Scaling

- Replace in-memory state with Redis/PostgreSQL
- Add agent timeouts and retry logic
- Implement circuit breakers for LLM API failures
- Use message queues (RabbitMQ/Kafka) for inter-agent communication
- Add A/B testing for guardrail configurations
- Implement human-in-the-loop for high-value discount approvals

---

*Report generated from codebase analysis of the Personalized Shopping Agent system.*
*Architecture demonstrates 4 guardrail layers, 3 agent collaboration patterns, and real-time orchestration.*
