import os

from agents import Agent, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from .tools import get_product_details, get_recommendations, search_products

set_tracing_disabled(disabled=True)


def _build_model() -> OpenAIChatCompletionsModel | None:
    if key := os.environ.get("OPENROUTER_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
        )
    if key := os.environ.get("GROQ_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://api.groq.com/openai/v1"),
        )
    if key := os.environ.get("GEMINI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "gemini-2.0-flash"),
            openai_client=AsyncOpenAI(api_key=key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/"),
        )
    if key := os.environ.get("OPENAI_API_KEY", ""):
        return OpenAIChatCompletionsModel(
            model=os.environ.get("LLM_MODEL", "gpt-4o-mini"),
            openai_client=AsyncOpenAI(api_key=key),
        )
    return None


_model = _build_model()

SYSTEM_PROMPT = (
    "You are a friendly product recommendation assistant with access to a catalog of products "
    "across many categories.\n\n"
    "Your tools:\n"
    "1. search_products — Search the catalog by name, category, price range, rating, etc.\n"
    "2. get_recommendations — Get top-rated recommendations in a specific category.\n"
    "3. get_product_details — Get full details for a specific product by ID.\n\n"
    "Help users find the perfect products. Be concise, friendly, and informative. "
    "Always use your tools to search for products rather than inventing information."
)

recommendation_agent = (
    Agent(
        name="RecommendationAgent",
        instructions=SYSTEM_PROMPT,
        tools=[search_products, get_recommendations, get_product_details],
        model=_model,
    )
    if _model
    else None
)


async def run_recommendation(user_input: str) -> str:
    if recommendation_agent is None:
        return "Error: No API key configured. Set GROQ_API_KEY, OPENAI_API_KEY, GEMINI_API_KEY, or OPENROUTER_API_KEY."
    result = await Runner.run(recommendation_agent, input=user_input)
    return result.final_output
