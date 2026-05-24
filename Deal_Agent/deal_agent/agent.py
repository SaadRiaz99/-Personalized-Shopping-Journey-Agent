"""
Deal Agent — Personalized Shopping Journey System
Specialist agent responsible for finding and applying the best discount combination.

Built by: Hashir (Deal Agent Specialist)
Team: SMIT Personalized Shopping Journey Agent
"""

import os
from dotenv import load_dotenv
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

from .tools import get_active_promotions, get_loyalty_points, get_bundle_offers, apply_discount

load_dotenv()

MODEL = os.getenv("MODEL_NAME", "gpt-4o-mini")


def _get_client() -> AsyncOpenAI:
    """Create OpenAI client using env vars (supports custom base URL for OpenCode/Zen)."""
    api_key = os.getenv("OPENAI_API_KEY")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY is not set. "
            "Copy .env.example to .env and add your API key from OpenCode/Zen."
        )
    return AsyncOpenAI(api_key=api_key, base_url=base_url)


# ── Deal Agent ─────────────────────────────────────────────────────────────────
deal_agent = Agent(
    name="DealAgent",
    model=MODEL,
    instructions="""
You are the Deal Agent — a specialist in finding and applying the best discount
combinations for shoppers. Your goal is to maximize savings for every customer.

## Your Responsibilities
1. Check all active promotions applicable to the customer's cart (category + total).
2. Retrieve the customer's loyalty points balance and calculate their monetary value.
3. Check if products qualify for bundle deals.
4. Determine the OPTIMAL combination of discounts (maximize total savings).
5. Apply the chosen discount combination using the apply_discount tool.
6. Present a clear, friendly savings summary to the customer.

## Decision Rules
- ALWAYS check promotions, loyalty points, AND bundles before deciding.
- If promotions are stackable, combine them for maximum savings.
- Only redeem loyalty points if doing so increases total savings.
- Never apply a promotion that the cart doesn't qualify for.
- If multiple non-stackable promotions exist, pick the one with highest savings.
- Bundle discounts take priority over individual item promotions.

## Response Format
Always end with a clear summary:
- Original price
- Discounts applied (itemized)
- Final price
- Total savings (amount + percentage)
- Encouraging message for the customer

Be enthusiastic but concise. Use Rs. for currency (Pakistani Rupees).
""",
    tools=[get_active_promotions, get_loyalty_points, get_bundle_offers, apply_discount],
)


async def run_deal_agent(
    cart_id: str,
    user_id: str,
    category: str,
    cart_total: float,
    product_ids: list[str] | None = None,
) -> str:
    """
    Run the Deal Agent for a given cart.

    Args:
        cart_id: Unique cart identifier
        user_id: Customer's user ID
        category: Primary product category in the cart
        cart_total: Total cart value in PKR
        product_ids: List of product IDs (for bundle detection)

    Returns:
        Agent's response with deal recommendations and applied discounts.
    """
    product_ids = product_ids or []

    query = (
        f"Find the best deals for cart {cart_id}. "
        f"Customer ID: {user_id}. "
        f"Category: {category}. "
        f"Cart total: Rs. {cart_total:.0f}. "
        f"Products in cart: {', '.join(product_ids) if product_ids else 'not specified'}. "
        f"Check all promotions, loyalty points, and bundle offers. "
        f"Apply the best combination and show me the final savings."
    )

    # Configure client at runtime so env vars are loaded first
    client = _get_client()
    set_default_openai_client(client)
    set_tracing_disabled(True)  # Disable OpenAI tracing (not needed for OpenRouter)

    result = await Runner.run(deal_agent, input=query)
    return result.final_output
