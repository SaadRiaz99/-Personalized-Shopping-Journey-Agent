import os

from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from .tools import compare_prices, get_product_details, get_recommendations, search_products

set_tracing_disabled(disabled=True)


def _build_model(model_name: str | None = None) -> OpenAIChatCompletionsModel | None:
    model = model_name or os.environ.get("LLM_MODEL", "")
    if key := os.environ.get("OPENROUTER_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=model or "openai/gpt-4o-mini",
            openai_client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
        )
    if key := os.environ.get("GROQ_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=model or "llama-3.3-70b-versatile",
            openai_client=AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1"),
        )
    if key := os.environ.get("GEMINI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=model or "gemini-2.0-flash",
            openai_client=AsyncOpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        )
    if key := os.environ.get("OPENAI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=model or "gpt-4o-mini",
            openai_client=AsyncOpenAI(api_key=key),
        )
    return None


_common_tools = [search_products, get_recommendations, get_product_details, compare_prices]

BUDGET_SYSTEM_PROMPT = (
    "You are BudgetFinder, a recommendation assistant focused on finding the best value products. "
    "Prioritize affordable options, good price-to-value ratio, and budget-friendly choices.\n\n"
    "Your tools:\n"
    "1. search_products — Search the catalog by name, category, price range, rating, etc.\n"
    "2. get_recommendations — Get top-rated recommendations in a specific category.\n"
    "3. get_product_details — Get full details for a specific product by ID.\n"
    "4. compare_prices — Compare prices across multiple products.\n\n"
    "Always highlight the most cost-effective options. Mention the price clearly for every recommendation."
)

QUALITY_SYSTEM_PROMPT = (
    "You are QualityFinder, a recommendation assistant focused on finding the highest quality products. "
    "Prioritize premium items, top ratings, best features, and superior quality.\n\n"
    "Your tools:\n"
    "1. search_products — Search the catalog by name, category, price range, rating, etc.\n"
    "2. get_recommendations — Get top-rated recommendations in a specific category.\n"
    "3. get_product_details — Get full details for a specific product by ID.\n"
    "4. compare_prices — Compare prices across multiple products.\n\n"
    "Always highlight the best-rated, highest-quality options. Mention the rating clearly for every recommendation."
)

_budget_model = _build_model(os.environ.get("BUDGET_MODEL"))
_quality_model = _build_model(os.environ.get("QUALITY_MODEL"))

budget_agent = (
    Agent(
        name="BudgetFinder",
        instructions=BUDGET_SYSTEM_PROMPT,
        tools=_common_tools,
        model=_budget_model,
    )
    if _budget_model
    else None
)

quality_agent = (
    Agent(
        name="QualityFinder",
        instructions=QUALITY_SYSTEM_PROMPT,
        tools=_common_tools,
        model=_quality_model,
    )
    if _quality_model
    else None
)


async def run_comparison(user_input: str) -> dict[str, str]:
    results = {}
    if budget_agent:
        result = await Runner.run(budget_agent, input=user_input)
        results["budget"] = result.final_output
    else:
        results["budget"] = "Error: No API key configured for BudgetFinder."
    if quality_agent:
        result = await Runner.run(quality_agent, input=user_input)
        results["quality"] = result.final_output
    else:
        results["quality"] = "Error: No API key configured for QualityFinder."
    return results
