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
# Provider setup  (same as Catalog Agent — just set your env var)
# ---------------------------------------------------------------------------
# Set one of these:
#   $env:OPENROUTER_API_KEY = "sk-or-v1-..."   (openrouter.ai — many free models)
#   $env:GROQ_API_KEY       = "..."             (console.groq.com — free, fast)
#   $env:GEMINI_API_KEY     = "..."             (aistudio.google.com — free tier)
#   $env:OPENAI_API_KEY     = "..."             (platform.openai.com)

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
# Promotions data
# ---------------------------------------------------------------------------

PROMOTIONS: list[dict] = json.load(open("promotions.json"))["promotions"]
USERS: list[dict]      = json.load(open("promotions.json"))["users"]


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclass
class UserContext:
    user_id: str
    name: str
    category: Optional[str] = None
    cart_total: Optional[float] = None


# ---------------------------------------------------------------------------
# Structured output types
# ---------------------------------------------------------------------------

class PromoResult(BaseModel):
    code: str              = Field(description="Promotion code")
    description: str       = Field(description="What the promotion offers")
    discount_type: str     = Field(description="Type: percentage, fixed, or bundle")
    discount_value: float  = Field(description="Discount amount or percentage")
    min_order: float       = Field(description="Minimum order value required")
    stackable: bool        = Field(description="Can be combined with other promos")


class DealSearchResults(BaseModel):
    query: str                    = Field(description="What was searched")
    total_found: int              = Field(description="Number of promotions found")
    promotions: list[PromoResult] = Field(description="List of matching promotions")
    note: Optional[str]           = Field(default=None, description="Helpful note for user")


class LoyaltyInfo(BaseModel):
    user_id: str        = Field(description="User ID")
    tier: str           = Field(description="Loyalty tier: bronze/silver/gold/platinum")
    points: int         = Field(description="Current points balance")
    monetary_value: float = Field(description="Points value in Rs.")
    message: str        = Field(description="Summary message")


class DiscountResult(BaseModel):
    original_price: float         = Field(description="Price before discounts")
    discounts_applied: list[str]  = Field(description="Each discount applied")
    total_saved: float            = Field(description="Total amount saved in Rs.")
    final_price: float            = Field(description="Final price after all discounts")
    savings_percentage: float     = Field(description="Percentage saved")
    summary: str                  = Field(description="One line summary of savings")


class DealQueryCheck(BaseModel):
    is_deal_query: bool = Field(description="Whether query is about deals, discounts or promotions")
    reasoning: str      = Field(description="Why this is or isn't a deal query")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def search_promotions(
    ctx: RunContextWrapper[UserContext],
    category: Optional[str] = None,
    max_discount: Optional[float] = None,
    min_order: Optional[float] = None,
) -> DealSearchResults:
    """Search available promotions. Filter by category, discount value, or minimum order."""
    results = list(PROMOTIONS)

    if category:
        results = [p for p in results if p["category"] == "all" or p["category"] == category.lower()]
    if max_discount is not None:
        results = [p for p in results if p["value"] <= max_discount]
    if min_order is not None:
        results = [p for p in results if p["min_order"] <= min_order]

    promos = [
        PromoResult(
            code=p["code"],
            description=p["description"],
            discount_type=p["type"],
            discount_value=p["value"],
            min_order=p["min_order"],
            stackable=p["stackable"],
        )
        for p in results
    ]
    return DealSearchResults(query=f"category={category}", total_found=len(promos), promotions=promos)


@function_tool
def get_promotion_details(promo_code: str) -> PromoResult:
    """Get full details for a specific promotion code."""
    p = next((p for p in PROMOTIONS if p["code"].upper() == promo_code.upper()), None)
    if not p:
        return PromoResult(code=promo_code, description="Not found", discount_type="", discount_value=0, min_order=0, stackable=False)
    return PromoResult(code=p["code"], description=p["description"], discount_type=p["type"], discount_value=p["value"], min_order=p["min_order"], stackable=p["stackable"])


@function_tool
def get_loyalty_account(
    ctx: RunContextWrapper[UserContext],
    user_id: str,
) -> LoyaltyInfo:
    """Get loyalty points balance and tier info for a user."""
    user = next((u for u in USERS if u["user_id"] == user_id), None)
    if not user:
        return LoyaltyInfo(user_id=user_id, tier="bronze", points=0, monetary_value=0.0,
                           message="No account found. You start at Bronze with 0 points.")
    val = user["points"] * user["value_per_point"]
    return LoyaltyInfo(
        user_id=user["user_id"],
        tier=user["tier"],
        points=user["points"],
        monetary_value=val,
        message=f"{user['tier'].upper()} member — {user['points']} points worth Rs. {val:.0f}",
    )


@function_tool
def apply_best_discount(
    ctx: RunContextWrapper[UserContext],
    cart_total: float,
    category: str,
    user_id: str,
    use_loyalty_points: bool = True,
) -> DiscountResult:
    """
    Automatically find and apply the best combination of promotions and loyalty points
    to maximize savings on the cart.
    """
    applicable = [
        p for p in PROMOTIONS
        if (p["category"] == "all" or p["category"] == category.lower())
        and cart_total >= p["min_order"]
    ]

    price = cart_total
    applied = []
    total_saved = 0.0

    non_stack = [p for p in applicable if not p["stackable"]]
    stackable  = [p for p in applicable if p["stackable"]]

    if non_stack:
        def saving(p):
            return price * p["value"] / 100 if p["type"] == "percentage" else p["value"]
        best = max(non_stack, key=saving)
        amt = price * best["value"] / 100 if best["type"] == "percentage" else best["value"]
        price -= amt
        total_saved += amt
        applied.append(f"{best['code']}: {best['description']} = -Rs. {amt:.0f}")

    for p in stackable:
        if price >= p["min_order"]:
            if p["type"] == "fixed":
                price -= p["value"]
                total_saved += p["value"]
                applied.append(f"{p['code']}: {p['description']} = -Rs. {p['value']:.0f}")
            elif p["type"] in ("percentage", "bundle"):
                amt = price * p["value"] / 100
                price -= amt
                total_saved += amt
                applied.append(f"{p['code']}: {p['description']} = -Rs. {amt:.0f}")

    if use_loyalty_points:
        user = next((u for u in USERS if u["user_id"] == user_id), None)
        if user and user["points"] > 0:
            max_pts = min(user["points"], int(price / user["value_per_point"]))
            if max_pts > 0:
                loyalty_discount = max_pts * user["value_per_point"]
                price -= loyalty_discount
                total_saved += loyalty_discount
                applied.append(f"Loyalty ({max_pts} pts) = -Rs. {loyalty_discount:.0f}")

    price = max(price, 0)
    pct   = round((total_saved / cart_total) * 100, 1) if cart_total > 0 else 0

    return DiscountResult(
        original_price=cart_total,
        discounts_applied=applied if applied else ["No applicable discounts found"],
        total_saved=round(total_saved, 2),
        final_price=round(price, 2),
        savings_percentage=pct,
        summary=f"Saved Rs. {total_saved:.0f} ({pct}%) — Final price: Rs. {price:.0f}",
    )


@function_tool
def list_categories(dummy: Optional[str] = None) -> str:
    """List all promotion categories available."""
    cats = sorted(set(p["category"] for p in PROMOTIONS))
    return f"Available categories ({len(cats)}): " + ", ".join(cats)


# ---------------------------------------------------------------------------
# Agent instructions (dynamic — uses context)
# ---------------------------------------------------------------------------

def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    base = (
        "You are a friendly Deal Agent for a Pakistani e-commerce platform. "
        "Your job is to help customers find the best promotions, apply discounts, "
        "and maximize their savings.\n\n"
        "Guidelines:\n"
        "- Use search_promotions to find deals by category or filter\n"
        "- Use get_loyalty_account to check a user's points balance\n"
        "- Use apply_best_discount to calculate maximum savings automatically\n"
        "- Use get_promotion_details for info on a specific promo code\n"
        "- Use list_categories to show available categories\n"
        "- Always show: original price, each discount applied, final price, total saved\n"
        "- Be enthusiastic — saving money is exciting!\n"
        "- Use Rs. for currency (Pakistani Rupees)"
    )
    user = ctx.context
    prefs = []
    if user.category:
        prefs.append(f"Shopping category: {user.category}")
    if user.cart_total is not None:
        prefs.append(f"Cart total: Rs. {user.cart_total:.0f}")
    if prefs:
        base += "\n\nCustomer Info:\n" + "\n".join(prefs)
    return base


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    from dotenv import load_dotenv
    load_dotenv()

    agent_model, provider_label = build_model()

    if not agent_model:
        print("=" * 60)
        print("  Deal Agent  |  Hashir  |  SMIT Batch")
        print("=" * 60)
        print("  No API key found. Set one of these in PowerShell:")
        print('    $env:OPENROUTER_API_KEY = "sk-or-v1-..."  (openrouter.ai)')
        print('    $env:GROQ_API_KEY       = "..."            (console.groq.com — free)')
        print('    $env:GEMINI_API_KEY     = "..."            (aistudio.google.com — free)')
        print("=" * 60)
        print("  Or run offline: python deal_agent_mock.py")
        print("=" * 60)
        return

    print("=" * 60)
    print("  Deal Agent  |  Hashir  |  SMIT Batch")
    print(f"  Provider : {provider_label}")
    print("  Type 'exit' to quit")
    print("=" * 60)

    user_id    = input("\n  Enter User ID  (e.g. U001 - U020) : ").strip() or "U001"
    category   = input("  Category (electronics/fashion/books): ").strip() or "electronics"
    cart_total = input("  Cart Total in Rs.                   : ").strip()
    cart_total = float(cart_total) if cart_total else 1500.0

    user_ctx = UserContext(
        user_id=user_id,
        name=f"Customer {user_id}",
        category=category,
        cart_total=cart_total,
    )

    guardrail_agent = Agent[UserContext](
        name="DealGuardrail",
        instructions=(
            "Determine if the user's query is about deals, discounts, promotions, "
            "loyalty points, savings, coupons, or cart pricing. "
            "Accept: asking about offers, applying discounts, checking points, finding deals. "
            "Reject: math, coding, general knowledge, or anything unrelated to shopping deals."
        ),
        output_type=DealQueryCheck,
        model=agent_model,
    )

    @input_guardrail
    async def deal_relevance_guardrail(
        ctx: RunContextWrapper[UserContext],
        agent: Agent[UserContext],
        input: str | list[TResponseInputItem],
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_deal_query,
        )

    agent = Agent[UserContext](
        name="DealAgent",
        instructions=dynamic_instructions,
        model=agent_model,
        tools=[search_promotions, get_promotion_details, get_loyalty_account, apply_best_discount, list_categories],
        input_guardrails=[deal_relevance_guardrail],
    )

    print("\n  Deal Agent ready! Ask me about deals & discounts.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() in ("exit", "quit"):
            print("Deal Agent: Goodbye! Happy saving!")
            break

        try:
            result = await Runner.run(agent, user_input, context=user_ctx)
            print(f"\nDeal Agent: {result.final_output}\n")
        except InputGuardrailTripwireTriggered:
            print("\nDeal Agent: I only help with deals and discounts! Ask me about promotions, savings, or loyalty points.\n")


if __name__ == "__main__":
    asyncio.run(main())
