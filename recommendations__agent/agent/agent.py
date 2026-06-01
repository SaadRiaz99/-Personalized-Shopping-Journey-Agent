"""
agent.py
--------
Defines the ShopBot agent, its system prompt, and the run_turn() entry point.
Wires config, tools, guardrails, session memory, context, and tracing together.
"""

from __future__ import annotations
import uuid                               # Generate unique request IDs
from agents import Agent, Runner, RunConfig, trace        # Core SDK classes
from agents import InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered
from agents.run_context import RunContextWrapper

from .config   import get_model           # Returns the Gemini model string from .env
from .context  import AgentContext         # Per-request context (session, logs, user info)
from .session_memory import get_or_create_session  # Fetch/create conversation session
from .tools    import (
    search_items,          # Full-text search by keyword (title, category, tags)
    filter_by_tag,         # Filter products by tag + optional min rating
    get_item_details,      # Get full details of one product by ID
    list_categories,       # List all product categories
)
from .guardrails import (
    injection_abuse_guardrail,   # Blocks prompt injection & jailbreak attempts
    off_topic_guardrail,         # Redirects non-product queries
    response_quality_guardrail,  # Rejects too-short or error-containing responses
)
from . import tracing   # Registers the custom tracing processor on import

# ── Base system prompt ─────────────────────────────────────────────────────────
# This text is sent to the LLM at the start of every conversation turn.
# Edit this to change the agent's personality, rules, or response style.
_BASE_SYSTEM_PROMPT = """
You are ShopBot, a friendly and knowledgeable product recommendation assistant.
You have access to a catalogue of over 1,000,000 products across 10 categories.

## Your goal
Help users discover products they'll love by asking clarifying questions,
searching the catalogue, and presenting clear, concise recommendations.

## Tool usage rules
1. Use `search_items` when the user mentions a keyword or product type (searches by title, category, and tags).
2. Use `filter_by_tag` when the user specifies a category, genre, or feature (filters by tag, optional rating, and optional category).
3. Use `get_item_details` only when asked for more info on a specific item by its ID.
4. CRITICAL: Never invent products, IDs, ratings, or prices. Only reference what the tools actually return. If a tool returns no results, say so honestly and suggest a broader search.
5. IMPORTANT: You ONLY have the tools listed above. NEVER attempt to call any other tools (like get_weather, get_news, etc.). If the user asks for something outside product recommendations, politely explain you can only help with product recommendations.
6. Never list a product in your response unless you called `search_items`, `filter_by_tag`, or `get_item_details` and the product was in the returned results.
7. You MUST use your tools to answer product questions. Do NOT say "I cannot access product information" or "that information is not available". Instead, call `search_items`, `filter_by_tag`, or `list_categories` to find the answer. Only if ALL tools return empty results, then say no products were found.

## Response format
- Lead with a brief acknowledgement of what the user is looking for.
- List 3–5 top picks with: title, rating, tags, and a short reason why it fits.
- End with a follow-up question to refine further.

## Examples

Here are examples of correct tool usage and response formatting:

**Example 1 — Category + rating search**
User: "Find me good sci-fi books with rating at least 4.5"
Agent: `search_items(query="sci-fi", category="Book", min_rating=4.5, sort_by="rating")`
Response: *Based on your preference for highly-rated sci-fi books, here are some top picks…*

**Example 2 — Price-filtered search**
User: "I need wireless headphones under $100"
Agent: `search_items(query="wireless headphones", max_price=100, sort_by="rating")`
Response: *Here are the best-rated wireless headphones under $100…*

**Example 3 — Tag + category filter**
User: "Show me sci-fi movies rated 4.7+"
Agent: `filter_by_tag(tag="sci-fi", category="Movie", min_rating=4.7)`
Response: *Here are highly-rated sci-fi movies…*

**Example 4 — Listing categories then narrowing down**
User: "What do you have in Electronics?"
Agent: `search_items(query="", category="Electronics", sort_by="rating")`
Response: *Here are popular products in Electronics…*

## Guardrails
- Do not discuss topics unrelated to product recommendations.
- If no products match, say so honestly and suggest a broader search.
"""


def _build_instructions(ctx_wrapper: RunContextWrapper[AgentContext], agent: Agent[AgentContext]) -> str:
    """Build dynamic instructions by appending session context to the base prompt.

    Injects seen_ids so the LLM knows which products were already shown.
    """
    ctx = ctx_wrapper.context
    seen = ctx.session.seen_ids
    if seen:
        suffix = (
            "\n\n## Products already shown to this user (DO NOT recommend these again)\n"
            f"The following product IDs have already been shown to the user: {sorted(seen)}\n"
            "Do NOT suggest any of these products again unless the user explicitly asks about them."
        )
    else:
        suffix = ""

    prefs = ctx.session.preferences
    if prefs:
        pref_str = ", ".join(f"{k}={v}" for k, v in prefs.items())
        suffix += f"\n\n## Known user preferences\n{pref_str}"

    return _BASE_SYSTEM_PROMPT + suffix


# ── Agent definition ──────────────────────────────────────────────────────────
# The Agent object ties together the model, system prompt, tools, and guardrails.
# instructions=_build_instructions is a callable — it runs on every turn with the
# current context so seen_ids and preferences are always up to date.
recommendation_agent = Agent[AgentContext](
    name="ShopBot",
    instructions=_build_instructions,
    model=get_model(),                                # Gemini model from .env
    tools=[
        search_items,                                 # Tool #1: keyword search
        filter_by_tag,                                # Tool #2: tag filter
        get_item_details,                             # Tool #3: product details
        list_categories,                              # Tool #4: list categories
    ],
    input_guardrails=[
        injection_abuse_guardrail,                    # Runs BEFORE agent processes
        off_topic_guardrail,                          # Runs BEFORE agent processes
    ],
    output_guardrails=[
        response_quality_guardrail,                   # Runs AFTER agent responds
    ],
)


# ── Public entry point ────────────────────────────────────────────────────────
async def run_turn(
    user_message: str,
    session_id:   str  = "default",
    user_id:      str  = "anonymous",
) -> dict:
    """
    Run one conversational turn.

    Parameters
    ----------
    user_message : the user's latest message (string, e.g. "find me a sci-fi book")
    session_id   : identifies this user's conversation thread
    user_id      : caller identity for logging

    Returns
    -------
    dict with keys:
        response        – agent's final text
        tool_calls      – list of tool call summaries for this turn
        session_summary – session stats after this turn
    """
    session    = get_or_create_session(session_id)      # Load or create session
    request_id = str(uuid.uuid4())[:8]                   # Short unique ID for logging

    # Build per-request context (passed to tools via RunContextWrapper)
    ctx = AgentContext(
        session=session,
        user_id=user_id,
        request_id=request_id,
    )

    # Save session state before run (restored if a guardrail triggers)
    saved_history = list(session._history)
    saved_turn_count = session.turn_count
    saved_seen_ids = set(session.seen_ids)
    saved_preferences = dict(session.preferences)

    try:
        # Wrap in a named trace (visible in OpenAI tracing dashboard)
        with trace(f"recommendation_turn:{session_id}"):
            result = await Runner.run(
                recommendation_agent,                 # The agent definition above
                input=user_message,                   # User's latest text
                context=ctx,                          # Per-request context object
                session=session,                      # Conversation history
                run_config=RunConfig(
                    workflow_name="RecommendationAgent",
                    trace_metadata={
                        "session_id": session_id,
                        "user_id":    user_id,
                        "request_id": request_id,
                    },
                ),
            )

        return {
            "response":        result.final_output,    # Agent's reply text
            "tool_calls":      ctx.tool_call_log,      # Summary of tools used this turn
            "session_summary": session.summary(),       # Turn count, seen products, etc.
        }
    except (InputGuardrailTripwireTriggered, OutputGuardrailTripwireTriggered):
        # Restore session state when guardrails trigger (SDK may have mutated it)
        session._history = saved_history
        session.turn_count = saved_turn_count
        session.seen_ids = saved_seen_ids
        session.preferences = saved_preferences
        raise


# ── Backward-compatible wrapper ───────────────────────────────────────────────
async def run_recommendation(user_input: str) -> str:
    """Simple wrapper that returns only the text response (no metadata)."""
    result = await run_turn(user_message=user_input)
    return result["response"]
