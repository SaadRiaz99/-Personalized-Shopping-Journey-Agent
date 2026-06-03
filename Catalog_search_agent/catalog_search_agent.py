import asyncio
import difflib
import json
import os
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    input_guardrail,
    set_tracing_disabled,
)
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

set_tracing_disabled(disabled=True)


# ---------------------------------------------------------------------------
# Provider setup
# ---------------------------------------------------------------------------
# Set one of these env vars:
#   GROQ_API_KEY  -> https://console.groq.com/keys  (free: 14400 req/day)
#   GEMINI_API_KEY -> https://aistudio.google.com/apikey (free tier)
#   OPENAI_API_KEY -> https://platform.openai.com/api-keys

def build_model():
    if key := os.environ.get("OPENROUTER_API_KEY", ""):
        clients["openrouter"] = provider_entry(
            client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
            model=os.environ.get("LLM_MODEL", "meta-llama/llama-3.3-70b-instruct:free"),
        ), f"OpenRouter ({os.environ.get('LLM_MODEL', 'meta-llama/llama-3.3-70b-instruct:free')})"

    if key := os.environ.get("GROQ_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1"),
        ), "Groq (llama-3.3-70b) [free]"

    if key := os.environ.get("GEMINI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "gemini-2.0-flash"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        ), "Google Gemini (gemini-2.0-flash) [free tier]"

    if key := os.environ.get("OPENAI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            openai_client=AsyncOpenAI(api_key=key),
        ), "OpenAI"

    return None, None


# ---------------------------------------------------------------------------
# Product catalog
# ---------------------------------------------------------------------------

PRODUCTS: list[dict] = json.load(open("products.json"))
FEEDBACK_STORE: dict[str, list[dict]] = {}


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclass
class UserContext:
    user_id: str
    name: str
    preferred_categories: Optional[list[str]] = None
    max_budget: Optional[float] = None


# ---------------------------------------------------------------------------
# Structured output types
# ---------------------------------------------------------------------------

class ProductResult(BaseModel):
    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    category: str = Field(description="Product category")
    price: float = Field(description="Current price in USD")
    rating: float = Field(description="Average customer rating (1-5)")
    in_stock: bool = Field(description="Whether the product is currently in stock")
    description: str = Field(description="Short product description")


class SearchResults(BaseModel):
    query: str = Field(description="The original search query")
    total_found: int = Field(description="Number of matching products")
    products: list[ProductResult] = Field(description="List of matching products")
    note: Optional[str] = Field(default=None, description="Any helpful note for the user")


class CategoriesResult(BaseModel):
    categories: list[str] = Field(description="Available product categories")
    total: int = Field(description="Number of categories")


class CatalogQueryCheck(BaseModel):
    is_catalog_query: bool = Field(description="Whether the user's query is about the product catalog")
    reasoning: str = Field(description="Reasoning for the classification")


# ---------------------------------------------------------------------------
# Semantic search helpers
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    text = text.lower()
    table = str.maketrans("-_/.,:;!?()[]{}\"'", " " * 17)
    text = text.translate(table)
    return [t for t in text.split() if len(t) > 1]


def _stem(word: str) -> str:
    w = word
    if len(w) > 4 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    return w


def _token_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if _stem(a) == _stem(b):
        return 0.9
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= len(longer) * 0.5 and shorter in longer:
        return 0.8
    return difflib.SequenceMatcher(None, a, b).ratio()


def _semantic_score(query: str, product: dict) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 1.0

    stops = {
        "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "and", "or", "but", "not",
        "this", "that", "these", "those", "it", "its", "i", "you", "we", "they",
        "me", "my", "your", "our", "do", "does", "did", "have", "has", "had",
        "can", "will", "would", "could", "should", "may", "all", "each", "every",
        "some", "any", "no", "both", "what", "which", "who", "how", "why",
        "when", "where", "there", "here", "about", "up", "out", "if", "so",
    }
    relevant = [t for t in q_tokens if t not in stops]
    if not relevant:
        return 1.0

    name_tokens = _tokenize(product["name"])
    desc_tokens = _tokenize(product["description"])

    score = 0.0
    matched_strong = 0
    any_strong = False

    for qt in relevant:
        best = 0.0
        for pt in name_tokens:
            s = _token_similarity(qt, pt)
            if s > best:
                best = s
        for pt in desc_tokens:
            s = _token_similarity(qt, pt) * 0.7
            if s > best:
                best = s

        if best >= 0.7:
            matched_strong += 1
            any_strong = True
        score += best

    if not any_strong:
        return 0.0

    coverage = matched_strong / len(relevant)
    score *= (1 + coverage * 0.5)
    return score


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def search_products(
    ctx: RunContextWrapper[UserContext],
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
) -> SearchResults:
    """Search the product catalog using semantic matching. Returns results sorted by relevance."""
    results = list(PRODUCTS)
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]

    scored = [(p, _semantic_score(query, p)) for p in results]
    scored.sort(key=lambda x: -x[1])
    scored = [(p, s) for p, s in scored if s > 0]

    products = [ProductResult(
        id=p["id"], name=p["name"], category=p["category"],
        price=p["price"], rating=p["rating"],
        in_stock=p["stock"] > 0, description=p["description"],
    ) for p, _ in scored]
    return SearchResults(query=query, total_found=len(products), products=products)


@function_tool
def get_product_details(product_id: int) -> ProductResult:
    """Get full details for a single product by its ID."""
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not p:
        return ProductResult(id=product_id, name="Not found", category="", price=0, rating=0, in_stock=False, description=f"No product found with ID {product_id}.")
    return ProductResult(id=p["id"], name=p["name"], category=p["category"], price=p["price"], rating=p["rating"], in_stock=p["stock"] > 0, description=p["description"])


@function_tool
def list_categories(dummy: Optional[str] = None) -> str:
    """List all available product categories in the catalog."""
    cats = sorted(set(p["category"] for p in PRODUCTS))
    return f"Available categories ({len(cats)}): " + ", ".join(cats)


@function_tool
def add_feedback(
    ctx: RunContextWrapper[UserContext],
    product_id: int,
    rating: int,
    comment: Optional[str] = None,
) -> str:
    """Record user feedback (rating 1-5) for a product. Use this whenever a user rates or reviews a product."""
    uid = ctx.context.user_id
    if uid not in FEEDBACK_STORE:
        FEEDBACK_STORE[uid] = []
    entry = {"product_id": product_id, "rating": rating, "comment": comment}
    FEEDBACK_STORE[uid].append(entry)
    return f"Thanks! Your {rating}/5 rating for product {product_id} has been saved."


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------

def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    base = (
        "You are a friendly catalog search assistant. "
        "Help users find products by searching, browsing categories, and getting details.\n\n"
        "Guidelines:\n"
        "- Use search_products when filtering by name, category, price, or rating\n"
        "- Use get_product_details for more info on a specific product\n"
        "- Use list_categories to show available categories\n"
        "- Use add_feedback when a user rates or reviews a product (1-5 stars)\n"
        "- If a product is out of stock, mention it and suggest alternatives\n"
        "- Be concise but helpful"
    )
    user = ctx.context
    prefs = []
    if user.preferred_categories:
        prefs.append(f"Preferred categories: {', '.join(user.preferred_categories)}")
    if user.max_budget is not None:
        prefs.append(f"Max budget: ${user.max_budget:.2f}")
    if prefs:
        base += "\n\nUser preferences:\n" + "\n".join(prefs)
    return base


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    agent_model, provider_label = build_model()
    if not agent_model:
        print("=" * 60)
        print("  Catalog Search Agent")
        print("=" * 60)
        print("  No API key found. Set one of these:")
        print("    $env:OPENROUTER_API_KEY = \"...\"  (many free models)")
        print("    $env:GROQ_API_KEY = \"...\"        (free, 14400 req/day)")
        print("    $env:GEMINI_API_KEY = \"...\"      (free tier)")
        print("    $env:OPENAI_API_KEY = \"...\"")
        print("=" * 60)
        print("  Or run: python catalog_search_agent_mock.py")
        print("=" * 60)
        return

    user_ctx = UserContext(user_id="user_001", name="Ali", preferred_categories=["Electronics", "Sports & Fitness"], max_budget=200.0)

    guardrail_agent = Agent[UserContext](
        name="CatalogGuardrail",
        instructions=(
            "Determine if the user's query is about searching, browsing, or asking about "
            "products in a product catalog. Topics include: finding products, checking prices, "
            "filtering by category, product details, stock/availability, ratings, recommendations, "
            "and comparing products. Reject math, coding, general knowledge, or unrelated chat."
        ),
        output_type=CatalogQueryCheck,
        model=agent_model,
    )

    @input_guardrail
    async def catalog_relevance_guardrail(
        ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], input: str | list[TResponseInputItem]
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_catalog_query,
        )

    agent = Agent[UserContext](
        name="CatalogSearchAgent",
        instructions=dynamic_instructions,
        model=agent_model,
        tools=[search_products, get_product_details, list_categories, add_feedback],
        input_guardrails=[catalog_relevance_guardrail],
    )

    print("=" * 60)
    print("  Catalog Search Agent")
    print(f"  Provider: {provider_label}")
    print("  Type 'exit' to quit")
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input or user_input.lower() in ("exit", "quit"):
            break

        try:
            result = await Runner.run(agent, user_input, context=user_ctx)
            print(f"\nAssistant: {result.final_output}")
        except InputGuardrailTripwireTriggered:
            print("\nAssistant: I can only answer questions about the product catalog. Please ask me about products, categories, pricing, or availability.")


if __name__ == "__main__":
    asyncio.run(main())
