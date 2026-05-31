import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta
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
# Data
# ---------------------------------------------------------------------------

DATA: dict = json.load(open("customers.json"))
CUSTOMERS: list[dict] = DATA["customers"]
ORDERS: list[dict] = DATA["orders"]
TIER_RULES: dict = DATA["tier_rules"]

_now = datetime.now()


# ---------------------------------------------------------------------------
# Context
# ---------------------------------------------------------------------------

@dataclass
class UserContext:
    customer_id: str
    name: str
    order_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Structured output types
# ---------------------------------------------------------------------------

class CustomerProfile(BaseModel):
    customer_id: str = Field(description="Customer ID")
    name: str = Field(description="Customer name")
    tier: str = Field(description="Loyalty tier: bronze/silver/gold/platinum")
    points: int = Field(description="Current loyalty points balance")
    total_orders: int = Field(description="Total number of orders placed")
    total_spent: float = Field(description="Total amount spent in Rs.")
    milestones: list[str] = Field(description="Achieved loyalty milestones")
    next_tier: Optional[str] = Field(description="Next tier they can reach")
    points_to_next: Optional[int] = Field(description="Points needed for next tier")
    benefits: list[str] = Field(description="Current tier benefits")
    message: str = Field(description="Personalized message for the customer")


class OrderStatus(BaseModel):
    order_id: str = Field(description="Order ID")
    customer_name: str = Field(description="Customer name")
    status: str = Field(description="Current order status")
    items: list[dict] = Field(description="Items in the order")
    total: float = Field(description="Order total in Rs.")
    order_date: str = Field(description="Date order was placed")
    estimated_delivery: str = Field(description="Estimated delivery date")
    carrier: str = Field(description="Shipping carrier")
    tracking: str = Field(description="Tracking number")
    delivery_address: str = Field(description="Delivery address")
    delay_info: Optional[str] = Field(default=None, description="Information about delays if any")
    update_message: str = Field(description="Proactive update message for the customer")


class SentimentResult(BaseModel):
    sentiment: str = Field(description="Detected sentiment: positive/negative/mixed/neutral")
    confidence: float = Field(description="Confidence score (0-1)")
    emotional_signals: list[str] = Field(description="Emotional signals detected")
    response_tone: str = Field(description="Recommended response tone")


class RetentionAction(BaseModel):
    action_type: str = Field(description="Type: offer/recommendation/loyalty_boost/escalation/engagement")
    customer_id: str = Field(description="Customer ID")
    tier: str = Field(description="Current loyalty tier")
    sentiment: Optional[str] = Field(default=None, description="Current sentiment if available")
    offer: Optional[dict] = Field(default=None, description="Offer details if applicable")
    message: str = Field(description="Personalized retention message")
    priority: str = Field(description="Action priority: urgent/high/normal/low")
    reasoning: str = Field(description="Why this action was chosen")


class PostPurchaseCheck(BaseModel):
    is_post_purchase_query: bool = Field(description="Whether query relates to order tracking, delivery, feedback, loyalty, or post-purchase")
    reasoning: str = Field(description="Why this is or isn't a post-purchase query")


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _find_customer(customer_id: str) -> Optional[dict]:
    return next((c for c in CUSTOMERS if c["customer_id"] == customer_id), None)


def _find_order(order_id: str) -> Optional[dict]:
    return next((o for o in ORDERS if o["order_id"] == order_id), None)


def _get_tier_benefits(tier: str) -> list[str]:
    info = TIER_RULES.get(tier, TIER_RULES["bronze"])
    return info["benefits"]


def _get_next_tier_info(tier: str, points: int):
    tiers = ["bronze", "silver", "gold", "platinum"]
    idx = tiers.index(tier)
    if idx >= len(tiers) - 1:
        return None, 0
    next_tier = tiers[idx + 1]
    next_min = TIER_RULES[next_tier]["min_points"]
    return next_tier, max(0, next_min - points)


def _detect_milestones(customer: dict) -> list[str]:
    existing = set(customer.get("milestones", []))
    new_milestones = []
    orders = [o for o in ORDERS if o["customer_id"] == customer["customer_id"]]
    delivered = [o for o in orders if o["status"] == "delivered"]
    total_delivered = len(delivered)

    if total_delivered == 1 and "first_purchase" not in existing:
        new_milestones.append("first_purchase")
    if total_delivered >= 2 and "second_purchase" not in existing:
        new_milestones.append("second_purchase")
    if total_delivered >= 5 and "5_orders" not in existing:
        new_milestones.append("5_orders")
    if total_delivered >= 10 and "10_orders" not in existing:
        new_milestones.append("10_orders")
    if total_delivered >= 20 and "20_orders" not in existing:
        new_milestones.append("20_orders")

    if customer["tier"] in ("gold", "platinum") and "vip_eligible" not in existing:
        new_milestones.append("vip_eligible")
    if customer["tier"] == "platinum" and "platinum" not in existing:
        new_milestones.append("vip")
        new_milestones.append("platinum")

    return new_milestones


def _calculate_loyalty_message(customer: dict, new_milestones: list[str]) -> str:
    if "first_purchase" in new_milestones:
        return f"Welcome to the family {customer['name']}! Your first order is on its way. Earn points with every purchase!"
    if "second_purchase" in new_milestones:
        return f"You're back, {customer['name']}! Thanks for your second order — loyalty starts here. You've earned bonus points!"
    if "5_orders" in new_milestones:
        return f"Five orders strong, {customer['name']}! You're now a regular. Keep shopping to unlock Silver tier!"
    if "10_orders" in new_milestones:
        return f"Double digits! 10 orders with us, {customer['name']}. We appreciate your trust. VIP perks await!"
    if "20_orders" in new_milestones:
        return f"Incredible — 20 orders, {customer['name']}! You're one of our most valued customers."
    if "platinum" in new_milestones:
        return f"Platinum status unlocked, {customer['name']}! You now have a dedicated manager and exclusive benefits."
    return None


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@function_tool
def get_customer_profile(
    ctx: RunContextWrapper[UserContext],
    customer_id: str,
) -> CustomerProfile:
    """Get loyalty profile and benefits for a customer."""
    customer = _find_customer(customer_id)
    if not customer:
        return CustomerProfile(
            customer_id=customer_id, name="Unknown", tier="bronze",
            points=0, total_orders=0, total_spent=0, milestones=[],
            next_tier="silver", points_to_next=1000, benefits=_get_tier_benefits("bronze"),
            message="No account found. Shop with us to start earning loyalty points!",
        )

    new_ms = _detect_milestones(customer)
    msg = _calculate_loyalty_message(customer, new_ms)
    if not msg:
        msg = f"Welcome back, {customer['name']}! You're a {customer['tier'].upper()} member."

    next_tier, pts_needed = _get_next_tier_info(customer["tier"], customer["points"])
    return CustomerProfile(
        customer_id=customer["customer_id"],
        name=customer["name"],
        tier=customer["tier"],
        points=customer["points"],
        total_orders=customer["total_orders"],
        total_spent=customer["total_spent"],
        milestones=customer.get("milestones", []) + new_ms,
        next_tier=next_tier,
        points_to_next=pts_needed if next_tier else None,
        benefits=_get_tier_benefits(customer["tier"]),
        message=msg,
    )


@function_tool
def track_order(
    ctx: RunContextWrapper[UserContext],
    order_id: str,
) -> OrderStatus:
    """Track the current status of an order by its ID."""
    order = _find_order(order_id)
    if not order:
        return OrderStatus(
            order_id=order_id, customer_name="Unknown", status="not_found",
            items=[], total=0, order_date="", estimated_delivery="",
            carrier="", tracking="", delivery_address="",
            update_message=f"No order found with ID {order_id}.",
        )

    customer = _find_customer(order["customer_id"])
    name = customer["name"] if customer else "Customer"

    delay = None
    if order.get("status") == "delayed":
        delay = f"Delay: {order.get('delay_reason', 'Unknown')}. Expected by {order.get('delay_expected_resolution', 'TBD')}."
        msg = f"Hello {name}, we apologise — your order {order_id} is delayed due to {order.get('delay_reason', 'operational reasons')}. We expect to resolve by {order.get('delay_expected_resolution', 'soon')}. We'll keep you updated."
    elif order["status"] == "confirmed":
        msg = f"Hi {name}, order {order_id} confirmed! We're preparing your items. Estimated delivery: {order['estimated_delivery']}."
    elif order["status"] == "shipped":
        msg = f"Great news {name}, order {order_id} has shipped via {order['carrier']}! Tracking: {order['tracking']}. Expected by {order['estimated_delivery']}."
    elif order["status"] == "in_transit":
        msg = f"Your order {order_id} is in transit, {name}! {order['carrier']} tracking: {order['tracking']}. On track for {order['estimated_delivery']}."
    elif order["status"] == "delivered":
        msg = f"Delivered! Order {order_id} arrived, {name}. We'd love to hear your feedback!"
    else:
        msg = f"Order {order_id} status: {order['status']}."

    return OrderStatus(
        order_id=order["order_id"],
        customer_name=name,
        status=order["status"],
        items=order["items"],
        total=order["total"],
        order_date=order["order_date"],
        estimated_delivery=order["estimated_delivery"],
        carrier=order["carrier"],
        tracking=order["tracking"],
        delivery_address=order["delivery_address"],
        delay_info=delay,
        update_message=msg,
    )


@function_tool
def analyze_feedback_sentiment(
    ctx: RunContextWrapper[UserContext],
    feedback_text: str,
) -> SentimentResult:
    """Analyze the sentiment of a customer's feedback or review text."""
    text = feedback_text.lower()

    positive_words = ["amazing", "great", "love", "perfect", "beautiful", "happy", "excellent",
                      "wonderful", "fantastic", "best", "impressed", "satisfied", "comfortable",
                      "fast", "good", "nice"]
    negative_words = ["disappointed", "stopped working", "broken", "poor", "bad", "worst",
                      "terrible", "frustrating", "defective", "damaged", "useless", "return",
                      "refund", "waste", "issue", "different", "wrong", "problem"]
    mixed_signals = ["but", "however", "although", "slightly", "still", "overall"]

    pos_count = sum(1 for w in positive_words if w in text)
    neg_count = sum(1 for w in negative_words if w in text)
    is_mixed = any(s in text for s in mixed_signals) and pos_count > 0 and neg_count > 0

    if is_mixed:
        sentiment = "mixed"
        confidence = 0.75
        signals = ["contains both positive and negative elements"]
        tone = "appreciative and problem-solving"
    elif pos_count > neg_count:
        sentiment = "positive"
        confidence = min(0.5 + pos_count * 0.15, 0.95)
        signals = [w for w in positive_words if w in text][:3]
        tone = "warm and grateful"
    elif neg_count > pos_count:
        sentiment = "negative"
        confidence = min(0.5 + neg_count * 0.15, 0.95)
        signals = [w for w in negative_words if w in text][:3]
        tone = "empathetic and urgent"
    else:
        sentiment = "neutral"
        confidence = 0.5
        signals = ["factual or short feedback"]
        tone = "helpful and neutral"

    return SentimentResult(
        sentiment=sentiment,
        confidence=round(confidence, 2),
        emotional_signals=signals,
        response_tone=tone,
    )


@function_tool
def generate_retention_action(
    ctx: RunContextWrapper[UserContext],
    customer_id: str,
) -> RetentionAction:
    """Generate a personalized retention action for a customer based on their
    profile, recent orders, and any feedback sentiment."""
    customer = _find_customer(customer_id)
    if not customer:
        return RetentionAction(
            action_type="engagement",
            customer_id=customer_id,
            tier="bronze",
            offer=None,
            message="Welcome! Start shopping to earn loyalty points.",
            priority="low",
            reasoning="New customer with no order history.",
        )

    orders = [o for o in ORDERS if o["customer_id"] == customer_id]
    active_orders = [o for o in orders if o["status"] in ("confirmed", "shipped", "in_transit", "delayed")]
    delivered = [o for o in orders if o["status"] == "delivered"]
    has_feedback = [o for o in delivered if o.get("feedback")]

    # Check for delivery issues first
    delayed_orders = [o for o in active_orders if o["status"] == "delayed"]
    if delayed_orders:
        o = delayed_orders[0]
        return RetentionAction(
            action_type="escalation",
            customer_id=customer_id,
            tier=customer["tier"],
            offer={"type": "apology", "details": f"Rs. 200 off on next order for delay on {o['order_id']}"},
            message=f"We apologise for the delay on {o['order_id']}. Here's Rs. 200 off your next purchase as our apology.",
            priority="urgent",
            reasoning="Active delay detected — prioritise issue resolution before marketing.",
        )

    # Negative feedback — escalate and offer
    for o in delivered:
        if o.get("sentiment") == "negative":
            return RetentionAction(
                action_type="offer",
                customer_id=customer_id,
                tier=customer["tier"],
                sentiment="negative",
                offer={"type": "discount", "value": 15, "unit": "percent", "code": "WEARE15",
                       "details": "15% off on next order as apology"},
                message=f"{customer['name']}, we're sorry about your experience with {o['items'][0]['product']}. Here's 15% off your next order.",
                priority="urgent",
                reasoning="Negative sentiment detected — immediate retention offer to prevent churn.",
            )

    # Mixed feedback — engage and follow up
    for o in delivered:
        if o.get("sentiment") == "mixed":
            return RetentionAction(
                action_type="engagement",
                customer_id=customer_id,
                tier=customer["tier"],
                sentiment="mixed",
                offer={"type": "points_boost", "value": 200, "details": "200 bonus loyalty points"},
                message=f"{customer['name']}, thanks for your honest feedback! We've added 200 bonus points to your account.",
                priority="normal",
                reasoning="Mixed sentiment — positive reinforcement to build goodwill.",
            )

    # Loyalty milestones
    new_ms = _detect_milestones(customer)
    if "second_purchase" in new_ms:
        return RetentionAction(
            action_type="loyalty_boost",
            customer_id=customer_id,
            tier=customer["tier"],
            offer={"type": "points_boost", "value": 500, "details": "500 bonus points for 2nd purchase"},
            message=f"Congratulations {customer['name']} on your second purchase! You've earned 500 bonus points!",
            priority="high",
            reasoning="Second purchase milestone — reward to encourage repeat buying.",
        )

    # VIP-eligible
    if "vip_eligible" in customer.get("milestones", []) and customer["tier"] == "gold":
        return RetentionAction(
            action_type="loyalty_boost",
            customer_id=customer_id,
            tier=customer["tier"],
            offer={"type": "upgrade", "details": "Complimentary upgrade to Platinum on next purchase over Rs. 5000"},
            message=f"{customer['name']}, you're VIP-eligible! Spend Rs. 5000 more and unlock Platinum with a dedicated manager!",
            priority="high",
            reasoning="VIP-eligible customer — nudge toward next tier.",
        )

    # Based on order value
    recent = sorted(orders, key=lambda o: o["order_date"], reverse=True)
    if recent and recent[0]["total"] > 10000:
        return RetentionAction(
            action_type="recommendation",
            customer_id=customer_id,
            tier=customer["tier"],
            offer={"type": "cross_sell", "details": "Recommend accessories based on recent high-value purchase"},
            message=f"{customer['name']}, check out our accessories that pair perfectly with your recent purchase!",
            priority="normal",
            reasoning="High-value recent order — cross-sell complementary products.",
        )

    # New buyer — engagement
    if customer["total_orders"] <= 2:
        return RetentionAction(
            action_type="engagement",
            customer_id=customer_id,
            tier=customer["tier"],
            offer={"type": "welcome", "details": "10% off on next order with code WELCOME10"},
            message=f"Welcome {customer['name']}! Use WELCOME10 for 10% off your next order.",
            priority="normal",
            reasoning="New buyer — incentive to make another purchase.",
        )

    return RetentionAction(
        action_type="engagement",
        customer_id=customer_id,
        tier=customer["tier"],
        message=f"{customer['name']}, thank you for being a loyal {customer['tier'].upper()} member! We value you.",
        priority="low",
        reasoning="Regular engagement — maintain relationship.",
    )


@function_tool
def record_customer_feedback(
    ctx: RunContextWrapper[UserContext],
    order_id: str,
    feedback_text: str,
    rating: Optional[int] = None,
) -> str:
    """Record feedback from a customer for a specific order."""
    order = _find_order(order_id)
    if not order:
        return f"Order {order_id} not found."
    order["feedback"] = feedback_text
    result = analyze_feedback_sentiment(ctx, feedback_text)
    order["sentiment"] = result.sentiment
    note = f"Rating: {rating}/5. " if rating else ""
    return f"Feedback recorded for {order_id}. {note}Sentiment: {result.sentiment.upper()}. Response tone: {result.response_tone}."


# ---------------------------------------------------------------------------
# Agent instructions
# ---------------------------------------------------------------------------

def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    return (
        "You are the Post-Purchase Loyalty & Retention Agent, a post-purchase lifecycle specialist.\n\n"
        "Your job is to manage customers immediately after they complete a purchase through delivery, "
        "unboxing, product experience, and early retention.\n\n"
        "Key responsibilities:\n"
        "- Track order status and send proactive shipping updates\n"
        "- Identify customer loyalty tier (bronze/silver/gold/platinum) and celebrate milestones\n"
        "- Analyze feedback sentiment (positive/negative/mixed/neutral) and respond appropriately\n"
        "- Generate personalized retention offers, rewards, and re-engagement strategies\n"
        "- Escalate delivery issues or dissatisfaction immediately\n\n"
        "Decision rules:\n"
        "- Always prioritize issue resolution before marketing\n"
        "- Never send promotions without behavioral or sentiment justification\n"
        "- Keep messaging minimal but high-impact\n"
        "- Be warm, emotionally aware, and proactive\n\n"
        "Tools available:\n"
        "- get_customer_profile — view loyalty tier, points, milestones, benefits\n"
        "- track_order — get order status and send proactive update\n"
        "- analyze_feedback_sentiment — detect sentiment in feedback text\n"
        "- generate_retention_action — create personalized retention strategy\n"
        "- record_customer_feedback — store feedback and auto-analyze sentiment\n\n"
        "Always structure responses clearly and be helpful. Use the structured output format "
        "with Customer Status, Action Taken, Retention Plan, and Reasoning."
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    from dotenv import load_dotenv
    load_dotenv()

    agent_model, provider_label = build_model()

    if not agent_model:
        print("=" * 60)
        print("  Post-Purchase Loyalty & Retention Agent")
        print("  Built by Hashir | SMIT Batch")
        print("=" * 60)
        print("  No API key found. Set one of these in PowerShell:")
        print('    $env:OPENROUTER_API_KEY = "sk-or-v1-..."  (openrouter.ai)')
        print('    $env:GROQ_API_KEY       = "..."            (console.groq.com — free)')
        print('    $env:GEMINI_API_KEY     = "..."            (aistudio.google.com — free)')
        print("=" * 60)
        print("  Or run offline: python post_purchase_agent_mock.py")
        print("=" * 60)
        return

    print("=" * 60)
    print("  Post-Purchase Loyalty & Retention Agent")
    print("  Built by Hashir | SMIT Batch")
    print(f"  Provider: {provider_label}")
    print("  Type 'exit' to quit")
    print("=" * 60)

    customer_id = input("\n  Enter Customer ID (C001-C008): ").strip() or "C001"
    order_id = input("  Enter Order ID (optional): ").strip() or None

    user_ctx = UserContext(
        customer_id=customer_id,
        name=_find_customer(customer_id)["name"] if _find_customer(customer_id) else "Customer",
        order_id=order_id,
    )

    guardrail_agent = Agent[UserContext](
        name="PostPurchaseGuardrail",
        instructions=(
            "Determine if the user's query relates to post-purchase activities: "
            "order tracking, delivery status, shipping updates, feedback and reviews, "
            "loyalty points, tier benefits, milestones, returns, complaints, "
            "product experience, or retention offers. "
            "Reject: math, coding, general knowledge, pre-purchase browsing, or unrelated chat."
        ),
        output_type=PostPurchaseCheck,
        model=agent_model,
    )

    @input_guardrail
    async def post_purchase_relevance_guardrail(
        ctx: RunContextWrapper[UserContext],
        agent: Agent[UserContext],
        input: str | list[TResponseInputItem],
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_post_purchase_query,
        )

    agent = Agent[UserContext](
        name="PostPurchaseRetentionAgent",
        instructions=dynamic_instructions,
        model=agent_model,
        tools=[
            get_customer_profile,
            track_order,
            analyze_feedback_sentiment,
            generate_retention_action,
            record_customer_feedback,
        ],
        input_guardrails=[post_purchase_relevance_guardrail],
    )

    print(f"\n  Agent ready for {user_ctx.name}! Ask about orders, loyalty, or feedback.\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input or user_input.lower() in ("exit", "quit"):
            print("Retention Agent: Goodbye! We'll keep taking care of your experience.")
            break

        try:
            result = await Runner.run(agent, user_input, context=user_ctx)
            print(f"\nRetention Agent: {result.final_output}\n")
        except InputGuardrailTripwireTriggered:
            print("\nRetention Agent: I can only help with post-purchase topics — order tracking, delivery, feedback, loyalty, and retention offers.\n")


if __name__ == "__main__":
    asyncio.run(main())
