# Deal Agent — Personalized Shopping Journey System

**Built by:** Hashir (Deal Agent Specialist)  
**Team:** SMIT Personalized Shopping Journey Multi-Agent System  
**Role:** Specialist Agent — Checks active promotions, loyalty points, bundle opportunities, and automatically applies the best discount combination.

---

## What This Agent Does

The Deal Agent is a specialist in the Personalized Shopping Journey pipeline. It:

1. Checks all active promotions for the customer's cart
2. Retrieves the customer's loyalty points balance
3. Detects bundle deals for products in the cart
4. Calculates the **optimal discount combination** for maximum savings
5. Applies discounts and returns a clear savings summary

---

## Architecture

```
RecommendationAgent
       |
       | calls as tool
       v
   DealAgent  ──tools──> get_active_promotions
                    ──>  get_loyalty_points
                    ──>  get_bundle_offers
                    ──>  apply_discount
```

---

## Setup

### 1. Clone the repo
```bash
git clone https://github.com/SaadRiaz99/Shopping-Journey-Agent.git
cd Shopping-Journey-Agent
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
```bash
cp .env.example .env
```

Edit `.env` and add your API credentials from OpenCode / Zen:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=https://api.your-provider.com/v1
MODEL_NAME=gpt-4o-mini
```

### 4. Run the demo
```bash
python main.py
```

---

## Tools

| Tool | Description |
|------|-------------|
| `get_active_promotions` | Fetches promotions by category + cart total |
| `get_loyalty_points` | Gets user's points balance and tier info |
| `get_bundle_offers` | Checks if products qualify for bundle deals |
| `apply_discount` | Applies chosen discounts and returns final price |

---

## Integration with Team

When the **Recommendation Agent** (Moiz) calls this agent as a tool:
```python
deal_agent.as_tool("find_best_deal", "Find optimal discount for item set")
```

The Deal Agent returns structured JSON with the best discount applied.

---

## Team

| Agent | Specialist |
|-------|-----------|
| Orchestrator / Intent Agent | After All Agent |
| Catalog Search Agent | Hamza Qadri |
| Recommendation Agent | Moiz |
| **Deal Agent** | **Hashir** |
| Abandonment Recovery Agent | Mohib |
| Privacy Guardrail Agent | Saad Bin Riaz |
