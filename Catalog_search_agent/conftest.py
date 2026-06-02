import os
import json
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
    PRODUCTS,
    UserContext,
    CatalogQueryCheck,
    dynamic_instructions,
    search_products,
    get_product_details,
    list_categories,
)

set_tracing_disabled(disabled=True)


def pytest_collection_modifyitems(items):
    for item in items:
        if "needs_api" in item.keywords:
            item.add_marker(pytest.mark.skipif(
                not os.environ.get("OPENROUTER_API_KEY"),
                reason="set $env:OPENROUTER_API_KEY to run API tests",
            ))


@pytest.fixture(scope="session")
def model():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        pytest.skip("OPENROUTER_API_KEY not set")
    return OpenAIChatCompletionsModel(
        model=os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
        openai_client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
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
        tools=[search_products, get_product_details, list_categories],
        input_guardrails=[catalog_relevance_guardrail],
    )
