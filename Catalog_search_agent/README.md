# Catalog Search Agent

An AI-powered product catalog search agent built with the OpenAI Agents SDK. Search 900+ products across 9 categories using natural language.

## Quick Start

1. **Install dependencies**
   ```
   pip install -r requirements.txt
   ```

2. **Set your API key** (any of these):
   ```
   $env:OPENROUTER_API_KEY = "your-key"   # https://openrouter.ai/keys
   ```
   Or use Groq (free, 14400 req/day):
   ```
   $env:GROQ_API_KEY = "your-key"         # https://console.groq.com/keys
   ```

3. **Generate the product catalog** (first time only):
   ```
   python generate_catalog.py
   ```

4. **Run the agent**:
   ```
   python catalog_search_agent.py
   ```

## Offline Mode (no API key needed)

```
python catalog_search_agent_mock.py
```

## Usage Examples

- "Show me electronics under $200"
- "What categories are available?"
- "Tell me about product 42"
- "Find me running shoes in stock"

## Guardrails

The agent only answers product-catalog-related questions. Irrelevant queries (math, coding, general chat) are automatically rejected.

## Files

| File | Description |
|------|-------------|
| `catalog_search_agent.py` | Main agent using OpenAI Agents SDK |
| `catalog_search_agent_mock.py` | Offline keyword-based version |
| `generate_catalog.py` | Generates 906 products into `products.json` |
| `products.json` | Product catalog (generated) |
| `requirements.txt` | Python dependencies |
