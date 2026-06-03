from __future__ import annotations
import uuid
import logging
from agents import Agent, Runner, RunConfig, trace
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from agents.run_context import RunContextWrapper

from .config   import get_model, get_fallback_model, get_deep_fallback_model, get_fallback_3_model, get_fallback_4_model, active_model_name
from .context  import AgentContext
from .session_memory import get_or_create_session
from .tools    import (
    search_items,
    filter_by_tag,
    get_item_details,
    list_categories,
    compare_products,
    rapidapi_search,
    save_preference,
)
from .guardrails import (
    injection_abuse_guardrail,
    off_topic_guardrail,
    response_quality_guardrail,
)
from . import tracing

logger = logging.getLogger(__name__)

_SEARCH_PROMPT = """
You are SearchAgent — you find products. Use search_items, filter_by_tag,
compare_products, or get_item_details. When the user asks for "more" or
"next page", increment the offset. Prefer the local catalogue; use
rapidapi_search only when nothing is found locally.
"""

_SUPPORT_PROMPT = """
You are SupportAgent — you handle complaints, returns, and questions.
Be empathetic. Ask for order/product IDs if needed. If the user wants
to find a product, transfer back to RecommendationAgent.
"""

_MAIN_PROMPT = """
You are RecommendationAgent — the main product recommendation assistant.

You have two specialists you can transfer to:
- **SearchAgent** — for finding, filtering, comparing products
- **SupportAgent** — for complaints, returns, customer service

You can also handle things directly using your own tools. When a user
asks for products, either handle it yourself or transfer to SearchAgent.
Learn preferences and personalize — call save_preference when you infer
what the user likes.
"""


def _build_instructions(ctx_wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]) -> str:
    ctx = ctx_wrapper.context
    session = ctx.session
    seen = session.seen_ids
    prefs = session.preferences
    last_search = session.get_last_search()

    suffix = ""
    if seen:
        suffix += f"\n## Products already shown to this user (DO NOT recommend again)\nIDs: {sorted(seen)}"
    if prefs:
        suffix += f"\n## Known user preferences\n{', '.join(f'{k}={v}' for k, v in prefs.items())}"
    if last_search:
        suffix += f"\n## Last search params (for pagination)\n{last_search}"

    return _MAIN_PROMPT + suffix


def _make_agents(model):
    search = Agent[AgentContext](
        name="SearchAgent",
        instructions=_SEARCH_PROMPT,
        model=model,
        tools=[search_items, filter_by_tag, get_item_details, list_categories, compare_products, rapidapi_search],
    )
    support = Agent[AgentContext](
        name="SupportAgent",
        instructions=_SUPPORT_PROMPT,
        model=model,
    )
    main = Agent[AgentContext](
        name="RecommendationAgent",
        instructions=_build_instructions,
        model=model,
        tools=[save_preference],
        handoffs=[search, support],
        input_guardrails=[injection_abuse_guardrail, off_topic_guardrail],
        output_guardrails=[response_quality_guardrail],
    )
    return main, search, support


async def run_turn(
    user_message: str,
    session_id:   str  = "default",
    user_id:      str  = "anonymous",
    on_token:     callable | None = None,
) -> dict:
    session    = get_or_create_session(session_id)
    request_id = str(uuid.uuid4())[:8]

    ctx = AgentContext(session=session, user_id=user_id, request_id=request_id)

    saved_history = list(session._history)
    saved_turn_count = session.turn_count
    saved_seen_ids = set(session.seen_ids)
    saved_preferences = dict(session.preferences)

    models_to_try = [
        ("gemma", get_model),
        ("kimi", get_fallback_model),
        ("gpt-oss-120b", get_deep_fallback_model),
        ("gpt-oss-20b", get_fallback_3_model),
        ("qwen3-next-80b", get_fallback_4_model),
    ]

    last_error = None
    for model_label, model_fn in models_to_try:
        try:
            model = model_fn()
            main_agent, *_ = _make_agents(model)

            with trace(f"recommendation_turn:{session_id}"):
                result = Runner.run_streamed(
                    main_agent,
                    input=user_message,
                    context=ctx,
                    session=session,
                    run_config=RunConfig(
                        workflow_name="RecommendationAgent",
                        trace_metadata={
                            "session_id": session_id,
                            "user_id":    user_id,
                            "request_id": request_id,
                            "model":      active_model_name(),
                        },
                    ),
                )

                async for event in result.stream_events():
                    if on_token and event.type == "raw_response_event" and hasattr(event.data, "delta"):
                        on_token(event.data.delta)

                final_output = result.final_output

            ctx.log_tool("MODEL", f"used {active_model_name()}")
            return {
                "response":        final_output,
                "tool_calls":      ctx.tool_call_log,
                "session_summary": session.summary(),
            }

        except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
            session._history = saved_history
            session.turn_count = saved_turn_count
            session.seen_ids = saved_seen_ids
            session.preferences = saved_preferences
            raise

        except Exception as e:
            last_error = e
            logger.debug("Model %s failed: %s — trying fallback", model_label, e)
            ctx.log_tool("MODEL_FAIL", f"{model_label} rate limited")
            session._history = list(saved_history)
            session.turn_count = saved_turn_count
            session.seen_ids = set(saved_seen_ids)
            session.preferences = dict(saved_preferences)
            continue

    ctx.log_tool("ALL_MODELS_FAILED", "all models exhausted")
    return {
        "response":        "Our recommendation service is temporarily unavailable. Please try again in a moment.",
        "tool_calls":      ctx.tool_call_log,
        "session_summary": session.summary(),
    }


async def run_recommendation(user_input: str) -> str:
    result = await run_turn(user_message=user_input)
    return result["response"]
