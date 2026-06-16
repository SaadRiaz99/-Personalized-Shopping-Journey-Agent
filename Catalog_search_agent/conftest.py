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

ZEN_API_KEY = os.environ.get("ZEN_API_KEY", "")
ZEN_BASE_URL = "https://opencode.ai/zen/v1"
ZEN_MODEL = os.environ.get("LLM_MODEL", "big-pickle")


@pytest.fixture(scope="session")
def vcr_config():
    record_mode = "once" if ZEN_API_KEY else "none"
    return {
        "record_mode": record_mode,
        "match_on": ["method", "scheme", "host", "port", "path", "query", "body"],
        "filter_headers": ["authorization"],
        "filter_query_parameters": ["api_key"],
    }


def pytest_collection_modifyitems(items):
    for item in items:
        if "needs_api" in item.keywords:
            item.add_marker(pytest.mark.skipif(
                not ZEN_API_KEY,
                reason="set ZEN_API_KEY to run integration tests",
            ))


@pytest.fixture(scope="session")
def model():
    if ZEN_API_KEY:
        key = ZEN_API_KEY
        base_url = ZEN_BASE_URL
        model_name = ZEN_MODEL
    else:
        key = "sk-zen-dummy-vcr-replay"
        base_url = ZEN_BASE_URL
        model_name = ZEN_MODEL
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
            "Determine if the user's query is about the product catalog. "
            "You must NOT use any tools. Only return a JSON object with "
            "'is_catalog_query' (bool) and 'reasoning' (str). "
            "Reject math, coding, general knowledge, or unrelated chat."
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
        try:
            result = await Runner.run(guardrail_agent, input, context=ctx.context)
            return GuardrailFunctionOutput(
                output_info=result.final_output,
                tripwire_triggered=not result.final_output.is_catalog_query,
            )
        except Exception:
            return GuardrailFunctionOutput(
                output_info=CatalogQueryCheck(is_catalog_query=True, reasoning="Guardrail error, allowing query by default"),
                tripwire_triggered=False,
            )

    return Agent[UserContext](
        name="CatalogSearchAgent",
        instructions=dynamic_instructions,
        model=model,
        tools=[search_products, get_product_details, list_categories, add_feedback],
        input_guardrails=[catalog_relevance_guardrail],
    )
