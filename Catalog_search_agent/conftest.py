import json
import os

import pytest
from openai import AsyncOpenAI

from agents import (
    Agent,
    GuardrailFunctionOutput,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    input_guardrail,
    set_tracing_disabled,
)
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from catalog_search_agent import (
    FEEDBACK_STORE,
    PRODUCTS,
    UserContext,
    CatalogQueryCheck,
    dynamic_instructions,
    search_products,
    get_product_details,
    list_categories,
    add_feedback,
)

set_tracing_disabled(disabled=True)


@pytest.fixture(scope="session")
def vcr_config():
    return {
        "record_mode": "none",
        "filter_headers": ["authorization", "x-api-key"],
        "filter_query_parameters": ["api_key"],
    }


def _api_key() -> tuple[str, str, str] | None:
    candidates = [
        ("OPENROUTER_API_KEY", "https://openrouter.ai/api/v1", os.environ.get("LLM_MODEL", "openai/gpt-4o-mini")),
        ("GROQ_API_KEY", "https://api.groq.com/openai/v1", os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")),
        ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com/v1beta/openai/", os.environ.get("LLM_MODEL", "gemini-2.0-flash")),
    ]
    for var, base_url, model in candidates:
        if key := os.environ.get(var):
            return key, base_url, model
    return None


def pytest_collection_modifyitems(items):
    for item in items:
        if "needs_api" in item.keywords:
            item.add_marker(pytest.mark.skipif(
                not bool(_api_key()),
                reason="set an API key (e.g. OPENROUTER_API_KEY) to run integration tests",
            ))


@pytest.fixture(scope="session")
def model():
    info = _api_key()
    if info:
        key, base_url, model_name = info
    else:
        key = "sk-or-v1-dummy-vcr-replay"
        base_url = "https://openrouter.ai/api/v1"
        model_name = "openai/gpt-4o-mini"
    return OpenAIChatCompletionsModel(
        model=model_name,
        openai_client=AsyncOpenAI(api_key=key, base_url=base_url),
    )


@pytest.fixture(scope="session")
def user_ctx():
    return UserContext(user_id="test_user", name="Tester")


@pytest.fixture(scope="session")
def guardrail_agent(model):
    return Agent[UserContext](
        name="CatalogGuardrail",
        instructions=(
            "Determine if the user's query is about searching, browsing, or asking about "
            "products in a product catalog. Topics include: finding products, checking prices, "
            "filtering by category, product details, stock/availability, ratings, recommendations, "
            "and comparing products. Reject math, coding, general knowledge, or unrelated chat."
        ),
        output_type=CatalogQueryCheck,
        model=model,
    )


@pytest.fixture(scope="session")
def catalog_agent(model, guardrail_agent):
    @input_guardrail
    async def catalog_relevance_guardrail(
        ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], input: str | list[TResponseInputItem]
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_catalog_query,
        )

    return Agent[UserContext](
        name="CatalogSearchAgent",
        instructions=dynamic_instructions,
        model=model,
        tools=[search_products, get_product_details, list_categories, add_feedback],
        input_guardrails=[catalog_relevance_guardrail],
    )
