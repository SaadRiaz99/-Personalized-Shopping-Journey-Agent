import asyncio
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
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
        ), f"OpenRouter ({os.environ.get('LLM_MODEL', 'openai/gpt-4o-mini')})"

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
# Tools
# ---------------------------------------------------------------------------

@function_tool
def search_products(
    ctx: RunContextWrapper[UserContext],
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
) -> SearchResults:
    """Search the product catalog. Returns matching products with full details."""
    results = list(PRODUCTS)
    q = query.lower()
    results = [p for p in results if q in p["name"].lower() or q in p["description"].lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]
    products = [ProductResult(id=p["id"], name=p["name"], category=p["category"], price=p["price"], rating=p["rating"], in_stock=p["stock"] > 0, description=p["description"]) for p in results]
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
        tools=[search_products, get_product_details, list_categories],
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
